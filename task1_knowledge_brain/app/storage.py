import os
import json
import sqlite3
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pathlib import Path
from task1_knowledge_brain.app.config import settings

def get_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def compute_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

class Database:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or settings.db_path
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        # Enable WAL mode for high performance concurrency
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                body_text TEXT NOT NULL,
                published_at TEXT,
                images_json TEXT NOT NULL DEFAULT '[]',
                content_hash TEXT NOT NULL,
                crawled_at TEXT NOT NULL,
                is_expert_answer INTEGER NOT NULL DEFAULT 0
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER NOT NULL,
                chunk_index INTEGER NOT NULL,
                text TEXT NOT NULL,
                FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS crawl_state (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS expert_tasks (
                task_id TEXT PRIMARY KEY,
                question TEXT NOT NULL,
                context TEXT,
                status TEXT NOT NULL DEFAULT 'pending_review',
                suggested_answer TEXT,
                approved_answer TEXT,
                expert_name TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT
            );
            """)

            # Index for fast URL lookup and chunk searching
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_url ON articles(url);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_article ON chunks(article_id);")
            conn.commit()

    def get_article_count(self) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM articles;")
            return cursor.fetchone()[0]

    def get_last_refresh_time(self) -> Optional[str]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM crawl_state WHERE key = 'last_refresh_at';")
            row = cursor.fetchone()
            return row["value"] if row else None

    def set_crawl_state(self, key: str, value: str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO crawl_state (key, value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at;
            """, (key, value, get_now_iso()))
            conn.commit()

    def get_all_article_urls(self) -> Dict[str, str]:
        """Returns dict of {url: content_hash}"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT url, content_hash FROM articles WHERE is_expert_answer = 0;")
            return {row["url"]: row["content_hash"] for row in cursor.fetchall()}

    def upsert_article(
        self,
        url: str,
        title: str,
        body_text: str,
        published_at: Optional[str] = None,
        images: Optional[List[str]] = None,
        is_expert_answer: bool = False,
    ) -> Tuple[int, bool]:
        """
        Inserts or updates an article and recreates its chunks.
        Returns (article_id, is_new)
        """
        content_hash = compute_hash(f"{title}\n{body_text}")
        images_json = json.dumps(images or [])
        now = get_now_iso()

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, content_hash FROM articles WHERE url = ?;", (url,))
            existing = cursor.fetchone()

            if existing:
                article_id = existing["id"]
                if existing["content_hash"] == content_hash:
                    # Content unchanged
                    return article_id, False
                # Update article
                cursor.execute("""
                UPDATE articles
                SET title = ?, body_text = ?, published_at = ?, images_json = ?,
                    content_hash = ?, crawled_at = ?, is_expert_answer = ?
                WHERE id = ?;
                """, (title, body_text, published_at, images_json, content_hash, now, int(is_expert_answer), article_id))
                cursor.execute("DELETE FROM chunks WHERE article_id = ?;", (article_id,))
                is_new = False
            else:
                cursor.execute("""
                INSERT INTO articles (url, title, body_text, published_at, images_json, content_hash, crawled_at, is_expert_answer)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """, (url, title, body_text, published_at, images_json, content_hash, now, int(is_expert_answer)))
                article_id = cursor.lastrowid
                is_new = True

            # Create Chunks (sliding window: ~250 words per chunk with 40 words overlap)
            words = body_text.split()
            chunk_size = 250
            overlap = 40
            chunk_index = 0
            i = 0
            if not words:
                words = [title]

            while i < len(words):
                chunk_words = words[i : i + chunk_size]
                chunk_text = " ".join(chunk_words)
                cursor.execute("""
                INSERT INTO chunks (article_id, chunk_index, text)
                VALUES (?, ?, ?);
                """, (article_id, chunk_index, chunk_text))
                chunk_index += 1
                if i + chunk_size >= len(words):
                    break
                i += (chunk_size - overlap)

            conn.commit()
            return article_id, is_new

    def remove_articles_by_urls(self, urls: List[str]) -> int:
        if not urls:
            return 0
        with self.get_connection() as conn:
            cursor = conn.cursor()
            placeholders = ",".join("?" for _ in urls)
            cursor.execute(f"DELETE FROM articles WHERE url IN ({placeholders});", urls)
            removed = cursor.rowcount
            conn.commit()
            return removed

    def get_all_chunks_with_articles(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT c.id AS chunk_id, c.text AS chunk_text, a.id AS article_id,
                   a.url, a.title, a.published_at, a.images_json, a.is_expert_answer
            FROM chunks c
            JOIN articles a ON c.article_id = a.id;
            """)
            rows = cursor.fetchall()
            return [
                {
                    "chunk_id": row["chunk_id"],
                    "chunk_text": row["chunk_text"],
                    "article_id": row["article_id"],
                    "url": row["url"],
                    "title": row["title"],
                    "published_at": row["published_at"],
                    "images": json.loads(row["images_json"]),
                    "is_expert_answer": bool(row["is_expert_answer"]),
                }
                for row in rows
            ]

    def create_expert_task(self, task_id: str, question: str, context: Optional[str] = None, suggested_answer: Optional[str] = None) -> Dict[str, Any]:
        now = get_now_iso()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO expert_tasks (task_id, question, context, status, suggested_answer, created_at)
            VALUES (?, ?, ?, 'pending_review', ?, ?);
            """, (task_id, question, context, suggested_answer, now))
            conn.commit()
        return {
            "task_id": task_id,
            "question": question,
            "context": context,
            "status": "pending_review",
            "created_at": now,
        }

    def answer_expert_task(self, task_id: str, approved_answer: str, expert_name: str, source_reference: str) -> Optional[Dict[str, Any]]:
        now = get_now_iso()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT question FROM expert_tasks WHERE task_id = ?;", (task_id,))
            row = cursor.fetchone()
            if not row:
                return None
            question = row["question"]

            cursor.execute("""
            UPDATE expert_tasks
            SET approved_answer = ?, expert_name = ?, status = 'incorporated', updated_at = ?
            WHERE task_id = ?;
            """, (approved_answer, expert_name, now, task_id))
            conn.commit()

        # Immediately index this approved expert answer into the retrieval database!
        doc_url = f"https://support.brilliantdirectories.com/expert-answers/{task_id}"
        doc_title = f"Expert Verified Answer: {question}"
        body = f"Question: {question}\n\nApproved Expert Answer (Verified by {expert_name} - {source_reference}):\n{approved_answer}"
        article_id, _ = self.upsert_article(
            url=doc_url,
            title=doc_title,
            body_text=body,
            published_at=now,
            images=[],
            is_expert_answer=True,
        )

        return {
            "task_id": task_id,
            "status": "incorporated",
            "indexed_article_id": f"article_{article_id}",
            "updated_at": now,
        }

    def get_expert_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM expert_tasks WHERE task_id = ?;", (task_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return dict(row)

db = Database()
