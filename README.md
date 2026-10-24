# Autonomous R&D System (Deep-Tech Sprint)

From a single mission brief to structured, persistent outputs: **Firestore** memory, **Google ADK** multi-agent orchestration, **Notion** Kanban and run workspaces, **Google Calendar** deep-work blocks with **guest invitations**, live web research, optional **on-disk workspace** scaffolding, and a **web control dashboard** served alongside the API.

## Capabilities at a glance

| Area | Implementation |
|------|----------------|
| **Orchestration** | **Tech Lead** coordinates **Research** (web + arXiv), **Scrum Master** (Notion + Calendar), and **Workspace Prep** (filesystem layout + README). |
| **Persistence** | **Firestore** for project memory, action logs, and **run history**. |
| **Workflow** | **`POST /trigger-pipeline`** sequences memory → optional research → Scrum (tasks, dates, calendar, Notion) → optional workspace artifacts and download links. |
| **Operations & UI** | **FastAPI**, **OpenAPI (Swagger)**, static **`/`** dashboard, and **Cloud Run**–friendly packaging for a single HTTP service. |

## Quick start (local)

```bash
python3 -m venv .adk_env
source .adk_env/bin/activate   # Windows: .adk_env\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # fill in values (see below)
python auth_setup.py            # Calendar OAuth → token.json (run on your laptop)
python main.py
```

| URL | Purpose |
|-----|---------|
| **`/`** | Dashboard UI (`frontend/`) |
| **`/docs`** | Swagger |
| **`/health`** | Liveness |

## Repo layout

| Path | Role |
|------|------|
| `main.py` | FastAPI: pipeline, static UI, run history API |
| `agents.py` | ADK agents (Tech Lead, Research, Scrum, Workspace) + model defaults |
| `database.py` | Firestore + memory / history tools |

## Security

- Never commit **`.env`**, **`token.json`**, or service account JSON.

Multi-agent planning with integrated tools, durable context, and a production-style API plus operator UI.

# NEXUS-0
