import { renderCoreCurves } from "./render-curves.js";
import { renderProductNav } from "./render-navigation.js";
import { escapeHtml, humanize, inventorySummary } from "./render-utils.js";

function stateResources(state) {
  return [
    ["Battery", state.resources.batteryCharge],
    ["Oxygen", `${state.resources.oxygen}%`],
    ["Reactor heat", state.resources.reactorHeat],
    ["Turn", `${state.turn} / ${state.mission.turnLimit}`],
  ].map(([label, value]) => `<article><span>${label}</span><strong>${value}</strong></article>`).join("");
}

function actors(state) {
  return Object.values(state.agents).map((actor) => `
    <article class="replay-actor">
      <header><strong>${escapeHtml(actor.name)}</strong><span>${actor.health}% health</span></header>
      <p>${escapeHtml(humanize(actor.locationRoomId))}</p>
      <small>${escapeHtml(inventorySummary(actor.inventory))}</small>
    </article>`).join("");
}

function systems(state) {
  return Object.values(state.systems).map((system) => `
    <article class="replay-system ${system.powered ? "online" : "offline"}">
      <strong>${escapeHtml(system.name)}</strong>
      <span>${Math.round(system.integrity * 100)}% integrity · ${system.powered ? "powered" : "offline"}</span>
    </article>`).join("");
}

function keyTurns(report, revision) {
  return report.keyTurns.map((turn) => `
    <button class="key-turn ${turn.revision === revision ? "active" : ""}" data-replay-jump="${turn.revision}">
      <span>R${turn.revision} · ${escapeHtml(humanize(turn.kind))}</span>
      <strong>${escapeHtml(turn.title)}</strong>
    </button>`).join("");
}

function evidence(frame) {
  const proposalItems = frame.proposals.map((proposal) => `
    <li><strong>${escapeHtml(humanize(proposal.actorId))}</strong> proposed ${escapeHtml(humanize(proposal.command.kind))} · ${escapeHtml(humanize(proposal.status))}</li>`).join("");
  const facts = frame.facts.map((fact) => `<li>${escapeHtml(humanize(fact.kind))}</li>`).join("");
  return `
    <section class="panel replay-evidence">
      <div class="section-heading"><div><p class="eyebrow">RETAINED EVIDENCE</p><h2>What advanced this revision</h2></div><span>${frame.evidenceNodeIds.length} nodes</span></div>
      <div class="evidence-columns">
        <div><h3>Round</h3><p>${frame.round ? `${escapeHtml(humanize(frame.round.status))} · ${frame.proposals.length} proposals` : "Genesis or no retained Round"}</p><ul>${proposalItems || "<li>No proposals</li>"}</ul></div>
        <div><h3>Execution</h3><p>${frame.effect ? `${escapeHtml(humanize(frame.effect.status))} Effect` : "No Effect"}</p><p>${frame.dispatch ? `${escapeHtml(humanize(frame.dispatch.status))} Dispatch` : "No Dispatch"}</p><p>${frame.observation ? `${frame.observation.verifiedIntentCommandIds.length} verified intents` : "No Observation"}</p></div>
        <div><h3>World facts</h3><ul>${facts || "<li>No facts at Genesis</li>"}</ul></div>
      </div>
    </section>`;
}

export function renderReplay(report, frame, { compareReady = false } = {}) {
  const revision = frame.revision;
  const maximum = report.summary.terminalRevision;
  return `
    <main class="product-shell">
      ${renderProductNav({ surface: "replay", runId: report.runId, compareReady })}
      <header class="product-header">
        <div><p class="eyebrow">VERIFIED REPLAY</p><h1>Revision ${revision}</h1><p>World state and the evidence that advanced it. Timestamp order is not authority.</p></div>
        <div class="digest-chip"><span>${frame.verified ? "Verified" : "Unverified"}</span><code>${escapeHtml(frame.digest.slice(0, 16))}</code></div>
      </header>
      <section class="replay-controls panel">
        <label for="replay-revision"><span>World revision</span><strong>${revision} / ${maximum}</strong></label>
        <input id="replay-revision" data-replay-revision type="range" min="0" max="${maximum}" value="${revision}" />
        <div class="key-turn-list">${keyTurns(report, revision)}</div>
      </section>
      <section class="replay-resource-strip">${stateResources(frame.state)}</section>
      ${renderCoreCurves(report.curves, revision)}
      <section class="replay-state-grid">
        <section class="panel"><div class="section-heading"><div><p class="eyebrow">ACTORS</p><h2>State at revision ${revision}</h2></div></div><div class="replay-actors">${actors(frame.state)}</div></section>
        <section class="panel"><div class="section-heading"><div><p class="eyebrow">SYSTEMS</p><h2>Station configuration</h2></div></div><div class="replay-systems">${systems(frame.state)}</div></section>
      </section>
      ${evidence(frame)}
    </main>`;
}
