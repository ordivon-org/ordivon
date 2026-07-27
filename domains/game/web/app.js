const $ = (selector) => document.querySelector(selector);
const elements = {
  status: $("#mission-status"), resources: $("#resources"), rooms: $("#rooms"), systems: $("#systems"),
  location: $("#location"), agentName: $("#agent-name"), agent: $("#agent"), actions: $("#actions"),
  output: $("#output"), suggest: $("#suggest"), replay: $("#replay"),
};

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
    case "crew_stabilized": return `${fact.crewId} stabilized`;
    case "distress_signal_sent": return `distress signal sent`;
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

function render(next) {
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

async function load() { render(await request("/api/state")); }
async function execute(action) {
  try {
    const result = await request("/api/actions", {
      method: "POST", headers: { "content-type": "application/json" },
      body: JSON.stringify({ ...action.command, commandId: crypto.randomUUID() }),
    });
    show(result);
    await load();
  } catch (error) { show({ error: String(error) }); }
}

elements.suggest.addEventListener("click", async () => {
  try { show(await request("/api/suggestion")); } catch (error) { show({ error: String(error) }); }
});
elements.replay.addEventListener("click", async () => {
  try { show(await request("/api/replay")); } catch (error) { show({ error: String(error) }); }
});
load().catch((error) => show({ error: String(error) }));
