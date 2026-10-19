# AGENTS.md — Persistent Instructions for AI Agents

## Mission
Build and maintain the Capstone MVP for **Task 1: Knowledge Brain** (Python / FastAPI) — an AI-powered technical knowledge brain for Brilliant Directories:
1. **Documentation Ingestion & Crawler**: Polite, bounded, resumable crawling of the Brilliant Directories Solution Center from `https://support.brilliantdirectories.com/support/sitemap.xml`.
2. **Hybrid Search & Retrieval**: SQLite WAL persistence with sliding-window chunking, pure-Python BM25 keyword matching, and normalized relevance scoring with source citations (URL, title, relevance score, snippet, timestamp, images).
3. **Cited RAG & Honest Refusal**: Grounded answering using Claude (`claude-3-5-sonnet-20241022` / `claude-3-5-haiku-20241022`) with deterministic mock fallback for offline tests. Return an honest `insufficient_evidence: true` when documentation is absent or relevance is below threshold.
4. **Incremental Refresh**: Detect new, updated, and removed pages (`POST /refresh`).
5. **Expert Review Loop**: Unanswered questions convert into human-review tasks (`POST /expert-tasks`). Approved answers (`POST /expert-tasks/{task_id}/answer`) are immediately indexed into retrieval for subsequent queries.

## Architecture Principles
1. **Documented HTTP Contract**: Expose standard REST endpoints:
   - `GET /health`
   - `POST /query`
   - `POST /refresh`
   - `POST /expert-tasks`
   - `POST /expert-tasks/{task_id}/answer`
2. **Model Tiering & Mock Fallback**: Anthropic Claude is the central LLM. When `ANTHROPIC_API_KEY` is not present or during automated unit tests, deterministic mock providers execute to ensure 100% reproducible, zero-cost test runs.
3. **Honest Evaluation**: No hardcoded fake success responses. Real citations from real ingested articles. Honest `insufficient_evidence` when facts are not in the corpus.
4. **Resilience & Politeness**: Rate limiting, bounded crawl batches, retry with exponential backoff on HTTP and LLM calls, and transactional persistence in SQLite.

## Local Execution Commands
- Python Virtual Environment: `.venv\Scripts\python` (Windows) or `.venv/bin/python` (Unix)
- Run Unit & Integration Tests: `.venv\Scripts\python -m pytest task1_knowledge_brain/tests/`
- Run Knowledge Brain Server: `.venv\Scripts\python -m uvicorn task1_knowledge_brain.app.main:app --host 127.0.0.1 --port 8001`
- Run Evaluations & Model Comparison: `.venv\Scripts\python evals/run_all_evals.py`
- Full Startup & Demo: `powershell -ExecutionPolicy Bypass -File ./scripts/run_all.ps1` or `scripts\run_all.bat`
