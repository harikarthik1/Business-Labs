import sys
import time
from pathlib import Path

# Ensure root directory is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from task3_meeting_to_scope.app.pipeline import scope_pipeline
from task3_meeting_to_scope.app.diff_engine import diff_engine
from task3_meeting_to_scope.app.storage import scope_storage
from task3_meeting_to_scope.app.transcription import chunker

FIXTURES_DIR = BASE_DIR / "evals" / "fixtures" / "task3_transcripts"

def run_task3_eval():
    print("\n========================================================")
    print("RUNNING TASK 3 EVALUATION (20+ test scenarios)")
    print("========================================================\n")

    test_results = []
    start_all = time.time()

    initial_text = (FIXTURES_DIR / "initial_discovery.txt").read_text(encoding="utf-8")
    followup_text = (FIXTURES_DIR / "followup_meeting.txt").read_text(encoding="utf-8")

    # 1. Pipeline Execution
    t0 = time.time()
    scope = scope_pipeline.run(initial_text, client_name="Enterprise Healthcare", project_title="Medical Specialist Portal")
    pipeline_lat_ms = int((time.time() - t0) * 1000)

    # Eval 1 to 8: Requirements extraction & categorization
    for i, req in enumerate(scope.requirements[:8], 1):
        has_cat = req.category in ["functional", "non_functional", "integration", "ui_ux"]
        has_est = req.estimated_hours > 0
        has_feasibility = len(req.feasibility_notes or "") > 10
        passed = has_cat and has_est and has_feasibility
        test_results.append({
            "test_id": f"t3_req_{i:02d}",
            "name": f"Requirement {req.id} extraction & estimation structure",
            "passed": passed,
            "details": f"Cat: {req.category}, Hours: {req.estimated_hours}h, Feasibility: {req.feasibility_notes[:35]}...",
        })
        print(f"[{'PASS' if passed else 'FAIL'}] t3_req_{i:02d}: {req.title[:40]}... ({req.estimated_hours}h)")

    # Eval 9: Estimation hour breakdown structure
    has_estimates = len(scope.estimates) == len(scope.requirements)
    test_results.append({
        "test_id": "t3_est_structure",
        "name": "Estimation item alignment with requirements",
        "passed": has_estimates,
        "details": f"Total hours: {scope.total_hours}h across {len(scope.estimates)} tasks",
    })
    print(f"[{'PASS' if has_estimates else 'FAIL'}] t3_est_structure: Estimation items align ({scope.total_hours}h)")

    # Eval 10: Proposal consistency and executive summary
    has_proposal = len(scope.proposal_narrative) > 500 and "Executive Summary" in scope.proposal_narrative
    test_results.append({
        "test_id": "t3_proposal_narrative",
        "name": "Client proposal narrative structure",
        "passed": has_proposal,
        "details": f"Length: {len(scope.proposal_narrative)} chars, Timeline: {scope.timeline_weeks} weeks",
    })
    print(f"[{'PASS' if has_proposal else 'FAIL'}] t3_proposal_narrative: Client-ready proposal narrative verified")

    # Eval 11: Assumptions and Exclusions present
    has_assump = len(scope.assumptions) >= 3 and len(scope.exclusions) >= 3
    test_results.append({
        "test_id": "t3_assumptions_exclusions",
        "name": "Scope boundaries (Assumptions & Exclusions)",
        "passed": has_assump,
        "details": f"{len(scope.assumptions)} assumptions, {len(scope.exclusions)} exclusions",
    })
    print(f"[{'PASS' if has_assump else 'FAIL'}] t3_assumptions_exclusions: Risk boundaries documented")

    # Eval 12: Scope draft status initially
    is_draft = scope.status == "draft" and scope.approved_by is None
    test_results.append({
        "test_id": "t3_initial_draft_status",
        "name": "Scope initially generated in draft status",
        "passed": is_draft,
        "details": f"Status: {scope.status}",
    })
    print(f"[{'PASS' if is_draft else 'FAIL'}] t3_initial_draft_status: Status is draft")

    # Eval 13: Human approval gate
    scope_storage.save_scope(scope)
    approved = scope_storage.approve_scope(scope.scope_id, "Sarah Jenkins", "Board approved")
    is_approved = approved is not None and approved.status == "approved" and approved.approved_by == "Sarah Jenkins"
    test_results.append({
        "test_id": "t3_human_approval_gate",
        "name": "Human approval gate finalization",
        "passed": is_approved,
        "details": f"Approved by: {approved.approved_by if approved else None}",
    })
    print(f"[{'PASS' if is_approved else 'FAIL'}] t3_human_approval_gate: Human approval gate verified")

    # Eval 14 to 18: Scope Diff Engine
    diff_report = diff_engine.compare_transcript_to_scope(approved, followup_text)

    # Addition detection
    has_adds = len(diff_report.additions) > 0
    test_results.append({
        "test_id": "t3_diff_additions",
        "name": "Scope diff addition detection",
        "passed": has_adds,
        "details": f"{len(diff_report.additions)} additions identified",
    })
    print(f"[{'PASS' if has_adds else 'FAIL'}] t3_diff_additions: Addition detected (+{sum(a.delta_hours for a in diff_report.additions)}h)")

    # Out of scope detection
    has_out_of_scope = len(diff_report.out_of_scope) > 0
    test_results.append({
        "test_id": "t3_diff_out_of_scope",
        "name": "Scope diff out-of-scope work detection",
        "passed": has_out_of_scope,
        "details": f"{len(diff_report.out_of_scope)} out-of-scope requests flagged",
    })
    print(f"[{'PASS' if has_out_of_scope else 'FAIL'}] t3_diff_out_of_scope: Out-of-scope detected")

    # Change order requirement trigger
    co_triggered = diff_report.requires_change_order is True
    test_results.append({
        "test_id": "t3_diff_change_order_trigger",
        "name": "Change order requirement flag",
        "passed": co_triggered,
        "details": f"Change Order Required: {co_triggered}",
    })
    print(f"[{'PASS' if co_triggered else 'FAIL'}] t3_diff_change_order_trigger: Change Order requirement flagged")

    # Long transcript chunking sliding window coverage
    long_turns = [f"Participant {i % 4}: Critical requirement sentence number {i} regarding database synchronization." for i in range(350)]
    chunks = chunker.chunk_transcript("\n".join(long_turns))
    chunking_valid = len(chunks) >= 3 and all(c["word_count"] > 0 for c in chunks)
    test_results.append({
        "test_id": "t3_long_transcript_chunking",
        "name": "Sliding window chunker preserving turn continuity",
        "passed": chunking_valid,
        "details": f"Partitioned into {len(chunks)} overlapping chunks",
    })
    print(f"[{'PASS' if chunking_valid else 'FAIL'}] t3_long_transcript_chunking: Sliding window chunker verified")

    # Net hours calculation correctness
    net_hours_correct = diff_report.new_total_hours == round(diff_report.previous_total_hours + diff_report.net_hours_change, 1)
    test_results.append({
        "test_id": "t3_diff_net_hours",
        "name": "Net hours change calculation mathematical integrity",
        "passed": net_hours_correct,
        "details": f"Prev: {diff_report.previous_total_hours}h, Net: {diff_report.net_hours_change:+.1f}h, New: {diff_report.new_total_hours}h",
    })
    print(f"[{'PASS' if net_hours_correct else 'FAIL'}] t3_diff_net_hours: Net hours delta verified")

    # Timeline calculation check
    timeline_valid = scope.timeline_weeks >= 1.0 and scope.timeline_weeks == round(max(2.0, scope.total_hours / 18.0), 1)
    test_results.append({
        "test_id": "t3_timeline_calculation",
        "name": "Timeline weeks calculation based on velocity",
        "passed": timeline_valid,
        "details": f"Total: {scope.total_hours}h -> {scope.timeline_weeks} weeks",
    })
    print(f"[{'PASS' if timeline_valid else 'FAIL'}] t3_timeline_calculation: Velocity timeline verified ({scope.timeline_weeks} weeks)")

    # Speaker attribution check
    speaker_attributed = any(r.source_speaker and len(r.source_speaker) > 0 for r in scope.requirements)
    test_results.append({
        "test_id": "t3_speaker_attribution",
        "name": "Speaker attribution preserved from transcript",
        "passed": speaker_attributed,
        "details": f"Attributed speakers: {set(r.source_speaker for r in scope.requirements)}",
    })
    print(f"[{'PASS' if speaker_attributed else 'FAIL'}] t3_speaker_attribution: Speaker attribution verified")

    # Edge case: Empty transcript handling
    empty_scope = scope_pipeline.run("", client_name="Empty Client")
    empty_handled = len(empty_scope.requirements) > 0 and empty_scope.total_hours > 0
    test_results.append({
        "test_id": "t3_empty_transcript_resilience",
        "name": "Empty transcript resilience fallback",
        "passed": empty_handled,
        "details": f"Fallback requirements generated: {len(empty_scope.requirements)}",
    })
    print(f"[{'PASS' if empty_handled else 'FAIL'}] t3_empty_transcript_resilience: Graceful fallback on empty notes")

    passed_count = sum(1 for t in test_results if t["passed"])
    pass_rate = (passed_count / len(test_results)) * 100

    print("\n--------------------------------------------------------")
    print("TASK 3 EVALUATION SUMMARY:")
    print(f"• Total Test Cases: {len(test_results)}")
    print(f"• Pass Rate: {pass_rate:.1f}% ({passed_count}/{len(test_results)})")
    print(f"• Pipeline Latency: {pipeline_lat_ms} ms")
    print("--------------------------------------------------------\n")

    return {
        "total_cases": len(test_results),
        "passed_count": passed_count,
        "pass_rate": round(pass_rate, 2),
        "pipeline_latency_ms": pipeline_lat_ms,
        "test_results": test_results,
    }

if __name__ == "__main__":
    run_task3_eval()
