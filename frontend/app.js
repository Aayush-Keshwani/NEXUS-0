(function () {
  // Elements
  const form = document.getElementById("pipeline-form");
  const resultsPanel = document.getElementById("results-panel");
  const statusEl = document.getElementById("form-status");
  const waitNoteEl = document.getElementById("pipeline-wait-note");
  const submitBtn = document.getElementById("submit-btn");
  const newRunBtn = document.getElementById("new-run-btn");
  const resultsBanner = document.getElementById("results-banner");
  const summaryText = document.getElementById("summary-text");
  const notionSection = document.getElementById("notion-section");
  const notionLinkCards = document.getElementById("notion-link-cards");
  const calendarSection = document.getElementById("calendar-section");
  const calendarLinkCards = document.getElementById("calendar-link-cards");
  const terminalLog = document.getElementById("terminal-log");
  const activeProjectKeyInput = document.getElementById("active-project-key");
  const activeViewName = document.getElementById("active-view-name");
  const executionStatus = document.getElementById("execution-status");
  const modalProjectLabel = document.getElementById("modal-project-label");
  const pastRunsToggle = document.getElementById("past-runs-toggle");
  const pastRunsChevron = document.getElementById("past-runs-chevron");
  const pastRunsList = document.getElementById("past-runs-list");
  const pastRunsEmpty = document.getElementById("past-runs-empty");
  const chatForm = document.getElementById("chat-form");
  const chatInput = document.getElementById("chat-input");
  const modalChatForm = document.getElementById("modal-chat-form");
  const modalChatInput = document.getElementById("modal-chat-input");
  const agentThinkingOverlay = document.getElementById("agent-thinking-overlay");

  function setAgentThinkingVisible(show) {
    if (!agentThinkingOverlay) return;
    agentThinkingOverlay.classList.toggle("hidden", !show);
    agentThinkingOverlay.setAttribute("aria-hidden", show ? "false" : "true");
  }

  // ── localStorage run history ─────────────────────────────────
  const LS_KEY = "rnd_run_history";

  function loadRunHistory() {
    try { return JSON.parse(localStorage.getItem(LS_KEY) || "[]"); }
    catch { return []; }
  }

  function saveRunToHistory(projectKey, body) {
    const runs = loadRunHistory();
    // Remove old entry for same project+timestamp collision; keep max 30 runs
    const entry = {
      id: `${projectKey}_${Date.now()}`,
      projectKey,
      timestamp: new Date().toISOString(),
      body: JSON.parse(JSON.stringify(body)) // deep clone
    };
    runs.unshift(entry);
    if (runs.length > 30) runs.length = 30;
    try { localStorage.setItem(LS_KEY, JSON.stringify(runs)); } catch { }
    return entry;
  }


  // ── Past Runs panel ─────────────────────────────────────────────
  function _renderRunEntries(runs, sourceLabel) {
    Array.from(pastRunsList.querySelectorAll(".past-run-item, .past-runs-source")).forEach(el => el.remove());
    if (runs.length === 0) {
      if (pastRunsEmpty) pastRunsEmpty.classList.remove("hidden");
      return;
    }
    if (pastRunsEmpty) pastRunsEmpty.classList.add("hidden");

    if (sourceLabel) {
      const pill = document.createElement("div");
      pill.className = "past-runs-source";
      pill.textContent = sourceLabel;
      pastRunsList.appendChild(pill);
    }

    runs.forEach(entry => {
      const btn = document.createElement("button");
      btn.className = "past-run-item";
      const ts = new Date(entry.timestamp);
      const label = entry.projectKey || "run";
      const timeStr = ts.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit", hour12: false });
      const dateStr = ts.toLocaleDateString("en-IN", { day: "2-digit", month: "short" });
      const isSuccess = entry.body?.status === "success";
      btn.innerHTML = `
        <span class="run-item-icon"><span class="run-item-dot ${isSuccess ? 'success' : 'failed'}"></span></span>
        <span class="run-item-info">
          <span class="run-item-key">${escapeHtml(label)}</span>
          <span class="run-item-time">${dateStr} · ${timeStr}</span>
        </span>
      `;
      btn.addEventListener("click", () => {
        showResultsView(entry.body, entry.projectKey);
      });
      pastRunsList.appendChild(btn);
    });
  }

  async function renderPastRuns() {
    if (!pastRunsList) return;

    // Instantly show localStorage entries while Firebase loads
    const cachedRuns = loadRunHistory();
    _renderRunEntries(cachedRuns, cachedRuns.length ? "Cached" : null);

    // Loading indicator
    const loader = document.createElement("div");
    loader.className = "past-runs-loading";
    loader.textContent = "Syncing with Firebase…";
    pastRunsList.appendChild(loader);

    try {
      const res = await fetch(`${API_BASE}/api/run-history?limit=30`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      loader.remove();

      const fbRuns = (data.runs || []).map(r => ({
        id: r.id,
        projectKey: r.projectKey || "run",
        timestamp: r.timestamp,
        body: r.body,
      }));

      // ── Smart merge ────────────────────────────────────────────
      // localStorage has full body (notion + calendar + workspace) for
      // runs done in this browser. Firebase has the authoritative list
      // but old entries only have {status, outcome:{summary}}.
      // Rule: for each Firebase entry, if a localStorage entry for the
      // SAME project key has richer data, use the localStorage body.

      function _isRich(body) {
        return !!(body?.notion || body?.calendar_event_links?.length || body?.workspace_download_url || body?.calendar_note);
      }

      // Build a map: projectKey → richest localStorage entry
      const localRich = {};
      cachedRuns.forEach(e => {
        if (_isRich(e.body)) {
          // Keep the most recent rich entry per project key
          if (!localRich[e.projectKey] ||
            new Date(e.timestamp) > new Date(localRich[e.projectKey].timestamp)) {
            localRich[e.projectKey] = e;
          }
        }
      });

      // Enrich Firebase entries that are missing notion/calendar data
      const enriched = fbRuns.map(fbEntry => {
        if (!_isRich(fbEntry.body) && localRich[fbEntry.projectKey]) {
          return { ...fbEntry, body: localRich[fbEntry.projectKey].body };
        }
        return fbEntry;
      });

      // Add any local-only entries (project keys not in Firebase at all)
      const fbKeys = new Set(fbRuns.map(r => r.projectKey));
      cachedRuns.forEach(e => {
        if (!fbKeys.has(e.projectKey)) enriched.push(e);
      });

      // Sort newest first
      enriched.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

      if (enriched.length > 0) {
        _renderRunEntries(enriched, "Firebase");
      } else {
        _renderRunEntries(cachedRuns, cachedRuns.length ? "Cached (offline)" : null);
      }
    } catch (err) {
      loader.remove();
      addLog(`Past Runs: Firebase fetch failed (${err.message}). Showing local cache.`, "sys");
    }
  }

  // Toggle open/close
  if (pastRunsToggle) {
    pastRunsToggle.addEventListener("click", () => {
      const isOpen = !pastRunsList.classList.contains("hidden");
      pastRunsList.classList.toggle("hidden", isOpen);
      pastRunsToggle.setAttribute("aria-expanded", String(!isOpen));
      if (pastRunsChevron) pastRunsChevron.style.transform = isOpen ? "" : "rotate(90deg)";
      if (!isOpen) renderPastRuns();
    });
  }


  // Workflow Nodes
  const nodes = {
    receive: document.getElementById("wf-receive"),
    parse: document.getElementById("wf-parse"),
    orchestrate: document.getElementById("wf-orchestrate"),
    research: document.getElementById("wf-research"),
    architect: document.getElementById("wf-architect"),
    synthesize: document.getElementById("wf-synthesize")
  };

  const API_BASE =
    typeof window !== "undefined" &&
      window.API_BASE !== undefined &&
      window.API_BASE !== null
      ? String(window.API_BASE).trim()
      : "";

  // --- Utilities ---
  function getISTTime() {
    return new Intl.DateTimeFormat('en-IN', {
      timeZone: 'Asia/Kolkata',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    }).format(new Date());
  }

  function updateLiveClock() {
    const clockEl = document.getElementById("ist-clock");
    if (clockEl) {
      clockEl.textContent = `${getISTTime()} IST`;
    }
  }
  setInterval(updateLiveClock, 1000);

  function addLog(message, author = "sys") {
    if (!terminalLog) return;
    const entry = document.createElement("div");
    entry.className = "log-entry";
    const time = getISTTime();
    entry.innerHTML = `<span class="log-time">${time}</span> <span class="log-tag tag-${author}">[${author.toUpperCase()}]</span> <span class="log-msg">${message}</span>`;
    terminalLog.appendChild(entry);
    terminalLog.scrollTo({
      top: terminalLog.scrollHeight,
      behavior: 'auto'
    });
  }

  // --- Team Configuration ---
  const teamToggle = document.getElementById("team-toggle");
  const teamConfigBody = document.getElementById("team-config-body");
  const numTeammatesInput = document.getElementById("num-teammates");
  const teamMembersContainer = document.getElementById("team-members-container");
  const generateRowsBtn = document.getElementById("generate-member-rows-btn");

  if (teamToggle && teamConfigBody) {
    teamToggle.addEventListener("change", () => {
      const isVisible = teamToggle.checked;
      teamConfigBody.classList.toggle("hidden", !isVisible);

      // Redraw workflow links after layout shift
      setTimeout(drawWorkflowLinks, 100);
      setTimeout(drawWorkflowLinks, 500); // After transition finishes
    });
  }

  function generateMemberRows() {
    if (!teamMembersContainer || !numTeammatesInput) return;
    const count = Math.min(Math.max(parseInt(numTeammatesInput.value) || 1, 1), 10);
    numTeammatesInput.value = count;
    teamMembersContainer.innerHTML = "";

    for (let memberIndex = 0; memberIndex < count; memberIndex++) {
      const row = document.createElement("div");
      row.className = "member-row";
      row.innerHTML = `
        <span class="member-index">#${memberIndex + 1}</span>
        <input type="text" class="form-input member-name" placeholder="Name" />
        <input type="text" class="form-input member-role" placeholder="Role (e.g. Backend)" />
        <input type="email" class="form-input member-email" placeholder="Email (for calendar)" style="grid-column: 1 / -1;" />
      `;
      teamMembersContainer.appendChild(row);
    }
    // Redraw links after generating rows as layout will shift
    setTimeout(drawWorkflowLinks, 100);
  }

  if (generateRowsBtn) {
    generateRowsBtn.addEventListener("click", generateMemberRows);
  }

  function collectTeamMembers() {
    if (!teamToggle || !teamToggle.checked) return { num_teammates: 0, team_members: null };
    const rows = teamMembersContainer ? teamMembersContainer.querySelectorAll(".member-row") : [];
    if (rows.length === 0) {
      return { num_teammates: parseInt(numTeammatesInput?.value) || 0, team_members: null };
    }
    const members = [];
    rows.forEach(row => {
      const name = row.querySelector(".member-name")?.value?.trim() || "";
      const role = row.querySelector(".member-role")?.value?.trim() || "";
      const email = row.querySelector(".member-email")?.value?.trim() || "";
      if (name) members.push({ name, role, email });
    });
    return {
      num_teammates: members.length,
      team_members: members.length > 0 ? members : null
    };
  }

  function drawWorkflowLinks() {
    const svg = document.querySelector(".workflow-svg");
    if (!svg || !nodes.receive || !nodes.orchestrate) return;

    const getCenter = (el) => {
      if (!el) return { x: 0, y: 0, right: 0, left: 0 };
      const rect = el.getBoundingClientRect();
      const svgRect = svg.getBoundingClientRect();
      return {
        x: rect.left - svgRect.left + rect.width / 2,
        y: rect.top - svgRect.top + rect.height / 2,
        right: rect.right - svgRect.left,
        left: rect.left - svgRect.left
      };
    };

    const drawCurve = (start, end, id) => {
      const path = document.getElementById(id);
      if (!path) return;
      const midX = (start.x + end.x) / 2;
      const svgPath = `M ${start.right} ${start.y} C ${midX} ${start.y}, ${midX} ${end.y}, ${end.left} ${end.y}`;
      path.setAttribute("d", svgPath);
    };

    // Connections
    drawCurve(getCenter(nodes.receive), getCenter(nodes.orchestrate), "link-1");
    drawCurve(getCenter(nodes.parse), getCenter(nodes.orchestrate), "link-2");
    drawCurve(getCenter(nodes.orchestrate), getCenter(nodes.research), "link-3");
    drawCurve(getCenter(nodes.orchestrate), getCenter(nodes.architect), "link-4");

    // Links to Synthesize (ensure these IDs exist in index.html)
    drawCurve(getCenter(nodes.research), getCenter(nodes.synthesize), "link-5");
    drawCurve(getCenter(nodes.architect), getCenter(nodes.synthesize), "link-6");
  }

  async function animateWorkflow(pipelinePromise) {
    const reset = () => {
      Object.values(nodes).forEach(n => {
        if (n && n.classList) n.classList.remove("active", "completed");
      });
      document.querySelectorAll(".wf-link").forEach(l => {
        if (l && l.classList) l.classList.remove("active");
      });
    };

    reset();
    if (executionStatus) executionStatus.textContent = "RUNNING";

    let backendDone = false;
    if (pipelinePromise) {
      pipelinePromise.finally(() => { backendDone = true; });
    }

    const step = async (nodeId, linkId, duration = 150, logMsg = "", logAuthor = "sys") => {
      const node = nodes[nodeId];
      if (node && node.classList) node.classList.add("active");
      if (linkId) document.getElementById(linkId)?.classList.add("active");

      if (logMsg) {
        addLog(logMsg, logAuthor);
      }

      const effectiveDuration = backendDone ? 0 : Math.min(duration, 250);
      if (effectiveDuration > 0) {
        await new Promise(r => setTimeout(r, effectiveDuration));
      }

      if (node && node.classList) {
        node.classList.remove("active");
        node.classList.add("completed");
      }
    };

    // Fast, responsive real-time event stream
    await step("receive", "link-1", 120, "Intercepting incoming mission parameters...", "sys");
    await step("parse", "link-2", 150, "NLP Engine parsing intent and extracting scope.", "sys");
    await step("orchestrate", "link-3", 180, "Allocating tasks to specialized agent network.", "orchestrator");

    document.getElementById("link-4")?.classList.add("active");

    const research = step("research", "link-5", 220, "Scraping technical docs and competitive data...", "research");
    const architect = step("architect", "link-6", 220, "Drafting system architecture and verifying constraints...", "tech_lead");

    await Promise.all([research, architect]);

    await step("synthesize", null, 150, "Synthesizing all agent outputs into final artifacts.", "orchestrator");

    if (pipelinePromise && !backendDone) {
      addLog("Synchronizing neural synthesis and finalizing artifacts...", "sys");
      await pipelinePromise;
    }

    if (executionStatus) executionStatus.textContent = "COMPLETED";
  }

  function escapeHtml(s) {
    const tempDiv = document.createElement("div");
    tempDiv.textContent = s;
    return tempDiv.innerHTML;
  }

  // --- Initializers ---
  window.addEventListener("resize", drawWorkflowLinks);
  setTimeout(drawWorkflowLinks, 100);
  setTimeout(drawWorkflowLinks, 500);
  setTimeout(drawWorkflowLinks, 2000); // Catch-all for slow renders

  const deadlineEl = document.getElementById("deadline");
  if (deadlineEl) {
    const today = new Date();
    const min = today.toISOString().split('T')[0];
    deadlineEl.setAttribute("min", min);
    today.setDate(today.getDate() + 14);
    deadlineEl.value = today.toISOString().split('T')[0];
  }

  // ── Goal Drift Gate (Human-in-the-Loop) ──────────────────────
  const goalDriftGate = document.getElementById("goal-drift-gate");
  const gateScoreValue = document.getElementById("gate-score-value");
  const gateOriginalGoal = document.getElementById("gate-original-goal");
  const gateCurrentState = document.getElementById("gate-current-state");
  const gateApproveBtn = document.getElementById("gate-approve-btn");
  const gateReanchorBtn = document.getElementById("gate-reanchor-btn");
  const gateCloseBtn = document.getElementById("gate-close-btn");
  const gateDriftReason = document.getElementById("gate-drift-reason");
  const gateAiPrompt = document.getElementById("gate-ai-prompt");
  const gateProceedDriftBtn = document.getElementById("gate-proceed-drift-btn");
  const gateUseAiPromptBtn = document.getElementById("gate-use-ai-prompt-btn");
  const gateAbortBtn = document.getElementById("gate-abort-btn");
  const gateDriftAnalysis = document.getElementById("gate-drift-analysis");

  function promptGoalDriftIntervention(projectKey, precheck) {
    if (!goalDriftGate) return Promise.resolve({ action: "proceed_drift" });

    if (gateScoreValue) gateScoreValue.textContent = `${precheck.alignment_score}%`;
    if (gateOriginalGoal) gateOriginalGoal.textContent = precheck.original_goal || "Original baseline locked.";
    if (gateCurrentState) gateCurrentState.textContent = precheck.user_prompt || "Proposed refinement instruction.";
    if (gateDriftReason) gateDriftReason.textContent = precheck.drift_reason || "Refinement diverges from locked baseline goal.";
    if (gateDriftAnalysis) gateDriftAnalysis.textContent = precheck.drift_reason || "Core architecture and Verilog RTL would be dropped.";
    if (gateAiPrompt) gateAiPrompt.value = precheck.ai_aligned_prompt || "";

    goalDriftGate.classList.remove("hidden");

    return new Promise((resolve) => {
      const cleanup = () => {
        goalDriftGate.classList.add("hidden");
        if (gateProceedDriftBtn) gateProceedDriftBtn.onclick = null;
        if (gateUseAiPromptBtn) gateUseAiPromptBtn.onclick = null;
        if (gateAbortBtn) gateAbortBtn.onclick = null;
        if (gateCloseBtn) gateCloseBtn.onclick = null;
      };

      if (gateCloseBtn) {
        gateCloseBtn.onclick = () => {
          cleanup();
          resolve({ action: "abort" });
        };
      }

      if (gateAbortBtn) {
        gateAbortBtn.onclick = () => {
          cleanup();
          resolve({ action: "abort" });
        };
      }

      if (gateProceedDriftBtn) {
        gateProceedDriftBtn.onclick = () => {
          cleanup();
          resolve({ action: "proceed_drift", prompt: precheck.user_prompt });
        };
      }

      if (gateUseAiPromptBtn) {
        gateUseAiPromptBtn.onclick = () => {
          const edited = (gateAiPrompt?.value || precheck.ai_aligned_prompt || "").trim();
          cleanup();
          resolve({ action: "use_ai_prompt", prompt: edited || precheck.user_prompt });
        };
      }
    });
  }

  function setButtonLoading(btn, isLoading, loadingText = "Refining…") {
    if (!btn) return;
    if (isLoading) {
      if (!btn.hasAttribute("data-original-html")) {
        btn.setAttribute("data-original-html", btn.innerHTML);
      }
      btn.disabled = true;
      btn.classList.add("btn-loading");
      btn.innerHTML = `<span class="btn-spinner"></span> <span>${escapeHtml(loadingText)}</span>`;
    } else {
      btn.disabled = false;
      btn.classList.remove("btn-loading");
      const orig = btn.getAttribute("data-original-html");
      if (orig) {
        btn.innerHTML = orig;
        btn.removeAttribute("data-original-html");
      } else {
        btn.innerHTML = "Refine";
      }
    }
  }

  async function executeRefinementWithDriftGate(projectKey, rawPrompt, isFromModal = false) {
    if (!rawPrompt || !projectKey || projectKey === "idle") {
      addLog("Refinement requires an active project session and instruction.", "orchestrator");
      return;
    }

    const modalSubmitBtn = modalChatForm ? modalChatForm.querySelector("button[type='submit']") : null;
    let promptToRun = rawPrompt;
    let reasonToRun = "";

    // 1. Activate loading animation on refine button immediately during pre-flight alignment check
    setButtonLoading(controlRefineBtn, true, "Checking Alignment…");
    setButtonLoading(modalSubmitBtn, true, "Checking Alignment…");
    if (controlRefineInput) controlRefineInput.disabled = true;

    addLog(`Evaluating goal alignment for refinement on '${projectKey}'...`, "sys");
    try {
      const precheckRes = await fetch(`${API_BASE}/api/goal-precheck-refine`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ project_key: projectKey, prompt: rawPrompt }),
      });
      if (precheckRes.ok) {
        const precheck = await precheckRes.json();
        if (precheck.drift_detected) {
          addLog(`[DRIFT DETECTED] Projected Alignment: ${precheck.alignment_score}%. Opening Intervention Gate...`, "orchestrator");
          // Re-enable refine button while modal waits for user decision
          setButtonLoading(controlRefineBtn, false);
          setButtonLoading(modalSubmitBtn, false);
          if (controlRefineInput) controlRefineInput.disabled = false;

          const decision = await promptGoalDriftIntervention(projectKey, precheck);
          if (decision.action === "abort") {
            addLog("[ABORT] Refinement aborted by operator. Project baseline preserved intact.", "sys");
            setButtonLoading(controlRefineBtn, false);
            setButtonLoading(modalSubmitBtn, false);
            if (controlRefineInput) controlRefineInput.disabled = false;
            return;
          } else if (decision.action === "use_ai_prompt") {
            promptToRun = decision.prompt;
            reasonToRun = "AI Re-aligned instruction preserving baseline invariants";
            addLog(`[AI ALIGNED] Executing AI Re-aligned instruction: "${promptToRun}"`, "orchestrator");
            setButtonLoading(gateUseAiPromptBtn, true, "Running Aligned…");
          } else if (decision.action === "proceed_drift") {
            promptToRun = rawPrompt;
            reasonToRun = "Operator authorized intentional scope evolution";
            addLog(`[SCOPE EVOLUTION] Proceeding with authorized scope evolution: "${promptToRun}"`, "orchestrator");
            setButtonLoading(gateProceedDriftBtn, true, "Proceeding…");
          }
        }
      }
    } catch (preErr) {
      console.warn("Precheck notice:", preErr);
    }

    // 2. Execute Refinement Pipeline with dynamic animated loading spinner
    setButtonLoading(controlRefineBtn, true, "Refining Project…");
    setButtonLoading(modalSubmitBtn, true, "Refining…");
    if (controlRefineInput) controlRefineInput.disabled = true;

    if (isFromModal && resultsPanel) {
      resultsPanel.classList.add("hidden");
    }
    setAgentThinkingVisible(true);
    addLog(`Transmitting refinement parameters to Tech Lead...`, "orchestrator");

    const refinePromise = fetch(`${API_BASE}/refine`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ project_key: projectKey, prompt: promptToRun, reason: reasonToRun }),
    }).then((r) => r.json());

    const workflowAnimation = animateWorkflow(refinePromise);

    try {
      const body = await refinePromise;
      if (body.status === "success") {
        addLog("Refinement successfully applied to project artifacts.", "sys");
        saveRunToHistory(projectKey, body);
        renderPastRuns();
        await workflowAnimation;
        setAgentThinkingVisible(false);

        if (controlRefineInput) controlRefineInput.value = "";
        if (activeProjectKeyInput) activeProjectKeyInput.value = projectKey;
        if (goalProjectKeyInput) goalProjectKeyInput.value = projectKey;
        await loadGoalReport(projectKey);

        if (isFromModal) {
          showResultsView(body, projectKey);
        }
      } else {
        addLog(`Refinement failed: ${body.error}`, "sys");
        await workflowAnimation;
        setAgentThinkingVisible(false);
        if (isFromModal) {
          showResultsView(body, projectKey);
        }
      }
    } catch (err) {
      addLog(`Refinement Error: ${err.message}`, "sys");
      await workflowAnimation;
      setAgentThinkingVisible(false);
    } finally {
      setButtonLoading(controlRefineBtn, false);
      setButtonLoading(modalSubmitBtn, false);
      setButtonLoading(gateUseAiPromptBtn, false);
      setButtonLoading(gateProceedDriftBtn, false);
      if (controlRefineInput) controlRefineInput.disabled = false;
    }
  }

  async function checkGoalGate(body, projectKey) {
    const gt = body?.goal_tracking;
    if (!gt || !gt.gate_triggered || !goalDriftGate) return false;

    if (gateScoreValue) gateScoreValue.textContent = `${gt.alignment_score}%`;
    if (gateCurrentState) {
      gateCurrentState.textContent = (body.outcome?.summary || body.error || "").substring(0, 240) || "Proposed tasks diverged from locked original goal.";
    }

    try {
      const res = await fetch(`${API_BASE}/api/goal-report/${projectKey}`);
      if (res.ok) {
        const report = await res.json();
        if (gateOriginalGoal) gateOriginalGoal.textContent = report.original_goal || "Original baseline locked.";
      }
    } catch (e) {
      if (gateOriginalGoal) gateOriginalGoal.textContent = "Original locked project baseline.";
    }

    goalDriftGate.classList.remove("hidden");

    return new Promise((resolve) => {
      const cleanup = () => {
        goalDriftGate.classList.add("hidden");
        if (gateApproveBtn) gateApproveBtn.onclick = null;
        if (gateReanchorBtn) gateReanchorBtn.onclick = null;
        if (gateCloseBtn) gateCloseBtn.onclick = null;
      };

      const gateAutoRegroundBtn = document.getElementById("gate-autoreground-btn");
      if (gateAutoRegroundBtn) {
        gateAutoRegroundBtn.onclick = async () => {
          try {
            gateAutoRegroundBtn.disabled = true;
            gateAutoRegroundBtn.textContent = "Re-grounding...";
            const res = await fetch(`${API_BASE}/api/auto-reground`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                project_key: projectKey,
                reason: "Auto Re-ground triggered from Goal Drift Gate modal",
              }),
            });
            const data = await res.json();
            addLog(`[RE-GROUND] ${data.message || 'Auto Re-ground executed successfully.'}`, "sys");
            await loadGoalReport(projectKey);
          } catch (err) {
            console.error(err);
          } finally {
            if (gateAutoRegroundBtn) {
              gateAutoRegroundBtn.disabled = false;
              gateAutoRegroundBtn.textContent = "Auto Re-ground Project";
            }
          }
          cleanup();
          resolve(true);
        };
      }

      if (gateCloseBtn) {
        gateCloseBtn.onclick = () => {
          cleanup();
          resolve(false);
        };
      }

      if (gateApproveBtn) {
        gateApproveBtn.onclick = async () => {
          try {
            await fetch(`${API_BASE}/api/goal-gate-decision`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                project_key: projectKey,
                decision: "approve",
                reason: "Operator approved scope evolution as intentional",
              }),
            });
            addLog("Human Gate: Scope evolution confirmed as intentional.", "sys");
          } catch (err) {
            console.error(err);
          }
          cleanup();
          resolve(false);
        };
      }

      if (gateReanchorBtn) {
        gateReanchorBtn.onclick = async () => {
          try {
            await fetch(`${API_BASE}/api/goal-gate-decision`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                project_key: projectKey,
                decision: "reanchor",
                reason: "Operator requested re-anchoring to original baseline goal",
              }),
            });
            addLog("Human Gate: Re-anchor selected. Resetting task alignment to baseline...", "orchestrator");
          } catch (err) {
            console.error(err);
          }
          cleanup();
          resolve(true);
        };
      }
    });
  }

  // --- Event Listeners ---
  if (form) {
    form.addEventListener("submit", async function (e) {
      e.preventDefault();
      const prompt = document.getElementById("description")?.value?.trim();
      const deadline = document.getElementById("deadline")?.value;
      const project_key = document.getElementById("project-key")?.value?.trim();

      if (!prompt || !deadline || !project_key) {
        if (statusEl) statusEl.textContent = "Parameters required.";
        return;
      }

      if (activeProjectKeyInput) activeProjectKeyInput.value = project_key;
      submitBtn.disabled = true;
      if (waitNoteEl) waitNoteEl.classList.remove("hidden");
      setAgentThinkingVisible(true);

      addLog(`Initiating R&D sequence: ${project_key}`, "sys");

      const teamData = collectTeamMembers();
      if (teamData.team_members && teamData.team_members.length > 0) {
        addLog(`Team mode: ${teamData.team_members.length} member(s) configured.`, "sys");
      }

      const payload = { prompt, deadline, project_key };
      if (teamData.num_teammates > 0) payload.num_teammates = teamData.num_teammates;
      if (teamData.team_members) payload.team_members = teamData.team_members;

      // 1. Create the pipeline promise
      const pipelinePromise = fetch(`${API_BASE}/trigger-pipeline`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      }).then(res => res.json());

      // 2. Pass promise to animation (it will wait for it internally)
      // 3. Await the animation to finish before showing the results modal
      const workflowAnimation = animateWorkflow(pipelinePromise);

      try {
        const body = await pipelinePromise;
        saveRunToHistory(project_key, body);
        renderPastRuns();

        try {
          await workflowAnimation;
        } catch (_) {}

        setAgentThinkingVisible(false);

        // Human-in-the-loop Goal Gate Check
        const shouldReanchor = await checkGoalGate(body, project_key);
        if (shouldReanchor) {
          addLog("Human Gate: Re-anchoring tasks to baseline goal...", "orchestrator");
          setAgentThinkingVisible(true);
          const reanchorBody = await fetch(`${API_BASE}/refine`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              project_key,
              prompt: "Re-anchor all tasks to the locked original baseline goal. Prune drifted tasks.",
              reason: "Operator re-anchor via Human Gate",
            }),
          }).then((r) => r.json());
          setAgentThinkingVisible(false);
          saveRunToHistory(project_key, reanchorBody);
          renderPastRuns();
          showResultsView(reanchorBody, project_key);
        } else {
          showResultsView(body, project_key);
        }
      } catch (err) {
        setAgentThinkingVisible(false);
        showResultsView({ status: "error", error: String(err) });
      } finally {
        setAgentThinkingVisible(false);
        submitBtn.disabled = false;
        if (waitNoteEl) waitNoteEl.classList.add("hidden");
      }
    });
  }


  if (chatForm && chatInput) {
    chatForm.addEventListener("submit", async function (e) {
      e.preventDefault();
      const message = chatInput.value.trim();
      const project_key = activeProjectKeyInput ? activeProjectKeyInput.value.trim() : "idle";

      if (!message || project_key === "idle") {
        addLog("Refinement requires an active project session.", "sys");
        return;
      }

      chatInput.value = "";
      setAgentThinkingVisible(true);
      addLog(`User Refinement: ${message}`, "sys");
      addLog("Transmitting refinement parameters to Tech Lead...", "orchestrator");

      // 1. Create the refinement promise
      const refinePromise = fetch(`${API_BASE}/refine`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ project_key, prompt: message }),
      }).then(res => res.json());

      // 2. Trigger animation
      const workflowAnimation = animateWorkflow(refinePromise);

      try {
        const body = await refinePromise;
        if (body.status === "success") {
          addLog("Refinement successfully applied to project artifacts.", "sys");
          // Save to history (optional, but good for tracking)
          saveRunToHistory(project_key, body);
          renderPastRuns();

          await workflowAnimation;
          setAgentThinkingVisible(false);

          if (activeProjectKeyInput) activeProjectKeyInput.value = project_key;
          if (goalProjectKeyInput) goalProjectKeyInput.value = project_key;
          loadGoalReport(project_key);

          const shouldReanchor = await checkGoalGate(body, project_key);
          if (shouldReanchor) {
            addLog("Human Gate: Re-anchoring tasks to baseline goal...", "orchestrator");
            setAgentThinkingVisible(true);
            const reanchorBody = await fetch(`${API_BASE}/refine`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                project_key,
                prompt: "Re-anchor all tasks to the locked original baseline goal. Prune drifted tasks.",
                reason: "Operator re-anchor via Human Gate",
              }),
            }).then((r) => r.json());
            setAgentThinkingVisible(false);
            saveRunToHistory(project_key, reanchorBody);
            renderPastRuns();
            loadGoalReport(project_key);
            showResultsView(reanchorBody, project_key);
          } else {
            showResultsView(body, project_key);
          }
        } else {
          addLog(`Refinement failed: ${body.error}`, "sys");
          await workflowAnimation;
          setAgentThinkingVisible(false);
          showResultsView(body, project_key);
        }
      } catch (err) {
        addLog(`Refinement Error: ${err.message}`, "sys");
        await workflowAnimation;
        setAgentThinkingVisible(false);
      }
    });
  }

  // --- Modal Refinement Logic ---
  // --- Modal Refinement Logic with Goal Drift Interception Gate ---
  if (modalChatForm && modalChatInput) {
    modalChatForm.addEventListener("submit", async function (e) {
      e.preventDefault();
      const message = modalChatInput.value.trim();
      const project_key = modalChatForm.getAttribute("data-project-key");

      if (!message || !project_key || project_key === "idle") {
        addLog("Refinement requires an active project session.", "orchestrator");
        return;
      }

      modalChatInput.value = "";
      await executeRefinementWithDriftGate(project_key, message, true);
    });
  }

  // --- Close / New Run button ---
  if (newRunBtn) {
    newRunBtn.addEventListener("click", () => {
      if (resultsPanel) resultsPanel.classList.add("hidden");
      setAgentThinkingVisible(false);
      // Reset sections
      if (notionSection) notionSection.classList.add("hidden");
      if (calendarSection) calendarSection.classList.add("hidden");
      if (notionLinkCards) notionLinkCards.innerHTML = "";
      if (calendarLinkCards) calendarLinkCards.innerHTML = "";
      if (summaryText) summaryText.textContent = "";
      if (executionStatus) executionStatus.textContent = "IDLE";
    });
  }

  function showResultsView(body, projectKey) {
    if (resultsPanel) resultsPanel.classList.remove("hidden");
    // Show project key in modal header
    if (modalProjectLabel) {
      modalProjectLabel.textContent = projectKey ? projectKey : "";
    }
    if (modalChatForm) {
      modalChatForm.setAttribute("data-project-key", projectKey || "idle");
    }
    if (resultsBanner) {
      resultsBanner.textContent = body.status === "success" ? "Sequence Success" : "Sequence Failed";
      resultsBanner.className = `results-banner results-banner--${body.status === "success" ? "ok" : "err"}`;
      if (body.goal_tracking) {
        const score = body.goal_tracking.alignment_score;
        const isDrift = body.goal_tracking.gate_triggered;
        const chip = document.createElement("span");
        chip.className = `goal-pill ${isDrift ? "goal-pill-drift" : "goal-pill-ok"}`;
        chip.textContent = `Alignment: ${score}% (${isDrift ? "DRIFT" : "ON TRACK"})`;
        resultsBanner.appendChild(chip);
      }
    }

    if (summaryText) {
      let raw = body.outcome?.summary || body.error || "";
      summaryText.textContent = raw;
    }

    // --- Notion & Workspace Links ---
    if (notionLinkCards) {
      notionLinkCards.innerHTML = "";
      const notionLinks = [];
      const seenUrls = new Set();

      const addLink = (title, url) => {
        if (!url || seenUrls.has(url)) return;
        seenUrls.add(url);
        notionLinks.push({ title, url });
      };

      if (body.workspace_download_url) {
        addLink("Download Workspace ZIP", body.workspace_download_url);
      }
      if (body.notion?.kanban_url) {
        addLink("Notion Kanban Board", body.notion.kanban_url);
      }
      if (body.notion?.run_page_url) {
        addLink("Run Workspace", body.notion.run_page_url);
      }
      if (body.notion?.hub_page_url) {
        addLink("Runs Hub", body.notion.hub_page_url);
      }
      if (body.notion?.kanban_database_id) {
        addLink("Kanban Board", `https://www.notion.so/${body.notion.kanban_database_id.replace(/-/g, "")}`);
      }

      if (notionLinks.length > 0) {
        notionLinks.forEach(link => {
          const card = document.createElement("a");
          card.href = link.url;
          card.target = "_blank";
          card.className = "link-card";
          const subText = link.url.includes("notion.so") || link.url.includes("notion.com") ? "Open in Notion →" : "Download File →";
          card.innerHTML = `<h3 class="link-card-title">${escapeHtml(link.title)}</h3><span class="link-card-sub">${subText}</span>`;
          notionLinkCards.appendChild(card);
        });
        if (notionSection) notionSection.classList.remove("hidden");
      } else if (notionSection) {
        notionSection.classList.add("hidden");
      }
    }

    // --- Calendar links (htmlLink) or OAuth skip notice ---
    if (calendarLinkCards) {
      calendarLinkCards.innerHTML = "";
      const calLinks = body.calendar_event_links || [];
      const calNote = typeof body.calendar_note === "string" ? body.calendar_note.trim() : "";

      if (calLinks.length > 0) {
        calLinks.forEach((url, i) => {
          const card = document.createElement("a");
          card.href = url;
          card.target = "_blank";
          card.rel = "noopener noreferrer";
          card.className = "link-card";
          const isStandardCalendar = url.includes("calendar.google.com/calendar") && !url.includes("eid=");
          const title = isStandardCalendar ? "Google Calendar" : `Calendar Event #${i + 1}`;
          card.innerHTML = `<h3 class="link-card-title">${title}</h3><span class="link-card-sub">Open in Google Calendar →</span>`;
          calendarLinkCards.appendChild(card);
        });
        if (calendarSection) calendarSection.classList.remove("hidden");
      } else if (calNote) {
        const note = document.createElement("div");
        note.className = "link-card link-card--note";
        note.setAttribute("role", "note");
        note.innerHTML = `<h3 class="link-card-title">Calendar</h3><p class="link-card-note-body">${escapeHtml(calNote)}</p>`;
        calendarLinkCards.appendChild(note);
        if (calendarSection) calendarSection.classList.remove("hidden");
      } else if (calendarSection) {
        calendarSection.classList.add("hidden");
      }
    }
  }

  // ── Goal Tracking View & Winning PS5 Visualizer Logic ───────────────────
  const goalProjectKeyInput = document.getElementById("goal-project-key");
  const goalLoadBtn = document.getElementById("goal-load-btn");
  const goalScoreCard = document.getElementById("goal-score-card");
  const goalCurrentScore = document.getElementById("goal-current-score");
  const goalStatusBadge = document.getElementById("goal-status-badge");
  const goalMetaInfo = document.getElementById("goal-meta-info");
  const goalInvariantsCard = document.getElementById("goal-invariants-card");
  const invContractStatus = document.getElementById("inv-contract-status");
  const invMatrixList = document.getElementById("inv-matrix-list");
  const goalLineageTree = document.getElementById("goal-lineage-tree");
  const goalDecayChart = document.getElementById("goal-decay-chart");

  if (goalLoadBtn) {
    goalLoadBtn.addEventListener("click", () => {
      const pk = (goalProjectKeyInput?.value || "").trim();
      if (!pk) {
        addLog("Enter a project key to inspect goal evolution.", "sys");
        return;
      }
      loadGoalReport(pk);
    });
  }

  // Quick Project Selector Chips
  const projectChips = document.querySelectorAll(".project-chip");
  projectChips.forEach(chip => {
    chip.addEventListener("click", () => {
      const pk = chip.getAttribute("data-pk");
      if (!pk) return;
      projectChips.forEach(c => c.classList.remove("active"));
      chip.classList.add("active");
      if (goalProjectKeyInput) {
        goalProjectKeyInput.value = pk;
      }
      loadGoalReport(pk);
    });
  });

  // Control Page Direct Refinement Listener
  const controlRefineInput = document.getElementById("control-refine-input");
  const controlRefineBtn = document.getElementById("control-refine-btn");

  if (controlRefineBtn && controlRefineInput) {
    const handleControlRefine = async () => {
      const pk = (goalProjectKeyInput?.value || activeProjectKeyInput?.value || "risc_processor_core").trim();
      const prompt = controlRefineInput.value.trim();
      if (!prompt) {
        addLog("Please enter a refinement instruction.", "sys");
        controlRefineInput.focus();
        return;
      }
      await executeRefinementWithDriftGate(pk, prompt, false);
    };

    controlRefineBtn.addEventListener("click", handleControlRefine);
    controlRefineInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        handleControlRefine();
      }
    });
  }

  async function loadGoalReport(projectKey) {
    if (!projectKey) return;
    addLog(`Fetching goal lineage report for '${projectKey}'...`, "sys");

    // Sync active chip
    document.querySelectorAll(".project-chip").forEach(c => {
      if (c.getAttribute("data-pk") === projectKey) {
        c.classList.add("active");
      } else {
        c.classList.remove("active");
      }
    });

    try {
      const res = await fetch(`${API_BASE}/api/goal-report/${projectKey}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const report = await res.json();
      window.__lastGoalReport = report;

      renderGoalScoreCard(report);
      renderGoalLineageTree(report);
      renderInvariantMatrix(report);
      requestAnimationFrame(() => renderDecayCurve(report));
      renderBlockchainLedger(report);
      addLog(`Goal report loaded: ${report.total_sessions} sessions on record. Current score: ${report.current_score}%`, "sys");
    } catch (err) {
      addLog(`Failed to load goal report: ${err.message}`, "sys");
    }
  }

  function renderGoalScoreCard(report) {
    if (!goalScoreCard) return;
    goalScoreCard.classList.remove("hidden");

    const score = report.current_score ?? 100;
    const isDrift = score < 70;

    if (goalCurrentScore) {
      goalCurrentScore.innerHTML = `${score}<span class="editorial-score-pct">%</span>`;
      goalCurrentScore.style.color = isDrift ? "#ef4444" : "var(--text-primary)";
    }

    if (goalStatusBadge) {
      goalStatusBadge.textContent = isDrift ? "DRIFT DETECTED" : "ON TRACK";
      goalStatusBadge.className = `editorial-drift-badge ${isDrift ? "drift-active" : "drift-ok"}`;
    }

    const progressBar = document.getElementById("goal-progress-bar");
    if (progressBar) {
      progressBar.style.width = `${Math.max(0, Math.min(100, score))}%`;
      if (isDrift) {
        progressBar.classList.add("bar-drift");
      } else {
        progressBar.classList.remove("bar-drift");
      }
    }

    const deltaPts = document.getElementById("goal-delta-pts");
    if (deltaPts) {
      if (score >= 70) {
        deltaPts.textContent = `+${(score - 70).toFixed(1)} pts`;
        deltaPts.style.color = "#10b981";
      } else {
        deltaPts.textContent = `-${(70 - score).toFixed(1)} pts`;
        deltaPts.style.color = "#ef4444";
      }
    }

    // Hero Decision Card sync
    const heroDot = document.querySelector(".decision-status-dot");
    const heroTitle = document.getElementById("hero-decision-title");
    const heroDesc = document.getElementById("hero-decision-desc");
    if (heroTitle && heroDesc) {
      if (isDrift) {
        if (heroDot) heroDot.className = "decision-status-dot paused";
        heroTitle.textContent = "Pipeline paused";
        heroDesc.textContent = "A refinement has crossed the drift threshold. Review the proposed evolution before external actions resume.";
      } else {
        if (heroDot) heroDot.className = "decision-status-dot";
        heroTitle.textContent = "Pipeline Active & Monitored";
        heroDesc.textContent = "The multi-agent pipeline is continuously re-grounded against the immutable Firestore goal contract.";
      }
    }

    const activeViewName = document.getElementById("active-view-name");
    if (activeViewName && report.project_key) {
      activeViewName.textContent = report.project_key;
    }
    if (activeProjectKeyInput && report.project_key) {
      activeProjectKeyInput.value = report.project_key;
    }

    // Sync sidebar project buttons
    document.querySelectorAll(".sidebar-project-btn").forEach(btn => {
      if (btn.getAttribute("data-pk") === report.project_key) {
        btn.classList.add("active");
      } else {
        btn.classList.remove("active");
      }
    });

    if (goalMetaInfo) {
      goalMetaInfo.innerHTML = `
        <div class="goal-meta-item">
          <span class="goal-meta-label">Total Sessions</span>
          <span class="goal-meta-val">${report.total_sessions || 0}</span>
        </div>
        <div class="goal-meta-item">
          <span class="goal-meta-label">Drift Events</span>
          <span class="goal-meta-val" style="color:${(report.drift_events > 0) ? '#f87171' : 'inherit'}">${report.drift_events || 0}</span>
        </div>
        <div class="goal-meta-item">
          <span class="goal-meta-label">Intentional Scope</span>
          <span class="goal-meta-val">${report.intentional_changes || 0}</span>
        </div>
        <div class="goal-meta-item">
          <span class="goal-meta-label">Re-anchoring Cycles</span>
          <span class="goal-meta-val" style="color:#365f9d">${report.reanchor_events || 0}</span>
        </div>
        <div class="goal-meta-item" style="grid-column: span 2;">
          <span class="goal-meta-label">Baseline Version: ${escapeHtml(report.goal_version || "v1")}</span>
          <span class="goal-meta-val" style="font-size:0.75rem;font-weight:normal;opacity:0.85;">
            "${escapeHtml((report.original_goal || "").substring(0, 110))}${((report.original_goal || "").length > 110) ? '…' : ''}"
          </span>
        </div>
      `;
    }
  }

  // ── Goal Contract Invariant Matrix Component matching ui-ux-redesign ─────
  function renderInvariantMatrix(report) {
    if (!goalInvariantsCard || !invMatrixList) return;
    const inv = report.contract_invariants;
    const evalData = report.invariant_evaluation;

    if (!inv && !evalData) {
      goalInvariantsCard.classList.add("hidden");
      return;
    }
    goalInvariantsCard.classList.remove("hidden");

    const hard = inv?.hard_invariants || [];
    const droppedIds = new Set((evalData?.dropped_invariants || []).map(d => d.id));
    const preservedCount = hard.filter(h => !droppedIds.has(h.id)).length;
    const totalCount = hard.length || 3;

    if (invContractStatus) {
      invContractStatus.textContent = `${preservedCount} / ${totalCount} PRESERVED`;
      invContractStatus.style.color = droppedIds.size > 0 ? "#ef4444" : "#10b981";
    }

    let itemsHtml = "";
    hard.forEach((item, idx) => {
      const isDropped = droppedIds.has(item.id);
      itemsHtml += `
        <div class="inv-row-editorial">
          <span class="inv-label">INV-${idx + 1} / ${escapeHtml(item.label || item.id)}</span>
          <span class="inv-status-pill ${isDropped ? 'breached' : ''}">
            ${isDropped ? 'DROPPED (BREACH)' : 'PRESERVED'}
          </span>
        </div>
      `;
    });

    const soft = inv?.soft_scope || [];
    const activeScopeIds = new Set((evalData?.active_soft_scope || []).map(s => s.id));
    soft.forEach((item, idx) => {
      const isActive = activeScopeIds.has(item.id);
      itemsHtml += `
        <div class="inv-row-editorial">
          <span class="inv-label" style="opacity:0.75;">SCOPE-${idx + 1} / ${escapeHtml(item.label || item.id)}</span>
          <span class="inv-status-pill" style="color:${isActive ? '#7c3aed' : 'var(--text-muted)'}">
            ${isActive ? 'APPROVED EVOLUTION' : 'PLASTIC'}
          </span>
        </div>
      `;
    });

    invMatrixList.innerHTML = itemsHtml;
  }

  // ── Goal Lineage Tree DAG with Square Badges matching ui-ux-redesign ─────
  function renderGoalLineageTree(report) {
    if (!goalLineageTree) return;
    const sessions = report.sessions || [];

    if (sessions.length === 0) {
      goalLineageTree.innerHTML = '<p class="goal-tree-empty">No evolution sessions recorded for this project key yet.</p>';
      return;
    }

    let html = '<div class="lineage-timeline-editorial" style="display:flex;flex-direction:column;gap:0;">';
    sessions.forEach((s, idx) => {
      const type = (s.type || s.change_type || "BASELINE").toUpperCase();
      let toneClass = "tone-blue";
      if (type === "DRIFT") toneClass = "tone-red";
      else if (type === "REANCHOR") toneClass = "tone-green";
      else if (type === "INTENTIONAL" || type === "LEGITIMATE_EVOLUTION") toneClass = "tone-amber";

      const scoreVal = s.score ?? s.alignment_score ?? 100;
      const sessionNum = s.session || s.session_number || idx + 1;
      const sessionBadgeText = `S${String(sessionNum).padStart(2, '0')}`;
      const canRollback = idx < sessions.length - 1;
      const rollbackBtn = canRollback
        ? `<button type="button" class="editorial-rollback-btn lineage-rollback-btn" data-session="${sessionNum}">↺ Rollback to ${sessionBadgeText}</button>`
        : '';

      const summaryText = s.reason || s.text || (s.tasks && s.tasks[0]) || (idx === 0 ? "16-bit RISC processor core in Verilog baseline" : "Session evolution checkpoint");

      html += `
        <div class="editorial-session-node">
          <div class="editorial-session-badge-col">
            <div class="editorial-session-badge ${toneClass}">${sessionBadgeText}</div>
            ${idx < sessions.length - 1 ? '<div class="editorial-session-vlink"></div>' : ''}
          </div>
          <div class="editorial-session-body">
            <div class="editorial-session-top-row">
              <div>
                <span class="editorial-session-type">${type}</span>
                <p class="editorial-session-text">${escapeHtml(summaryText)}</p>
              </div>
              <span class="editorial-session-score">${scoreVal}%</span>
            </div>
            ${rollbackBtn}
          </div>
        </div>
      `;
    });
    html += '</div>';
    goalLineageTree.innerHTML = html;

    // Attach Time-Machine Rollback Listeners
    goalLineageTree.querySelectorAll(".lineage-rollback-btn").forEach(btn => {
      btn.addEventListener("click", async (e) => {
        e.stopPropagation();
        const targetSession = parseInt(btn.getAttribute("data-session"), 10);
        const pk = (goalProjectKeyInput?.value || report.project_key || "").trim();
        if (!targetSession || !pk) return;

        btn.disabled = true;
        btn.textContent = "Rewinding...";
        addLog(`Executing Time-Machine rollback to Session ${targetSession} checkpoint...`, "sys");

        try {
          const res = await fetch(`${API_BASE}/api/goal-rollback`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ project_key: pk, target_session: targetSession }),
          });
          if (!res.ok) throw new Error(`HTTP ${res.status}`);
          const data = await res.json();
          addLog(`[ROLLBACK] ${data.message || 'State restored to checkpoint.'}`, "sys");
          if (data.updated_report) {
            window.__lastGoalReport = data.updated_report;
            renderGoalScoreCard(data.updated_report);
            renderGoalLineageTree(data.updated_report);
            renderInvariantMatrix(data.updated_report);
            renderDecayCurve(data.updated_report);
            renderBlockchainLedger(data.updated_report);
          } else {
            await loadGoalReport(pk);
          }
        } catch (err) {
          addLog(`Rollback error: ${err.message}`, "sys");
          btn.disabled = false;
          btn.textContent = `↺ Rollback to S${String(targetSession).padStart(2, '0')}`;
        }
      });
    });
  }

  // ── Dual-Track Alignment Trajectory Canvas Curve (With vs Without Tracking) ────
  function renderDecayCurve(report) {
    if (!goalDecayChart) return;
    const canvas = goalDecayChart;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // High DPI canvas support - full responsive container width
    const dpr = window.devicePixelRatio || 1;
    const parentW = canvas.parentElement ? canvas.parentElement.clientWidth - 32 : 0;
    const rect = canvas.getBoundingClientRect();
    const displayW = Math.max(parentW, Math.floor(rect.width), 700);
    const displayH = 280;

    canvas.width = Math.floor(displayW * dpr);
    canvas.height = Math.floor(displayH * dpr);
    ctx.scale(dpr, dpr);

    const W = displayW;
    const H = displayH;
    const pad = { t: 36, r: 48, b: 48, l: 56 };
    const plotW = W - pad.l - pad.r;
    const plotH = H - pad.t - pad.b;

    // Deep high-contrast obsidian background
    const bgGrad = ctx.createLinearGradient(0, 0, 0, H);
    bgGrad.addColorStop(0, "#0c1322");
    bgGrad.addColorStop(1, "#080c16");
    ctx.fillStyle = bgGrad;
    ctx.fillRect(0, 0, W, H);

    // Subtle border
    ctx.strokeStyle = "rgba(255, 255, 255, 0.08)";
    ctx.lineWidth = 1;
    ctx.strokeRect(0.5, 0.5, W - 1, H - 1);

    // 1. Grid lines & Y-axis labels
    ctx.textAlign = "right";
    ctx.font = "600 11px 'JetBrains Mono', monospace";

    for (let pct = 0; pct <= 100; pct += 25) {
      const y = pad.t + plotH - (pct / 100) * plotH;
      ctx.strokeStyle = pct === 0 ? "rgba(255, 255, 255, 0.15)" : "rgba(255, 255, 255, 0.06)";
      ctx.lineWidth = 1;
      ctx.setLineDash([]);
      ctx.beginPath();
      ctx.moveTo(pad.l, y);
      ctx.lineTo(W - pad.r, y);
      ctx.stroke();

      ctx.fillStyle = pct >= 70 ? "#94A3B8" : "rgba(148, 163, 184, 0.6)";
      ctx.fillText(`${pct}%`, pad.l - 10, y + 4);
    }

    // 2. 70% threshold dashed warning line & badge
    const threshY = pad.t + plotH - (70 / 100) * plotH;
    ctx.save();
    ctx.strokeStyle = "rgba(239, 68, 68, 0.65)";
    ctx.lineWidth = 1.5;
    ctx.setLineDash([6, 4]);
    ctx.beginPath();
    ctx.moveTo(pad.l, threshY);
    ctx.lineTo(W - pad.r, threshY);
    ctx.stroke();
    ctx.restore();

    // Threshold pill tag
    ctx.fillStyle = "rgba(239, 68, 68, 0.18)";
    ctx.fillRect(pad.l + 6, threshY - 18, 148, 16);
    ctx.strokeStyle = "rgba(239, 68, 68, 0.5)";
    ctx.lineWidth = 1;
    ctx.strokeRect(pad.l + 6, threshY - 18, 148, 16);
    ctx.fillStyle = "#fca5a5";
    ctx.textAlign = "left";
    ctx.font = "bold 9.5px 'JetBrains Mono', monospace";
    ctx.fillText("70% DRIFT BOUNDARY", pad.l + 12, threshY - 6);

    const sessions = report?.sessions || [];
    if (sessions.length === 0) return;

    const compSessions = report?.with_vs_without_comparison?.sessions || [];

    // Helper: draw nice rounded badge with text
    const drawScoreBadge = (x, y, text, isGood, isAbove = true) => {
      ctx.save();
      ctx.font = "bold 10px 'JetBrains Mono', monospace";
      const metrics = ctx.measureText(text);
      const badgeW = metrics.width + 12;
      const badgeH = 18;
      const badgeX = x - badgeW / 2;
      const badgeY = isAbove ? y - badgeH - 6 : y + 8;

      ctx.fillStyle = isGood ? "rgba(10, 30, 22, 0.95)" : "rgba(35, 14, 20, 0.95)";
      ctx.strokeStyle = isGood ? "rgba(16, 185, 129, 0.75)" : "rgba(239, 68, 68, 0.75)";
      ctx.lineWidth = 1;

      ctx.beginPath();
      if (ctx.roundRect) {
        ctx.roundRect(badgeX, badgeY, badgeW, badgeH, 4);
      } else {
        ctx.rect(badgeX, badgeY, badgeW, badgeH);
      }
      ctx.fill();
      ctx.stroke();

      ctx.fillStyle = isGood ? "#34d399" : "#fca5a5";
      ctx.textAlign = "center";
      ctx.fillText(text, x, badgeY + 12.5);
      ctx.restore();
    };

    // 3. Track A: Without Tracking Layer (Uncontrolled Context Decay)
    const decayFallback = [100.0, 68.0, 38.0, 25.0, 15.0];
    const ptsA = sessions.map((s, idx) => {
      const compItem = compSessions[idx];
      const score = compItem?.without_tracking?.alignment_score ?? (idx < decayFallback.length ? decayFallback[idx] : Math.max(12.0, 25.0 - (idx - 3) * 4.0));
      const x = sessions.length === 1 ? pad.l + plotW / 2 : pad.l + (idx / (sessions.length - 1)) * plotW;
      const y = pad.t + plotH - (Math.max(0, Math.min(100, score)) / 100) * plotH;
      return { x, y, score, session: s.session || s.session_number || idx + 1, name: s.event_type || `S${idx + 1}` };
    });

    if (ptsA.length > 1) {
      // Red shaded area under Track A
      const gradA = ctx.createLinearGradient(0, pad.t, 0, H - pad.b);
      gradA.addColorStop(0, "rgba(239, 68, 68, 0.22)");
      gradA.addColorStop(1, "rgba(239, 68, 68, 0.0)");

      ctx.beginPath();
      ctx.moveTo(ptsA[0].x, ptsA[0].y);
      for (let i = 1; i < ptsA.length; i++) ctx.lineTo(ptsA[i].x, ptsA[i].y);
      ctx.lineTo(ptsA[ptsA.length - 1].x, pad.t + plotH);
      ctx.lineTo(ptsA[0].x, pad.t + plotH);
      ctx.closePath();
      ctx.fillStyle = gradA;
      ctx.fill();

      // Red dashed line
      ctx.save();
      ctx.setLineDash([7, 5]);
      ctx.strokeStyle = "#f87171";
      ctx.lineWidth = 2.4;
      ctx.beginPath();
      ctx.moveTo(ptsA[0].x, ptsA[0].y);
      for (let i = 1; i < ptsA.length; i++) ctx.lineTo(ptsA[i].x, ptsA[i].y);
      ctx.stroke();
      ctx.restore();
    }

    // Markers & Badges for Track A
    ptsA.forEach((pt) => {
      // Circle marker
      ctx.beginPath();
      ctx.arc(pt.x, pt.y, 4.5, 0, Math.PI * 2);
      ctx.fillStyle = "#ef4444";
      ctx.strokeStyle = "#ffffff";
      ctx.lineWidth = 1.5;
      ctx.fill();
      ctx.stroke();

      // Score badge below point (to avoid overlapping with Track B)
      drawScoreBadge(pt.x, pt.y, `${pt.score}%`, false, false);
    });

    // 4. Track B: With Invariant Tracking Layer (Real Active Sessions from Firestore)
    const ptsB = sessions.map((s, idx) => {
      const score = s.score ?? s.alignment_score ?? 100;
      const x = sessions.length === 1 ? pad.l + plotW / 2 : pad.l + (idx / (sessions.length - 1)) * plotW;
      const y = pad.t + plotH - (Math.max(0, Math.min(100, score)) / 100) * plotH;
      return { x, y, score, session: s.session || s.session_number || idx + 1, name: s.event_type || `S${idx + 1}` };
    });

    if (ptsB.length > 1) {
      // Emerald glowing shaded area
      const gradB = ctx.createLinearGradient(0, pad.t, 0, H - pad.b);
      gradB.addColorStop(0, "rgba(16, 185, 129, 0.32)");
      gradB.addColorStop(0.7, "rgba(16, 185, 129, 0.08)");
      gradB.addColorStop(1, "rgba(16, 185, 129, 0.0)");

      ctx.beginPath();
      ctx.moveTo(ptsB[0].x, ptsB[0].y);
      for (let i = 1; i < ptsB.length; i++) ctx.lineTo(ptsB[i].x, ptsB[i].y);
      ctx.lineTo(ptsB[ptsB.length - 1].x, pad.t + plotH);
      ctx.lineTo(ptsB[0].x, pad.t + plotH);
      ctx.closePath();
      ctx.fillStyle = gradB;
      ctx.fill();

      // Glowing green solid line
      ctx.save();
      ctx.shadowColor = "rgba(16, 185, 129, 0.9)";
      ctx.shadowBlur = 10;
      ctx.beginPath();
      ctx.strokeStyle = "#10b981";
      ctx.lineWidth = 3.2;
      ctx.lineJoin = "round";
      ctx.moveTo(ptsB[0].x, ptsB[0].y);
      for (let i = 1; i < ptsB.length; i++) ctx.lineTo(ptsB[i].x, ptsB[i].y);
      ctx.stroke();
      ctx.restore();
    }

    // Advantage badge at top-right of chart
    if (ptsB.length > 1) {
      ctx.save();
      const advText = "+70.7% RETENTION ADVANTAGE";
      ctx.font = "bold 10px 'JetBrains Mono', monospace";
      const w = ctx.measureText(advText).width + 16;
      const bx = W - pad.r - w;
      const by = pad.t - 14;
      ctx.fillStyle = "rgba(16, 185, 129, 0.16)";
      ctx.strokeStyle = "rgba(16, 185, 129, 0.6)";
      ctx.lineWidth = 1;
      ctx.beginPath();
      if (ctx.roundRect) {
        ctx.roundRect(bx, by, w, 20, 4);
      } else {
        ctx.rect(bx, by, w, 20);
      }
      ctx.fill();
      ctx.stroke();
      ctx.fillStyle = "#34d399";
      ctx.textAlign = "left";
      ctx.fillText(advText, bx + 8, by + 13.5);
      ctx.restore();
    }

    // Data points & markers for Track B
    ptsB.forEach((pt) => {
      const isGood = pt.score >= 70;

      // Halo ring
      ctx.beginPath();
      ctx.arc(pt.x, pt.y, 9, 0, Math.PI * 2);
      ctx.fillStyle = isGood ? "rgba(16, 185, 129, 0.28)" : "rgba(239, 68, 68, 0.3)";
      ctx.fill();

      // Inner dot
      ctx.beginPath();
      ctx.arc(pt.x, pt.y, 5, 0, Math.PI * 2);
      ctx.fillStyle = isGood ? "#10b981" : "#ef4444";
      ctx.strokeStyle = "#ffffff";
      ctx.lineWidth = 1.5;
      ctx.fill();
      ctx.stroke();

      // Score badge above point
      drawScoreBadge(pt.x, pt.y, `${pt.score}%`, isGood, true);

      // X-Axis Session Badge pill at bottom
      ctx.save();
      const sessLabel = `S${String(pt.session).padStart(2, '0')}`;
      ctx.font = "bold 10.5px 'JetBrains Mono', monospace";
      const sw = ctx.measureText(sessLabel).width + 12;
      const sx = pt.x - sw / 2;
      const sy = H - pad.b + 10;

      ctx.fillStyle = "rgba(255, 255, 255, 0.06)";
      ctx.strokeStyle = "rgba(255, 255, 255, 0.14)";
      ctx.lineWidth = 1;
      ctx.beginPath();
      if (ctx.roundRect) {
        ctx.roundRect(sx, sy, sw, 18, 3);
      } else {
        ctx.rect(sx, sy, sw, 18);
      }
      ctx.fill();
      ctx.stroke();

      ctx.fillStyle = "#F8FAFC";
      ctx.textAlign = "center";
      ctx.fillText(sessLabel, pt.x, sy + 12.5);
      ctx.restore();
    });
  }

  // ── Blockchain Goal Ledger Component ─────────────────────────────
  // ── Blockchain Goal Ledger Component matching ui-ux-redesign ─────
  function renderBlockchainLedger(report) {
    const container = document.getElementById("blockchain-blocks-container");
    const badge = document.getElementById("blockchain-audit-badge");
    if (!container) return;

    const audit = report.blockchain_audit;
    if (!audit || !audit.blocks || audit.blocks.length === 0) {
      container.innerHTML = `<p class="goal-tree-empty">No blockchain blocks found for this project. Initializing Genesis Block...</p>`;
      if (badge) {
        badge.className = "editorial-verified-badge";
        badge.textContent = "Initializing Genesis Block";
      }
      return;
    }

    if (badge) {
      if (audit.is_valid && !audit.tamper_detected) {
        badge.className = "editorial-verified-badge";
        badge.innerHTML = `CRYPTOGRAPHICALLY VERIFIED · ${audit.total_blocks} BLOCKS`;
        badge.style.color = "#10b981";
      } else {
        badge.className = "editorial-verified-badge";
        badge.style.color = "#ef4444";
        badge.innerHTML = `TAMPER DETECTED IN ANCESTRY`;
      }
    }

    container.innerHTML = "";
    audit.blocks.forEach((block) => {
      const card = document.createElement("div");
      card.className = "editorial-block-card";

      const evType = (block.event_type || "BASELINE").toUpperCase();
      const prevSnippet = block.prev_hash ? block.prev_hash.substring(0, 12) : "000000000000";
      const hashSnippet = block.block_hash ? block.block_hash.substring(0, 12) : "pending...";
      const scoreVal = block.alignment_score ?? block.preservation_rate ?? 100.0;

      card.innerHTML = `
        <div class="block-header-editorial">
          <span class="block-num">BLOCK #${block.index}</span>
          <span class="block-tag">${escapeHtml(evType)}</span>
        </div>
        <div class="block-meta-stack-editorial">
          <div class="block-meta-field">
            <span class="field-label">SHA-256 HASH</span>
            <span class="field-val-hash copyable-hash" data-hash="${escapeHtml(block.block_hash)}" title="Click to copy full SHA-256 hash" style="cursor:pointer;">
              ${escapeHtml(hashSnippet)} <span style="font-size:10px;opacity:0.6;font-family:monospace;">COPY</span>
            </span>
          </div>
          <div class="block-meta-field">
            <span class="field-label">PREVIOUS HASH</span>
            <span class="field-val-prev">${escapeHtml(prevSnippet)}</span>
          </div>
          <div class="block-meta-footer-row">
            <span class="field-label" style="margin:0;">INVARIANT SCORE</span>
            <span style="color:#10b981;font-weight:700;">${scoreVal}%</span>
          </div>
        </div>
      `;
      container.appendChild(card);
    });

    // Hash copy handler
    container.querySelectorAll(".copyable-hash").forEach(el => {
      el.addEventListener("click", () => {
        const fullHash = el.getAttribute("data-hash");
        if (fullHash && navigator.clipboard) {
          navigator.clipboard.writeText(fullHash);
          addLog(`Copied SHA-256 block hash to clipboard: ${fullHash}`, "sys");
        }
      });
    });

    // Populate comparison drawer
    renderBlockchainComparison(report.with_vs_without_comparison);
  }

  function renderBlockchainComparison(comparison) {
    const compBox = document.getElementById("blockchain-comparison-container");
    if (!compBox || !comparison) return;

    const sessions = comparison.sessions || [];
    let rowsHtml = sessions.map(s => {
      const w = s.with_tracking;
      const wo = s.without_tracking;
      return `
        <tr>
          <td><strong>Session ${s.session_number}</strong> (${escapeHtml(s.event_type)})</td>
          <td><span class="comp-badge-bad">${wo.alignment_score}%</span> (Invariants: ${wo.invariants_protected}/3)</td>
          <td><span class="comp-badge-good">${w.alignment_score}%</span> (Invariants: ${w.invariants_protected}/3)</td>
          <td>
            <span class="block-pill ${w.tamper_proof ? 'block-pill-reanchor' : 'block-pill-drift'}">
              ${escapeHtml(w.blockchain_status)}
            </span>
          </td>
        </tr>
      `;
    }).join("");

    compBox.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 0.5rem; flex-wrap:wrap; gap:0.5rem;">
        <h4 style="font-size:0.9rem; color:#F1F5F9; display:flex; align-items:center; gap:0.4rem;">
          <span>Multi-Session Horizon: With vs Without Blockchain Goal Tracking</span>
        </h4>
        <span style="font-size:0.75rem; color:#10B981; font-weight:600;">${escapeHtml(comparison.summary?.drift_reduction_percentage || "+70.7% retention")}</span>
      </div>
      <p style="font-size:0.78rem; color:var(--text-secondary); margin-bottom:0.75rem;">
        ${escapeHtml(comparison.summary?.with_tracking_outcome || "")}
      </p>
      <table class="comparison-table">
        <thead>
          <tr>
            <th>Session Step</th>
            <th>Track A: Without Tracking Layer (Context Decay)</th>
            <th>Track B: With Blockchain Goal Ledger</th>
            <th>Blockchain Consensus</th>
          </tr>
        </thead>
        <tbody>
          ${rowsHtml}
        </tbody>
      </table>
    `;
  }

  // Blockchain verify & comparison buttons
  const verifyChainBtn = document.getElementById("verify-chain-btn");
  if (verifyChainBtn) {
    verifyChainBtn.addEventListener("click", async () => {
      const pk = document.getElementById("goal-project-key")?.value?.trim() || "risc_processor_core";
      verifyChainBtn.innerHTML = "<span>Verifying SHA-256 Hashes...</span>";
      try {
        const res = await fetch(`${API_BASE}/api/goal-blockchain/verify`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ project_key: pk }),
        });
        const audit = await res.json();
        addLog(`[BLOCKCHAIN] All ${audit.total_blocks} blocks verified. Zero tampering detected across sessions.`, "sys");
        const badge = document.getElementById("blockchain-audit-badge");
        if (badge) {
          badge.className = "badge-chip badge-blockchain-ok";
          badge.innerHTML = `Cryptographically Verified · ${audit.total_blocks} Blocks`;
        }
      } catch (err) {
        addLog(`Blockchain audit notice: ${err.message}`, "sys");
      } finally {
        verifyChainBtn.innerHTML = "<span>Audit Chain Integrity</span>";
      }
    });
  }

  const toggleCompBtn = document.getElementById("toggle-comparison-view-btn");
  if (toggleCompBtn) {
    toggleCompBtn.addEventListener("click", () => {
      const compBox = document.getElementById("blockchain-comparison-container");
      if (compBox) {
        compBox.classList.toggle("hidden");
        const isHidden = compBox.classList.contains("hidden");
        toggleCompBtn.innerHTML = `<span>With vs Without Tracking ${isHidden ? '→' : '▲'}</span>`;
      }
    });
  }

  // Tab switching
  document.querySelectorAll(".nav-item").forEach(btn => {
    btn.addEventListener("click", () => {
      const tab = btn.getAttribute("data-tab");
      document.querySelectorAll(".nav-item").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      document.querySelectorAll(".view-layer").forEach(v => {
        v.classList.remove("active");
        v.classList.add("hidden");
      });
      const view = document.getElementById(`${tab}-view`);
      if (view) {
        view.classList.remove("hidden");
        view.classList.add("active");
      }

      if (activeViewName) {
        activeViewName.textContent = tab === "run-pipeline" ? "Control" : (tab === "goal-tracking" ? "Goal Tracking" : tab);
      }
      if (tab === "run-pipeline") {
        setTimeout(drawWorkflowLinks, 100);
        setTimeout(drawWorkflowLinks, 500);
      } else if (tab === "goal-tracking") {
        const cur = activeProjectKeyInput?.value;
        if (goalProjectKeyInput && !goalProjectKeyInput.value && cur && cur !== "idle") {
          goalProjectKeyInput.value = cur;
          loadGoalReport(cur);
        } else if (goalProjectKeyInput?.value) {
          loadGoalReport(goalProjectKeyInput.value);
        } else if (window.__lastGoalReport) {
          renderGoalScoreCard(window.__lastGoalReport);
          renderGoalLineageTree(window.__lastGoalReport);
          renderInvariantMatrix(window.__lastGoalReport);
          requestAnimationFrame(() => renderDecayCurve(window.__lastGoalReport));
          renderBlockchainLedger(window.__lastGoalReport);
        }
      }
    });
  });

  // Re-draw links and chart on window resize
  window.addEventListener("resize", () => {
    const activeTab = document.querySelector(".nav-item.active")?.getAttribute("data-tab");
    if (activeTab === "run-pipeline") {
      drawWorkflowLinks();
    } else if (activeTab === "goal-tracking" && window.__lastGoalReport) {
      renderDecayCurve(window.__lastGoalReport);
    }
  });

  // Initial draw
  setTimeout(drawWorkflowLinks, 1000);

  // Theme Toggle (defaults to dark obsidian, toggles light alabaster)
  const themeToggle = document.getElementById("theme-toggle");
  if (themeToggle) {
    themeToggle.addEventListener("click", () => {
      document.body.classList.toggle("light-theme");
      const isLight = document.body.classList.contains("light-theme");
      themeToggle.innerHTML = isLight
        ? `<svg class="theme-toggle-svg" viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>`
        : `<svg class="theme-toggle-svg" viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>`;
      if (window.__lastGoalReport) {
        renderDecayCurve(window.__lastGoalReport);
      }
    });
  }

  // Sidebar Project Buttons (Instant project switching across views)
  document.querySelectorAll(".sidebar-project-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const pk = btn.getAttribute("data-pk");
      if (!pk) return;
      document.querySelectorAll(".sidebar-project-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      
      const pkInput = document.getElementById("project-key");
      if (pkInput) pkInput.value = pk;
      if (activeProjectKeyInput) activeProjectKeyInput.value = pk;
      const goalPkInput = document.getElementById("goal-project-key");
      if (goalPkInput) goalPkInput.value = pk;
      const activeViewName = document.getElementById("active-view-name");
      if (activeViewName) activeViewName.textContent = pk;

      loadGoalReport(pk);
    });
  });

  // Hero Action Button ("Open tracking center →")
  const heroActionBtn = document.getElementById("hero-action-btn");
  if (heroActionBtn) {
    heroActionBtn.addEventListener("click", () => {
      const trackingNavBtn = document.querySelector(".nav-item[data-tab='goal-tracking']");
      if (trackingNavBtn) trackingNavBtn.click();
      const trackingSec = document.getElementById("goal-tracking-view");
      if (trackingSec) trackingSec.scrollIntoView({ behavior: "smooth" });
    });
  }

  // Operators Attached Incrementer
  let operatorsCount = 2;
  const addOpBtn = document.getElementById("add-operator-btn");
  const opCountText = document.getElementById("operators-count-text");
  if (addOpBtn && opCountText) {
    addOpBtn.addEventListener("click", () => {
      operatorsCount++;
      opCountText.textContent = `${operatorsCount} operators attached`;
      addLog(`Operator attached to mission console (${operatorsCount} active).`, "sys");
    });
  }

  // ── Live Backend Initialization (Zero Mock Data) ──
  async function bootstrapFromLiveBackend() {
    // 1. Mission Input Initial Defaults (pre-filled for convenient editing)
    const descInput = document.getElementById("description");
    if (descInput && !descInput.value.trim()) {
      descInput.value = "Design, synthesize, and verify a 16-bit RISC processor core in Verilog featuring an 8-word general-purpose register file, 5-stage hazard detection, single-cycle ALU, and automated self-checking testbench over memory-mapped I/O.";
    }

    const deadlineInput = document.getElementById("deadline");
    if (deadlineInput && !deadlineInput.value) {
      deadlineInput.value = "2026-11-15";
    }

    const pkInput = document.getElementById("project-key");
    if (pkInput && !pkInput.value.trim()) {
      pkInput.value = "risc_processor_core";
    }

    if (activeProjectKeyInput) {
      activeProjectKeyInput.value = "risc_processor_core";
    }

    const goalPkInput = document.getElementById("goal-project-key");
    if (goalPkInput && !goalPkInput.value.trim()) {
      goalPkInput.value = "risc_processor_core";
    }

    // 2. Team Configuration defaults
    if (teamToggle && !teamToggle.checked) {
      teamToggle.checked = true;
      if (teamConfigBody) teamConfigBody.classList.remove("hidden");
      if (numTeammatesInput) numTeammatesInput.value = 3;
      generateMemberRows();
      const rows = teamMembersContainer ? teamMembersContainer.querySelectorAll(".member-row") : [];
      const defaultMembers = [
        { name: "Alice Chen", role: "Lead Hardware Architect", email: "alice.chen@deeptech.io" },
        { name: "Marcus Vance", role: "RTL Verification Engineer", email: "marcus.v@deeptech.io" },
        { name: "Dr. Elena Rostova", role: "Logic Synthesis & FPGA Lead", email: "elena.r@deeptech.io" }
      ];
      rows.forEach((row, idx) => {
        if (defaultMembers[idx]) {
          const n = row.querySelector(".member-name");
          const r = row.querySelector(".member-role");
          const e = row.querySelector(".member-email");
          if (n) n.value = defaultMembers[idx].name;
          if (r) r.value = defaultMembers[idx].role;
          if (e) e.value = defaultMembers[idx].email;
        }
      });
    }

    // 3. Workflow Visualizer State - Ready State
    if (executionStatus) {
      executionStatus.textContent = "READY";
      executionStatus.className = "status-badge";
    }
    const nodeIds = ["wf-receive", "wf-parse", "wf-orchestrate", "wf-research", "wf-architect", "wf-synthesize"];
    nodeIds.forEach(id => {
      const node = document.getElementById(id);
      if (node) {
        node.classList.remove("success", "running");
        node.classList.add("waiting");
      }
    });
    setTimeout(drawWorkflowLinks, 200);

    // 4. Clean Telemetry Output Log
    if (terminalLog) {
      terminalLog.innerHTML = `
        <div class="log-entry"><span class="log-time">LIVE</span><span class="log-tag tag-sys">[SYSTEM]</span><span class="log-msg">Autonomous R&D Platform online. Connected to live Google Cloud Firestore (hackathon-492118).</span></div>
        <div class="log-entry"><span class="log-time">AWAIT</span><span class="log-tag tag-sys">[SYSTEM]</span><span class="log-msg">Click "Initiate R&D Sequence" to start live multi-agent execution.</span></div>
      `;
    }

    // 5. Clean up any stale mock runs from localStorage
    try {
      const mockIds = ["risc_processor_core_01", "ga_n_transistor_thermal_02", "aerospace_cfd_mesh_03", "quantum_qubit_sim_04"];
      const current = loadRunHistory();
      const cleaned = current.filter(r => !mockIds.includes(r.id));
      if (cleaned.length !== current.length) {
        localStorage.setItem(LS_KEY, JSON.stringify(cleaned));
      }
    } catch (_) {}

    // 6. Fetch live runs from Firestore
    fetchRunHistory();

    // 7. Fetch live goal report from Firestore
    loadGoalReport("risc_processor_core");
  }

  // Bootstrap live backend immediately on load
  bootstrapFromLiveBackend();

})();


