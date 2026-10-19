import pytest
from task1_knowledge_brain.app.extractor import extract_article_data, clean_title
from task1_knowledge_brain.app.storage import db
from task1_knowledge_brain.app.retrieval import retriever

def test_clean_title():
    raw = "Can I Send A Mass Email Campaign Using Brilliant Directories? | Brilliant Directories Documentation | BD Support"
    assert clean_title(raw) == "Can I Send A Mass Email Campaign Using Brilliant Directories?"

def test_extract_article_data():
    sample_html = """
    <html>
      <head>
        <title>How To Set Up Webhooks | Brilliant Directories Documentation</title>
        <meta property="article:published_time" content="2024-03-15T12:00:00Z" />
      </head>
      <body>
        <nav><a href="#">Home</a></nav>
        <div class="article-body">
          <h1 class="article-title">How To Set Up Webhooks</h1>
          <p>Webhooks allow Brilliant Directories to notify external endpoints about events like member signups.</p>
          <img src="https://support.brilliantdirectories.com/images/webhook-settings.png" />
          <script>console.log("ignore me");</script>
        </div>
        <footer>Copyright BD</footer>
      </body>
    </html>
    """
    data = extract_article_data(sample_html, "https://support.brilliantdirectories.com/solutions/webhooks")
    assert data["title"] == "How To Set Up Webhooks"
    assert "notify external endpoints" in data["body_text"]
    assert "console.log" not in data["body_text"]
    assert data["published_at"] == "2024-03-15T12:00:00Z"
    assert "https://support.brilliantdirectories.com/images/webhook-settings.png" in data["images"]

def test_storage_and_chunking():
    url = "https://support.brilliantdirectories.com/solutions/long-article"
    # Create text with 600 words to test chunking
    words = [f"word{i}" for i in range(600)]
    body_text = " ".join(words)
    article_id, is_new = db.upsert_article(
        url=url,
        title="Long Documentation Article",
        body_text=body_text,
    )
    assert is_new is True

    # Verify chunks created
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM chunks WHERE article_id = ?;", (article_id,))
        count = cursor.fetchone()[0]
        assert count >= 2
