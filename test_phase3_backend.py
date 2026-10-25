"""
Verification test suite for Phase 3: FastAPI Backend Endpoints
"""

import sys
from fastapi.testclient import TestClient

def test_phase_3():
    print("=" * 60)
    print("RUNNING VERIFICATION FOR PHASE 3: main.py FastAPI Endpoints")
    print("=" * 60)

    try:
        from main import app, RefineRequest
    except Exception as e:
        print(f"❌ Failed to import main.py: {e}")
        sys.exit(1)

    client = TestClient(app)

    # 1. Test RefineRequest schema
    rr = RefineRequest(project_key="pk_1", prompt="update prompt", reason="scope change")
    assert rr.reason == "scope change", "RefineRequest.reason not captured!"
    rr_default = RefineRequest(project_key="pk_2", prompt="only prompt")
    assert rr_default.reason == "", "RefineRequest default reason not empty string!"
    print("✅ Step 1: RefineRequest schema backwards compatibility verified")

    # 2. Test POST /demo/simulate-drift
    demo_resp = client.post("/demo/simulate-drift")
    assert demo_resp.status_code == 200, f"Expected 200 from /demo/simulate-drift, got {demo_resp.status_code}: {demo_resp.text}"
    demo_data = demo_resp.json()
    assert demo_data["status"] == "success"
    demo_pk = demo_data["demo_project_key"]
    assert demo_pk.startswith("demo_drift_"), f"Unexpected demo key: {demo_pk}"
    sessions = demo_data["sessions"]
    assert len(sessions) == 3, f"Expected 3 sessions in simulation demo, got {len(sessions)}"
    assert sessions[0]["type"] == "BASELINE"
    assert sessions[1]["type"] == "DRIFT"
    assert sessions[2]["type"] == "REANCHOR"
    assert sessions[1]["score"] < 60.0, f"Drift score too high: {sessions[1]['score']}"
    assert sessions[2]["score"] >= 70.0, f"Reanchor score too low: {sessions[2]['score']}"
    assert "narrative" in demo_data
    print(f"✅ Step 2: POST /demo/simulate-drift verified ({demo_pk}):")
    print(f"   S1 Baseline: {sessions[0]['score']}%")
    print(f"   S2 Drift: {sessions[1]['score']}%")
    print(f"   S3 Re-anchor: {sessions[2]['score']}%")

    # 3. Test GET /api/goal-report/{demo_pk}
    report_resp = client.get(f"/api/goal-report/{demo_pk}")
    assert report_resp.status_code == 200, f"Expected 200, got {report_resp.status_code}"
    report_data = report_resp.json()
    assert report_data["project_key"] == demo_pk
    assert report_data["total_sessions"] == 3
    assert report_data["drift_events"] == 1
    assert report_data["reanchor_events"] == 1
    print(f"✅ Step 3: GET /api/goal-report/{demo_pk} verified with full report DAG")

    # 4. Test POST /api/goal-gate-decision (approve)
    gate_approve = client.post(
        "/api/goal-gate-decision",
        json={"project_key": demo_pk, "decision": "approve", "reason": "User approves feature addition"}
    )
    assert gate_approve.status_code == 200, f"Gate approve failed: {gate_approve.text}"
    assert gate_approve.json()["status"] == "approved"
    print("✅ Step 4: POST /api/goal-gate-decision (approve) verified")

    # 5. Test POST /api/goal-gate-decision (reanchor)
    gate_reanchor = client.post(
        "/api/goal-gate-decision",
        json={"project_key": demo_pk, "decision": "reanchor", "reason": "User chose to realign"}
    )
    assert gate_reanchor.status_code == 200, f"Gate reanchor failed: {gate_reanchor.text}"
    assert gate_reanchor.json()["status"] == "reanchored"
    print("✅ Step 5: POST /api/goal-gate-decision (reanchor) verified")

    # 6. Verify updated report shows new evolution sessions
    report_after = client.get(f"/api/goal-report/{demo_pk}").json()
    assert report_after["total_sessions"] == 5, f"Expected 5 sessions, got {report_after['total_sessions']}"
    assert report_after["intentional_changes"] >= 1
    print(f"✅ Step 6: Full lineage progression verified (now {report_after['total_sessions']} sessions in DAG)")

    print("\n🎉 ALL PHASE 3 VERIFICATION CHECKS PASSED SUCCESSFULLY!\n")

if __name__ == "__main__":
    test_phase_3()
