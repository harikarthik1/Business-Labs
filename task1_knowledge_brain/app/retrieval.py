import re
import math
from typing import List, Dict, Any, Tuple
from task1_knowledge_brain.app.storage import db
from task1_knowledge_brain.app.schemas import SourceCitation

STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
    "aren't", "as", "at", "be", "because", "been", "before", "being", "below", "between", "both",
    "but", "by", "can", "can't", "cannot", "could", "couldn't", "did", "didn't", "do", "does",
    "doesn't", "doing", "don't", "down", "during", "each", "few", "for", "from", "further",
    "had", "hadn't", "has", "hasn't", "have", "haven't", "having", "he", "her", "here", "hers",
    "herself", "him", "himself", "his", "how", "i", "if", "in", "into", "is", "isn't", "it",
    "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself", "no", "nor",
    "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours", "ourselves",
    "out", "over", "own", "same", "shan't", "she", "should", "shouldn't", "so", "some", "such",
    "than", "that", "the", "their", "theirs", "them", "themselves", "then", "there", "these",
    "they", "this", "those", "through", "to", "too", "under", "until", "up", "very", "was",
    "wasn't", "we", "were", "weren't", "what", "when", "where", "which", "while", "who", "whom",
    "why", "with", "won't", "would", "wouldn't", "you", "your", "yours", "yourself", "yourselves",
    # Domain generic terms that occur in nearly every BD document title/body
    "brilliant", "directories", "directory", "bd", "website", "site"
}

def tokenize(text: str) -> List[str]:
    clean = re.sub(r"[^\w\s]", " ", text.lower())
    tokens = clean.split()
    return [t for t in tokens if len(t) > 1 and t not in STOPWORDS]

class BM25Index:
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus: List[Dict[str, Any]] = []
        self.doc_lengths: List[int] = []
        self.avg_doc_len: float = 0.0
        self.doc_freqs: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self.is_indexed: bool = False

    def build_index(self):
        chunks = db.get_all_chunks_with_articles()
        self.corpus = chunks
        self.doc_lengths = []
        self.doc_freqs = {}
        self.idf = {}

        if not self.corpus:
            self.avg_doc_len = 0.0
            self.is_indexed = True
            return

        total_tokens = 0
        for doc in self.corpus:
            text = f"{doc['title']} {doc['chunk_text']}"
            tokens = tokenize(text)
            self.doc_lengths.append(len(tokens))
            total_tokens += len(tokens)
            unique_tokens = set(tokens)
            for t in unique_tokens:
                self.doc_freqs[t] = self.doc_freqs.get(t, 0) + 1

        n_docs = len(self.corpus)
        self.avg_doc_len = total_tokens / max(n_docs, 1)

        for token, df in self.doc_freqs.items():
            # BM25 standard IDF with smoothing
            self.idf[token] = math.log(1.0 + (n_docs - df + 0.5) / (df + 0.5))

        self.is_indexed = True

    def search(self, query: str, top_k: int = 4, confidence_threshold: float = 0.35) -> Tuple[List[SourceCitation], bool, float]:
        """
        Returns (citations, has_sufficient_evidence, top_confidence)
        """
        if not self.is_indexed or not self.corpus:
            self.build_index()

        if not self.corpus:
            return [], False, 0.0

        query_tokens = tokenize(query)
        if not query_tokens:
            return [], False, 0.0

        scores: List[float] = [0.0] * len(self.corpus)

        for i, doc in enumerate(self.corpus):
            doc_text = f"{doc['title']} {doc['chunk_text']}"
            tokens = tokenize(doc_text)
            doc_len = self.doc_lengths[i]
            if doc_len == 0:
                continue

            # Token frequencies in this document
            tf: Dict[str, int] = {}
            for t in tokens:
                tf[t] = tf.get(t, 0) + 1

            doc_score = 0.0
            matched_terms = 0

            for q in query_tokens:
                if q in tf:
                    matched_terms += 1
                    term_freq = tf[q]
                    idf_val = self.idf.get(q, 0.5)
                    # BM25 formula
                    num = term_freq * (self.k1 + 1.0)
                    denom = term_freq + self.k1 * (1.0 - self.b + self.b * (doc_len / max(self.avg_doc_len, 1.0)))
                    doc_score += idf_val * (num / denom)

                    # Boost if term in title
                    if q in doc["title"].lower():
                        doc_score += 1.8

            # Extra boost for expert verified answers
            if doc.get("is_expert_answer"):
                doc_score *= 1.35

            # Require that at least a reasonable portion of query terms match
            term_overlap_ratio = matched_terms / max(len(query_tokens), 1)
            if term_overlap_ratio < 0.4:
                doc_score *= 0.15
            else:
                doc_score *= (0.5 + 0.5 * term_overlap_ratio)

            scores[i] = doc_score

        max_score = max(scores) if scores else 0.0
        if max_score <= 0.0:
            return [], False, 0.0

        # Rank documents
        ranked_indices = sorted(range(len(scores)), key=lambda idx: scores[idx], reverse=True)

        # Normalize score into [0.0, 1.0] range using a sigmoid-like curve
        # Typical raw BM25 max scores range from 2 to 20
        normalized_scores = [min(round(score / (score + 5.0), 3), 1.0) for score in scores]

        # Deduplicate by article URL so we cite distinct articles
        seen_urls = set()
        citations: List[SourceCitation] = []

        for idx in ranked_indices:
            score = normalized_scores[idx]
            if score < 0.2:
                break
            doc = self.corpus[idx]
            url = doc["url"]
            if url in seen_urls:
                continue
            seen_urls.add(url)

            # Create clean snippet from chunk
            snippet_words = doc["chunk_text"].split()[:55]
            snippet = " ".join(snippet_words) + ("..." if len(doc["chunk_text"].split()) > 55 else "")

            citations.append(
                SourceCitation(
                    title=doc["title"],
                    url=doc["url"],
                    relevance_score=score,
                    snippet=snippet,
                    published_at=doc["published_at"],
                    images=doc.get("images", [])[:3],
                )
            )
            if len(citations) >= top_k:
                break

        top_confidence = citations[0].relevance_score if citations else 0.0
        has_sufficient = bool(citations and top_confidence >= confidence_threshold)

        return citations, has_sufficient, top_confidence

retriever = BM25Index()
