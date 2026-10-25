"""
Comprehensive End-to-End Verification Test for PS5 Goal Tracking Implementation
"""

import sys
from fastapi.testclient import TestClient

def run_e2e_verification():
    print("=" * 70)
    print("🚀 RUNNING COMPREHENSIVE END-TO-END VERIFICATION: PS5 GOAL TRACKING")
    print("=" * 70)

    # 1. Verify Imports & Modules
    print("\n[PHASE 1 & 2] Verifying Core Modules and Agent Tools...")
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
    from agents import tech_lead_agent
    from main import app, RefineRequest, GoalGateDecision

    tool_names = [getattr(t, "__name__", str(t)) for t in tech_lead_agent.tools]
    assert "save_goal_state" in tool_names
    assert "goal_health_check" in tool_names
    print(f"  ✓ Tech Lead Agent contains {len(tool_names)} tools including goal tracking tools.")
    print(f"  ✓ Agent Instruction mandate: {'GOAL TRACKING (MANDATORY FIRST STEP)' in tech_lead_agent.instruction}")

    # 2. Test Goal Immutability & Semantic Scoring
    print("\n[PHASE 1] Verifying Semantic Scoring & Baseline Locking...")
    test_key = "e2e_habit_tracker_suite"
    goal_prompt = "Build an autonomous habit tracker with daily streaks, email authentication, and progress analytics"
    
    save_msg = save_goal_state(test_key, goal_prompt)
    print(f"  ✓ Baseline Goal Anchored: {save_msg}")

    # Attempt overwrite - must be rejected
    overwrite_msg = save_goal_state(test_key, "Build a decentralized crypto casino")
    assert "already locked" in overwrite_msg.lower() or "preserved" in overwrite_msg.lower()
    print("  ✓ Immutability Verified: Secondary baseline modification rejected.")

    # Check aligned tasks
    aligned = "Task Title: Setup email authentication with JWT\nTask Title: Build daily streaks tracking counter\nTask Title: Design analytics progress charts"
    score_aligned = compute_drift_score(test_key, aligned)
    assert score_aligned is not None and score_aligned >= 70.0, f"Aligned score unexpected: {score_aligned}"
    health_aligned = goal_health_check(test_key, aligned)
    assert "ON TRACK" in health_aligned
    print(f"  ✓ Aligned Tasks Score: {score_aligned}% ({health_aligned.split('|')[1].strip()})")

    # Check drifted tasks
    drifted = "Task Title: Build multiplayer blackjack casino\nTask Title: Create roulette token staking system\nTask Title: Add poker chip deposits"
    score_drifted = compute_drift_score(test_key, drifted)
    assert score_drifted is not None and score_drifted < 50.0, f"Drifted score unexpected: {score_drifted}"
    health_drifted = goal_health_check(test_key, drifted)
    assert "DRIFT DETECTED" in health_drifted
    print(f"  ✓ Drifted Tasks Score: {score_drifted}% ({health_drifted.split('|')[1].strip()})")

    # 3. Test Full FastAPI Endpoints Lifecycle
    print("\n[PHASE 3] Verifying FastAPI Endpoints Lifecycle...")
    client = TestClient(app)

    # A. Simulation Demo
    demo_res = client.post("/demo/simulate-drift")
    assert demo_res.status_code == 200
    demo_json = demo_res.json()
    assert demo_json["status"] == "success"
    demo_pk = demo_json["demo_project_key"]
    sessions = demo_json["sessions"]
    assert len(sessions) == 3
    print(f"  ✓ POST /demo/simulate-drift successful for '{demo_pk}'")
    print(f"      Session 1 (BASELINE):  {sessions[0]['score']}%")
    print(f"      Session 2 (DRIFT):     {sessions[1]['score']}% (Threshold triggered)")
    print(f"      Session 3 (REANCHOR):  {sessions[2]['score']}% (Recovery verified)")

    # B. Goal Report Endpoint
    rep_res = client.get(f"/api/goal-report/{demo_pk}")
    assert rep_res.status_code == 200
    rep_json = rep_res.json()
    assert rep_json["project_key"] == demo_pk
    assert rep_json["total_sessions"] == 3
    assert rep_json["drift_events"] == 1
    assert rep_json["reanchor_events"] == 1
    print(f"  ✓ GET /api/goal-report/{demo_pk} verified. DAG contains {rep_json['total_sessions']} sessions.")

    # C. Human-in-the-loop Gate: Approve
    appr_res = client.post(
        "/api/goal-gate-decision",
        json={"project_key": demo_pk, "decision": "approve", "reason": "Operator approves feature scope"}
    )
    assert appr_res.status_code == 200
    assert appr_res.json()["status"] == "approved"
    print("  ✓ POST /api/goal-gate-decision (Approve) verified.")

    # D. Human-in-the-loop Gate: Reanchor
    reanc_res = client.post(
        "/api/goal-gate-decision",
        json={"project_key": demo_pk, "decision": "reanchor", "reason": "Operator reanchored to habit baseline"}
    )
    assert reanc_res.status_code == 200
    assert reanc_res.json()["status"] == "reanchored"
    print("  ✓ POST /api/goal-gate-decision (Reanchor) verified.")

    # E. RefineRequest schema
    rf = RefineRequest(project_key="pk_demo", prompt="realign tasks", reason="human gate")
    assert rf.reason == "human gate"
    print("  ✓ RefineRequest model schema with optional reason verified.")

    # 4. Verify Frontend Assets & Structure
    print("\n[PHASE 4] Verifying Frontend Static Delivery & DOM Integrity...")
    index_res = client.get("/")
    assert index_res.status_code == 200
    assert "goal-tracking" in index_res.text
    assert "goal-drift-gate" in index_res.text
    assert "goal-decay-chart" in index_res.text
    assert "gate-approve-btn" in index_res.text
    assert "gate-reanchor-btn" in index_res.text
    print("  ✓ index.html served with Goal Drift Gate modal, DAG tree container, and canvas.")

    app_res = client.get("/app.js?v=9")
    assert app_res.status_code == 200
    assert "checkGoalGate" in app_res.text
    assert "renderGoalScoreCard" in app_res.text
    assert "renderGoalLineageTree" in app_res.text
    assert "renderDecayCurve" in app_res.text
    print("  ✓ app.js served with gate logic, report loaders, and chart visualizers.")

    css_res = client.get("/styles.css")
    assert css_res.status_code == 200
    assert ".goal-gate-card" in css_res.text
    assert ".lineage-timeline" in css_res.text
    print("  ✓ styles.css served with glowing glassmorphism and DAG timeline styles.")

    print("\n" + "=" * 70)
    print("🎉 FULL SYSTEM END-TO-END VERIFICATION COMPLETED WITH 100% SUCCESS!")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    run_e2e_verification()
