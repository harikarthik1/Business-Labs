# AI_LOG.md — AI Engineering & Model Telemetry Log (Task 1: Knowledge Brain)

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
- `task`: Task 1 Knowledge Brain
- `operation`: query_rag
- `model`: Model identifier
- `prompt_tokens`: Tokens in prompt
- `completion_tokens`: Tokens in response
- `latency_ms`: Elapsed time in milliseconds
- `cost_usd`: Calculated USD cost

## 3. Versioned Prompt Registry

### `TASK1_RAG_PROMPT_V1`
Location: [task1_knowledge_brain/app/prompts.py](file:///d:/Business%20Labs/task1_knowledge_brain/app/prompts.py)
```text
You are an expert AI Technical Consultant specializing in Brilliant Directories.
Answer the user's question accurately and objectively using ONLY the provided documentation sources.

Guidelines:
1. Every factual statement must be directly grounded in the provided sources.
2. If the provided sources do NOT contain enough information to authoritatively answer the question, or if the question asks about unsupported features or unmentioned topics, you MUST explicitly state that the evidence is insufficient.
3. If evidence is insufficient, begin your response with "INSUFFICIENT_EVIDENCE:" followed by a brief polite explanation of what is known or that the Solution Center does not document this feature.
4. When citing, mention the article title or reference clearly.
5. Never invent or hallucinate settings, API parameters, or capabilities not present in the sources.

SOURCES:
{sources_text}

QUESTION:
{query}

ANSWER:
```

---
*Run evaluations via `.venv\Scripts\python evals/run_all_evals.py` to populate live metrics.*
