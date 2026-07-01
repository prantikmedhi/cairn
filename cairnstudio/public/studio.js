      const body = document.body;
      const canvas = document.getElementById("canvas");
      const yamlEditor = document.getElementById("yamlEditor");
      const validationStatus = document.getElementById("validationStatus");
      const traceList = document.getElementById("traceList");
      const inspectorFields = document.getElementById("inspectorFields");
      const targetSelect = document.getElementById("targetSelect");
      const inputJson = document.getElementById("inputJson");
      const collaboratorNameInput = document.getElementById("collaboratorName");
      const shareSessionInput = document.getElementById("shareSession");
      const presenceList = document.getElementById("presenceList");
      const activityList = document.getElementById("activityList");
      const commentInput = document.getElementById("commentInput");
      const treeList = document.getElementById("treeList");
      const loopSummary = document.getElementById("loopSummary");
      const loopVersionChip = document.getElementById("loopVersionChip");
      const selectedNodeChip = document.getElementById("selectedNodeChip");
      const inspectorNodeType = document.getElementById("inspectorNodeType");
      const previewTargetPill = document.getElementById("previewTargetPill");
      const presenceCountChip = document.getElementById("presenceCountChip");
      const statusBarMessage = document.getElementById("statusBarMessage");
      const statusTheme = document.getElementById("statusTheme");
      const statusView = document.getElementById("statusView");
      const statusSession = document.getElementById("statusSession");
      const breadcrumbSession = document.getElementById("breadcrumbSession");
      const sessionLabel = document.getElementById("sessionLabel");
      const loopMetaSummary = document.getElementById("loopMetaSummary");
      const themeSelect = document.getElementById("themeSelect");
      const autoSyncToggle = document.getElementById("autoSyncToggle");
      
      // Inject CAIRN_CONFIG from global scope (set in HTML)
      const configSessionId = window.CAIRN_CONFIG ? window.CAIRN_CONFIG.defaultSessionId : "";
      const sessionId = new URLSearchParams(window.location.search).get("session") || configSessionId;
      const actorId = window.localStorage.getItem("cairnStudioActorId") || randomActorId();

      const loopModel = {
        loop: {
          id: "visual-starter",
          name: "Visual Starter",
          version: "0.1.0",
          description: "Visual starter loop",
          imports: [],
          budget: { max_iterations: 3, max_duration: "30s" },
          states: []
        }
      };

      let selectedNodeId = null;
      let replayTimer = null;
      let sessionVersion = 0;
      let remoteSyncTimer = null;
      let collaborationTimer = null;
      let activeSidebar = "explorer";
      let activeView = "graph";
      let followRemoteSession = true;

      function randomActorId() {
        const value = `actor-${Math.random().toString(36).slice(2, 10)}`;
        window.localStorage.setItem("cairnStudioActorId", value);
        return value;
      }

      async function postJson(url, payload) {
        const response = await fetch(url, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || "Request failed");
        return data;
      }

      async function fetchJson(url, fallbackMessage) {
        const response = await fetch(url);
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || fallbackMessage);
        return data;
      }

      function setStatus(text, kind = "") {
        validationStatus.textContent = text;
        validationStatus.className = kind ? `status-card ${kind}` : "status-card";
        statusBarMessage.textContent = text;
      }

      function applyTheme(theme) {
        body.dataset.theme = theme;
        themeSelect.value = theme;
        statusTheme.textContent = theme;
        window.localStorage.setItem("cairnStudioTheme", theme);
      }

      function setSidebarPanel(panel) {
        activeSidebar = panel;
        document.querySelectorAll(".activity-button[data-sidebar]").forEach((button) => {
          button.classList.toggle("active", button.dataset.sidebar === panel);
        });
        document.querySelectorAll(".sidebar-panel").forEach((panelNode) => {
          panelNode.classList.toggle("active", panelNode.dataset.panel === panel);
        });
      }

      function setEditorView(view) {
        activeView = view;
        document.querySelectorAll(".tab-button").forEach((button) => {
          button.classList.toggle("active", button.dataset.view === view);
        });
        document.querySelectorAll(".editor-view").forEach((panel) => {
          panel.classList.toggle("active", panel.dataset.viewPanel === view);
        });
        statusView.textContent = view;
      }

      function updateWorkspaceMeta() {
        const loopData = loopModel.loop || {};
        loopSummary.textContent = loopData.description || `${loopData.states?.length || 0} states configured`;
        loopVersionChip.textContent = loopData.version || "0.1.0";
        loopMetaSummary.textContent = `${loopData.name || "Visual Loop"} · ${loopData.states?.length || 0} states · ${loopData.imports?.length || 0} imports`;
        statusSession.textContent = sessionId;
        breadcrumbSession.textContent = sessionId;
        sessionLabel.textContent = sessionId;
      }

      async function fetchSession() {
        return fetchJson(`/api/session?id=${encodeURIComponent(sessionId)}`, "Session load failed");
      }

      async function syncSessionSave() {
        try {
          const response = await postJson("/api/session/save", {
            session_id: sessionId,
            version: sessionVersion,
            yaml: yamlEditor.value,
            model: loopModel,
            actor_id: actorId,
            actor_name: collaboratorNameInput.value.trim() || "Anonymous builder"
          });
          sessionVersion = response.version || sessionVersion;
        } catch (error) {
          setStatus(error.message, "error");
        }
      }

      async function pollSession() {
        if (!followRemoteSession) return;
        try {
          const remote = await fetchSession();
          if ((remote.version || 0) > sessionVersion) {
            sessionVersion = remote.version || 0;
            yamlEditor.value = remote.yaml || yamlEditor.value;
            Object.assign(loopModel, remote.model || loopModel);
            selectedNodeId = selectedNodeId && loopModel.loop.states.some((node) => node.id === selectedNodeId)
              ? selectedNodeId
              : loopModel.loop.states[0]?.id || null;
            renderAll();
            setStatus(`Synced shared session "${sessionId}"`, "ok");
          }
        } catch (error) {
          setStatus(error.message, "error");
        }
      }

      function randomId(prefix) {
        return `${prefix}-${Math.random().toString(36).slice(2, 8)}`;
      }

      function addNode(kind, handler, x, y) {
        const node = {
          id: randomId(kind === "subloop" ? "subloop" : "state"),
          label: kind === "subloop" ? "Sub-loop" : formatHandlerLabel(handler),
          kind,
          handler: kind === "subloop" ? "" : handler,
          loop: kind === "subloop" ? "import-name" : "",
          condition: "",
          parallel: [],
          guard: {},
          inputs: kind === "subloop" ? { name: "world" } : { value: "sample" },
          transitions: [],
          x,
          y
        };
        loopModel.loop.states.push(node);
        selectedNodeId = node.id;
        syncYamlFromModel();
        renderAll();
      }

      function formatHandlerLabel(handler) {
        return (handler || "state")
          .replace("core.", "")
          .split(".")
          .map((chunk) => chunk.charAt(0).toUpperCase() + chunk.slice(1))
          .join(" ");
      }

      function renderCanvas() {
        canvas.innerHTML = "";
        canvas.classList.toggle("empty", loopModel.loop.states.length === 0);
        for (const node of loopModel.loop.states) {
          const element = document.createElement("article");
          element.className = `node${node.id === selectedNodeId ? " active" : ""}`;
          element.style.left = `${node.x}px`;
          element.style.top = `${node.y}px`;
          element.draggable = true;
          element.innerHTML = `
            <header>
              <div class="node-title">${escapeHtml(node.label)}</div>
              <span class="node-kind">${escapeHtml(node.kind === "subloop" ? "sub-loop" : (node.handler || "handler"))}</span>
            </header>
            <div class="node-meta">${escapeHtml(node.condition || "No condition")}</div>
            <div class="transition-list">
              ${node.transitions.map((target) => `<span class="transition-pill">${escapeHtml(target)}</span>`).join("") || '<span class="transition-pill">no transitions</span>'}
            </div>
          `;
          element.addEventListener("click", () => {
            selectedNodeId = node.id;
            renderAll();
          });
          element.addEventListener("dragstart", (event) => {
            event.dataTransfer.setData("application/json", JSON.stringify({ type: "move-node", id: node.id }));
          });
          canvas.appendChild(element);
        }
        selectedNodeChip.textContent = selectedNodeId || "No selection";
      }

      function renderExplorer() {
        updateWorkspaceMeta();
        if (!loopModel.loop.states.length) {
          treeList.innerHTML = '<div class="status-card">No states loaded yet.</div>';
          return;
        }
        treeList.innerHTML = loopModel.loop.states.map((node) => `
          <button class="tree-item${node.id === selectedNodeId ? " active" : ""}" type="button" data-tree-id="${escapeHtml(node.id)}">
            <div class="tree-row">
              <strong>${escapeHtml(node.label)}</strong>
              <span class="meta-chip">${escapeHtml(node.kind === "subloop" ? "sub-loop" : "state")}</span>
            </div>
            <div class="tree-meta">${escapeHtml(node.kind === "subloop" ? (node.loop || "import missing") : (node.handler || "handler missing"))}</div>
          </button>
        `).join("");
        treeList.querySelectorAll("[data-tree-id]").forEach((button) => {
          button.addEventListener("click", () => {
            selectedNodeId = button.dataset.treeId;
            renderAll();
          });
        });
      }

      function renderInspector() {
        const node = loopModel.loop.states.find((item) => item.id === selectedNodeId);
        if (!node) {
          inspectorFields.innerHTML = '<div class="status-card">No node selected yet.</div>';
          inspectorNodeType.textContent = "state";
          return;
        }

        inspectorNodeType.textContent = node.kind === "subloop" ? "sub-loop" : "state";
        inspectorFields.innerHTML = `
          <label class="label" for="nodeLabel">Label</label>
          <input id="nodeLabel" value="${escapeHtml(node.label)}">
          <label class="label" for="nodeHandler">Handler</label>
          <input id="nodeHandler" value="${escapeHtml(node.handler || "")}" ${node.kind === "subloop" ? "disabled" : ""}>
          <label class="label" for="nodeLoop">Loop Ref</label>
          <input id="nodeLoop" value="${escapeHtml(node.loop || "")}" ${node.kind === "subloop" ? "" : "disabled"}>
          <label class="label" for="nodeCondition">Condition</label>
          <input id="nodeCondition" value="${escapeHtml(node.condition || "")}">
          <label class="label" for="nodeTransitions">Transitions (comma separated)</label>
          <input id="nodeTransitions" value="${escapeHtml((node.transitions || []).join(", "))}">
          <label class="label" for="nodeParallel">Parallel Branches (comma separated)</label>
          <input id="nodeParallel" value="${escapeHtml((node.parallel || []).join(", "))}">
          <label class="label" for="nodeRetry">Retry Count</label>
          <input id="nodeRetry" value="${escapeHtml(String(node.guard?.retry ?? ""))}">
          <label class="label" for="nodeInputs">Inputs JSON</label>
          <textarea id="nodeInputs">${escapeHtml(JSON.stringify(node.inputs, null, 2))}</textarea>
        `;

        const bind = (id, updater) => {
          const field = document.getElementById(id);
          field.addEventListener("input", () => {
            updater(field.value);
            syncYamlFromModel();
            renderAll();
          });
        };

        bind("nodeLabel", (value) => { node.label = value || node.id; });
        bind("nodeHandler", (value) => { node.handler = value; });
        bind("nodeLoop", (value) => { node.loop = value; });
        bind("nodeCondition", (value) => { node.condition = value; });
        bind("nodeTransitions", (value) => { node.transitions = splitList(value); });
        bind("nodeParallel", (value) => { node.parallel = splitList(value); });
        bind("nodeRetry", (value) => {
          if (value === "") {
            node.guard = {};
          } else {
            node.guard = { retry: Number(value) || 0, backoff: "exponential" };
          }
        });
        bind("nodeInputs", (value) => {
          try { node.inputs = JSON.parse(value || "{}"); } catch (_error) {}
        });
      }

      function splitList(value) {
        return value.split(",").map((item) => item.trim()).filter(Boolean);
      }

      async function syncModelFromYaml() {
        try {
          const data = await postJson("/api/model/from-yaml", { yaml: yamlEditor.value });
          Object.assign(loopModel, data);
          selectedNodeId = loopModel.loop.states[0]?.id || null;
          renderAll();
          await syncSessionSave();
          setStatus("Canvas synced from YAML.", "ok");
        } catch (error) {
          setStatus(error.message, "error");
        }
      }

      async function syncYamlFromModel() {
        try {
          const data = await postJson("/api/model/to-yaml", loopModel);
          yamlEditor.value = data.yaml;
          await syncSessionSave();
          validateCurrentYaml();
        } catch (error) {
          setStatus(error.message, "error");
        }
      }

      async function validateCurrentYaml() {
        try {
          const data = await postJson("/api/validate", { yaml: yamlEditor.value });
          setStatus(`Valid loop: ${data.loop_id}. States: ${data.states.join(", ")}`, "ok");
        } catch (error) {
          setStatus(error.message, "error");
        }
      }

      async function previewLoop() {
        let inputs = {};
        try {
          inputs = JSON.parse(inputJson.value || "{}");
        } catch (_error) {
          setStatus("Preview inputs must be valid JSON.", "error");
          return;
        }

        try {
          const data = await postJson("/api/preview", {
            yaml: yamlEditor.value,
            inputs,
            target: targetSelect.value
          });
          renderTrace(data.state_results || []);
          previewTargetPill.textContent = targetSelect.value;
          setEditorView("preview");
          setStatus(data.success ? "Preview run completed." : (data.error || "Preview failed"), data.success ? "ok" : "error");
        } catch (error) {
          setStatus(error.message, "error");
        }
      }

      function renderTrace(states) {
        if (!states.length) {
          traceList.innerHTML = '<div class="status-card">No trace yet. Run preview to inspect execution path.</div>';
          return;
        }
        traceList.innerHTML = states.map((state, index) => `
          <div class="trace-card" data-trace-index="${index}">
            <strong>${escapeHtml(state.state_id)}</strong>
            <div class="trace-meta">${state.skipped ? "skipped" : "executed"}</div>
          </div>
        `).join("");
        const steps = [...traceList.querySelectorAll(".trace-card")];
        if (replayTimer) window.clearInterval(replayTimer);
        let index = 0;
        replayTimer = window.setInterval(() => {
          steps.forEach((step) => step.classList.remove("active"));
          if (steps[index]) steps[index].classList.add("active");
          index = (index + 1) % Math.max(steps.length, 1);
        }, 650);
      }

      function renderPresence(items) {
        presenceCountChip.textContent = `${items.length} active`;
        if (!items.length) {
          presenceList.innerHTML = '<div class="status-card">No collaborators active yet.</div>';
          return;
        }
        presenceList.innerHTML = items.map((item) => `
          <div class="presence-card">
            <strong>${escapeHtml(item.actor_name)}</strong>
            <div class="collab-copy">${escapeHtml(item.actor_id)}</div>
          </div>
        `).join("");
      }

      function renderActivity(activity, comments) {
        const merged = [
          ...activity.map((item) => ({ ...item, kindLabel: item.kind || "event" })),
          ...comments.map((item) => ({ ...item, kindLabel: "comment" }))
        ]
          .sort((left, right) => String(right.at).localeCompare(String(left.at)))
          .slice(0, 14);
        if (!merged.length) {
          activityList.innerHTML = '<div class="status-card">Waiting for collaboration events.</div>';
          return;
        }
        activityList.innerHTML = merged.map((item) => `
          <div class="activity-card">
            <strong>${escapeHtml(item.actor_name || "unknown")}</strong>
            <div class="collab-copy">${escapeHtml(item.kindLabel)} · ${escapeHtml(item.message || "")}</div>
          </div>
        `).join("");
      }

      async function refreshCollaboration() {
        try {
          const presence = await postJson("/api/session/presence", {
            session_id: sessionId,
            actor_id: actorId,
            actor_name: collaboratorNameInput.value.trim() || "Anonymous builder"
          });
          const activity = await fetchJson(`/api/session/activity?id=${encodeURIComponent(sessionId)}`, "Activity load failed");
          renderPresence(presence.presence || []);
          renderActivity(activity.activity || [], activity.comments || []);
        } catch (error) {
          setStatus(error.message, "error");
        }
      }

      async function sendComment() {
        if (!commentInput.value.trim()) {
          setStatus("Comment cannot be empty.", "error");
          return;
        }
        try {
          await postJson("/api/session/comment", {
            session_id: sessionId,
            actor_id: actorId,
            actor_name: collaboratorNameInput.value.trim() || "Anonymous builder",
            message: commentInput.value
          });
          commentInput.value = "";
          await refreshCollaboration();
          setStatus("Comment sent to shared room.", "ok");
        } catch (error) {
          setStatus(error.message, "error");
        }
      }

      function renderAll() {
        renderExplorer();
        renderCanvas();
        renderInspector();
        updateWorkspaceMeta();
      }

      function downloadYaml() {
        const blob = new Blob([yamlEditor.value], { type: "text/yaml" });
        const url = URL.createObjectURL(blob);
        const anchor = document.createElement("a");
        anchor.href = url;
        anchor.download = `${loopModel.loop.id || "cairn-loop"}.crn`;
        anchor.click();
        URL.revokeObjectURL(url);
      }

      async function copyShareLink() {
        try {
          await navigator.clipboard.writeText(shareSessionInput.value);
          setStatus("Share link copied.", "ok");
        } catch (_error) {
          shareSessionInput.select();
          setStatus("Select share link and copy manually.", "ok");
        }
      }

      function escapeHtml(value) {
        return String(value)
          .replaceAll("&", "&amp;")
          .replaceAll("<", "&lt;")
          .replaceAll(">", "&gt;")
          .replaceAll('"', "&quot;");
      }

      document.querySelectorAll(".activity-button[data-sidebar]").forEach((button) => {
        button.addEventListener("click", () => setSidebarPanel(button.dataset.sidebar));
      });

      document.querySelectorAll(".tab-button").forEach((button) => {
        button.addEventListener("click", () => setEditorView(button.dataset.view));
      });

      document.querySelectorAll(".palette-card").forEach((button) => {
        button.addEventListener("dragstart", (event) => {
          event.dataTransfer.setData("application/json", JSON.stringify({
            type: "create-node",
            kind: button.dataset.kind,
            handler: button.dataset.handler
          }));
        });
        button.addEventListener("click", () => addNode(button.dataset.kind, button.dataset.handler, 80, 120));
      });

      canvas.addEventListener("dragover", (event) => event.preventDefault());
      canvas.addEventListener("drop", (event) => {
        event.preventDefault();
        const payload = JSON.parse(event.dataTransfer.getData("application/json"));
        const rect = canvas.getBoundingClientRect();
        const x = event.clientX - rect.left - 108;
        const y = event.clientY - rect.top - 42;
        if (payload.type === "create-node") {
          addNode(payload.kind, payload.handler, x, y);
          return;
        }
        if (payload.type === "move-node") {
          const node = loopModel.loop.states.find((item) => item.id === payload.id);
          if (!node) return;
          node.x = x;
          node.y = y;
          renderCanvas();
          syncYamlFromModel();
        }
      });

      document.getElementById("validateYaml").addEventListener("click", validateCurrentYaml);
      document.getElementById("previewLoop").addEventListener("click", previewLoop);
      document.getElementById("syncFromYaml").addEventListener("click", () => {
        setEditorView("graph");
        syncModelFromYaml();
      });
      document.getElementById("downloadYaml").addEventListener("click", downloadYaml);
      document.getElementById("sendComment").addEventListener("click", sendComment);
      document.getElementById("shareSessionButton").addEventListener("click", copyShareLink);
      document.getElementById("uploadYaml").addEventListener("change", async (event) => {
        const file = event.target.files?.[0];
        if (!file) return;
        yamlEditor.value = await file.text();
        setEditorView("yaml");
        syncModelFromYaml();
      });

      themeSelect.addEventListener("change", () => applyTheme(themeSelect.value));
      autoSyncToggle.addEventListener("change", () => {
        followRemoteSession = autoSyncToggle.value === "on";
        setStatus(followRemoteSession ? "Remote session sync enabled." : "Remote session sync paused.", "ok");
      });
      targetSelect.addEventListener("change", () => {
        previewTargetPill.textContent = targetSelect.value;
      });
      collaboratorNameInput.addEventListener("input", () => {
        window.localStorage.setItem("cairnStudioActorName", collaboratorNameInput.value);
      });

      let validateTimer = null;
      yamlEditor.addEventListener("input", () => {
        if (validateTimer) window.clearTimeout(validateTimer);
        validateTimer = window.setTimeout(async () => {
          await validateCurrentYaml();
          await syncSessionSave();
        }, 320);
      });

      async function bootstrap() {
        const persistedTheme = window.localStorage.getItem("cairnStudioTheme") || "midnight";
        collaboratorNameInput.value = window.localStorage.getItem("cairnStudioActorName") || "Builder";
        shareSessionInput.value = `${window.location.origin}${window.location.pathname}?session=${encodeURIComponent(sessionId)}`;
        applyTheme(persistedTheme);
        previewTargetPill.textContent = targetSelect.value;
        const remote = await fetchSession();
        sessionVersion = remote.version || 0;
        yamlEditor.value = remote.yaml || yamlEditor.value;
        Object.assign(loopModel, remote.model || loopModel);
        selectedNodeId = loopModel.loop.states[0]?.id || null;
        renderAll();
        await validateCurrentYaml();
        await refreshCollaboration();
        remoteSyncTimer = window.setInterval(pollSession, 1200);
        collaborationTimer = window.setInterval(refreshCollaboration, 2500);
      }

      bootstrap().catch((error) => {
        setStatus(error.message, "error");
      });
