import time
import urllib.request
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Tuple
from task1_knowledge_brain.app.config import settings
from task1_knowledge_brain.app.storage import db, get_now_iso
from task1_knowledge_brain.app.extractor import extract_article_data
from task1_knowledge_brain.app.retrieval import retriever

USER_AGENT = "AITechConsultantBot/1.0 (+https://github.com/ai-tech-consultant; research-mvp)"

def fetch_sitemap_urls(sitemap_url: str) -> List[str]:
    """Fetch and parse all article URLs from sitemap.xml."""
    req = urllib.request.Request(
        sitemap_url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/xml, text/xml"}
    )
    with urllib.request.urlopen(req, timeout=15) as res:
        xml_data = res.read()

    tree = ET.fromstring(xml_data)
    # Support standard sitemap namespace
    namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    loc_elements = tree.findall(".//sm:loc", namespace)
    if not loc_elements:
        loc_elements = tree.findall(".//loc")

    urls = [elem.text.strip() for elem in loc_elements if elem.text and elem.text.strip()]
    # Filter for solution articles
    article_urls = [u for u in urls if "/support/solutions/articles/" in u or "/support/solutions/" in u]
    return article_urls if article_urls else urls

def fetch_page_content(url: str, max_retries: int = 3, backoff_factor: float = 0.5) -> Tuple[str, int]:
    """Fetch a single page with exponential backoff retries."""
    last_exception = None
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"}
            )
            with urllib.request.urlopen(req, timeout=12) as response:
                status_code = response.status
                content = response.read().decode("utf-8", errors="ignore")
                return content, status_code
        except Exception as e:
            last_exception = e
            time.sleep(backoff_factor * (2 ** attempt))

    raise RuntimeError(f"Failed to fetch {url} after {max_retries} attempts: {last_exception}")

class CrawlerService:
    def __init__(self):
        self.sitemap_url = settings.sitemap_url
        self.batch_size = settings.crawl_batch_size
        self.delay_sec = settings.crawl_delay_sec

    def run_refresh(self, max_pages: int = 25, force_full: bool = False) -> Dict[str, Any]:
        """
        Executes bounded, polite, resumable incremental refresh.
        Detects:
        - New pages
        - Updated pages
        - Removed pages
        """
        start_time = time.time()
        try:
            sitemap_urls = fetch_sitemap_urls(self.sitemap_url)
        except Exception as e:
            # If network error, return safe error report
            return {
                "pages_scanned": 0,
                "pages_added": 0,
                "pages_updated": 0,
                "pages_removed": 0,
                "elapsed_seconds": round(time.time() - start_time, 2),
                "total_articles_in_db": db.get_article_count(),
                "error": str(e),
            }

        existing_urls_map = db.get_all_article_urls()
        current_sitemap_set = set(sitemap_urls)

        # 1. Detect removed pages
        removed_count = 0
        if force_full:
            urls_to_remove = [u for u in existing_urls_map.keys() if u not in current_sitemap_set]
            if urls_to_remove:
                removed_count = db.remove_articles_by_urls(urls_to_remove)

        # 2. Resumable pointer for polite bounded batching
        cursor_str = db.get_last_refresh_time()
        last_index_val = 0
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM crawl_state WHERE key = 'last_crawl_index';")
            row = cursor.fetchone()
            if row and not force_full:
                try:
                    last_index_val = int(row["value"])
                except ValueError:
                    last_index_val = 0

        # Slice bounded batch
        if last_index_val >= len(sitemap_urls):
            last_index_val = 0

        end_index = min(last_index_val + max_pages, len(sitemap_urls))
        batch_urls = sitemap_urls[last_index_val:end_index]

        added_count = 0
        updated_count = 0
        scanned_count = 0

        for url in batch_urls:
            scanned_count += 1
            try:
                # Polite crawl delay
                time.sleep(self.delay_sec)
                html, status = fetch_page_content(url)
                if status == 200:
                    data = extract_article_data(html, url)
                    if data["body_text"]:
                        _, is_new = db.upsert_article(
                            url=data["url"],
                            title=data["title"],
                            body_text=data["body_text"],
                            published_at=data["published_at"],
                            images=data["images"],
                            is_expert_answer=False,
                        )
                        if is_new:
                            added_count += 1
                        else:
                            updated_count += 1
            except Exception as crawl_err:
                # Skip and log individual page failure without aborting entire batch
                continue

        # Update crawl state
        next_index = end_index if end_index < len(sitemap_urls) else 0
        db.set_crawl_state("last_crawl_index", str(next_index))
        db.set_crawl_state("last_refresh_at", get_now_iso())

        # Rebuild search index with newly crawled chunks
        retriever.build_index()

        elapsed = round(time.time() - start_time, 2)
        return {
            "pages_scanned": scanned_count,
            "pages_added": added_count,
            "pages_updated": updated_count,
            "pages_removed": removed_count,
            "elapsed_seconds": elapsed,
            "total_articles_in_db": db.get_article_count(),
        }

crawler = CrawlerService()
