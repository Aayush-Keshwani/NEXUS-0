"""
Goal Registry — First-class goal representation layer.
Survives across sessions, separate from working memory/context.
"""

import json
import os
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any

from database import db, FieldFilter


@dataclass
class Goal:
    goal_id: str
    project_key: str
    original_goal: str              # The immutable original mission statement
    current_goal: str               # Evolved goal (may change legitimately)
    created_at: str
    updated_at: str
    version: int                    # Incremented on legitimate evolution
    acceptance_criteria: List[str]  # Measurable success criteria
    constraints: List[str]          # Hard constraints that must never change
    tags: List[str]                 # e.g. ["deep-tech", "verilog", "hardware"]
    parent_goal_id: Optional[str]   # For goal hierarchies
    metadata: Dict[str, Any]        # Extensible metadata

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Goal":
        # Handle backward compatibility
        return cls(
            goal_id=data.get("goal_id", ""),
            project_key=data.get("project_key", ""),
            original_goal=data.get("original_goal", ""),
            current_goal=data.get("current_goal", ""),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            version=data.get("version", 1),
            acceptance_criteria=data.get("acceptance_criteria", []),
            constraints=data.get("constraints", []),
            tags=data.get("tags", []),
            parent_goal_id=data.get("parent_goal_id"),
            metadata=data.get("metadata", {}),
        )


GOALS_COLLECTION = "goal_registry"
GOAL_EVOLUTION_LOG = "goal_evolution_log"


def _get_db():
    """Get Firestore client, handling mock mode."""
    return db


def create_goal(
    project_key: str,
    original_goal: str,
    acceptance_criteria: List[str],
    constraints: List[str],
    tags: List[str] = None,
    metadata: Dict[str, Any] = None,
) -> Goal:
    """Create a new goal for a project."""
    db_client = _get_db()
    goal_id = f"goal_{project_key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    now = datetime.now().isoformat()
    goal = Goal(
        goal_id=goal_id,
        project_key=project_key,
        original_goal=original_goal,
        current_goal=original_goal,
        created_at=now,
        updated_at=now,
        version=1,
        acceptance_criteria=acceptance_criteria or [],
        constraints=constraints or [],
        tags=tags or [],
        parent_goal_id=None,
        metadata=metadata or {},
    )
    try:
        db_client.collection(GOALS_COLLECTION).document(goal_id).set(goal.to_dict())
        print(f"🎯 Goal created: {goal_id} for project {project_key}")
    except Exception as e:
        print(f"⚠️ Goal create error (may be mock mode): {e}")
    return goal


def get_goal(project_key: str) -> Optional[Goal]:
    """Get the latest goal for a project."""
    db_client = _get_db()
    try:
        docs = db_client.collection(GOALS_COLLECTION).where(
            filter=FieldFilter("project_key", "==", project_key)
        ).order_by("created_at", direction="DESCENDING").limit(1).stream()
        for doc in docs:
            return Goal.from_dict(doc.to_dict())
    except Exception as e:
        print(f"⚠️ Goal retrieve error: {e}")
    return None


def get_goal_by_id(goal_id: str) -> Optional[Goal]:
    """Get a specific goal by ID."""
    db_client = _get_db()
    try:
        doc = db_client.collection(GOALS_COLLECTION).document(goal_id).get()
        if doc.exists:
            return Goal.from_dict(doc.to_dict())
    except Exception as e:
        print(f"⚠️ Goal get_by_id error: {e}")
    return None


def evolve_goal(
    project_key: str,
    new_goal: str,
    reason: str,
    acceptance_criteria: List[str] = None,
    constraints: List[str] = None,
    metadata: Dict[str, Any] = None,
) -> Goal:
    """
    Legitimate goal evolution — increments version, preserves history.
    This is for APPROVED changes, not drift.
    """
    db_client = _get_db()
    goal = get_goal(project_key)
    if not goal:
        raise ValueError(f"No goal found for {project_key}")

    # Archive old version
    old_version = Goal.from_dict(goal.to_dict())
    old_version.goal_id = f"{goal.goal_id}_v{goal.version}"
    try:
        db_client.collection(GOALS_COLLECTION).document(old_version.goal_id).set(old_version.to_dict())
    except Exception as e:
        print(f"⚠️ Goal archive error: {e}")

    # Create new version
    goal.version += 1
    goal.current_goal = new_goal
    goal.updated_at = datetime.now().isoformat()
    if acceptance_criteria is not None:
        goal.acceptance_criteria = acceptance_criteria
    if constraints is not None:
        goal.constraints = constraints
    if metadata is not None:
        goal.metadata.update(metadata)

    try:
        db_client.collection(GOALS_COLLECTION).document(goal.goal_id).set(goal.to_dict())
    except Exception as e:
        print(f"⚠️ Goal update error: {e}")

    # Log evolution reason
    try:
        db_client.collection(GOAL_EVOLUTION_LOG).document().set({
            "goal_id": goal.goal_id,
            "version": goal.version,
            "reason": reason,
            "timestamp": goal.updated_at,
            "previous_goal": old_version.current_goal,
            "new_goal": new_goal,
            "type": "legitimate_evolution",
        })
    except Exception as e:
        print(f"⚠️ Evolution log error: {e}")

    print(f"🎯 Goal evolved to v{goal.version}: {goal.goal_id}")
    return goal


def log_drift_event(
    project_key: str,
    drift_type: str,
    proposed_action: str,
    drift_score: float,
    explanation: str,
) -> None:
    """Log a detected drift event (not an evolution)."""
    db_client = _get_db()
    goal = get_goal(project_key)
    if not goal:
        return
    try:
        db_client.collection(GOAL_EVOLUTION_LOG).document().set({
            "goal_id": goal.goal_id,
            "version": goal.version,
            "reason": explanation,
            "timestamp": datetime.now().isoformat(),
            "previous_goal": goal.current_goal,
            "new_goal": goal.current_goal,  # unchanged
            "type": "drift_detected",
            "drift_type": drift_type,
            "proposed_action": proposed_action,
            "drift_score": drift_score,
        })
    except Exception as e:
        print(f"⚠️ Drift log error: {e}")


def get_goal_history(project_key: str) -> List[Dict[str, Any]]:
    """Full evolution history for drift analysis."""
    db_client = _get_db()
    try:
        docs = db_client.collection(GOALS_COLLECTION).where(
            filter=FieldFilter("project_key", "==", project_key)
        ).stream()
        return [doc.to_dict() for doc in docs]
    except Exception as e:
        print(f"⚠️ Goal history error: {e}")
        return []


def get_evolution_log(project_key: str) -> List[Dict[str, Any]]:
    """Get the evolution/drift log for a project's goal."""
    db_client = _get_db()
    goal = get_goal(project_key)
    if not goal:
        return []
    try:
        docs = db_client.collection(GOAL_EVOLUTION_LOG).where(
            filter=FieldFilter("goal_id", "==", goal.goal_id)
        ).order_by("timestamp").stream()
        return [doc.to_dict() for doc in docs]
    except Exception as e:
        print(f"⚠️ Evolution log retrieve error: {e}")
        return []


# ADK Tool Wrappers

def create_goal_tool(
    project_key: str,
    original_goal: str,
    acceptance_criteria: str,  # JSON string of list
    constraints: str,          # JSON string of list
    tags: str = "[]",          # JSON string of list
) -> str:
    """
    Create a new goal for a project.
    Use this at the START of a project to establish the goal tracking layer.
    """
    import json
    try:
        ac = json.loads(acceptance_criteria)
        cons = json.loads(constraints)
        tg = json.loads(tags)
    except json.JSONDecodeError as e:
        return f"❌ Invalid JSON in criteria/constraints/tags: {e}"

    goal = create_goal(project_key, original_goal, ac, cons, tg)
    return f"✅ Goal created: {goal.goal_id} (v{goal.version})\nOriginal: {goal.original_goal}"


def get_goal_tool(project_key: str) -> str:
    """Retrieve the current goal for a project."""
    goal = get_goal(project_key)
    if not goal:
        return f"No goal found for project: {project_key}"
    return (
        f"🎯 GOAL FOR {project_key}\n"
        f"ID: {goal.goal_id} (v{goal.version})\n"
        f"Original: {goal.original_goal}\n"
        f"Current: {goal.current_goal}\n"
        f"Acceptance Criteria: {goal.acceptance_criteria}\n"
        f"Constraints: {goal.constraints}\n"
        f"Tags: {goal.tags}"
    )


def evolve_goal_tool(
    project_key: str,
    new_goal: str,
    reason: str,
    acceptance_criteria: str = "[]",
    constraints: str = "[]",
) -> str:
    """
    Evolve the goal legitimately (user-approved change).
    Increments version, archives history, logs reason.
    """
    import json
    try:
        ac = json.loads(acceptance_criteria) if acceptance_criteria != "[]" else None
        cons = json.loads(constraints) if constraints != "[]" else None
    except json.JSONDecodeError as e:
        return f"❌ Invalid JSON: {e}"

    try:
        goal = evolve_goal(project_key, new_goal, reason, ac, cons)
        return f"✅ Goal evolved to v{goal.version}\nNew Goal: {goal.current_goal}\nReason: {reason}"
    except Exception as e:
        return f"❌ Evolution failed: {e}"


def get_goal_history_tool(project_key: str) -> str:
    """Get full goal evolution history."""
    history = get_goal_history(project_key)
    if not history:
        return f"No goal history for {project_key}"
    output = f"📜 GOAL HISTORY FOR {project_key}\n" + "=" * 50 + "\n"
    for h in history:
        output += f"v{h.get('version', 1)} | {h.get('updated_at', '')[:19]} | {h.get('current_goal', '')[:80]}\n"
    return output


goal_registry_tools = [
    create_goal_tool,
    get_goal_tool,
    evolve_goal_tool,
    get_goal_history_tool,
]


if __name__ == "__main__":
    # Quick test
    print("🧪 Testing Goal Registry...")
    g = create_goal(
        "test_project",
        "Build a 16-bit RISC-V CPU in Verilog",
        ["Verilog RTL simulates", "5-stage pipeline", "ALU ops: ADD,SUB,AND,OR,XOR,SLT"],
        ["Must use Verilog", "Deadline 2026-04-30", "Single synthesizable module"],
        ["risc-v", "verilog", "hardware"],
    )
    print(get_goal_tool("test_project"))
    evolve_goal("test_project", "Build a 16-bit RISC-V CPU in Verilog with cache", "Added cache per stakeholder request")
    print(get_goal_tool("test_project"))
    print(get_goal_history_tool("test_project"))