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

function tokenLabel(value) {
  return String(value ?? "")
    .split(":")
    .at(-1)
    .split("-")
    .filter(Boolean)
    .map((part) => `${part[0]?.toUpperCase() ?? ""}${part.slice(1)}`)
    .join(" ");
}

const SPECIALIST_VISUALS = {
  "engineer-imani": { role: "engineer", glyph: "E", x: 0 },
  "medic-reyes": { role: "medic", glyph: "M", x: 24 },
  "security-chen": { role: "security", glyph: "S", x: 48 },
};

function specialistToken(actorId, className = "") {
  const visual = SPECIALIST_VISUALS[actorId];
  if (!visual) return "";
  return `<span class="specialist-token ${escapeHtml(visual.role)} ${escapeHtml(className)}" style="--portrait-x:-${visual.x}px" title="${escapeHtml(tokenLabel(actorId))}" aria-label="${escapeHtml(tokenLabel(actorId))}"><span aria-hidden="true">${escapeHtml(visual.glyph)}</span></span>`;
}

function metric(label, value, maximum, warningAt = null) {
  const danger = warningAt !== null && value >= warningAt;
  return `<article class="metric${danger ? " danger" : ""}">
    <span>${escapeHtml(label)}</span>
    <strong>${escapeHtml(value)}${maximum === null ? "" : ` / ${escapeHtml(maximum)}`}</strong>
    ${maximum === null ? "" : `<div class="meter"><i style="width:${pct(value, maximum)}%"></i></div>`}
  </article>`;
}

function caseLabel(catalog, caseId) {
  return catalog?.cases?.find((entry) => entry.caseId === caseId)?.label ?? tokenLabel(caseId);
}

function renderLanding(runs, catalog) {
  const retained = runs.length ? `<section class="panel retained-runs">
    <div class="section-heading"><div><p class="eyebrow">Retained operations</p><h2>Resume a command</h2></div></div>
    <div class="run-list">${runs.map((run) => `<button class="run-card" data-action="resume-run" data-run-id="${escapeHtml(run.runId)}">
      <span><strong>${escapeHtml(run.runId)}</strong><small>${escapeHtml(caseLabel(catalog, run.scenarioCaseId))} · Turn ${run.turn} / ${run.turnLimit}</small></span>
      <em class="status ${escapeHtml(run.status)}">${escapeHtml(run.status)}</em>
    </button>`).join("")}</div>
  </section>` : "";
  return `<main class="landing">
    <section class="hero panel">
      <p class="eyebrow">Ordivon Game · Mission Control</p>
      <h1>Station Zero <span>v3</span></h1>
      <p class="lede">Command a rescue team inside a station contested by pirates and a biological swarm. You set mission intent and authority; specialists choose legal local actions; all factions resolve simultaneously.</p>
      <div class="hero-grid">
        <div><b>3</b><span>asymmetric factions</span></div>
        <div><b>${escapeHtml(catalog?.turnLimit ?? "—")}</b><span>turn limit</span></div>
        <div><b>1</b><span>simultaneous resolution</span></div>
      </div>
      <form id="new-run-form" class="start-form">
        <label>Operation call sign<input id="new-run-id" value="station-zero-${Date.now().toString(36)}" autocomplete="off"></label>
        <label>Encounter profile<select id="new-run-case" data-testid="scenario-case">${(catalog?.cases ?? []).map((entry) => option(entry.caseId, entry.label, catalog?.defaultScenarioCaseId)).join("")}</select></label>
        <button class="primary" type="submit" data-testid="start-run">Begin operation</button>
      </form>
      <p class="small-note">Encounter profile is retained with the operation and changes actual tactical geometry; it is not a cosmetic seed label.</p>
      <p class="small-note">Bounded specialist cognition · deterministic World consequence · enemy plans remain sealed until resolution.</p>
    </section>
    ${retained}
  </main>`;
}

function renderFirstCommand(view) {
  if (view.run.status !== "running" || view.run.turn !== 0 || view.experience.preview) return "";
  return `<section class="first-command" data-testid="first-command" data-phase="order">
    <span>First command</span>
    <p><b>Required objectives define success.</b> Mission intent persists; Remote capability is per-Turn. Generate a plan, review Plan impact, then Commit. Specialists choose local actions.</p>
  </section>`;
}

function renderOrder(view, catalog) {
  const order = view.experience.order;
  if (!order) return "";
  const disabled = !view.experience.canEditOrder ? " disabled" : "";
  const selectedDescription = (items, key, value) => items.find((item) => item[key] === value)?.description ?? "";
  const lethal = catalog.lethalForce.find((item) => item.value === order.lethalForce);
  const protectedActor = view.ownActors.find((actor) => actor.actorId === order.protectedActorId);
  const contingencySummary = [
    lethal?.label ?? order.lethalForce,
    `retreat ≤ ${Math.round(order.retreatHealthThreshold * 100)}%`,
    protectedActor ? `protect ${protectedActor.actorName ?? protectedActor.name}` : "no protection priority",
  ].join(" · ");
  const initialGuidance = selectedDescription(catalog.objectives, "objectiveId", order.primaryObjectiveId);
  return `<section class="panel command-panel" data-testid="commander-order">
    <div class="section-heading">
      <div><p class="eyebrow">Command phase</p><h2>Commander Order</h2></div>
      <span class="revision">Revision ${view.experience.orderRevision}</span>
    </div>
    <form id="order-form" class="commander-order-form" data-dirty="false">
      <fieldset class="order-section intent-section">
        <legend>Mission intent</legend>
        <div class="order-grid core-order-grid">
          <label>Primary objective<select name="primaryObjectiveId"${disabled}>${catalog.objectives.map((item) => option(item.objectiveId, item.label, order.primaryObjectiveId)).join("")}</select></label>
          <label>Posture<select name="posture"${disabled}>${catalog.postures.map((item) => option(item.posture, item.label, order.posture)).join("")}</select></label>
          <label>Formation<select name="formation"${disabled}>${catalog.formations.map((item) => option(item.formation, item.label, order.formation)).join("")}</select></label>
        </div>
      </fieldset>
      <fieldset class="order-section turn-section">
        <legend>This Turn</legend>
        <label>Remote capability<select name="commanderDirectiveId"${disabled}>${catalog.commanderDirectives.map((item) => option(item.directiveId, item.label, order.commanderDirectiveId)).join("")}</select></label>
      </fieldset>
      <div class="order-guidance" data-testid="order-guidance"><span data-order-guidance-label>Primary objective</span><p data-order-guidance-text>${escapeHtml(initialGuidance)}</p></div>
      <details class="order-contingencies" data-testid="order-contingencies">
        <summary><span><b>Standing contingencies</b><small>Only matter when matching local opportunities arise.</small></span><em data-contingency-summary>${escapeHtml(contingencySummary)}</em></summary>
        <div class="order-grid contingency-grid">
          <label>Lethal force<select name="lethalForce"${disabled}>${catalog.lethalForce.map((item) => option(item.value, item.label, order.lethalForce)).join("")}</select></label>
          <label>Retreat below <output id="retreat-output">${Math.round(order.retreatHealthThreshold * 100)}%</output><input name="retreatHealthThreshold" type="range" min="0" max="0.8" step="0.05" value="${order.retreatHealthThreshold}"${disabled}></label>
          <label>Protected specialist<select name="protectedActorId"${disabled}><option value="">None</option>${view.ownActors.map((actor) => option(actor.actorId, actor.actorName ?? actor.name, order.protectedActorId)).join("")}</select></label>
        </div>
      </details>
    </form>
    <p class="order-dirty-notice" data-order-dirty-notice hidden>Order changed locally. Regenerate the team plan before Commit so the preview is bound to these choices.</p>
    <div class="command-actions">
      <button type="button" data-action="save-order"${disabled}>Save Order</button>
      <button type="button" class="accent" data-action="generate-preview"${view.experience.canGeneratePreview ? "" : " disabled"} data-testid="generate-preview">Generate team plan</button>
    </div>
  </section>`;
}

function feedbackText(feedback) {
  if (!feedback) return "";
  const reason = String(feedback.reason).replaceAll("_", " ");
  return `Previous attempt: ${feedback.candidateLabel} · ${feedback.status} · ${reason}`;
}

function responsibilityText(responsibility) {
  if (!responsibility) return "";
  const target = responsibility.targetActorId ?? responsibility.targetZoneId;
  const action = responsibility.kind === "search-civilian"
    ? "Search civilian sector"
    : responsibility.kind === "recover-civilian"
      ? "Recover civilian"
      : "Support civilian recovery";
  const blockers = responsibility.blockerActorIds.length
    ? ` · blockers ${responsibility.blockerActorIds.join(", ")}`
    : "";
  return `${action}: ${target}${blockers}`;
}

function renderPlanImpact(preview) {
  const rows = preview.planImpact.filter((objective) => objective.mandatory || objective.selectedPriority);
  const impactLabel = (impact) => impact === "direct" ? "Direct action" : impact === "positioning" ? "Positioning" : "No direct action";
  return `<section class="plan-impact" data-testid="plan-impact">
    <div class="plan-impact-heading"><div><span>Plan impact</span><strong>Mission fronts touched by admitted Rescue actions</strong></div><small>Not an outcome forecast</small></div>
    <div class="plan-impact-list">${rows.map((objective) => `<article class="plan-impact-row ${escapeHtml(objective.impact)}${objective.selectedPriority ? " priority" : ""}" data-objective-id="${escapeHtml(objective.objectiveId)}" data-impact="${escapeHtml(objective.impact)}">
      <div><span>${objective.mandatory ? "Required" : "Optional"}${objective.selectedPriority ? " · Priority" : ""}</span><strong>${escapeHtml(objective.name)}</strong><small>${escapeHtml(objective.progress)} / ${escapeHtml(objective.target)} · ${escapeHtml(objective.status)}</small></div>
      <p><b>${escapeHtml(impactLabel(objective.impact))}</b>${objective.actorNames.length ? ` · ${escapeHtml(objective.actorNames.join(", "))}` : ""}</p>
    </article>`).join("")}</div>
  </section>`;
}

function renderPreview(view) {
  const preview = view.experience.preview;
  if (!preview) return `<section class="panel empty-preview"><p class="eyebrow">Deliberation</p><h2>No plan generated</h2><p>Adjust the Commander Order, then generate one simultaneous Turn plan. Review Plan impact and specialist actions before Commit.</p></section>`;
  return `<section class="panel plan-panel" data-testid="plan-preview">
    <div class="section-heading">
      <div><p class="eyebrow">Deliberation</p><h2>Rescue plan preview</h2></div>
      <span class="provider">${escapeHtml(preview.providerId)}</span>
    </div>
    <p class="plan-summary">${escapeHtml(preview.summary)}</p>
    ${renderPlanImpact(preview)}
    ${preview.commanderAction ? `<div class="commander-card"><span>Remote action</span><strong>${escapeHtml(preview.commanderAction.label)}</strong><small>${escapeHtml(preview.commanderAction.targetLabel)}</small></div>` : `<div class="commander-card muted"><span>Remote action</span><strong>Capacity held</strong></div>`}
    <div class="intent-list">${preview.actorIntents.map((intent) => `<article class="intent-card" data-testid="rescue-intent">
      <div><span>${escapeHtml(intent.roleId)}</span><h3>${escapeHtml(intent.actorName)}</h3></div>
      <strong>${escapeHtml(intent.action)}</strong>
      ${intent.responsibility ? `<small data-testid="rescue-responsibility">${escapeHtml(responsibilityText(intent.responsibility))}</small>` : ""}
      ${intent.responsibilityFeedback ? `<small data-testid="responsibility-feedback">${escapeHtml(feedbackText(intent.responsibilityFeedback))}</small>` : ""}
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
      <div class="actor-identity">${specialistToken(actor.actorId, "card-portrait")}<div><span>${escapeHtml(actor.roleId)}</span><h3>${escapeHtml(actor.name)}</h3></div></div>
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

function pointList(points) {
  return points.map((point) => `${Number(point.x).toFixed(1)},${Number(point.y).toFixed(1)}`).join(" ");
}

function compactToken(id, kind) {
  if (kind === "rescue" && SPECIALIST_VISUALS[id]) return specialistToken(id, "map-specialist");
  const label = tokenLabel(id);
  const glyph = kind === "contact" ? "?"
    : kind === "system" ? "◆"
      : kind === "hazard" ? "!"
        : "◇";
  return `<span class="map-token ${kind}" title="${escapeHtml(label)}" aria-label="${escapeHtml(label)}">${escapeHtml(glyph)}</span>`;
}

function expressionDelay(expression) {
  return Math.min(Number(expression.sequence) || 0, 12) * 0.12;
}

function renderExpressionVisual(expression) {
  const visual = expression.visual;
  if (visual?.kind === "sprite") {
    const frame = visual.frame;
    return `<span class="expression-sprite" aria-hidden="true" style="width:${Number(frame.width)}px;height:${Number(frame.height)}px;background-image:url('${escapeHtml(visual.src)}');background-size:${Number(visual.sheetWidth)}px ${Number(visual.sheetHeight)}px;background-position:-${Number(frame.x)}px -${Number(frame.y)}px"></span>`;
  }
  if (visual?.kind === "icon") {
    return `<img class="expression-icon" src="${escapeHtml(visual.src)}" alt="" aria-hidden="true">`;
  }
  const glyph = expression.kind === "move" ? "→" : expression.kind === "impact" || expression.kind === "health" ? "✦" : expression.kind === "objective" ? "◆" : "·";
  return `<span class="expression-glyph" aria-hidden="true">${escapeHtml(glyph)}</span>`;
}

function renderTemporalStrip(view, live) {
  if (!view.aftermath?.expressions.length) return "";
  return `<div class="expression-strip${live ? " is-live" : ""}" data-testid="temporal-expression-strip" aria-label="Visible Turn events">
    ${view.aftermath.expressions.map((expression) => `<article class="expression-card ${escapeHtml(expression.kind)} ${escapeHtml(expression.tone)}" data-testid="temporal-expression" data-expression-kind="${escapeHtml(expression.kind)}" data-fact-id="${escapeHtml(expression.factId)}" style="--event-delay:${expressionDelay(expression)}s">
      ${renderExpressionVisual(expression)}
      <div><span>${escapeHtml(expression.kind)}</span><strong>${escapeHtml(expression.label)}</strong><small>${escapeHtml(expression.detail)}</small></div>
    </article>`).join("")}
  </div>`;
}

function renderTemporalMapOverlay(view, live) {
  if (!live || !view.aftermath?.expressions.length) return "";
  return view.aftermath.expressions.map((expression) => {
    if (!expression.map) return "";
    const delay = expressionDelay(expression);
    if (expression.kind === "move" && expression.map.from && expression.map.to) {
      const from = expression.map.from;
      const to = expression.map.to;
      return `<g class="temporal-map-event move" data-expression-id="${escapeHtml(expression.expressionId)}" style="--event-delay:${delay}s">
        <line x1="${Number(from.x).toFixed(1)}" y1="${Number(from.y).toFixed(1)}" x2="${Number(to.x).toFixed(1)}" y2="${Number(to.y).toFixed(1)}"></line>
        <circle class="moving-pip" cx="${Number(from.x).toFixed(1)}" cy="${Number(from.y).toFixed(1)}" r="8">
          <animate attributeName="cx" from="${Number(from.x).toFixed(1)}" to="${Number(to.x).toFixed(1)}" begin="${delay.toFixed(2)}s" dur="0.7s" fill="freeze"></animate>
          <animate attributeName="cy" from="${Number(from.y).toFixed(1)}" to="${Number(to.y).toFixed(1)}" begin="${delay.toFixed(2)}s" dur="0.7s" fill="freeze"></animate>
        </circle>
      </g>`;
    }
    if (expression.map.points?.length > 1) {
      return `<polyline class="temporal-map-event passage" data-expression-id="${escapeHtml(expression.expressionId)}" points="${pointList(expression.map.points)}" style="--event-delay:${delay}s"></polyline>`;
    }
    const point = expression.map.point ?? expression.map.to ?? expression.map.from;
    if (!point) return "";
    if (expression.visual?.kind === "icon") {
      return `<image class="temporal-map-event signal" data-expression-id="${escapeHtml(expression.expressionId)}" href="${escapeHtml(expression.visual.src)}" x="${(Number(point.x) - 18).toFixed(1)}" y="${(Number(point.y) - 18).toFixed(1)}" width="36" height="36" style="--event-delay:${delay}s"></image>`;
    }
    return `<circle class="temporal-map-event pulse ${escapeHtml(expression.tone)}" data-expression-id="${escapeHtml(expression.expressionId)}" cx="${Number(point.x).toFixed(1)}" cy="${Number(point.y).toFixed(1)}" r="10" style="--event-delay:${delay}s"></circle>`;
  }).join("");
}

function renderMap(view, expressionTurnSequence = null) {
  const live = Boolean(view.aftermath && expressionTurnSequence === view.aftermath.turnSequence);
  const passageLines = view.map.passages.map((passage) => `<polyline class="map-passage" points="${pointList(passage.points)}" data-passage-id="${escapeHtml(passage.passageId)}"></polyline>`).join("");
  const frontierLines = view.map.frontiers.map((frontier) => {
    const tip = frontier.points.at(-1);
    return `<g class="map-frontier" data-frontier-from="${escapeHtml(frontier.fromZoneId)}"><polyline points="${pointList(frontier.points)}"></polyline>${tip ? `<circle cx="${Number(tip.x).toFixed(1)}" cy="${Number(tip.y).toFixed(1)}" r="5"></circle>` : ""}</g>`;
  }).join("");
  const zones = view.map.zones.map((zone) => `<foreignObject x="${Number(zone.geometry.x).toFixed(1)}" y="${Number(zone.geometry.y).toFixed(1)}" width="${Number(zone.geometry.width).toFixed(1)}" height="${Number(zone.geometry.height).toFixed(1)}" data-zone-id="${escapeHtml(zone.zoneId)}">
    <div xmlns="http://www.w3.org/1999/xhtml" class="map-zone-card cover-${escapeHtml(zone.cover)}">
      <span class="map-room-label">${escapeHtml(zone.roomName)}</span>
      <strong>${escapeHtml(zone.name)}</strong>
      <small>${escapeHtml(zone.cover)} cover · Cap ${escapeHtml(zone.capacity)}</small>
      <div class="map-zone-tokens">
        ${zone.ownActorIds.map((id) => compactToken(id, "rescue")).join("")}
        ${zone.contactActorIds.map((id) => compactToken(id, "contact")).join("")}
        ${zone.systemIds.map((id) => compactToken(id, "system")).join("")}
        ${zone.hazardIds.map((id) => compactToken(id, "hazard")).join("")}
        ${zone.groundItemIds.map((id) => compactToken(id, "item")).join("")}
      </div>
    </div>
  </foreignObject>`).join("");
  return `<section class="panel map-panel"><div class="section-heading"><div><p class="eyebrow">Known station</p><h2>Operational map</h2></div><span>${view.known.zoneIds.length} zones · ${view.map.frontiers.length} uncharted access</span></div>
    <div class="spatial-map-shell" data-testid="spatial-map">
      <svg class="spatial-map" viewBox="0 0 ${Number(view.map.width).toFixed(1)} ${Number(view.map.height).toFixed(1)}" role="img" aria-label="Known Station Zero tactical topology">
        <g class="map-grid"><path d="M0 0H${Number(view.map.width).toFixed(1)}V${Number(view.map.height).toFixed(1)}H0Z"></path></g>
        <g class="map-passages">${passageLines}${frontierLines}</g>
        <g class="map-zones">${zones}</g>
        <g class="temporal-map-layer">${renderTemporalMapOverlay(view, live)}</g>
      </svg>
    </div>
    <div class="map-legend"><span><i class="legend-token rescue">R</i> Rescue</span><span><i class="legend-token contact">?</i> Contact</span><span><i class="legend-token system">◆</i> System</span><span><i class="legend-token hazard">!</i> Hazard</span><span><i class="legend-frontier"></i> Uncharted access</span></div>
    <p class="map-boundary-note">Only Rescue-confirmed geometry is projected. Uncharted destinations remain withheld until discovery.</p>
  </section>`;
}

function renderPlanReview(review) {
  const impactLabel = (impact) => impact === "direct" ? "Direct" : impact === "positioning" ? "Positioning" : "None";
  return `<div class="plan-review" data-testid="plan-review">
    <div class="plan-review-heading"><span>Mission fronts</span><small>Committed plan → current visible state</small></div>
    <div class="plan-review-fronts">${review.objectives.map((objective) => {
      const changed = objective.beforeProgress !== objective.afterProgress || objective.beforeStatus !== objective.afterStatus;
      const progress = changed
        ? `${objective.beforeProgress}/${objective.target} → ${objective.afterProgress}/${objective.target} · ${objective.afterStatus}`
        : `${objective.afterProgress}/${objective.target} · ${objective.afterStatus}`;
      return `<article class="plan-review-front ${escapeHtml(objective.plannedImpact)}${objective.selectedPriority ? " priority" : ""}" data-testid="plan-review-front" data-objective-id="${escapeHtml(objective.objectiveId)}" data-planned-impact="${escapeHtml(objective.plannedImpact)}">
        <span>${objective.mandatory ? "Required" : "Optional"}${objective.selectedPriority ? " · Priority" : ""}</span>
        <strong>${escapeHtml(objective.name)}</strong>
        <small>Planned ${escapeHtml(impactLabel(objective.plannedImpact))} · ${escapeHtml(progress)}</small>
      </article>`;
    }).join("")}</div>
  </div>`;
}

function renderAftermath(view, expressionTurnSequence = null) {
  if (!view.aftermath) return "";
  const live = expressionTurnSequence === view.aftermath.turnSequence;
  return `<section class="panel aftermath${live ? " is-live" : ""}" data-testid="aftermath"><div class="section-heading"><div><p class="eyebrow">Aftermath</p><h2>Turn ${view.aftermath.turnSequence + 1} evidence</h2></div><span>${view.aftermath.expressions.length} high-signal events</span></div>
    ${renderTemporalStrip(view, live)}
    ${renderPlanReview(view.aftermath.planReview)}
    <div class="resolution-list">${view.aftermath.ownIntentResults.map((result) => `<article class="resolution ${escapeHtml(result.status)}" data-testid="intent-review"><div><strong>${escapeHtml(result.actorName)}</strong><small>Planned: ${escapeHtml(result.plannedAction)}</small></div><span>${escapeHtml(result.status)}</span><small class="resolution-reason">${escapeHtml(result.reason.replaceAll("_", " "))}</small></article>`).join("")}</div>
    <details><summary>Visible World facts (${view.aftermath.visibleFacts.length})</summary><ol>${view.aftermath.visibleFacts.map((fact) => `<li><span>${escapeHtml(fact.kind)}</span>${escapeHtml(fact.summary)}</li>`).join("")}</ol></details>
  </section>`;
}

function renderOperationDebrief(debrief) {
  if (!debrief) return "";
  const statusLabel = (objective) => objective.finalStatus === "completed" ? "completed" : "incomplete";
  const milestone = (objective) => objective.completedTurn !== null
    ? `Completed Turn ${objective.completedTurn}`
    : objective.firstProgressTurn !== null
      ? `First progress Turn ${objective.firstProgressTurn}`
      : "No verified progress";
  return `<section class="operation-debrief" data-testid="operation-debrief">
    <div class="debrief-heading"><div><span>Verified operation debrief</span><strong>${escapeHtml(debrief.terminalReasonLabel)} · ${escapeHtml(debrief.requiredCompleted)} / ${escapeHtml(debrief.requiredTotal)} required fronts completed</strong></div><small>Retained committed-plan and objective history · no counterfactual claim</small></div>
    <div class="debrief-focus">${debrief.focus.map((focus) => `<article data-testid="debrief-focus" data-objective-id="${escapeHtml(focus.objectiveId)}"><span>Committed focus</span><strong>${escapeHtml(focus.name)}</strong><small>${escapeHtml(focus.turns)} / ${escapeHtml(focus.totalTurns)} Turns</small></article>`).join("")}</div>
    <div class="debrief-objectives">${debrief.objectives.map((objective) => `<article class="debrief-objective ${objective.finalStatus === "completed" ? "completed" : "incomplete"}" data-testid="debrief-objective" data-objective-id="${escapeHtml(objective.objectiveId)}">
      <span>${objective.mandatory ? "Required" : "Selected optional"}${objective.focusTurns ? ` · focus ${escapeHtml(objective.focusTurns)} Turns` : ""}</span>
      <strong>${escapeHtml(objective.name)}</strong>
      <small>${escapeHtml(objective.finalProgress)} / ${escapeHtml(objective.target)} · ${escapeHtml(statusLabel(objective))} · ${escapeHtml(milestone(objective))}</small>
    </article>`).join("")}</div>
  </section>`;
}

function renderTerminal(view) {
  if (view.run.status !== "terminal") return "";
  return `<section class="panel terminal" data-testid="terminal-summary">
    <div class="terminal-heading"><div><p class="eyebrow">Encounter complete</p><h2>${escapeHtml(view.outcomes.rescue)} · Rescue</h2></div><button data-action="new-operation">Start another operation</button></div>
    <div class="outcomes"><span>Rescue <b>${escapeHtml(view.outcomes.rescue)}</b></span><span>Pirate <b>${escapeHtml(view.outcomes.pirate)}</b></span><span>Swarm <b>${escapeHtml(view.outcomes.swarm)}</b></span></div>
    ${renderOperationDebrief(view.debrief)}
  </section>`;
}

function renderSystemEvidence(view) {
  if (!view.known?.systems?.length) return "";
  return `<section class="system-evidence" data-testid="system-evidence"><div class="section-heading"><div><p class="eyebrow">Observed systems</p><h2>Last known condition</h2></div><span>bounded evidence</span></div><div class="system-evidence-list">${view.known.systems.map((system) => `<article data-system-id="${escapeHtml(system.systemId)}"><strong>${escapeHtml(system.name)}</strong><span>${Math.round(system.observedIntegrity * 100)}% integrity · ${system.observedPowered ? "powered" : "unpowered"}</span><small>Last confirmed Turn ${escapeHtml(system.observedAtTurn)} · known-system telemetry updates on visible system changes</small></article>`).join("")}</div></section>`;
}

function renderBusyState(busy, view) {
  if (!busy) return "";
  if (busy.kind === "deliberation" && view) {
    return `<div class="busy deliberation" data-testid="busy" data-busy-kind="deliberation">
      <section class="deliberation-card" data-testid="deliberation-state">
        <div class="deliberation-heading"><div><p class="eyebrow">Deliberation</p><h2>World paused at Turn ${escapeHtml(view.run.turn)}</h2></div><span class="status">Enemy plans sealed</span></div>
        <p>Binding the Commander Order. Engineer, Medic, and Security are selecting admitted local actions from bounded Knowledge. No World consequence has happened yet.</p>
        <div class="deliberation-team">
          <div>${specialistToken("engineer-imani", "deliberating")}<span>Engineer</span></div>
          <div>${specialistToken("medic-reyes", "deliberating")}<span>Medic</span></div>
          <div>${specialistToken("security-chen", "deliberating")}<span>Security</span></div>
        </div>
        <small>Elapsed <b data-busy-elapsed>0.0s</b> · client-observed wait only · no fake progress</small>
      </section>
    </div>`;
  }
  if (busy.kind === "resolution" && view) {
    return `<div class="busy resolution-busy" data-testid="busy" data-busy-kind="resolution">
      <section class="deliberation-card resolution-card">
        <div class="deliberation-heading"><div><p class="eyebrow">Commit</p><h2>Resolving all factions</h2></div><span class="status">Turn ${escapeHtml(view.run.turn + 1)}</span></div>
        <p>The selected Preview has been committed. Waiting for authoritative simultaneous resolution; no result is shown before the World response.</p>
        <small>Elapsed <b data-busy-elapsed>0.0s</b></small>
      </section>
    </div>`;
  }
  return `<div class="busy generic-busy" data-testid="busy" data-busy-kind="${escapeHtml(busy.kind ?? "generic")}"><div class="spinner"></div><strong>${escapeHtml(busy.label ?? busy)}</strong><small>Elapsed <b data-busy-elapsed>0.0s</b></small></div>`;
}

function renderMission(view, catalog, expressionTurnSequence = null, audioMuted = false, busy = null) {
  const busyAttrs = busy ? ' inert aria-busy="true"' : "";
  return `<main class="mission"${busyAttrs}>
    <header class="topbar"><div><p class="eyebrow">Station Zero v3 · ${escapeHtml(caseLabel(catalog, view.run.scenarioCaseId))}</p><h1>Mission Control</h1></div><div class="topbar-controls"><button type="button" class="audio-toggle" data-action="toggle-audio" data-testid="audio-toggle" aria-pressed="${audioMuted ? "true" : "false"}" title="Presentation audio does not affect Game state">${audioMuted ? "Audio off" : "Audio on"}</button><div class="turn"><span>Turn</span><strong data-testid="turn-number">${view.run.turn}</strong><small>/ ${view.run.turnLimit}</small></div></div></header>
    <section class="resource-grid">
      ${metric("Battery", view.resources.batteryCharge, view.resources.batteryInitial)}
      ${metric("Oxygen", view.resources.oxygen, 100)}
      ${metric("Reactor heat", view.resources.reactorHeat, 100, 85)}
      ${metric("Alert", view.resources.alertLevel, 5, 4)}
    </section>
    ${renderSystemEvidence(view)}
    ${renderTerminal(view)}
    ${renderAftermath(view, expressionTurnSequence)}
    ${renderFirstCommand(view)}
    <div class="situation-grid">
      ${renderMap(view, expressionTurnSequence)}
      <div class="situation-stack">${renderActors(view)}${renderObjectives(view)}</div>
    </div>
    ${view.run.status === "terminal" ? "" : `<div class="planning-grid">${renderOrder(view, catalog)}${renderPreview(view)}</div>`}
  </main>`;
}

export function renderStationZeroV3App({ view, catalog, runs, busy, error, expressionTurnSequence = null, audioMuted = false }) {
  const content = view ? renderMission(view, catalog, expressionTurnSequence, audioMuted, busy) : renderLanding(runs, catalog);
  return `${content}${renderBusyState(busy, view)}${error ? `<div class="toast error" role="alert">${escapeHtml(error)}</div>` : ""}`;
}
