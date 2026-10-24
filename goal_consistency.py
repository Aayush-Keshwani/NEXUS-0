"""
Goal Consistency Checker — Pre-step validation to detect drift.
Called BEFORE each major agent step.
"""

import json
import os
from dataclasses import dataclass
from typing import Optional

from goal_registry import get_goal, log_drift_event


@dataclass
class ConsistencyResult:
    aligned: bool
    drift_score: float          # 0.0 = perfectly aligned, 1.0 = completely drifted
    drift_type: str             # "none" | "scope_creep" | "goal_substitution" | "constraint_violation"
    explanation: str
    recommended_action: str     # "proceed" | "pause_for_human" | "replan"


# Simple keyword-based heuristic for immediate feedback (no LLM call)
# This runs FIRST as a fast path before optional LLM deep check
_DRIFT_KEYWORDS = {
    "scope_creep": [
        "add", "include", "implement", "build", "create", "support", "integrate",
        "extend", "enhance", "feature", "module", "component", "subsystem",
    ],
    "goal_substitution": [
        "switch", "rewrite", "migrate", "port", "translate", "convert",
        "replace", "change to", "use instead", "different", "alternative",
    ],
    "constraint_violation": [
        "chisel", "vhdl", "systemverilog", "python", "c++", "rust", "go",  # language changes
        "remove constraint", "ignore", "bypass", "skip", "workaround",
    ],
}


def _heuristic_check(proposed_action: str, goal) -> ConsistencyResult:
    """Fast heuristic check — no LLM needed."""
    action_lower = proposed_action.lower()
    goal_lower = goal.current_goal.lower()
    constraints_lower = [c.lower() for c in goal.constraints]

    # Check constraint violations first (highest priority)
    for constraint in constraints_lower:
        if any(kw in action_lower for kw in _DRIFT_KEYWORDS["constraint_violation"]):
            if constraint.replace("must use ", "").replace("must not ", "") in action_lower:
                return ConsistencyResult(
                    aligned=False,
                    drift_score=0.9,
                    drift_type="constraint_violation",
                    explanation=f"Proposed action may violate constraint: '{constraint}'",
                    recommended_action="pause_for_human",
                )

    # Check for goal substitution (tech stack changes, etc.)
    for kw in _DRIFT_KEYWORDS["goal_substitution"]:
        if kw in action_lower:
            # Check if it's actually a substitution vs just mentioning
            if any(tech in action_lower for tech in ["chisel", "vhdl", "systemverilog", "rust", "go", "python"]):
                if "verilog" in goal_lower and "chisel" in action_lower:
                    return ConsistencyResult(
                        aligned=False,
                        drift_score=0.85,
                        drift_type="goal_substitution",
                        explanation=f"Tech stack change detected: goal specifies Verilog, action proposes alternative",
                        recommended_action="pause_for_human",
                    )

    # Check for scope creep (adding features not in acceptance criteria)
    scope_creep_score = 0.0
    matched_keywords = []
    for kw in _DRIFT_KEYWORDS["scope_creep"]:
        if kw in action_lower:
            matched_keywords.append(kw)
            scope_creep_score += 0.1

    # If action adds significant new work not obviously in criteria
    if scope_creep_score > 0.3:
        # Check if any acceptance criteria keywords match
        criteria_text = " ".join(goal.acceptance_criteria).lower()
        criteria_match = any(kw in criteria_text for kw in matched_keywords)
        if not criteria_match:
            return ConsistencyResult(
                aligned=False,
                drift_score=min(0.7, scope_creep_score),
                drift_type="scope_creep",
                explanation=f"Action adds work ({', '.join(matched_keywords)}) not clearly in acceptance criteria",
                recommended_action="pause_for_human",
            )

    return ConsistencyResult(
        aligned=True,
        drift_score=0.0,
        drift_type="none",
        explanation="Heuristic check passed — no obvious drift",
        recommended_action="proceed",
    )


def _llm_deep_check(proposed_action: str, goal, action_type: str) -> Optional[ConsistencyResult]:
    """Optional LLM-based deep consistency check."""
    try:
        import google.generativeai as genai
        api_key = os.getenv("GOOGLE_API_KEY")
        vertex = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "0") == "1"

        if vertex:
            # Vertex AI path - would need vertexai init
            return None
        elif api_key:
            genai.configure(api_key=api_key)
        else:
            return None

        prompt = f"""
ORIGINAL GOAL (immutable): {goal.original_goal}
CURRENT GOAL (v{goal.version}): {goal.current_goal}
ACCEPTANCE CRITERIA: {goal.acceptance_criteria}
HARD CONSTRAINTS (must never violate): {goal.constraints}

PROPOSED ACTION: {proposed_action}
ACTION TYPE: {action_type}

Analyze for goal drift. Return ONLY valid JSON:
{{
  "aligned": true/false,
  "drift_score": 0.0-1.0,
  "drift_type": "none|scope_creep|goal_substitution|constraint_violation",
  "explanation": "specific reasoning",
  "recommended_action": "proceed|pause_for_human|replan"
}}

Drift types:
- scope_creep: Action adds work not in acceptance criteria
- goal_substitution: Action pursues different outcome than current_goal
- constraint_violation: Action violates a hard constraint
"""

        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        text = response.text.strip()

        # Extract JSON from response
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]

        result = json.loads(text)
        return ConsistencyResult(**result)
    except Exception as e:
        print(f"⚠️ LLM consistency check failed: {e}")
        return None


def check_consistency(
    proposed_action: str,
    project_key: str,
    action_type: str = "task_execution",
    use_llm: bool = True,
) -> ConsistencyResult:
    """
    Called BEFORE each major step (research, scrum planning, workspace creation, etc.)

    Returns ConsistencyResult with drift assessment.
    """
    goal = get_goal(project_key)
    if not goal:
        return ConsistencyResult(
            aligned=True,
            drift_score=0.0,
            drift_type="none",
            explanation="No goal registered for project — skipping consistency check",
            recommended_action="proceed",
        )

    # Fast heuristic first
    heuristic_result = _heuristic_check(proposed_action, goal)

    # If heuristic says proceed, optionally do LLM deep check
    if heuristic_result.aligned and use_llm:
        llm_result = _llm_deep_check(proposed_action, goal, action_type)
        if llm_result:
            return llm_result

    # If heuristic detected drift, log it
    if not heuristic_result.aligned:
        log_drift_event(
            project_key=project_key,
            drift_type=heuristic_result.drift_type,
            proposed_action=proposed_action,
            drift_score=heuristic_result.drift_score,
            explanation=heuristic_result.explanation,
        )

    return heuristic_result


def check_consistency_tool(
    proposed_action: str,
    project_key: str,
    action_type: str = "task_execution",
) -> str:
    """ADK tool wrapper for consistency check."""
    result = check_consistency(proposed_action, project_key, action_type)
    status = "✅ ALIGNED" if result.aligned else f"⚠️ DRIFT DETECTED ({result.drift_type})"
    return (
        f"{status}\n"
        f"Drift Score: {result.drift_score:.2f}\n"
        f"Explanation: {result.explanation}\n"
        f"Recommended Action: {result.recommended_action}"
    )


if __name__ == "__main__":
    # Test with a mock goal
    from goal_registry import create_goal

    g = create_goal(
        "test_consistency",
        "Build a 16-bit RISC-V CPU in Verilog",
        ["Verilog RTL simulates", "5-stage pipeline", "ALU ops: ADD,SUB,AND,OR,XOR,SLT"],
        ["Must use Verilog", "Deadline 2026-04-30"],
    )

    # Test cases
    tests = [
        ("Research RISC-V pipeline hazards", "research"),
        ("Add L1 cache subsystem", "task_creation"),
        ("Implement UART peripheral", "task_creation"),
        ("Rewrite in Chisel for better parametrization", "tech_stack_change"),
        ("Add formal verification with SVA", "scope_expansion"),
    ]

    for action, atype in tests:
        print(f"\n🔍 Action: {action} ({atype})")
        result = check_consistency(action, "test_consistency", atype, use_llm=False)
        print(f"   Aligned: {result.aligned} | Score: {result.drift_score:.2f} | Type: {result.drift_type}")
        print(f"   {result.explanation}")
        print(f"   → {result.recommended_action}")