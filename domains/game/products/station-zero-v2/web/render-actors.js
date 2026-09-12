import { commandAttribute, escapeHtml, humanize, inventorySummary } from "./render-utils.js";

function evidenceSections(actor) {
  return actor.evidence.map((entry) => {
    const items = entry.items.length
      ? `<ul>${entry.items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`
      : '<p class="empty-label">No retained evidence at this stage.</p>';
    const confidence = entry.confidence === null ? "" : `<span>${Math.round(entry.confidence * 100)}% confidence</span>`;
    return `<section class="evidence-stage ${entry.stage}"><header><strong>${escapeHtml(entry.label)}</strong>${confidence}</header>${items}</section>`;
  }).join("");
}

function actorControls(actor, objectives, catalog) {
  const objectiveIds = catalog?.actors?.find((candidate) => candidate.actorId === actor.actorId)?.objectiveIds ?? [];
  const objectiveOptions = objectiveIds.map((objectiveId) => {
    const objective = objectives.find((candidate) => candidate.objectiveId === objectiveId);
    return `<option value="${escapeHtml(objectiveId)}" ${actor.activeObjectiveId === objectiveId ? "selected" : ""}>${escapeHtml(objective?.label ?? humanize(objectiveId))}</option>`;
  }).join("");
  const control = actor.controlMode === "paused"
    ? `<button data-command="${commandAttribute({ action: "resume", actorId: actor.actorId })}">Resume</button>`
    : actor.controlMode === "cancelled"
      ? '<span class="control-note">Cancelled for this mission</span>'
      : `<button data-command="${commandAttribute({ action: "pause", actorId: actor.actorId })}">Pause</button>`;
  const cancel = actor.controlMode === "cancelled" ? "" : `<button class="danger" data-command="${commandAttribute({ action: "cancel", actorId: actor.actorId })}">Cancel</button>`;
  return `
    <details class="actor-command-drawer">
      <summary>Issue a direct command</summary>
      <div class="actor-controls">
        <label>Mission order<select data-objective-actor="${escapeHtml(actor.actorId)}">${objectiveOptions}</select></label>
        <div class="button-row">${control}${cancel}</div>
      </div>
    </details>`;
}

export function renderActors(view, catalog) {
  const cards = view.actors.map((actor) => `
    <article class="actor-card ${escapeHtml(actor.controlMode)}">
      <header>
        <div><p class="eyebrow">${escapeHtml(actor.role.toUpperCase())}</p><h3>${escapeHtml(actor.name)}</h3></div>
        <span class="task-state">${escapeHtml(humanize(actor.taskState))}</span>
      </header>
      <dl class="actor-facts">
        <div><dt>Location</dt><dd>${escapeHtml(actor.locationName)}</dd></div>
        <div><dt>Health</dt><dd>${actor.health}%</dd></div>
        <div><dt>Inventory</dt><dd>${escapeHtml(inventorySummary(actor.inventory))}</dd></div>
        <div><dt>Current mission order</dt><dd>${escapeHtml(humanize(actor.activeObjectiveId ?? "Awaiting assignment"))}</dd></div>
      </dl>
      ${actor.waitReason ? `<p class="wait-reason">Operational blocker: ${escapeHtml(actor.waitReason)}</p>` : ""}
      ${actorControls(actor, view.objectives, catalog)}
      <details class="evidence-drawer"><summary>Operational evidence</summary>${evidenceSections(actor)}</details>
    </article>`).join("");
  return `<section class="panel actor-panel"><div class="section-heading"><div><p class="eyebrow">SPECIALIST TEAM</p><h2>People carrying out the plan</h2></div><span>${view.actors.length} persistent specialists</span></div><div class="actor-grid">${cards}</div></section>`;
}
