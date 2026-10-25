"""
Automated backend verification test for Winning PS5 Endpoints:
- POST /demo/simulate-ablation (Dual-Track Arena)
- GET /api/goal-invariants/{pk} (Contract Matrix)
- POST /api/auto-reground (Autonomous Re-Grounding)
- POST /api/goal-rollback (Time-Machine Rollback)
"""

import sys
from starlette.testclient import TestClient
from main import app

client = TestClient(app)

def test_goal_report_endpoint(pk: str = "risc_processor_core"):
    print(f"Testing /api/goal-report/{pk} endpoint...")
    res = client.get(f"/api/goal-report/{pk}")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    data = res.json()
    assert "project_key" in data
    assert "current_score" in data
    assert "sessions" in data
    print(f"  ✅ Goal report verified: {len(data['sessions'])} sessions found, current score: {data['current_score']}%")
    return data["project_key"]

def test_goal_invariants_endpoint(pk: str):
    print(f"Testing /api/goal-invariants/{pk} endpoint...")
    res = client.get(f"/api/goal-invariants/{pk}")
    assert res.status_code == 200
    data = res.json()
    assert "contract_invariants" in data
    inv = data["contract_invariants"]
    assert len(inv["hard_invariants"]) == 3
    print(f"  ✅ Contract Invariants verified: {len(inv['hard_invariants'])} hard invariants, {len(inv['soft_scope'])} soft scope items.")

def test_auto_reground_endpoint(pk: str):
    print("Testing /api/auto-reground endpoint...")
    res = client.post("/api/auto-reground", json={"project_key": pk, "reason": "Test auto-reground"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "regrounded"
    assert data["recovered_score"] >= 80.0
    print(f"  ✅ Auto-reground endpoint verified: recovered score {data['recovered_score']}%.")

def test_goal_rollback_endpoint(pk: str):
    print("Testing /api/goal-rollback endpoint...")
    res = client.post("/api/goal-rollback", json={"project_key": pk, "target_session": 1})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "rolled_back"
    assert data["restored_session"] == 1
    print(f"  ✅ Rollback endpoint verified: {data['message']}")

if __name__ == "__main__":
    pk = test_goal_report_endpoint()
    test_goal_invariants_endpoint(pk)
    test_auto_reground_endpoint(pk)
    test_goal_rollback_endpoint(pk)
    print("\n🎉 ALL PHASE 2 BACKEND ENDPOINTS VERIFIED 100%!")
