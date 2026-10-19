# Task 1: Knowledge Brain — AI Technical Consultant MVP

An enterprise-grade, FastAPI-powered knowledge brain for **Brilliant Directories**:
- **Polite Bounded Crawling**: Ingests solution articles from `https://support.brilliantdirectories.com/support/sitemap.xml` with rate limiting, exponential backoff retries, and resumable state.
- **Article & Metadata Extraction**: Extracts clean article text, titles, timestamps, and image references.
- **Hybrid Retrieval & Sliding-Window Chunking**: Local SQLite WAL storage with pure-Python BM25 keyword matching and domain stopword normalization.
- **Cited RAG Answering**: Uses Anthropic Claude (`claude-3-5-sonnet-20241022` / `claude-3-5-haiku-20241022`) or deterministic mock fallback to generate cited responses.
- **Honest Insufficient Evidence Refusal**: Detects ungrounded or out-of-domain queries and returns `insufficient_evidence: true` without hallucinations.
- **Incremental Refresh**: Detects new, updated, and removed pages.
- **Expert Review Loop**: Unanswered queries become human-review tasks (`POST /expert-tasks`); approved answers are indexed immediately into retrieval for future questions.

---

## Quick Start

### 1. Prerequisites
- Python 3.10+ (Current environment: Python 3.14)
- Git / PowerShell / Command Prompt

### 2. Setup Environment
```bash
# Copy environment configuration
cp .env.example .env

# Activate Python virtual environment and install dependencies
.venv\Scripts\activate       # On Windows (On Linux/Mac: source .venv/bin/activate)
pip install -r task1_knowledge_brain/requirements.txt
```

### 3. Start Knowledge Brain API Server
```bash
.venv\Scripts\python -m uvicorn task1_knowledge_brain.app.main:app --host 127.0.0.1 --port 8001
```
The interactive Swagger API documentation is available at: `http://127.0.0.1:8001/docs`.

### 4. Run Unit & Integration Tests
```bash
.venv\Scripts\python -m pytest task1_knowledge_brain/tests/
```

### 5. Run Evaluations & Model Comparison
```bash
.venv\Scripts\python evals/run_all_evals.py
```

### 6. Single-Command Local Startup & Verification Demo
```powershell
powershell -ExecutionPolicy Bypass -File ./scripts/run_all.ps1
```
Or on Windows Command Prompt:
```cmd
scripts\run_all.bat
```

---

## API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | System status, indexed article count, and last refresh timestamp |
| `POST` | `/query` | Hybrid retrieval and cited RAG answering with honest refusal |
| `POST` | `/refresh` | Polite bounded crawler batch to scan sitemap and index new articles |
| `POST` | `/expert-tasks` | Create human-review task for unanswered or ambiguous questions |
| `POST` | `/expert-tasks/{id}/answer` | Submit approved human answer and index it into retrieval immediately |

See [DESIGN.md](file:///d:/Business%20Labs/DESIGN.md) for full architectural specs, schemas, and sequence diagrams.
See [EVALS.md](file:///d:/Business%20Labs/EVALS.md) for empirical benchmark evaluation results.
See [AI_LOG.md](file:///d:/Business%20Labs/AI_LOG.md) for versioned prompts and model telemetry logs.
