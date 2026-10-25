"""
Verification test suite for Phase 1 Winning PS5 Enhancements:
- Goal Contract Invariant Matrix (Hard Invariants vs Plastic Scope)
- Evolution vs Drift mathematical rule engine
- Autonomous Re-Grounding Engine (Delta vector synthesis)
- Time-Machine Rollback (Rewind & Branch)
"""

import sys
from goal_tracking import (
    save_goal_state,
    compute_drift_score,
    get_goal_drift_report,
    extract_goal_invariants,
    get_goal_invariants,
    check_invariant_preservation,
    generate_regrounding_payload,
    execute_auto_reground,
    rollback_goal_checkpoint,
)

def test_extract_goal_invariants():
    print("Testing Goal Contract Invariant Extraction...")
    # Habit tracker
    goal_habit = "Build a habit tracker app with email authentication, daily streak tracking, and habit analytics"
    inv_habit = extract_goal_invariants(goal_habit)
    assert len(inv_habit["hard_invariants"]) == 3, f"Expected 3 hard invariants, got {len(inv_habit['hard_invariants'])}"
    assert any("auth" in i["keywords"] for i in inv_habit["hard_invariants"])
    assert any("streak" in i["keywords"] for i in inv_habit["hard_invariants"])
    assert len(inv_habit["soft_scope"]) >= 2
    print("  ✅ Habit tracker invariant extraction verified.")

    # Hardware Verilog
    goal_hw = "Design a 16-bit RISC processor in Verilog with ALU"
    inv_hw = extract_goal_invariants(goal_hw)
    assert len(inv_hw["hard_invariants"]) == 3
    assert any("risc" in i["keywords"] for i in inv_hw["hard_invariants"])
    print("  ✅ Hardware invariant extraction verified.")

def test_contract_preservation_and_drift_distinction():
    print("Testing Evolution vs. Drift Mathematical Rule Engine...")
    pk = "test_evolution_vs_drift"
    goal = "Build a habit tracker app with email authentication, daily streak tracking, and habit analytics"
    save_goal_state(pk, goal)

    # 1. Aligned baseline tasks -> HEALTHY
    s1_tasks = "Setup email authentication with JWT\nBuild habit CRUD API\nDaily streak counter"
    eval_s1 = check_invariant_preservation(pk, s1_tasks)
    assert eval_s1["contract_status"] == "HEALTHY", f"Expected HEALTHY, got {eval_s1['contract_status']}"
    assert eval_s1["preservation_rate"] == 100.0
    print("  ✅ Baseline verified as HEALTHY (100% preservation).")

    # 2. Dropped authentication + roulette betting added -> CONTRACT_BREACH
    s2_tasks = "Build viral social feed\nAdd roulette betting mini-game\nDaily streak counter"
    eval_s2 = check_invariant_preservation(pk, s2_tasks)
    assert eval_s2["contract_status"] == "CONTRACT_BREACH", f"Expected CONTRACT_BREACH, got {eval_s2['contract_status']}"
    assert len(eval_s2["dropped_invariants"]) > 0
    assert "roulette" in eval_s2["rogue_additions"]
    print("  ✅ Silent invariant loss flagged as CONTRACT_BREACH.")

    # 3. All invariants preserved + soft scope added (leaderboards) -> LEGITIMATE_EVOLUTION
    s3_tasks = "Setup email authentication with JWT\nBuild habit CRUD API\nDaily streak counter\nAdd friend leaderboards and badges"
    eval_s3 = check_invariant_preservation(pk, s3_tasks)
    assert eval_s3["contract_status"] == "LEGITIMATE_EVOLUTION", f"Expected LEGITIMATE_EVOLUTION, got {eval_s3['contract_status']}"
    assert len(eval_s3["active_soft_scope"]) > 0
    print("  ✅ Scope addition flagged as LEGITIMATE_EVOLUTION.")

def test_autonomous_regrounding():
    print("Testing Autonomous Re-Grounding Engine...")
    pk = "test_auto_reground_flow"
    goal = "Build a habit tracker app with email authentication, daily streak tracking, and habit analytics"
    save_goal_state(pk, goal)

    drifted_tasks = "Task: Roulette betting mini-game\nTask: Follower viral post feed"
    payload = generate_regrounding_payload(pk, drifted_tasks)
    assert payload["dropped_invariants_count"] > 0
    assert "roulette" in payload["regrounding_directive"].lower()
    assert len(payload["repaired_tasks"]) >= 2
    print(f"  ✅ Re-grounding directive generated: {payload['regrounding_directive'][:90]}...")

    # Execute auto-reground
    result = execute_auto_reground(pk)
    assert result["status"] == "regrounded"
    assert result["recovered_score"] >= 80.0
    print(f"  ✅ Autonomous re-ground executed. Score recovered to: {result['recovered_score']}%")

def test_time_machine_rollback():
    print("Testing Time-Machine State Rollback...")
    pk = "test_rollback_pk"
    goal = "Build a habit tracker with email auth and streaks"
    save_goal_state(pk, goal)

    # Simulate drift in session 2
    from goal_tracking import log_goal_evolution
    log_goal_evolution(pk, "DRIFT", 35.0, "old", "new", reason="Drift to roulette", task_titles=["Roulette game"])
    log_goal_evolution(pk, "DRIFT", 15.0, "old", "new", reason="Drift to crypto casino", task_titles=["Crypto casino"])

    report_before = get_goal_drift_report(pk)
    assert len(report_before["sessions"]) == 3, f"Expected 3 sessions, got {len(report_before['sessions'])}"

    # Roll back to Session 1
    rollback_res = rollback_goal_checkpoint(pk, target_session=1)
    assert rollback_res["status"] == "rolled_back"
    assert rollback_res["pruned_sessions_count"] == 2
    
    report_after = get_goal_drift_report(pk)
    # Target session 1 + 1 rollback evolution event = 2 sessions
    assert len(report_after["sessions"]) == 2
    print("  ✅ Time-machine rollback verified: pruned 2 drifted downstream sessions.")

if __name__ == "__main__":
    test_extract_goal_invariants()
    test_contract_preservation_and_drift_distinction()
    test_autonomous_regrounding()
    test_time_machine_rollback()
    print("\n🎉 ALL PHASE 1 WINNING UNIT TESTS PASSED 100%!")
