const $ = (selector) => document.querySelector(selector);
const elements = {
  status: $("#mission-status"), resources: $("#resources"), rooms: $("#rooms"), systems: $("#systems"),
  location: $("#location"), agentName: $("#agent-name"), agent: $("#agent"), actions: $("#actions"),
  output: $("#output"), suggest: $("#suggest"), replay: $("#replay"), provider: $("#agent-provider"),
  initialize: $("#agent-initialize"), step: $("#agent-step"), run: $("#agent-run"),
  agentPhase: $("#agent-phase"), agentSummary: $("#agent-summary"), timeline: $("#agent-timeline"),
  teamProvider: $("#team-provider"), teamPolicy: $("#team-policy"), teamInitialize: $("#team-initialize"),
  teamStep: $("#team-step"), teamRun: $("#team-run"), teamPhase: $("#team-phase"),
  teamSummary: $("#team-summary"), teamDetail: $("#team-detail"),
};

let teamRunId = null;

const escapeHtml = (value) => String(value).replace(/[&<>"']/g, (character) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;",
})[character]);
const percent = (value) => `${Math.round(value)}%`;

async function request(path, options) {
  const response = await fetch(path, options);
  const body = await response.json();
  if (!response.ok) throw new Error(JSON.stringify(body));
  return body;
}

function post(path, value) {
  return request(path, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(value),
  });
}

function show(value) { elements.output.textContent = JSON.stringify(value, null, 2); }
function factText(fact) {
  switch (fact.kind) {
    case "agent_moved": return `${fact.actorId} moved: ${fact.fromRoomId} → ${fact.toRoomId}`;
    case "agent_waited": return `${fact.actorId} waited`;
    case "item_picked_up": return `${fact.actorId} picked up ${fact.quantity} × ${fact.itemId}`;
    case "item_consumed": return `${fact.quantity} × ${fact.itemId} consumed`;
    case "system_repaired": return `${fact.systemId} repaired to ${Math.round(fact.afterIntegrity * 100)}%`;
    case "power_state_changed": return `${fact.systemId} power ${fact.powered ? "enabled" : "disabled"}`;
    case "hull_breach_sealed": return `${fact.hazardId} sealed`;
    case "hazard_contained": return `${fact.hazardId} contained by ${fact.actorId}`;
    case "crew_stabilized": return `${fact.crewId} stabilized`;
    case "distress_signal_sent": return "distress signal sent";
    case "battery_consumed": return `${fact.amount} battery consumed`;
    case "oxygen_changed": return `oxygen ${fact.before} → ${fact.after}`;
    case "reactor_heat_changed": return `reactor heat ${fact.before} → ${fact.after}`;
    case "health_changed": return `${fact.subjectId} health ${fact.before} → ${fact.after}`;
    case "mission_succeeded": return `MISSION SUCCEEDED · ${fact.reason}`;
    case "mission_failed": return `MISSION FAILED · ${fact.reason}`;
    default: return fact.kind;
  }
}
function showEvent(event) {
  if (!event?.facts?.length) return show(event);
  const verification = event.verification?.success ? "VERIFIED" : "UNVERIFIED";
  elements.output.textContent = [`${event.commandKind} · ${verification}`, "", ...event.facts.map(factText)].join("\n");
}
function metric(label, value, warning = false) {
  return `<article class="metric ${warning ? "warning" : ""}"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></article>`;
}

function renderWorld(next) {
  const { state } = next;
  const engineer = state.agents["engineer-01"];
  const casualty = state.crew["crew-01"];
  elements.status.textContent = state.mission.status.toUpperCase();
  elements.status.dataset.state = state.mission.status;
  elements.location.textContent = `TURN ${state.turn} · REV ${state.revision}`;
  elements.resources.innerHTML = [
    metric("Battery", `${state.resources.batteryCharge}/${state.resources.batteryInitial}`, state.resources.batteryCharge < 12),
    metric("Oxygen", percent(state.resources.oxygen), state.resources.oxygen < 35),
    metric("Reactor heat", percent(state.resources.reactorHeat), state.resources.reactorHeat > 80),
    metric("Crew health", percent(casualty.health), casualty.health < 20),
  ].join("");
  elements.rooms.innerHTML = Object.values(state.rooms).map((room) => {
    const active = room.id === engineer.location;
    return `<article class="room ${active ? "active" : ""}"><strong>${escapeHtml(room.name)}</strong><small>${room.neighbors.length} link${room.neighbors.length === 1 ? "" : "s"}</small>${active ? "<span>ENGINEER</span>" : ""}</article>`;
  }).join("");
  elements.systems.innerHTML = Object.values(state.systems).map((system) => `
    <article class="system">
      <div><strong>${escapeHtml(system.name)}</strong><small>${escapeHtml(state.rooms[system.roomId].name)}</small></div>
      <div class="system-values"><span>${percent(system.integrity * 100)} integrity</span><span class="${system.powered ? "online" : "offline"}">${system.powered ? "POWERED" : "OFFLINE"}</span></div>
    </article>`).join("");
  const inventory = Object.entries(engineer.inventory).filter(([, quantity]) => quantity > 0).map(([item, quantity]) => `${quantity}× ${item}`).join(", ");
  elements.agentName.textContent = engineer.name;
  elements.agent.innerHTML = `<dl><div><dt>Location</dt><dd>${escapeHtml(state.rooms[engineer.location].name)}</dd></div><div><dt>Health</dt><dd>${percent(engineer.health)}</dd></div><div><dt>Inventory</dt><dd>${escapeHtml(inventory || "Empty")}</dd></div><div><dt>Casualty</dt><dd>${casualty.stabilized ? "Stabilized" : "Deteriorating"}</dd></div></dl>`;
  elements.actions.innerHTML = "";
  for (const action of next.availableActions) {
    const button = document.createElement("button");
    button.textContent = action.label;
    button.disabled = state.mission.status !== "running";
    button.addEventListener("click", () => execute(action));
    elements.actions.append(button);
  }
  if (next.recentEvents.length > 0) showEvent(next.recentEvents.at(-1));
  else show({ recovered: true, digest: next.digest, scenario: state.scenarioId });
}

function renderAgent(envelope) {
  if (!envelope.initialized) {
    elements.agentPhase.textContent = "NOT INITIALIZED";
    elements.agentPhase.dataset.state = "none";
    elements.agentSummary.innerHTML = "<p>Create a durable Goal and root Task. Provider sessions are replaceable.</p>";
    elements.timeline.innerHTML = "<p class=\"empty\">No Host events.</p>";
    return;
  }
  const { goal, task, attempts } = envelope.projection;
  const active = task.activeAttemptId ? attempts.find((attempt) => attempt.attemptId === task.activeAttemptId) : null;
  elements.agentPhase.textContent = task.phase.toUpperCase();
  elements.agentPhase.dataset.state = task.phase;
  elements.agentSummary.innerHTML = `
    <dl class="agent-grid">
      <div><dt>Goal</dt><dd>${escapeHtml(goal.status)}</dd></div>
      <div><dt>Task revision</dt><dd>${task.revision}</dd></div>
      <div><dt>Attempts</dt><dd>${attempts.length} · ${task.completedAttemptIds.length} complete</dd></div>
      <div><dt>Active attempt</dt><dd>${escapeHtml(active?.status ?? "None")}</dd></div>
      <div><dt>Provider</dt><dd>${escapeHtml(active?.providerId ?? "Pending")}</dd></div>
      <div><dt>Skill progress</dt><dd>${active ? `${active.skillStepIndex}/${active.skillStepCount}` : "—"}</dd></div>
      <div><dt>Effects</dt><dd>${envelope.effects.length}</dd></div>
      <div><dt>Dispatches</dt><dd>${envelope.dispatches.length}</dd></div>
    </dl>`;
  elements.timeline.innerHTML = envelope.timeline.slice(-16).reverse().map((event) => `
    <article class="timeline-event">
      <span>#${event.sequence}</span>
      <strong>${escapeHtml(event.eventType.replaceAll("_", " "))}</strong>
      <small>${escapeHtml(event.eventId)}</small>
    </article>`).join("") || "<p class=\"empty\">No Host events.</p>";
}

function renderTeam(envelope) {
  if (!envelope?.initialized) {
    elements.teamPhase.textContent = "NOT INITIALIZED";
    elements.teamPhase.dataset.state = "none";
    elements.teamSummary.innerHTML = "<p>Create a Scenario v2 / Ruleset v3 Run. Each specialist owns an independent durable Task.</p>";
    elements.teamDetail.innerHTML = '<p class="empty">No Team events.</p>';
    return;
  }
  const projection = envelope.projection;
  const latest = envelope.rounds.at(-1) ?? null;
  elements.teamPhase.textContent = (latest?.status ?? projection.goal.status).toUpperCase();
  elements.teamPhase.dataset.state = latest?.status ?? projection.goal.status;
  elements.teamSummary.innerHTML = `<div class="team-grid">${projection.profiles.map((profile) => {
    const task = projection.tasks.find((candidate) => candidate.actorId === profile.actorId);
    return `<article class="team-card"><strong>${escapeHtml(profile.role)}</strong><span>${escapeHtml(profile.actorId)}</span><small>${escapeHtml(task?.state ?? "missing")} · rev ${task?.revision ?? "—"}</small><small>${escapeHtml(task?.activeObjectiveId ?? "No active objective")}</small></article>`;
  }).join("")}</div>`;
  const objectives = projection.objectiveStatus.filter((objective) => objective.visible).map((objective) => `<li class="${objective.satisfied ? "done" : ""}">${objective.satisfied ? "✓" : "○"} ${escapeHtml(objective.objectiveId)}</li>`).join("");
  const proposals = envelope.proposals.slice(-12).reverse().map((proposal) => {
    const approval = proposal.authorityOutcome === "require-human" && proposal.status === "proposed"
      ? `<button class="approve-proposal" data-proposal-id="${escapeHtml(proposal.proposalId)}">Approve</button>` : "";
    return `<article class="proposal"><div><strong>${escapeHtml(proposal.actorId)}</strong><span>${escapeHtml(proposal.command.kind)}</span></div><small>${escapeHtml(proposal.status)} · ${escapeHtml(proposal.authorityOutcome)}</small>${approval}</article>`;
  }).join("") || '<p class="empty">No proposals yet.</p>';
  elements.teamDetail.innerHTML = `<div class="team-columns"><div><h3>Objectives</h3><ul class="objective-list">${objectives}</ul></div><div><h3>Recent proposals</h3>${proposals}</div></div>`;
  for (const button of document.querySelectorAll(".approve-proposal")) {
    button.addEventListener("click", () => teamInput("approve", { proposalId: button.dataset.proposalId }));
  }
}

function teamQuery() {
  const params = new URLSearchParams({ provider: elements.teamProvider.value, policyMode: elements.teamPolicy.value });
  if (teamRunId) params.set("runId", teamRunId);
  return params.toString();
}

async function loadTeam() {
  const envelope = await request(`/api/team/state?${teamQuery()}`);
  renderTeam(envelope);
  return envelope;
}

async function createTeamRun() {
  const runId = `run:web-team:${Date.now()}:${crypto.randomUUID()}`;
  await post("/api/runs", { runId, scenarioVersion: 2, rulesetVersion: 3 });
  teamRunId = runId;
  const result = await post(`/api/team/initialize?${teamQuery()}`, { provider: elements.teamProvider.value, policyMode: elements.teamPolicy.value });
  renderTeam(result.team);
  show({ runId, provider: result.provider, policyMode: result.policyMode, goal: result.projection.goal });
}

async function teamAction(path, extra = {}) {
  if (!teamRunId) return createTeamRun();
  elements.teamStep.disabled = true;
  elements.teamRun.disabled = true;
  elements.teamInitialize.disabled = true;
  try {
    const result = await post(`${path}?${teamQuery()}`, { provider: elements.teamProvider.value, policyMode: elements.teamPolicy.value, ...extra });
    show(result.receipt ?? result);
    if (result.team) renderTeam(result.team);
    if (result.world) renderWorld(result.world);
  } catch (error) { show({ error: String(error) }); }
  finally {
    elements.teamStep.disabled = false;
    elements.teamRun.disabled = false;
    elements.teamInitialize.disabled = false;
  }
}

async function teamInput(action, extra = {}) {
  if (!teamRunId) return;
  try {
    const result = await post(`/api/team/input?${teamQuery()}`, { provider: elements.teamProvider.value, policyMode: elements.teamPolicy.value, action, ...extra });
    show(result.result ?? result);
    renderTeam(result.team);
    if (result.world) renderWorld(result.world);
  } catch (error) { show({ error: String(error) }); }
}

async function loadWorld() { const world = await request("/api/state"); renderWorld(world); return world; }
async function loadAgent() {
  const envelope = await request(`/api/agent/state?provider=${encodeURIComponent(elements.provider.value)}`);
  renderAgent(envelope);
  return envelope;
}
async function refresh() { await Promise.all([loadWorld(), loadAgent(), loadTeam()]); }

async function execute(action) {
  try {
    const result = await post("/api/actions", { ...action.command, commandId: crypto.randomUUID() });
    show(result);
    await refresh();
  } catch (error) { show({ error: String(error) }); }
}

async function agentAction(path, extra = {}) {
  elements.step.disabled = true;
  elements.run.disabled = true;
  elements.initialize.disabled = true;
  try {
    const result = await post(path, { provider: elements.provider.value, ...extra });
    show(result.receipt ?? result);
    if (result.agent) renderAgent(result.agent);
    if (result.world) renderWorld(result.world);
    else await refresh();
  } catch (error) { show({ error: String(error) }); }
  finally {
    elements.step.disabled = false;
    elements.run.disabled = false;
    elements.initialize.disabled = false;
  }
}

elements.teamInitialize.addEventListener("click", () => createTeamRun().catch((error) => show({ error: String(error) })));
elements.teamStep.addEventListener("click", () => teamAction("/api/team/step"));
elements.teamRun.addEventListener("click", () => teamAction("/api/team/run", { maximumSteps: 512 }));
elements.teamProvider.addEventListener("change", () => loadTeam().catch((error) => show({ error: String(error) })));
elements.teamPolicy.addEventListener("change", () => loadTeam().catch((error) => show({ error: String(error) })));

elements.initialize.addEventListener("click", () => agentAction("/api/agent/initialize"));
elements.step.addEventListener("click", () => agentAction("/api/agent/step"));
elements.run.addEventListener("click", () => agentAction("/api/agent/run", { maximumSteps: 256 }));
elements.provider.addEventListener("change", () => loadAgent().catch((error) => show({ error: String(error) })));
elements.suggest.addEventListener("click", async () => {
  try { show(await request("/api/suggestion")); } catch (error) { show({ error: String(error) }); }
});
elements.replay.addEventListener("click", async () => {
  try { show(await request("/api/replay")); } catch (error) { show({ error: String(error) }); }
});
refresh().catch((error) => show({ error: String(error) }));
