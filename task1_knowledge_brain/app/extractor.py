import re
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup

def clean_title(raw_title: str) -> str:
    """Clean site suffix from article titles."""
    if not raw_title:
        return "Untitled Article"
    cleaned = raw_title.replace("| Brilliant Directories Documentation | BD Support", "")
    cleaned = cleaned.replace("| Brilliant Directories Documentation", "")
    cleaned = cleaned.replace("Brilliant Directories Support", "")
    cleaned = cleaned.replace("- Brilliant Directories", "")
    return cleaned.strip(" -|:\n\t")

def extract_article_data(html_content: str, source_url: str) -> Dict[str, Any]:
    """
    Extract structured article data from Brilliant Directories solution article HTML.
    Returns:
      url, title, body_text, timestamp, images, word_count
    """
    soup = BeautifulSoup(html_content, "html.parser")

    # 1. Extract Title
    title = "Untitled Article"
    h1_tag = soup.find("h1", class_=lambda c: c and "article-title" in c) or soup.find("h1")
    if h1_tag and h1_tag.get_text(strip=True):
        title = clean_title(h1_tag.get_text(strip=True))
    elif soup.title and soup.title.string:
        title = clean_title(soup.title.string)

    # 2. Extract Timestamp
    timestamp: Optional[str] = None
    time_tag = soup.find("time")
    if time_tag:
        timestamp = time_tag.get("datetime") or time_tag.get_text(strip=True)
    if not timestamp:
        # Check meta tags
        meta_time = soup.find("meta", property="article:modified_time") or soup.find("meta", property="article:published_time")
        if meta_time and meta_time.get("content"):
            timestamp = meta_time.get("content")

    # 3. Locate article body container
    article_body = (
        soup.find("div", class_=lambda c: c and ("article-body" in c or "solution-body" in c or "article__body" in c))
        or soup.find("article")
        or soup.find("main")
        or soup.find("div", id="content")
    )
    if not article_body:
        article_body = soup.body if soup.body else soup

    # Extract images inside article body
    images: List[str] = []
    for img in article_body.find_all("img"):
        src = img.get("src") or img.get("data-src")
        if src and not src.startswith("data:") and not any(ic in src.lower() for ic in ["icon", "logo", "avatar", "spacer", "blank.gif"]):
            if src.startswith("//"):
                src = "https:" + src
            images.append(src)
    # Deduplicate while preserving order
    images = list(dict.fromkeys(images))[:10]

    # Clean out unwanted tags from body
    for tag in article_body.find_all(["script", "style", "nav", "footer", "header", "aside", "form"]):
        tag.decompose()

    # Extract text
    body_text = article_body.get_text(separator="\n", strip=True)
    # Normalize multiple newlines and spaces
    body_text = re.sub(r"\n\s*\n+", "\n\n", body_text).strip()

    word_count = len(body_text.split())

    return {
        "url": source_url,
        "title": title,
        "body_text": body_text,
        "published_at": timestamp,
        "images": images,
        "word_count": word_count,
    }
