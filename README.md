# AI Tech Consultant — 12-Hour Capstone MVP

An enterprise-grade, three-tier AI technical consulting system tailored for **Brilliant Directories**:

1. **Task 1: Knowledge Brain (Python / FastAPI)** — Polite bounded ingestion of the Brilliant Directories Solution Center, incremental refresh, hybrid BM25 + vector retrieval, cited RAG answers, honest insufficient-evidence detection, and expert human-review loops.
2. **Task 2: Inbox Agent (TypeScript strict mode / Node.js)** — Synthetic fixture generation (50+ emails), intent classification, factual retrieval via Task 1 HTTP API, editable draft generation, and strict 20 consecutive unchanged-draft autonomy gate.
3. **Task 3: Meeting-to-Scope (Python / Pydantic)** — Staged agent pipeline for transcripts (chunking, requirements extraction, Task 1 knowledge lookup, hour estimation, proposal drafting), scope diff engine for follow-up meetings, and human review gating.

---

## Quick Start

### 1. Prerequisites
- Python 3.10+ (Current: Python 3.14)
- Node.js 18+ (Current: Node.js 24)
- Git

### 2. Setup Environment
```bash
# Clone and enter repository
cp .env.example .env

# Set up Python virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows: .venv\Scripts\activate (Linux/Mac: source .venv/bin/activate)
pip install -r task1_knowledge_brain/requirements.txt
pip install -r task3_meeting_to_scope/requirements.txt

# Set up TypeScript Inbox Agent
cd task2_inbox_agent
npm install
npm run build
cd ..
```

### 3. Running Services & Demos
```bash
# Start Task 1 Knowledge Brain API (runs on port 8001)
.venv\Scripts\python -m uvicorn task1_knowledge_brain.app.main:app --host 127.0.0.1 --port 8001

# Run Task 2 Inbox Agent CLI & Fixture Processor
cd task2_inbox_agent
npx ts-node src/cli.ts process-all
cd ..

# Run Task 3 Meeting-to-Scope Pipeline
.venv\Scripts\python task3_meeting_to_scope/app/cli.py generate-scope --file evals/fixtures/task3_transcripts/initial_discovery.txt

# Run Full End-to-End Evaluation Suite (20+ tests per task)
.venv\Scripts\python evals/run_all_evals.py
```

### 4. Single-Command Local Startup
Run the automated startup script:
```powershell
powershell -ExecutionPolicy Bypass -File ./scripts/run_all.ps1
```

---

## Architecture & Design
See [DESIGN.md](file:///d:/Business%20Labs/DESIGN.md) for detailed sequence diagrams, API schemas, and autonomy rules.
See [EVALS.md](file:///d:/Business%20Labs/EVALS.md) for evaluation methodology and benchmark metrics.
See [AI_LOG.md](file:///d:/Business%20Labs/AI_LOG.md) for model costs, latency logs, and versioned prompts.
