# Autonomous R&D Multi-Agent System — Comprehensive Project Status & Architecture Report

> **Target Audience:** AI brainstorming assistants, hackathon judges, technical reviewers, and collaborators.  
> **Last Updated:** October 24, 2026  
> **Repository:** `autonomous-rnd-system-main`  
> **Primary Hackathon Focus:** Long-Horizon Goal Tracking & Multi-Agent Deep-Tech Research & Development  
> **Master Hackathon Specification:** For exhaustive architecture diagrams, tech stack justifications ("why this, why that"), and PS5 compliance proofs, see [LONG_HORIZON_GOAL_TRACKING_AND_ARCHITECTURE.md](file:///home/fang/Downloads/Cognition-Hackthon/autonomous-rnd-system-main/LONG_HORIZON_GOAL_TRACKING_AND_ARCHITECTURE.md).

---

## 1. Executive Summary & Vision

The **Autonomous R&D System** is a production-grade multi-agent platform designed for long-horizon deep-tech engineering and scientific research (e.g., RISC processor synthesis, semiconductor thermal modeling, aerodynamic CFD optimization). 

The platform addresses the classic **"lost in the middle" context decay** failure mode of LLM agents operating over multi-day, multi-session horizons. Rather than allowing accumulating sub-tasks to drift the project away from its original requirements, our system introduces a **persistent, out-of-context Goal Invariant Contract layer**, an **automated re-grounding gate**, a **Time-Machine DAG Rollback engine**, and a **Live Dual-Track Ablation Arena** demonstrating agent performance with versus without tracking.

The entire system integrates with real-world developer workflows: auto-generating synthesized code repositories (e.g. Verilog RTL + testbenches), Notion Kanban project hubs, Google Calendar milestone synchronization, and live telemetry feeds.

---

## 2. Core Problem Statement Alignment: PS5 (Long-Horizon Goal Tracking)

Multi-session/multi-day agent workflows inevitably suffer from context decay: as sub-tasks accumulate, the agent loses track of foundational constraints.

| PS5 Requirement | How Our System Solves It | Technical Implementation |
| :--- | :--- | :--- |
| **1. Persistent Goal Layer** | Separated from the LLM's volatile working context; survives across sessions and reboots. | Ground truth contract anchored in Firestore (`goal_state` collection) and in-memory fallback. Content-addressed version hash (`goal_version`). |
| **2. Periodic Re-grounding** | Goal-consistency verification before each major engineering step. | `compute_drift_score()` and `goal_health_check()` ADK tools. Mathematical cosine similarity against 768-dim dense embeddings + deterministic feature hashing. |
| **3. Live Multi-Session Demonstration** | Genuine demonstration of goal drift with vs. without the tracking layer. | **Dual-Track Ablation Arena**: Track A (Uncontrolled context decay dropping to 14%) vs. Track B (Active invariant re-anchoring sustaining 94%). |
| **4. Evolution vs. Drift Distinction** | Mathematical differentiation between rogue drift (unlawful) and legitimate scope evolution (operator-approved). | **Goal Contract Invariant Matrix**: Separates non-negotiable **Hard Invariants** (`[INV-1..3]`) from **Plastic Soft Scope** (`[SCOPE-1..2]`). |

---

## 3. System Architecture & Tech Stack

```
                          ┌──────────────────────────────────────────────┐
                          │         MODERN SLATE WEB DASHBOARD           │
                          │   (Control Pipeline · Live Execution Graph   │
                          │    Dual-Track Arena · Time-Machine DAG)      │
                          └──────────────────────┬───────────────────────┘
                                                 │ HTTP / SSE / REST
                                                 ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 FASTAPI BACKEND RUNTIME                                │
│                                                                                        │
│  ┌──────────────────────┐  ┌─────────────────────────┐  ┌───────────────────────────┐  │
│  │   PIPELINE RUNNER    │  │  GOAL TRACKING ENGINE   │  │   EXTERNAL INTEGRATIONS   │  │
│  │ • Input Ingestion    │  │ • Invariant Extraction  │  │ • Notion Kanban / Hub     │  │
│  │ • Orchestrator Agent │  │ • Cosine Drift Math     │  │ • Google Calendar API     │  │
│  │ • Researcher Agent   │  │ • Re-grounding Gate     │  │ • Workspace Zipping       │  │
│  │ • Architect Agent    │  │ • Time-Machine DAG Tree │  │ • Firestore DB / Mock     │  │
│  │ • Synthesis Agent    │  │ • Dual-Track Ablation   │  │                           │  │
│  └──────────────────────┘  └─────────────────────────┘  └───────────────────────────┘  │
└────────────────────────────────────────┬───────────────────────────────────────────────┘
                                         │ Google GenAI SDK (ADK)
                                         ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                            LLM & EMBEDDING FOUNDATION LAYER                            │
│  • Primary Model: gemini-2.5-flash (with native thinking budget configuration)         │
│  • Embedding: text-embedding-004 / gemini-embedding-001 (Matryoshka 768-dim)           │
│  • Resiliency: Deterministic feature-hashing fallback + ADK tool error self-healing    │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### Technology Matrix
* **Backend:** Python 3.10+, FastAPI, Uvicorn, Pydantic v2.
* **LLM Core:** Google GenAI SDK (`google-genai`), Google ADK (`agent-development-kit`), `gemini-2.5-flash` with native thinking parameters (`ADK_THINKING_BUDGET`).
* **Database & Memory:** Google Cloud Firestore with zero-dependency `MockFirestoreClient` fallback for local/offline execution.
* **Embeddings:** `text-embedding-004` / `gemini-embedding-001` (768-dim) paired with a deterministic multi-salt n-gram/stem feature hashing fallback (`_fallback_hash_embedding`).
* **External APIs:** Notion API (Databases, Pages, Blocks), Google Calendar v3 API (OAuth2 + Service Account), MCP Bridge (`mcp_bridge.py`).
* **Frontend:** Vanilla CSS (Modern Calming Slate Dark Theme inspired by Linear & Supabase), Vanilla JavaScript (no bloat, pure reactive DOM), HTML5 Canvas for trajectory curves, SVG Bezier connector graphs.

---

## 4. Detailed Component Breakdown

### 4.1. The Multi-Agent Orchestration Pipeline (`agents.py`)
The pipeline coordinates four specialized Google ADK agents:
1. **Orchestrator / Intent Parser:** Ingests the initial deep-tech prompt, decomposes it into architectural milestones, sets timeline constraints, and extracts the goal contract.
2. **Research Agent (`research_tool.py`):** Conducts domain literature synthesis, mathematical formulations, and algorithm validation.
3. **Hardware / Software Architect Agent (`workspace_tool.py`):** Generates production directory structures, writes source files (e.g., Verilog RTL modules: `alu.v`, `regfile.v`, `control_unit.v`), testbenches, and architectural documentation.
4. **Synthesizer / Tech Lead Agent (`goal_tracking.py`):** Runs the `goal_health_check` tool before artifact signoff, verifies that zero hard invariants are violated, and generates executive summaries.

### 4.2. Long-Horizon Goal Tracking & Evolution Layer (`goal_tracking.py`)
* **Contract Invariant Matrix:**
  * **Hard Invariants (`hard_invariants`):** Foundational, non-negotiable clauses (e.g., `[INV-1] 16-Bit RISC ISA`, `[INV-2] 8-Word Register File & ALU`, `[INV-3] Automated Verilog Testbench`). Dropping any hard invariant triggers an immediate `CONTRACT_BREACH` and halts execution.
  * **Plastic Scope (`soft_scope`):** Permissible areas of growth (e.g., `[SCOPE-1] Memory-Mapped UART`, `[SCOPE-2] FPGA Synthesis Timing Constraints`). Incorporating soft scope with operator approval is classified as `LEGITIMATE_EVOLUTION`.
* **Cosine Drift Computation:**
  $$\text{Alignment Score} = \max(0.0, \min(100.0, \cos(\vec{E}_{\text{original}}, \vec{E}_{\text{current}}) \times 100))$$
  * Score $\ge 70\%$: `ON TRACK`
  * Score $< 70\%$: `DRIFT DETECTED` (Triggers human-in-the-loop gate or automated re-grounding).
* **Automated Re-Grounding Engine (`execute_auto_reground`):**
  * Synthesizes an injection payload containing the original anchor contract, identifies breached invariants, and prunes drifted tasks to realign subsequent agent steps.
* **Time-Machine DAG Rollback (`rollback_goal_checkpoint`):**
  * Maintains an append-only directed acyclic graph (DAG) of evolution sessions.
  * If an agent enters a dead-end or speculative branch in Session 3 or 4, the operator can click **"Rollback to S2"**, instantly pruning downstream drifted sessions and restoring the exact checkpoint baseline.

### 4.3. Dual-Track Live Ablation Arena
Simulates a multi-session horizon across two parallel tracks:
* **Track A (Uncontrolled / No Tracking):** Simulates context decay over 4 sessions without re-grounding:
  * Session 1: 100% (Baseline RISC ISA)
  * Session 2: 52% (Agent silently drops register testbench, adds crypto hashing unit)
  * Session 3: 28% (Agent drops instruction decoder, introduces speculative web server)
  * Session 4: 14% (Catastrophic collapse — core ISA completely abandoned)
* **Track B (Active Invariant Tracking):**
  * Session 1: 100% (Baseline ground truth contract anchored)
  * Session 2: 34.2% (Drift detected — gate triggered)
  * Session 3: 85.0% (Autonomous re-anchoring restores register file assertions `[INV-2, INV-3]`)
  * Session 4: 94.0% (Legitimate scope evolution: memory-mapped UART approved with 100% invariant preservation)
* **Visualizer:** Rendered on an HTML5 canvas featuring a glowing emerald curve (Track B) side-by-side with a red dashed decay line (Track A).

### 4.4. Developer Workflow Integrations
* **Notion Hub & Kanban Board (`notion_tool.py`):** Automatically creates a parent Notion R&D Hub, a dedicated Run Workspace page with embedded architecture specs, and a structured Kanban Board with task cards assigned to team members.
* **Google Calendar Scheduling (`calendar_tool.py`):** Schedules milestone check-ins, sprint reviews, and deadlines with attendee invites and Google Meet links.
* **Workspace Packager (`workspace_tool.py`):** Compiles all generated source code, documentation, and team member task breakdowns into a downloadable `.zip` archive.

---

## 5. Frontend UI/UX Architecture

The frontend is housed in `frontend/` and served directly by FastAPI at `/`:
* **Aesthetic:** Modern, calm slate dark theme (palette: dark slate `#0b0f19`, panel card `#111827`, border `#1f2937`, soft indigo accents `#6366f1`, emerald success `#10b981`, ruby warnings `#ef4444`).
* **Visualizer:** Live SVG bezier curves dynamically connecting pipeline nodes (`Receive Query` $\to$ `Parse Intent` $\to$ `Orchestration` $\to$ `Research` $\to$ `Architect` $\to$ `Synthesize`).
* **Control Tab:** Includes mission input textarea, deadline picker, sequence ID, dynamic team member generator (with role/email fields), and live terminal telemetry stream.
* **Goal Tracking Tab:** Displays the current alignment score hero pill, the Invariant Matrix checklist, the Goal Lineage DAG Tree with interactive Rollback buttons, and the Dual-Track Trajectory canvas.
* **Past Runs Sidebar:** Integrated collapsible history loaded from `localStorage` and synchronized with backend API, allowing one-click review of historical runs.
* **Instant Demo Seeding (`seedRichMockData`):** On startup, the UI immediately loads a completed, presentation-ready simulation of a 16-bit RISC core project (`risc_processor_core`) so reviewers can explore all tabs without waiting.

---

## 6. Complete API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/trigger-pipeline` | Ingests prompt, deadline, sequence key, and team members; triggers ADK agent workflow. |
| `GET` | `/api/goal-report/{project_key}` | Returns full goal evolution history, current score, invariant evaluation, and session DAG. |
| `GET` | `/api/goal-invariants/{project_key}` | Retrieves the hard constraints vs plastic scope matrix. |
| `POST` | `/demo/simulate-ablation` | Executes the 4-session Dual-Track Ablation simulation and returns trajectory coordinates. |
| `POST` | `/demo/simulate-drift` | Generates a single-session drift event and tests human gate triggering. |
| `POST` | `/api/auto-reground` | Executes autonomous re-anchoring payload injection for a drifted project. |
| `POST` | `/api/rollback-goal-checkpoint` | Rolls back project state to a target prior session in the DAG, pruning downstream sessions. |
| `POST` | `/api/goal-gate-decision` | Accepts operator decision (`approve` intentional evolution vs `reanchor` to genesis). |
| `GET` | `/api/run-history` | Returns the last $N$ pipeline execution summaries. |
| `GET` | `/api/download-workspace/{project_key}.zip` | Downloads the generated code repository ZIP. |

---

## 7. Verification & Test Suite Status

The codebase includes an exhaustive test suite covering all functional phases:
* `test_phase1_goal_tracking.py`: Mathematical embedding verification, drift threshold calculations, and Firestore persistence.
* `test_phase2_agents.py`: ADK tool signatures and prompt extraction.
* `test_phase3_backend.py`: FastAPI endpoints, gate decisions, and report endpoints.
* `test_phase5_e2e.py`: End-to-end integration across agents, database, and goal tracking.
* `test_phase6_winning_suite.py`: Multi-session invariant checking, rollback DAG pruning, and ablation metrics.
* `test_phase7_winning_backend.py`: HTTP endpoint testing for `/demo/simulate-ablation`, `/api/auto-reground`, and `/api/rollback-goal-checkpoint`.

**All test suites currently pass at 100%.**

---

## 8. Potential Brainstorming & Expansion Vectors (For AI Ideation)

When submitting this project status to another AI model for brainstorming, consider asking for ideas along the following high-value vectors:

1. **Blockchain & DeSci (Decentralized Science) Integration:**
   * On-chain immutable goal anchoring using Merkle Trees.
   * IP-NFT minting (ERC-721/ERC-6551) for prior-art timestamping and hardware patents.
   * Smart contract milestone escrows that only release funding when Goal Alignment $\ge 90\%$.
2. **Formal Verification & In-the-Loop Simulation:**
   * Hooking the hardware synthesis agent to formal Verilog verification tools (e.g. Yosys, Verilator, or SymbiYosys) to mathematically prove equivalence against the ISA invariants.
3. **Multi-Agent Adversarial Red-Teaming:**
   * Introducing a dedicated "Adversarial Drift Agent" whose explicit goal is to inject scope creep or subtle bugs into PRs, testing if the Goal Auditor catches them.
4. **Hierarchical Multi-Layer Invariant Trees:**
   * Nested goal contracts where system-level invariants decompose into subsystem invariants (e.g., ALU latency $< 2$ cycles, Register File 2-read/1-write port concurrency).
5. **Human-in-the-Loop Multi-Modal Interfaces:**
   * Voice-interactive architectural check-ins or interactive schematic diagram visualizers rendered directly in the canvas.
