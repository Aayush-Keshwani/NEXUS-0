"""
Verification test suite for Phase 1: goal_tracking.py
"""

import sys
from goal_tracking import (
    save_goal_state,
    compute_drift_score,
    goal_health_check,
    log_goal_evolution,
    get_goal_drift_report,
    goal_tracking_tools,
    _cosine_similarity,
    _get_embedding,
)

def test_phase_1():
    print("=" * 60)
    print("RUNNING VERIFICATION FOR PHASE 1: goal_tracking.py")
    print("=" * 60)

    # 1. Cosine similarity unit test
    v1 = [1.0, 0.0, 0.0]
    v2 = [1.0, 0.0, 0.0]
    v3 = [0.0, 1.0, 0.0]
    assert abs(_cosine_similarity(v1, v2) - 1.0) < 1e-5, "Cosine similarity identical failed"
    assert abs(_cosine_similarity(v1, v3) - 0.0) < 1e-5, "Cosine similarity orthogonal failed"
    print("✅ Step 1: Cosine similarity math verified")

    # 2. Embedding generation unit test
    emb = _get_embedding("Autonomous research system with calendar and notion")
    assert len(emb) == 768, f"Expected 768 dim vector, got {len(emb)}"
    print("✅ Step 2: Embedding generation (768-dim) verified")

    # 3. Save baseline goal state
    pk = "test_phase1_proj"
    baseline_goal = "Build a habit tracking app with email authentication and streak tracking"
    res1 = save_goal_state(pk, baseline_goal)
    assert "anchored" in res1.lower() or "baseline" in res1.lower(), f"Unexpected save response: {res1}"
    print("✅ Step 3: save_goal_state baseline anchored successfully")

    # 4. Idempotency check: saving a changed goal to the same project_key should preserve original
    res2 = save_goal_state(pk, "COMPLETELY DIFFERENT GOAL: build a crypto casino")
    assert "already locked" in res2.lower() or "preserved" in res2.lower(), f"Failed idempotency: {res2}"
    report_initial = get_goal_drift_report(pk)
    assert report_initial["original_goal"] == baseline_goal, "Original goal was overwritten!"
    print("✅ Step 4: Baseline goal immutability verified (prevented overwrite)")

    # 5. Drift computation: aligned tasks
    aligned_tasks = "Task 1: Setup email auth with JWT\nTask 2: Build habit CRUD API\nTask 3: Implement streak counter"
    aligned_score = compute_drift_score(pk, aligned_tasks)
    assert aligned_score is not None, "Score should not be None"
    assert aligned_score >= 60.0, f"Aligned score too low: {aligned_score}"
    health_aligned = goal_health_check(pk, aligned_tasks)
    assert "ON TRACK" in health_aligned or aligned_score >= 70.0, f"Health check failed for aligned: {health_aligned}"
    print(f"✅ Step 5: Aligned tasks score: {aligned_score}% ({health_aligned})")

    # 6. Drift computation: drifted tasks
    drifted_tasks = "Task 1: Build crypto casino roulette game\nTask 2: Implement solana wallet token staking\nTask 3: Add blackjack table"
    drifted_score = compute_drift_score(pk, drifted_tasks)
    assert drifted_score is not None, "Drifted score should not be None"
    assert drifted_score < 60.0, f"Drifted score unexpectedly high: {drifted_score}"
    health_drifted = goal_health_check(pk, drifted_tasks)
    assert "DRIFT DETECTED" in health_drifted, f"Expected DRIFT DETECTED, got: {health_drifted}"
    print(f"✅ Step 6: Drifted tasks score: {drifted_score}% ({health_drifted})")

    # 7. Evolution logging
    log_goal_evolution(
        project_key=pk,
        change_type="DRIFT",
        alignment_score=drifted_score,
        old_summary=aligned_tasks[:100],
        new_summary=drifted_tasks[:100],
        task_titles=["Crypto roulette", "Solana staking", "Blackjack table"]
    )
    log_goal_evolution(
        project_key=pk,
        change_type="REANCHOR",
        alignment_score=92.0,
        old_summary=drifted_tasks[:100],
        new_summary=baseline_goal[:100],
        reason="User requested re-anchoring to habit tracker",
        task_titles=["Restore auth", "Habit streaks", "Clean up non-habit tasks"]
    )
    print("✅ Step 7: Evolution logs appended (DRIFT + REANCHOR)")

    # 8. Report verification
    final_report = get_goal_drift_report(pk)
    assert final_report["total_sessions"] == 3, f"Expected 3 sessions, got {final_report['total_sessions']}"
    assert final_report["drift_events"] == 1, f"Expected 1 drift event, got {final_report['drift_events']}"
    assert final_report["reanchor_events"] == 1, f"Expected 1 reanchor event, got {final_report['reanchor_events']}"
    assert final_report["current_score"] == 92.0, f"Expected current_score 92.0, got {final_report['current_score']}"
    print(f"✅ Step 8: Full drift report structure verified: {final_report['total_sessions']} sessions, current score {final_report['current_score']}%")

    # 9. Tool exports
    assert len(goal_tracking_tools) == 2, f"Expected 2 tools, got {len(goal_tracking_tools)}"
    assert callable(goal_tracking_tools[0]) and callable(goal_tracking_tools[1])
    print("✅ Step 9: ADK goal_tracking_tools exported and callable")

    print("\n🎉 ALL PHASE 1 VERIFICATION CHECKS PASSED SUCCESSFULLY!\n")

if __name__ == "__main__":
    test_phase_1()
