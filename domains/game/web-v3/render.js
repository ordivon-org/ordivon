function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function pct(value, maximum) {
  if (!maximum) return 0;
  return Math.max(0, Math.min(100, Math.round((value / maximum) * 100)));
}

function option(value, label, selected) {
  return `<option value="${escapeHtml(value)}"${value === selected ? " selected" : ""}>${escapeHtml(label)}</option>`;
}

function metric(label, value, maximum, warningAt = null) {
  const danger = warningAt !== null && value >= warningAt;
  return `<article class="metric${danger ? " danger" : ""}">
    <span>${escapeHtml(label)}</span>
    <strong>${escapeHtml(value)}${maximum === null ? "" : ` / ${escapeHtml(maximum)}`}</strong>
    ${maximum === null ? "" : `<div class="meter"><i style="width:${pct(value, maximum)}%"></i></div>`}
  </article>`;
}

function renderLanding(runs) {
  const retained = runs.length ? `<section class="panel retained-runs">
    <div class="section-heading"><div><p class="eyebrow">Retained operations</p><h2>Resume a command</h2></div></div>
    <div class="run-list">${runs.map((run) => `<button class="run-card" data-action="resume-run" data-run-id="${escapeHtml(run.runId)}">
      <span><strong>${escapeHtml(run.runId)}</strong><small>Turn ${run.turn} / ${run.turnLimit}</small></span>
      <em class="status ${escapeHtml(run.status)}">${escapeHtml(run.status)}</em>
    </button>`).join("")}</div>
  </section>` : "";
  return `<main class="landing">
    <section class="hero panel">
      <p class="eyebrow">Ordivon Game · first-playable preview</p>
      <h1>Station Zero <span>v3</span></h1>
      <p class="lede">Command a rescue team inside a station contested by pirates and a biological swarm. You set intent and authority. Agents choose admitted local actions. The World resolves all factions simultaneously.</p>
      <div class="hero-grid">
        <div><b>3</b><span>asymmetric factions</span></div>
        <div><b>14</b><span>maximum turns</span></div>
        <div><b>1</b><span>explicit commit boundary</span></div>
      </div>
      <form id="new-run-form" class="start-form">
        <label>Run identity<input id="new-run-id" value="run:station-zero-v3:web:${Date.now()}" autocomplete="off"></label>
        <button class="primary" type="submit" data-testid="start-run">Begin operation</button>
      </form>
      <p class="small-note">Deterministic fixture Agents are used in this preview. Enemy plans are sealed until resolution.</p>
    </section>
    ${retained}
  </main>`;
}

function renderOrder(view, catalog) {
  const order = view.experience.order;
  if (!order) return "";
  const disabled = !view.experience.canEditOrder ? " disabled" : "";
  return `<section class="panel command-panel" data-testid="commander-order">
    <div class="section-heading">
      <div><p class="eyebrow">Command phase</p><h2>Commander Order</h2></div>
      <span class="revision">Revision ${view.experience.orderRevision}</span>
    </div>
    <form id="order-form" class="order-grid">
      <label>Primary objective<select name="primaryObjectiveId"${disabled}>${catalog.objectives.map((item) => option(item.objectiveId, item.label, order.primaryObjectiveId)).join("")}</select></label>
      <label>Posture<select name="posture"${disabled}>${catalog.postures.map((item) => option(item.posture, item.label, order.posture)).join("")}</select></label>
      <label>Formation<select name="formation"${disabled}>${catalog.formations.map((item) => option(item.formation, item.label, order.formation)).join("")}</select></label>
      <label>Remote capability<select name="commanderDirectiveId"${disabled}>${catalog.commanderDirectives.map((item) => option(item.directiveId, item.label, order.commanderDirectiveId)).join("")}</select></label>
      <label>Lethal force<select name="lethalForce"${disabled}>${catalog.lethalForce.map((item) => option(item.value, item.label, order.lethalForce)).join("")}</select></label>
      <label>Loot policy<select name="lootPolicy"${disabled}>${catalog.lootPolicies.map((item) => option(item.value, item.label, order.lootPolicy)).join("")}</select></label>
      <label>Retreat below <output id="retreat-output">${Math.round(order.retreatHealthThreshold * 100)}%</output><input name="retreatHealthThreshold" type="range" min="0" max="0.8" step="0.05" value="${order.retreatHealthThreshold}"${disabled}></label>
      <label>Protected specialist<select name="protectedActorId"${disabled}><option value="">None</option>${view.ownActors.map((actor) => option(actor.actorId, actor.actorName ?? actor.name, order.protectedActorId)).join("")}</select></label>
    </form>
    <div class="command-actions">
      <button type="button" data-action="save-order"${disabled}>Save Order</button>
      <button type="button" class="accent" data-action="generate-preview"${view.experience.canGeneratePreview ? "" : " disabled"} data-testid="generate-preview">Generate team plan</button>
    </div>
  </section>`;
}

function renderPreview(view) {
  const preview = view.experience.preview;
  if (!preview) return `<section class="panel empty-preview"><p class="eyebrow">Deliberation</p><h2>No plan generated</h2><p>Save the strategic Order, then ask the specialists and faction leaders to form one simultaneous Turn plan.</p></section>`;
  return `<section class="panel plan-panel" data-testid="plan-preview">
    <div class="section-heading">
      <div><p class="eyebrow">Deliberation</p><h2>Rescue plan preview</h2></div>
      <span class="provider">${escapeHtml(preview.providerId)}</span>
    </div>
    <p class="plan-summary">${escapeHtml(preview.summary)}</p>
    ${preview.commanderAction ? `<div class="commander-card"><span>Remote action</span><strong>${escapeHtml(preview.commanderAction.label)}</strong><small>${escapeHtml(preview.commanderAction.targetLabel)}</small></div>` : `<div class="commander-card muted"><span>Remote action</span><strong>Capacity held</strong></div>`}
    <div class="intent-list">${preview.actorIntents.map((intent) => `<article class="intent-card" data-testid="rescue-intent">
      <div><span>${escapeHtml(intent.roleId)}</span><h3>${escapeHtml(intent.actorName)}</h3></div>
      <strong>${escapeHtml(intent.action)}</strong>
      <p>${escapeHtml(intent.rationale)}</p>
      ${intent.confidence === null ? "" : `<small>Confidence ${Math.round(intent.confidence * 100)}%</small>`}
    </article>`).join("")}</div>
    <div class="sealed-plans">${preview.enemyPlansSealed.map((plan) => `<article data-testid="sealed-enemy-plan"><span>${escapeHtml(plan.factionId)}</span><strong>Plan sealed</strong><code>${escapeHtml(plan.planDigest.slice(0, 12))}…</code></article>`).join("")}</div>
    ${preview.risks.length ? `<div class="risk-list"><h3>Known risks</h3>${preview.risks.map((risk) => `<p>⚠ ${escapeHtml(risk)}</p>`).join("")}</div>` : ""}
    ${preview.warnings.map((warning) => `<p class="warning">${escapeHtml(warning)}</p>`).join("")}
    <button type="button" class="primary commit" data-action="commit-turn" data-preview-id="${escapeHtml(preview.previewId)}"${view.experience.canCommitPreview ? "" : " disabled"} data-testid="commit-turn">Commit simultaneous Turn</button>
  </section>`;
}

function renderActors(view) {
  return `<section class="panel"><div class="section-heading"><div><p class="eyebrow">Rescue team</p><h2>Specialists</h2></div></div>
    <div class="actor-list">${view.ownActors.map((actor) => `<article class="actor-card ${escapeHtml(actor.lifeState)}">
      <div><span>${escapeHtml(actor.roleId)}</span><h3>${escapeHtml(actor.name)}</h3></div>
      <strong>${escapeHtml(actor.health)} / ${escapeHtml(actor.maximumHealth)} HP</strong>
      <small>${escapeHtml(actor.zoneName)} · ${escapeHtml(actor.lifeState)}</small>
    </article>`).join("")}</div>
  </section>`;
}

function renderObjectives(view) {
  return `<section class="panel"><div class="section-heading"><div><p class="eyebrow">Mission</p><h2>Objectives</h2></div></div>
    <div class="objective-list">${view.objectives.map((objective) => `<article class="objective ${escapeHtml(objective.status)}">
      <span>${objective.mandatory ? "Required" : "Optional"}</span><strong>${escapeHtml(objective.name)}</strong><small>${escapeHtml(objective.progress)} / ${escapeHtml(objective.target)} · ${escapeHtml(objective.status)}</small>
    </article>`).join("")}</div>
  </section>`;
}

function renderMap(view) {
  return `<section class="panel map-panel"><div class="section-heading"><div><p class="eyebrow">Known station</p><h2>Operational map</h2></div><span>${view.known.zoneIds.length} zones known</span></div>
    <div class="room-grid">${view.map.rooms.map((room) => `<article class="room"><h3>${escapeHtml(room.name)}</h3><div>${room.zones.map((zone) => `<section class="zone">
      <strong>${escapeHtml(zone.name)}</strong><small>${escapeHtml(zone.cover)} cover</small>
      ${zone.ownActorIds.map((id) => `<span class="token rescue">${escapeHtml(id)}</span>`).join("")}
      ${zone.contactActorIds.map((id) => `<span class="token contact">${escapeHtml(id)}</span>`).join("")}
      ${zone.systemIds.map((id) => `<span class="token system">${escapeHtml(id)}</span>`).join("")}
      ${zone.hazardIds.map((id) => `<span class="token hazard">${escapeHtml(id)}</span>`).join("")}
    </section>`).join("")}</div></article>`).join("")}</div>
  </section>`;
}

function renderAftermath(view) {
  if (!view.aftermath) return "";
  return `<section class="panel aftermath" data-testid="aftermath"><div class="section-heading"><div><p class="eyebrow">Aftermath</p><h2>Turn ${view.aftermath.turnSequence + 1} evidence</h2></div></div>
    <div class="resolution-list">${view.aftermath.ownIntentResults.map((result) => `<article class="resolution ${escapeHtml(result.status)}"><strong>${escapeHtml(result.actorName)}</strong><span>${escapeHtml(result.status)}</span><small>${escapeHtml(result.reason)}</small></article>`).join("")}</div>
    <details open><summary>Visible World facts (${view.aftermath.visibleFacts.length})</summary><ol>${view.aftermath.visibleFacts.map((fact) => `<li><span>${escapeHtml(fact.kind)}</span>${escapeHtml(fact.summary)}</li>`).join("")}</ol></details>
  </section>`;
}

function renderTerminal(view) {
  if (view.run.status !== "terminal") return "";
  return `<section class="panel terminal" data-testid="terminal-summary">
    <p class="eyebrow">Encounter complete</p><h2>${escapeHtml(view.outcomes.rescue)} · Rescue</h2>
    <div class="outcomes"><span>Rescue <b>${escapeHtml(view.outcomes.rescue)}</b></span><span>Pirate <b>${escapeHtml(view.outcomes.pirate)}</b></span><span>Swarm <b>${escapeHtml(view.outcomes.swarm)}</b></span></div>
    <p>${escapeHtml(view.outcomes.reason)}</p><button data-action="new-operation">Start another operation</button>
  </section>`;
}

function renderMission(view, catalog) {
  return `<main class="mission">
    <header class="topbar"><div><p class="eyebrow">Station Zero v3 · Contested Signal</p><h1>Mission Control</h1></div><div class="turn"><span>Turn</span><strong data-testid="turn-number">${view.run.turn}</strong><small>/ ${view.run.turnLimit}</small></div></header>
    <section class="resource-grid">
      ${metric("Battery", view.resources.batteryCharge, view.resources.batteryInitial)}
      ${metric("Oxygen", view.resources.oxygen, 100)}
      ${metric("Reactor heat", view.resources.reactorHeat, 100, 85)}
      ${metric("Alert", view.resources.alertLevel, 5, 4)}
    </section>
    ${renderTerminal(view)}
    <div class="planning-grid">${renderOrder(view, catalog)}${renderPreview(view)}</div>
    ${renderAftermath(view)}
    <div class="intel-grid">${renderActors(view)}${renderObjectives(view)}</div>
    ${renderMap(view)}
  </main>`;
}

export function renderStationZeroV3App({ view, catalog, runs, busy, error }) {
  const content = view ? renderMission(view, catalog) : renderLanding(runs);
  return `${content}${busy ? `<div class="busy" data-testid="busy"><div class="spinner"></div><strong>${escapeHtml(busy)}</strong></div>` : ""}${error ? `<div class="toast error" role="alert">${escapeHtml(error)}</div>` : ""}`;
}
