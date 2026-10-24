"""
Drift Detector — Quantifies goal drift over time.
Enables with/without comparison and dashboard metrics.
"""

from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional

from database import get_run_history, db, FieldFilter
from goal_registry import get_goal, get_evolution_log


@dataclass
class DriftMetrics:
    project_key: str
    total_runs: int
    goal_versions: int
    semantic_drift_score: float      # 0.0 = identical, 1.0 = completely different
    action_alignment_rate: float     # % of runs where actions aligned with goal
    constraint_violations: int
    scope_creep_events: int
    legitimate_evolutions: int
    drift_events_total: int
    last_updated: str


def _embedding_distance(text1: str, text2: str) -> float:
    """
    Compute semantic distance between two texts.
    Uses simple word overlap as fallback (no external deps).
    Returns 0.0 = identical, 1.0 = no overlap.
    """
    if not text1 or not text2:
        return 1.0

    # Simple Jaccard similarity on word sets
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())

    if not words1 or not words2:
        return 1.0

    intersection = words1 & words2
    union = words1 | words2

    jaccard = len(intersection) / len(union) if union else 0.0
    return 1.0 - jaccard  # Convert to distance


def _is_aligned(summary: str, goal: str) -> bool:
    """Check if a run summary aligns with the goal (simple heuristic)."""
    if not summary or not goal:
        return True

    goal_words = set(goal.lower().split())
    summary_words = set(summary.lower().split())

    # Remove common words
    stopwords = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "is", "was", "were", "be", "been", "being", "have", "has", "had", "do", "does", "did", "will", "would", "could", "should", "may", "might", "can", "this", "that", "these", "those", "i", "you", "he", "she", "it", "we", "they", "them", "their", "our", "your", "my", "his", "her"}
    goal_words -= stopwords
    summary_words -= stopwords

    if not goal_words:
        return True

    overlap = goal_words & summary_words
    return len(overlap) / len(goal_words) > 0.3


def compute_drift_metrics(project_key: str) -> DriftMetrics:
    """Compute comprehensive drift metrics for a project."""
    from datetime import datetime

    goal = get_goal(project_key)
    if not goal:
        return DriftMetrics(
            project_key=project_key,
            total_runs=0,
            goal_versions=0,
            semantic_drift_score=0.0,
            action_alignment_rate=0.0,
            constraint_violations=0,
            scope_creep_events=0,
            legitimate_evolutions=0,
            drift_events_total=0,
            last_updated=datetime.now().isoformat(),
        )

    # Get all runs for this project
    runs = get_run_history(limit=200)
    project_runs = [r for r in runs if r.get("projectKey") == project_key]

    # Get evolution log
    evolution_log = get_evolution_log(project_key)

    legitimate = sum(1 for e in evolution_log if e.get("type") == "legitimate_evolution")
    constraint_violations = sum(1 for e in evolution_log if e.get("drift_type") == "constraint_violation")
    scope_creep = sum(1 for e in evolution_log if e.get("drift_type") == "scope_creep")
    drift_detected = sum(1 for e in evolution_log if e.get("type") == "drift_detected")

    # Semantic drift: original vs current goal
    semantic_drift = _embedding_distance(goal.original_goal, goal.current_goal)

    # Action alignment: check run summaries against current goal
    aligned_runs = 0
    for run in project_runs:
        summary = run.get("body", {}).get("outcome", {}).get("summary", "")
        if _is_aligned(summary, goal.current_goal):
            aligned_runs += 1

    alignment_rate = aligned_runs / len(project_runs) if project_runs else 0.0

    return DriftMetrics(
        project_key=project_key,
        total_runs=len(project_runs),
        goal_versions=goal.version,
        semantic_drift_score=semantic_drift,
        action_alignment_rate=alignment_rate,
        constraint_violations=constraint_violations,
        scope_creep_events=scope_creep,
        legitimate_evolutions=legitimate,
        drift_events_total=drift_detected,
        last_updated=datetime.now().isoformat(),
    )


def get_drift_timeline(project_key: str) -> List[Dict[str, Any]]:
    """Get timeline of goal evolution and drift events for visualization."""
    evolution_log = get_evolution_log(project_key)
    timeline = []

    for entry in evolution_log:
        timeline.append({
            "timestamp": entry.get("timestamp", ""),
            "version": entry.get("version", 1),
            "type": entry.get("type", "unknown"),
            "drift_type": entry.get("drift_type"),
            "reason": entry.get("reason", ""),
            "previous_goal": entry.get("previous_goal", ""),
            "new_goal": entry.get("new_goal", ""),
            "drift_score": entry.get("drift_score"),
            "proposed_action": entry.get("proposed_action"),
        })

    return timeline


def compute_drift_metrics_tool(project_key: str) -> str:
    """ADK tool wrapper for drift metrics."""
    metrics = compute_drift_metrics(project_key)
    return (
        f"📊 DRIFT METRICS FOR {project_key}\n"
        f"{'=' * 50}\n"
        f"Total Runs: {metrics.total_runs}\n"
        f"Goal Versions: {metrics.goal_versions}\n"
        f"Semantic Drift Score: {metrics.semantic_drift_score:.2%}\n"
        f"Action Alignment Rate: {metrics.action_alignment_rate:.2%}\n"
        f"Constraint Violations: {metrics.constraint_violations}\n"
        f"Scope Creep Events: {metrics.scope_creep_events}\n"
        f"Legitimate Evolutions: {metrics.legitimate_evolutions}\n"
        f"Drift Events Detected: {metrics.drift_events_total}\n"
        f"Last Updated: {metrics.last_updated[:19]}"
    )


def get_drift_timeline_tool(project_key: str) -> str:
    """ADK tool wrapper for drift timeline."""
    timeline = get_drift_timeline(project_key)
    if not timeline:
        return f"No drift timeline for {project_key}"

    output = f"📅 DRIFT TIMELINE FOR {project_key}\n" + "=" * 60 + "\n"
    for entry in timeline:
        ts = entry["timestamp"][:19] if entry["timestamp"] else "N/A"
        v = entry["version"]
        t = entry["type"]
        dt = entry.get("drift_type", "")
        reason = entry.get("reason", "")[:80]

        icon = "✅" if t == "legitimate_evolution" else "⚠️" if t == "drift_detected" else "📝"
        drift_label = f" [{dt}]" if dt else ""

        output += f"{icon} v{v} | {ts} | {t}{drift_label}\n"
        output += f"   Reason: {reason}\n"
        if entry.get("proposed_action"):
            output += f"   Action: {entry['proposed_action'][:80]}\n"
        output += "\n"

    return output


drift_detector_tools = [
    compute_drift_metrics_tool,
    get_drift_timeline_tool,
]


if __name__ == "__main__":
    from goal_registry import create_goal, evolve_goal, log_drift_event

    # Test
    create_goal(
        "test_drift",
        "Build a 16-bit RISC-V CPU in Verilog",
        ["Verilog RTL simulates", "5-stage pipeline"],
        ["Must use Verilog", "Deadline 2026-04-30"],
    )

    # Simulate some drift events
    log_drift_event("test_drift", "scope_creep", "Add cache subsystem", 0.5, "Not in acceptance criteria")
    log_drift_event("test_drift", "constraint_violation", "Rewrite in Chisel", 0.9, "Violates Verilog constraint")
    evolve_goal("test_drift", "Build a 16-bit RISC-V CPU in Verilog with cache", "Stakeholder approved cache addition")

    print(compute_drift_metrics_tool("test_drift"))
    print("\n" + get_drift_timeline_tool("test_drift"))