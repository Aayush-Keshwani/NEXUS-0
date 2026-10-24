"""
ADK agents: Tech Lead (Firestore) + Research (web + optional arXiv) + Scrum (Notion + Calendar) + Workspace Prep.
"""

import os

from dotenv import load_dotenv
from google.adk.agents import Agent

from database import memory_tools_phase3
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
    ],
)
