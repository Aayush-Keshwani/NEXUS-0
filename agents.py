"""
ADK agents: Tech Lead (Firestore) + Research (web + optional arXiv) + Scrum (Notion + Calendar) + Workspace Prep.
"""

import os

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.genai import types

from calendar_tool import create_calendar_block, get_free_slots, get_team_free_slots, spread_task_dates
from database import memory_tools_phase3
from notion_tool import create_kanban_card, list_kanban_cards
from research_tool import search_arxiv, search_web_snippets
from workspace_tool import prepare_project_workspace
from goal_tracking import goal_tracking_tools, goal_health_check, save_goal_state

load_dotenv()

# Active default Gemini model (Gemini 3.5 Flash: high throughput reasoning + ADK tool support)
ADK_MODEL = os.getenv("ADK_MODEL", "gemini-3.8-flash").strip() or "gemini-3.8-flash"

# Validated fallback models in order of priority (verified active on Google GenAI SDK)
ADK_FALLBACK_MODELS = list(dict.fromkeys([
    ADK_MODEL,
    "gemini-3.8-flash",
    "gemini-3.5-flash",
    "gemini-3-flash-preview",
]))

ADK_LITE = True

# Thinking budget configuration (Gemini 2.5 / 3.x feature)
# 0 = thinking disabled (lowest latency, fast tools); > 0 = thinking token budget
_raw_budget = os.getenv("ADK_THINKING_BUDGET", "0").strip()
try:
    _thinking_budget = int(_raw_budget)
except ValueError:
    _thinking_budget = 0


def get_agent_content_config(thinking_budget: int = _thinking_budget, temperature: float = 0.2) -> types.GenerateContentConfig:
    """Build modern GenerateContentConfig with thinking budget and temperature."""
    kwargs: dict = {"temperature": temperature}
    try:
        if thinking_budget >= 0:
            kwargs["thinking_config"] = types.ThinkingConfig(thinking_budget=thinking_budget)
    except Exception:
        pass
    return types.GenerateContentConfig(**kwargs)


def default_tool_error_handler(tool, args, context, error) -> dict:
    """Graceful ADK tool error callback: returns diagnostic info to agent instead of unhandled crash."""
    tool_name = getattr(tool, "name", str(tool))
    return {
        "status": "error",
        "tool": tool_name,
        "message": f"Tool execution failed: {str(error)}. Adjust input parameters or proceed with alternative approach.",
    }


# ----------------------------
# Research Agent
# ----------------------------

research_agent = Agent(
    name="research_agent",
    model=ADK_MODEL,
    description="Finds sources via web search (DuckDuckGo); optional arXiv for papers.",
    generate_content_config=get_agent_content_config(thinking_budget=0),
    on_tool_error_callback=default_tool_error_handler,
    instruction="""
You are the Research Agent (sub-agent only).

When given a technical topic:
1. Call search_web_snippets first with a short keyword query.
2. If academic preprints are needed, call search_arxiv.
3. Cite URLs from tool output.

Keep output concise bullet points only.
""",
    tools=[search_web_snippets, search_arxiv],
)


# ----------------------------
# Scrum Master Agent
# ----------------------------

scrum_master_agent = Agent(
    name="scrum_master_agent",
    model=ADK_MODEL,
    description="Creates real Kanban cards in Notion and blocks Deep Work time on Google Calendar.",
    generate_content_config=get_agent_content_config(thinking_budget=0, temperature=0.1),
    on_tool_error_callback=default_tool_error_handler,
    instruction="""
You are the Scrum Master Agent. Fast execution mode (1-min target):

When given a project and a deadline:
1. Create exactly 2 high-impact tasks (e.g. Task 1: Architecture & Design, Task 2: Core Implementation & Verification).
2. Call **spread_task_dates** with `num_tasks=2` and `plan_end_date`.
3. For EACH of the 2 tasks using date D_i from that list:
   a. Call **create_calendar_block** with `date=D_i`, `task_title`, `duration_hours=2`, `start_hour=10` (or 14).
      If the assignee has a work email, set `invite_email` to that address.
   b. Call **create_kanban_card** with `title`, `status='To Do'`, `deadline=D_i`, `assignee_name`, and a clear description containing:
      • **Objective**: Short technical goal.
      • **Implementation Path**: 2-3 key implementation steps.
      • **Definition of Done**: Measurable acceptance criterion.
4. Conclude with a 2-sentence summary of the created cards and calendar blocks.
Always create each calendar block before its matching Notion card.
""",
    tools=[
        spread_task_dates,
        create_calendar_block,
        create_kanban_card,
    ],
)


# ----------------------------
# Workspace Prep Agent (REAL)
# ----------------------------

workspace_prep_agent = Agent(
    name="workspace_prep_agent",
    model=ADK_MODEL,
    description="Creates a real starter folder layout and README on disk.",
    generate_content_config=get_agent_content_config(thinking_budget=0, temperature=0.1),
    on_tool_error_callback=default_tool_error_handler,
    instruction="""
You are the Workspace Preparation Agent.

After planning is clear:

1. Call prepare_project_workspace
2. Use a filesystem-safe project name
3. Return the path created

Do not invent paths.
""",
    tools=[prepare_project_workspace],
)


# ----------------------------
# Tech Lead Agent (Main)
# ----------------------------

tech_lead_agent = Agent(
    name="tech_lead_agent",
    model=ADK_MODEL,
    description="Main coordinator agent: plans tasks, evaluates goal health, books Google Calendar, and creates Notion Kanban cards.",
    generate_content_config=get_agent_content_config(thinking_budget=0, temperature=0.1),
    on_tool_error_callback=default_tool_error_handler,
    instruction="""
You are the Lead Project Architect. Fast execution mode (target < 30s):

Steps to execute:
1. Call **goal_health_check** with `project_key` and a 1-sentence summary of your 2 proposed core tasks.
   - If the health check reports drift warning or dropped invariants, immediately revise and realign your tasks to preserve all core invariants before proceeding!
2. Call **spread_task_dates** with `num_tasks=2` and `plan_end_date` (the deadline from the request).
3. For EACH of the 2 tasks (using date D_i from spread_task_dates):
   a. Call **create_calendar_block** with date=D_i, task_title, duration_hours=2, start_hour=10 (or 14).
      If the assignee has a work email in the team roster, set invite_email to that address.
   b. Call **create_kanban_card** with title, status='To Do', deadline=D_i, assignee_name, and a crisp description:
      • **Objective**: Technical goal.
      • **Implementation Path**: 2 key technical steps.
      • **Definition of Done**: Measurable acceptance criterion.
4. Output a concise 3-line summary of the plan and assigned team members.
Always create each calendar block before its matching Notion card.
""",
    tools=[
        goal_health_check,
        spread_task_dates,
        create_calendar_block,
        create_kanban_card,
        save_goal_state,
    ] + memory_tools_phase3,
    sub_agents=[
        scrum_master_agent,
        research_agent,
        workspace_prep_agent,
    ],
)

