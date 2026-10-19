import sys
import json
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from evals.task1_eval import run_task1_eval

def run_model_comparison():
    print("\n" + "=" * 70)
    print("AI TECH CONSULTANT: TWO-MODEL EVALUATION COMPARISON")
    print("Comparing: Claude 3.5 Sonnet vs. Claude 3.5 Haiku (or baseline profile)")
    print("=" * 70)

    # 1. Run on Model A: claude-3-5-sonnet-20241022
    results_sonnet = run_task1_eval(model_name="claude-3-5-sonnet-20241022")

    # 2. Run on Model B: claude-3-5-haiku-20241022
    results_haiku = run_task1_eval(model_name="claude-3-5-haiku-20241022")

    comparison = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "test_dataset": "evals/fixtures/task1_queries.json (25 queries)",
        "models": {
            "claude-3-5-sonnet-20241022": {
                "accuracy": f"{results_sonnet['overall_accuracy']}%",
                "factual_precision": f"{results_sonnet['factual_precision']}%",
                "insufficient_detection": f"{results_sonnet['insufficient_detection_rate']}%",
                "avg_latency_ms": results_sonnet['average_latency_ms'],
                "cost_per_1k_usd": round(results_sonnet['total_cost_usd'] * (1000 / results_sonnet['total_cases']), 4),
            },
            "claude-3-5-haiku-20241022": {
                "accuracy": f"{results_haiku['overall_accuracy']}%",
                "factual_precision": f"{results_haiku['factual_precision']}%",
                "insufficient_detection": f"{results_haiku['insufficient_detection_rate']}%",
                "avg_latency_ms": results_haiku['average_latency_ms'],
                "cost_per_1k_usd": round(results_haiku['total_cost_usd'] * (1000 / results_haiku['total_cases']), 4),
            }
        }
    }

    print("\n" + "=" * 70)
    print("HEAD-TO-HEAD COMPARISON SUMMARY TABLE")
    print("=" * 70)
    print(f"{'Metric':<35} | {'Claude 3.5 Sonnet':<18} | {'Claude 3.5 Haiku':<18}")
    print("-" * 75)
    print(f"{'Overall Pass Rate':<35} | {results_sonnet['overall_accuracy']:<18}% | {results_haiku['overall_accuracy']:<18}%")
    print(f"{'Factual Precision':<35} | {results_sonnet['factual_precision']:<18}% | {results_haiku['factual_precision']:<18}%")
    print(f"{'Insufficient Evidence Detection':<35} | {results_sonnet['insufficient_detection_rate']:<18}% | {results_haiku['insufficient_detection_rate']:<18}%")
    print(f"{'Average Latency':<35} | {results_sonnet['average_latency_ms']:<15} ms | {results_haiku['average_latency_ms']:<15} ms")
    print(f"{'Cost per 1,000 Queries':<35} | ${comparison['models']['claude-3-5-sonnet-20241022']['cost_per_1k_usd']:<17} | ${comparison['models']['claude-3-5-haiku-20241022']['cost_per_1k_usd']:<17}")
    print("=" * 70 + "\n")

    out_file = BASE_DIR / "evals" / "model_comparison_results.json"
    out_file.write_text(json.dumps(comparison, indent=2), encoding="utf-8")
    print(f"Results saved to: {out_file}")

    return comparison

if __name__ == "__main__":
    run_model_comparison()
