# AI_LOG.md — AI Engineering & Model Telemetry Log

## 1. Model Configuration & Pricing Reference
- **Primary Model**: `claude-3-5-sonnet-20241022`
  - Input: $3.00 / 1M tokens
  - Output: $15.00 / 1M tokens
- **Alternative / Comparison Model**: `claude-3-5-haiku-20241022`
  - Input: $0.80 / 1M tokens
  - Output: $4.00 / 1M tokens
- **Deterministic Mock Provider**: $0.00 / 0 ms network latency. Used in unit tests and offline test runs when `ANTHROPIC_API_KEY` is omitted.

## 2. Telemetry Schema
Every model execution (real or mock) tracks:
- `timestamp`: ISO-8601 UTC
- `task`: Task 1, Task 2, or Task 3
- `operation`: query_rag, classify_email, draft_response, extract_requirements, estimate_scope, diff_scope
- `model`: Model identifier
- `prompt_tokens`: Estimated or actual tokens in prompt
- `completion_tokens`: Estimated or actual tokens in response
- `latency_ms`: Elapsed time in milliseconds
- `cost_usd`: Calculated USD cost

## 3. Versioned Prompt Registry
- `TASK1_RAG_PROMPT_V1`: Factual synthesis requiring source citations and honest `INSUFFICIENT_EVIDENCE` fallback.
- `TASK2_CLASSIFY_PROMPT_V1`: Intent classification into 6 fixed categories with confidence score.
- `TASK2_DRAFT_PROMPT_V1`: Professional reply generator with intent, evidence citations, and confidence.
- `TASK3_REQUIREMENTS_PROMPT_V1`: Extraction of structured requirements, assumptions, and exclusions from conversational transcripts.
- `TASK3_ESTIMATE_PROMPT_V1`: Hours breakdown by task with low/med/high confidence and feasibility notes.
- `TASK3_DIFF_PROMPT_V1`: Semantic diffing between prior approved scope and follow-up discussion.

---
*Run evaluations via `python evals/run_all_evals.py` to populate live metrics.*
