# DESIGN.md — Architecture & Technical Specifications

## 1. System Overview

The AI Tech Consultant platform automates technical consulting workflows for software platforms (specifically Brilliant Directories) across three decoupled subsystems:

```mermaid
flowchart TD
    subgraph SolutionCenter [Brilliant Directories Solution Center]
        Sitemap[sitemap.xml] --> Articles[HTML Articles]
    end

    subgraph Task1 [Task 1: Knowledge Brain (Python / FastAPI)]
        Crawler[Polite Bounded Crawler] --> Articles
        Extractor[HTML / Metadata Extractor] --> DB[(SQLite + FTS5 & Chunks)]
        DB --> Retriever[Hybrid BM25 + Cosine Retriever]
        Retriever --> RAG[Claude / Mock RAG Engine]
        API[FastAPI Endpoints: /health, /query, /refresh, /expert-tasks]
    end

    subgraph Task2 [Task 2: Inbox Agent (TypeScript / Node)]
        EmailFixtures[50+ Synthetic Emails] --> Classifier[Intent Classifier]
        Classifier --> |HTTP Query| API
        Classifier --> DraftGen[Draft Generator]
        DraftGen --> AutonomyEngine[20-Streak Autonomy Guard]
        AutonomyEngine --> HumanReview[Human Review / Approval Gate]
    end

    subgraph Task3 [Task 3: Meeting-to-Scope (Python)]
        Transcripts[Meeting Transcripts] --> Chunker[Sliding Window Chunker]
        Chunker --> ReqExtractor[Requirements Extractor]
        ReqExtractor --> |HTTP Knowledge Lookup| API
        ReqExtractor --> Estimator[Complexity & Hours Estimator]
        Estimator --> ProposalGen[Proposal Generator]
        ProposalGen --> DiffEngine[Scope Diff vs Previous Approved Scope]
        DiffEngine --> ScopeApproval[Human Finalization Gate]
    end
```

---

## 2. Shared API Contract (Task 1 Knowledge Brain)

The Knowledge Brain provides an HTTP API consumed by Tasks 2 and 3.

### 2.1 `GET /health`
Returns system status, article count, and last refresh timestamp.

**Response `200 OK`**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "articles_count": 120,
  "last_refresh_at": "2026-10-18T15:30:00Z",
  "vector_store_ready": true
}
```

### 2.2 `POST /query`
Performs retrieval augmented generation against crawled Brilliant Directories articles.

**Request**:
```json
{
  "query": "How do I configure custom member form fields?",
  "top_k": 4,
  "confidence_threshold": 0.4
}
```

**Response `200 OK`**:
```json
{
  "query": "How do I configure custom member form fields?",
  "answer": "To configure custom member form fields in Brilliant Directories, navigate to Toolbox > Form Manager...",
  "sources": [
    {
      "title": "Form Manager: Customizing Member Fields",
      "url": "https://support.brilliantdirectories.com/support/solutions/articles/5000558401",
      "relevance_score": 0.88,
      "snippet": "In the Form Manager, select the form you wish to customize...",
      "published_at": "2024-01-15T00:00:00Z"
    }
  ],
  "insufficient_evidence": false,
  "confidence": 0.88,
  "model_used": "claude-3-5-sonnet-20241022",
  "latency_ms": 612
}
```

**Insufficient Evidence Response `200 OK`**:
When the knowledge base lacks authoritative support for the query:
```json
{
  "query": "What is the quantum encryption protocol of Brilliant Directories?",
  "answer": "Insufficient documentation available in the Brilliant Directories Knowledge Base to verify this capability.",
  "sources": [],
  "insufficient_evidence": true,
  "confidence": 0.05,
  "model_used": "claude-3-5-sonnet-20241022",
  "latency_ms": 210
}
```

### 2.3 `POST /refresh`
Triggers an incremental or full crawl of the sitemap.

**Request**:
```json
{
  "max_pages": 50,
  "force_full": false
}
```

**Response `200 OK`**:
```json
{
  "pages_scanned": 50,
  "pages_added": 8,
  "pages_updated": 2,
  "pages_removed": 0,
  "elapsed_seconds": 12.4
}
```

### 2.4 `POST /expert-tasks`
Creates a human-review task when an incoming customer query cannot be answered automatically.

**Request**:
```json
{
  "question": "Can I integrate a custom legacy COBOL mainframe with member signups?",
  "context": "Customer email inquiry from Enterprise client",
  "suggested_answer": null
}
```

**Response `201 Created`**:
```json
{
  "task_id": "exp_task_9812",
  "question": "Can I integrate a custom legacy COBOL mainframe with member signups?",
  "status": "pending_review",
  "created_at": "2026-10-18T15:35:00Z"
}
```

### 2.5 `POST /expert-tasks/{task_id}/answer`
Submits an approved human answer, immediately indexing it into retrieval for future questions.

**Request**:
```json
{
  "approved_answer": "Brilliant Directories supports webhook events and Zapier/API webhooks upon member signup which can trigger an intermediary middleware service to communicate with legacy mainframes.",
  "expert_name": "Senior BD Solutions Architect",
  "source_reference": "Verified architectural pattern"
}
```

**Response `200 OK`**:
```json
{
  "task_id": "exp_task_9812",
  "status": "incorporated",
  "indexed_article_id": "expert_exp_task_9812",
  "updated_at": "2026-10-18T15:36:00Z"
}
```

---

## 3. Task 2: Inbox Agent & Autonomous Sending Rule

### 3.1 Email Categories
1. `how_to` — Technical questions regarding how to configure features.
2. `project_request` — Requests to develop custom widgets, integrations, or directory redesigns.
3. `refund` — Billing grievances, subscription cancellations, refund disputes.
4. `complaint` — Bug reports, service downtime, unsatisfied delivery.
5. `quotation` — Inquiries regarding pricing, quotes for custom work.
6. `follow_up` — Status checks on ongoing tickets or proposals.

### 3.2 Unchanged Draft Rule & 20-Consecutive Autonomy Gate
- **Definition of Unchanged Draft**: A human reviewer accepts the generated draft with zero text modifications or only trivial whitespace normalization (Levenshtein similarity >= 0.99 with no semantic changes).
- **Streak Tracking**: Tracked **per category** in persistent storage.
- **Eligibility Threshold**: Exactly 20 consecutive unchanged approved drafts in that specific category (`consecutive_unchanged >= 20`).
- **Reset Trigger**:
  1. Any human edit with similarity < 0.99.
  2. Any rejection of the draft.
  3. Any factual error reported.
  4. If reset, `consecutive_unchanged` is set back to 0 immediately.
- **Safety Guarantee**: In this MVP, even if an email is marked `autonomous_eligible: true`, the system **never sends emails automatically**; it stamps the audit log and requires an explicit operator confirmation.

---

## 4. Task 3: Meeting-to-Scope Architecture

1. **Transcript Chunking**: Uses sliding window token/character chunking with 15% overlap to avoid losing context across turn boundaries.
2. **Four Agent Stages**:
   - `Requirements Extraction`: Extracts functional and non-functional requirements with speaker attribution.
   - `Knowledge Lookup`: Queries Task 1 HTTP API to verify BD platform feasibility and native vs custom capabilities.
   - `Estimation Engine`: Assigns hours, complexity (Low/Med/High), assumptions, and exclusions.
   - `Proposal Generation`: Compiles client-ready executive summary, deliverables, timeline, and investment breakdown.
3. **Scope Diff Engine**: Compares follow-up transcripts against prior approved scope versions to detect:
   - Added requirements (`ADD`)
   - Removed requirements (`REMOVE`)
   - Changed requirements (`MODIFY`)
   - Out-of-scope work requiring a Change Order (`OUT_OF_SCOPE`).
4. **Approval Workflow**: Explicit status `draft` -> `under_review` -> `approved`.

---

## 5. Storage & Minimal Footprint
- SQLite with WAL mode for local ACID storage.
- In-memory/SQLite hybrid lexical BM25 + vector cosine scoring.
- Zero external paid services required to run full tests and evaluations.
