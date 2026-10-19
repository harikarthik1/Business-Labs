import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from task1_knowledge_brain.app.config import settings
from task1_knowledge_brain.app.storage import db
from task1_knowledge_brain.app.retrieval import retriever
from task1_knowledge_brain.app.crawler import crawler
from task1_knowledge_brain.app.llm import llm_provider
from task1_knowledge_brain.app.schemas import (
    HealthResponse,
    QueryRequest,
    QueryResponse,
    RefreshRequest,
    RefreshResponse,
    ExpertTaskCreate,
    ExpertTaskResponse,
    ExpertTaskAnswerRequest,
    ExpertTaskAnswerResponse,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # On startup: initialize DB and build BM25 retriever index from existing articles
    db.init_db()
    retriever.build_index()
    yield

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Knowledge Brain API providing polite documentation ingestion, hybrid retrieval, cited RAG, and expert review loops for Brilliant Directories.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", response_model=HealthResponse, tags=["System"])
async def get_health():
    """Returns system status, total indexed articles, and last refresh timestamp."""
    article_count = db.get_article_count()
    last_refresh = db.get_last_refresh_time()
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        articles_count=article_count,
        last_refresh_at=last_refresh,
        vector_store_ready=True,
    )

@app.post("/query", response_model=QueryResponse, tags=["Retrieval & RAG"])
async def query_knowledge(req: QueryRequest):
    """
    Query the Knowledge Brain with source article citations.
    Returns an honest insufficient-evidence response when documentation is inadequate.
    """
    citations, has_sufficient_evidence, top_confidence = retriever.search(
        query=req.query,
        top_k=req.top_k,
        confidence_threshold=req.confidence_threshold,
    )

    # Format source text for RAG
    sources_text = ""
    for c in citations:
        sources_text += f"\n--- SOURCE: {c.title} ({c.url})\n{c.snippet}\n"

    answer, is_insufficient, model_used, latency_ms, telemetry = llm_provider.generate_rag_answer(
        query=req.query,
        sources_text=sources_text,
        has_sufficient_context=has_sufficient_evidence,
    )

    # If the LLM declared insufficient evidence or confidence was below threshold
    insufficient = is_insufficient or not has_sufficient_evidence

    return QueryResponse(
        query=req.query,
        answer=answer,
        sources=citations if not insufficient else [],
        insufficient_evidence=insufficient,
        confidence=top_confidence if not insufficient else round(min(top_confidence, 0.2), 3),
        model_used=model_used,
        latency_ms=latency_ms,
    )

@app.post("/refresh", response_model=RefreshResponse, tags=["Crawler"])
async def refresh_knowledge(req: RefreshRequest):
    """Triggers polite bounded crawler batch to refresh articles and index."""
    result = crawler.run_refresh(max_pages=req.max_pages, force_full=req.force_full)
    if "error" in result and result.get("pages_scanned", 0) == 0:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Crawl refresh failed: {result['error']}",
        )
    return RefreshResponse(
        pages_scanned=result["pages_scanned"],
        pages_added=result["pages_added"],
        pages_updated=result["pages_updated"],
        pages_removed=result["pages_removed"],
        elapsed_seconds=result["elapsed_seconds"],
        total_articles_in_db=result["total_articles_in_db"],
    )

@app.post("/expert-tasks", response_model=ExpertTaskResponse, status_code=status.HTTP_201_CREATED, tags=["Expert Review"])
async def create_expert_task(req: ExpertTaskCreate):
    """Create a human-review task for unanswered or ambiguous questions."""
    task_id = f"task_{uuid.uuid4().hex[:8]}"
    created = db.create_expert_task(
        task_id=task_id,
        question=req.question,
        context=req.context,
        suggested_answer=req.suggested_answer,
    )
    return ExpertTaskResponse(
        task_id=created["task_id"],
        question=created["question"],
        context=created["context"],
        status=created["status"],
        created_at=created["created_at"],
    )

@app.post("/expert-tasks/{task_id}/answer", response_model=ExpertTaskAnswerResponse, tags=["Expert Review"])
async def answer_expert_task(task_id: str, req: ExpertTaskAnswerRequest):
    """Submit approved human answer, incorporating it immediately into future retrieval."""
    task = db.get_expert_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Expert task with ID '{task_id}' not found.",
        )

    res = db.answer_expert_task(
        task_id=task_id,
        approved_answer=req.approved_answer,
        expert_name=req.expert_name,
        source_reference=req.source_reference or "Approved Subject Matter Expert response",
    )
    # Rebuild index so new answer is instantly searchable
    retriever.build_index()

    return ExpertTaskAnswerResponse(
        task_id=res["task_id"],
        status=res["status"],
        indexed_article_id=res["indexed_article_id"],
        updated_at=res["updated_at"],
    )
