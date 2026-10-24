"""
ADK agents: Tech Lead (Firestore) + Research (web + optional arXiv) + Scrum (Notion + Calendar) + Workspace Prep.
"""

import os

from dotenv import load_dotenv
from google.adk.agents import Agent

from calendar_tool import (
    create_calendar_block,
    get_free_slots,
    get_team_free_slots,
    spread_task_dates,
)
from database import memory_tools_phase3
from notion_tool import create_kanban_card, list_kanban_cards
from research_tool import search_arxiv, search_web_snippets

load_dotenv()

ADK_MODEL = os.getenv("ADK_MODEL", "gemini-2.5-flash")
ADK_LITE = True


# ----------------------------
# Research Agent
# ----------------------------

research_agent = Agent(
    name="research_agent",
    model=ADK_MODEL,
    description="Finds sources via web search (DuckDuckGo); optional arXiv for papers.",
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
# Notion Kanban + Google Calendar Deep Work blocks.

scrum_master_agent = Agent(
    name="scrum_master_agent",
    model=ADK_MODEL,
    description="Creates real Kanban cards in Notion and blocks Deep Work time on Google Calendar.",
    instruction="""
You are the Scrum Master Agent.

When given a project and a **deadline** (plan end date) in the user message, you MUST **spread work in time**:

1. Decide how many concrete tasks you will create (typically 4–8; each gets a card + calendar block).
2. Call **spread_task_dates** with `plan_end_date` = that deadline (YYYY-MM-DD) and `num_tasks` = that count.
3. **Check availability BEFORE booking:**
   - **get_team_free_slots** only works if those Google calendars are shared with the OAuth account; if unsure or it errors, use **get_free_slots** with `date` only (organizer’s primary) to pick a start hour, or use the default hour pattern from **spread_task_dates** output.
   - If team member emails are provided and calendars are shared, call **get_team_free_slots** with `date` and `team_emails` (comma-separated) for each unique date.
   - Otherwise call **get_free_slots** with `date` and no `calendar_email` (or optional calendar_email for the token owner’s calendar only).
4. For **each** task **i** (1-based) in order, using date **D_i** from that list:
   a. Call **create_calendar_block** with `date=D_i`, this task’s title, `duration_hours=2`, `start_hour` from an available slot.
      If the assignee has a **work email** in the team roster, set **`invite_email`** to that address (event is created on the server’s calendar; **Google emails them a standard calendar invite** with the time). Do **not** set `calendar_email` to a teammate’s address unless you know that calendar is writable by the OAuth account; prefer **invite_email** for normal teammates.
   b. Call **create_kanban_card** with **deadline=D_i** and `assignee_name` = the team member's name so the card lands in their personal Kanban board.

5. Card fields (every task):
   - title: short, action-oriented
   - status='To Do'
   - deadline: **must match** **D_i** for that task’s calendar block
   - assignee_name: the **exact name** of the assigned team member (routes the card to their personal board)
   - description: **highly detailed** (at least 8–12 sentences or bullet blocks) including:
     • **Objective**: Clearly state the technical goal.
     • **Implementation Path**: Step-by-step logic or pseudo-code approach.
     • **Definition of Done**: Specific, measurable acceptance criteria.
     • **Architecture Context**: How this task fits into the broader system.
     • **Risks & Mitigation**: Potential blockers and how to avoid them.

6. Return a SHORT summary (2-3 sentences): how many cards created, how many calendar blocks booked, date range used.

Always create each **calendar block** before its matching **Notion** card.
Use status 'To Do' for all new tasks.

""",
    tools=[
        spread_task_dates,
        get_free_slots,
        get_team_free_slots,
        create_calendar_block,
        create_kanban_card,
        list_kanban_cards,
    ],
)


# ----------------------------
# Tech Lead Agent (Main)
# ----------------------------

tech_lead_agent = Agent(
    name="tech_lead_agent",
    model=ADK_MODEL,
    description="Main coordinator agent.",
    instruction="""
You are the Tech Lead Agent.

Your responsibilities:

1. Read existing project memory using the project_key.
2. Break the project into concrete tasks.
3. Assign each task to a specific team member.

You MUST always:

- Assign responsibility to a named team member.
- Ensure every task has an owner.
- Avoid duplicate task creation.

TEAM ASSIGNMENT:

Use each teammate's **real name and role** from the user's request (e.g. team_members in the payload),
from Firestore memory (`TEAM_MEMBERS`), or from earlier turns — do **not** use hardcoded example names.
If no roster exists, derive sensible role-only labels (e.g. "Backend engineer", "QA lead") and keep
assignments consistent with whatever the user specified.

When generating tasks, include:

Task Title  
Assigned To  
Description:
Acceptance Criteria:
Dependencies:
Risks:
Estimated Time:

If this is a refinement request:

You MUST:

- Identify what changed
- Update only affected tasks
- Keep existing tasks unchanged
- Do NOT recreate everything

Never generate a completely new plan from scratch during refinement.

OUTPUT FORMAT RULE (MANDATORY):

Every task MUST be printed using this structure:

Task Title:
Assigned To:
Description:
Acceptance Criteria:
Dependencies:
Risks:
Estimated Time:

Never omit the "Assigned To" field.

""",
    tools=memory_tools_phase3,
    sub_agents=[
        research_agent,
        scrum_master_agent,
    ],
)
