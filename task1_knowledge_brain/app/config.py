import os
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

# Load root .env if available
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

class Settings(BaseModel):
    app_name: str = "Knowledge Brain API"
    app_version: str = "1.0.0"
    host: str = os.getenv("TASK1_HOST", "127.0.0.1")
    port: int = int(os.getenv("TASK1_PORT", "8001"))
    db_path: str = os.getenv("TASK1_DB_PATH", str(BASE_DIR / "task1_knowledge_brain" / "data" / "knowledge_brain.db"))
    sitemap_url: str = os.getenv("TASK1_SITEMAP_URL", "https://support.brilliantdirectories.com/support/sitemap.xml")
    crawl_batch_size: int = int(os.getenv("TASK1_CRAWL_BATCH_SIZE", "20"))
    crawl_delay_sec: float = float(os.getenv("TASK1_CRAWL_DELAY_SEC", "0.2"))
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    default_model: str = "claude-3-5-sonnet-20241022"
    comparison_model: str = "claude-3-5-haiku-20241022"

settings = Settings()
