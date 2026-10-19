import sys
import json
import time
from pathlib import Path

# Ensure root directory is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from task1_knowledge_brain.app.retrieval import retriever
from task1_knowledge_brain.app.storage import db
from task1_knowledge_brain.app.llm import llm_provider

FIXTURES_FILE = BASE_DIR / "evals" / "fixtures" / "task1_queries.json"

def run_task1_eval(model_name: str = "claude-3-5-sonnet-20241022"):
    queries = json.loads(FIXTURES_FILE.read_text(encoding="utf-8"))
    db.init_db()
    retriever.build_index()

    results = []
    total_latency = 0
    correct_retrieval_count = 0
    correct_insufficient_count = 0
    total_cost = 0.0

    print(f"\n========================================================")
    print(f"RUNNING TASK 1 EVALUATION ({len(queries)} cases) [Model: {model_name}]")
    print(f"========================================================\n")

    for q in queries:
        qid = q["id"]
        qtext = q["query"]
        expected_insufficient = q["expected_insufficient"]

        start = time.time()
        citations, has_suff, top_conf = retriever.search(qtext, top_k=3)

        sources_text = "\n".join([f"--- SOURCE: {c.title}\n{c.snippet}" for c in citations])
        answer, is_llm_insufficient, used_model, lat_ms, telemetry = llm_provider.generate_rag_answer(
            query=qtext,
            sources_text=sources_text,
            has_sufficient_context=has_suff,
            model_override=model_name,
        )

        total_latency += lat_ms
        total_cost += telemetry.get("cost_usd", 0.0)

        insufficient_detected = is_llm_insufficient or not has_suff
        is_pass = False

        if expected_insufficient:
            if insufficient_detected:
                correct_insufficient_count += 1
                is_pass = True
        else:
            if not insufficient_detected and len(citations) > 0:
                correct_retrieval_count += 1
                is_pass = True

        results.append({
            "id": qid,
            "query": qtext,
            "expected_insufficient": expected_insufficient,
            "actual_insufficient": insufficient_detected,
            "citations_count": len(citations),
            "top_citation": citations[0].title if citations else None,
            "confidence": top_conf if not insufficient_detected else round(min(top_conf, 0.2), 3),
            "latency_ms": lat_ms,
            "cost_usd": telemetry.get("cost_usd", 0.0),
            "passed": is_pass,
        })

        status_str = "PASS" if is_pass else "FAIL"
        print(f"[{status_str}] {qid}: {qtext[:45]}... (Citations: {len(citations)}, Insufficient: {insufficient_detected}, Latency: {lat_ms}ms)")

    factual_total = sum(1 for q in queries if not q["expected_insufficient"])
    out_domain_total = sum(1 for q in queries if q["expected_insufficient"])

    factual_acc = (correct_retrieval_count / factual_total) * 100 if factual_total else 0
    refusal_acc = (correct_insufficient_count / out_domain_total) * 100 if out_domain_total else 0
    overall_acc = ((correct_retrieval_count + correct_insufficient_count) / len(queries)) * 100
    avg_latency = round(total_latency / len(queries), 1)

    print("\n--------------------------------------------------------")
    print(f"TASK 1 EVALUATION SUMMARY:")
    print(f"• Overall Pass Rate: {overall_acc:.1f}% ({correct_retrieval_count + correct_insufficient_count}/{len(queries)})")
    print(f"• Factual Retrieval Precision: {factual_acc:.1f}% ({correct_retrieval_count}/{factual_total})")
    print(f"• Honest Insufficient-Evidence Detection: {refusal_acc:.1f}% ({correct_insufficient_count}/{out_domain_total})")
    print(f"• Average Latency: {avg_latency} ms")
    print(f"• Total Evaluated Cost: ${total_cost:.6f} USD")
    print("--------------------------------------------------------\n")

    return {
        "model": model_name,
        "total_cases": len(queries),
        "overall_accuracy": round(overall_acc, 2),
        "factual_precision": round(factual_acc, 2),
        "insufficient_detection_rate": round(refusal_acc, 2),
        "average_latency_ms": avg_latency,
        "total_cost_usd": round(total_cost, 6),
        "results": results,
    }

if __name__ == "__main__":
    run_task1_eval()
