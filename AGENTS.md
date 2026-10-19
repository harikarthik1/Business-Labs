# AGENTS.md — Persistent Instructions for AI Agents

## Mission
Build and maintain the 12-Hour Capstone MVP for the AI Tech Consultant system consisting of:
1. **Task 1: Knowledge Brain** (Python / FastAPI) — Ingest Brilliant Directories Solution Center documentation, support incremental refresh and polite crawling, hybrid retrieval with citations, honest insufficient-evidence detection, and expert human-review loops.
2. **Task 2: Inbox Agent** (TypeScript strict mode / Node.js) — Classify customer emails, query Task 1 API via HTTP, generate editable drafts with intent/evidence/confidence/review status, track feedback, and enforce a strict 20 consecutive unchanged-draft autonomy rule.
3. **Task 3: Meeting-to-Scope** (Python / Pydantic) — Ingest meeting transcripts with long-transcript chunking, execute agent stages (requirements, knowledge lookup via Task 1 HTTP API, estimates, proposal), perform scope diffs against previous approved scopes, and enforce human approval before finalization.

## Architecture Principles
1. **Decoupled HTTP Contract**: Tasks 2 and 3 must interact with Task 1 exclusively through its HTTP API (`GET /health`, `POST /query`, `POST /refresh`, `POST /expert-tasks`, `POST /expert-tasks/{task_id}/answer`). No direct database access or shared code between Task 1 and 2/3.
2. **Model Tiering & Mock Fallback**: Anthropic Claude (`claude-3-5-sonnet-20241022` or `claude-3-5-haiku-20241022`) is the central LLM. When `ANTHROPIC_API_KEY` is not present or during automated unit tests, deterministic mock providers are executed to ensure 100% reproducible, zero-cost test runs.
3. **Honest Evaluation**: No hardcoded fake success responses. Real citations from real ingested articles. Honest `insufficient_evidence` when facts are not in the corpus.
4. **Resilience & Politeness**: Rate limiting, bounded crawl batches, retry with exponential backoff on HTTP and LLM calls, and transactional persistence in SQLite.

## Local Execution Commands
- Python Environment: `.venv\Scripts\python`
- Node/TypeScript: `npm install`, `npm run build`, `npm test` inside `task2_inbox_agent/`
- Full Startup / Integration Demo: `powershell -ExecutionPolicy Bypass -File ./scripts/run_all.ps1`
- Evaluations: `python evals/run_all_evals.py`
