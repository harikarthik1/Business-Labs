from typing import List, Optional
from pydantic import BaseModel, Field

class HealthResponse(BaseModel):
    status: str
    version: str
    articles_count: int
    last_refresh_at: Optional[str] = None
    vector_store_ready: bool = True

class SourceCitation(BaseModel):
    title: str
    url: str
    relevance_score: float = Field(..., ge=0.0, le=1.0)
    snippet: str
    published_at: Optional[str] = None
    images: List[str] = Field(default_factory=list)

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=2, description="The customer or consultant question")
    top_k: int = Field(default=4, ge=1, le=10, description="Number of source articles to retrieve")
    confidence_threshold: float = Field(default=0.35, ge=0.0, le=1.0, description="Minimum relevance score threshold")

class QueryResponse(BaseModel):
    query: str
    answer: str
    sources: List[SourceCitation]
    insufficient_evidence: bool
    confidence: float = Field(..., ge=0.0, le=1.0)
    model_used: str
    latency_ms: int

class RefreshRequest(BaseModel):
    max_pages: int = Field(default=25, ge=1, le=2000, description="Maximum pages to fetch in this batch")
    force_full: bool = Field(default=False, description="Whether to re-crawl already indexed pages")

class RefreshResponse(BaseModel):
    pages_scanned: int
    pages_added: int
    pages_updated: int
    pages_removed: int
    elapsed_seconds: float
    total_articles_in_db: int

class ExpertTaskCreate(BaseModel):
    question: str = Field(..., min_length=5)
    context: Optional[str] = Field(default=None, description="Inquiry source or context")
    suggested_answer: Optional[str] = None

class ExpertTaskResponse(BaseModel):
    task_id: str
    question: str
    context: Optional[str] = None
    status: str  # pending_review, incorporated
    created_at: str
    approved_answer: Optional[str] = None
    expert_name: Optional[str] = None
    updated_at: Optional[str] = None

class ExpertTaskAnswerRequest(BaseModel):
    approved_answer: str = Field(..., min_length=10)
    expert_name: str = Field(default="Solutions Architect")
    source_reference: Optional[str] = "Approved Subject Matter Expert response"

class ExpertTaskAnswerResponse(BaseModel):
    task_id: str
    status: str
    indexed_article_id: str
    updated_at: str
