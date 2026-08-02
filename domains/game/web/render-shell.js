import { renderActors } from "./render-actors.js";
import { renderMissionFronts } from "./render-fronts.js";
import { renderInbox } from "./render-inbox.js";
import { renderMap } from "./render-map.js";
import { renderProductNav } from "./render-navigation.js";
import { renderObjectives } from "./render-objectives.js";
import { renderTimeline } from "./render-timeline.js";
import { bandClass, escapeHtml, humanize, providerOptions } from "./render-utils.js";

function errorBanner(error) {
  return error
    ? `<div class="error-banner" role="alert"><strong>Station Zero error</strong><span>${escapeHtml(error.message ?? error)}</span></div>`
    : "";
}

function runCards(runs) {
  if (!runs.length) return '<p class="empty-label">No retained Station Zero missions.</p>';
  return runs.slice(0, 8).map((run) => `
    <article class="resume-card">
      <div><strong>${escapeHtml(humanize(run.status))}</strong><span>${new Date(run.createdAt).toLocaleString()}</span><small>${escapeHtml(humanize(run.scenarioCaseId))}</small></div>
      <button data-resume-run="${escapeHtml(run.runId)}">${run.status === "running" ? "Resume mission" : "Open report"}</button>
    </article>`).join("");
}

function selected(value, expected) {
  return value === expected ? "selected" : "";
}

function providerReadiness(preflight) {
  return (preflight?.providers ?? []).map((entry) => `
    <li class="${entry.ready ? "ready" : "unavailable"}"><strong>${escapeHtml(humanize(entry.providerId))}</strong><span>${escapeHtml(entry.summary)}</span></li>`).join("");
}

function doctrineIdForManifest(catalog, manifest) {
  return catalog?.doctrines?.find((entry) => entry.authorityPolicyMode === manifest?.authorityPolicyMode)?.doctrineId
    ?? catalog?.playDefaults?.doctrineId
    ?? "critical-approval";
}

export function renderDeployment(runs, options = {}, legacySelectedRunId = null, legacyCatalog = null) {
  const normalized = options === null || options instanceof Error || typeof options !== "object"
    ? { error: options, selectedRunId: legacySelectedRunId, catalog: legacyCatalog }
    : options;
  const {
    error = null,
    selectedRunId = null,
    catalog = legacyCatalog,
    preflight = null,
    cloneManifest = null,
    compareBaseRunId = null,
  } = normalized;
  const actorFields = (catalog?.actors ?? []).map((actor) => {
    const retained = cloneManifest?.actors?.find((item) => item.actorId === actor.actorId);
    const provider = retained?.providerOrder?.[0] ?? actor.defaultProvider;
    return `<label class="provider-field"><span>${escapeHtml(actor.name)} · ${escapeHtml(humanize(actor.role))}</span><select name="${escapeHtml(actor.actorId)}">${providerOptions(catalog?.providers, provider, preflight)}</select></label>`;
  }).join("");
  const scenarioCaseId = cloneManifest?.scenarioCaseId ?? catalog?.playDefaults?.scenarioCaseId ?? "baseline";
  const caseOptions = (catalog?.cases ?? []).map((scenarioCase) => `
    <option value="${escapeHtml(scenarioCase.caseId)}" ${selected(scenarioCase.caseId, scenarioCaseId)}>${escapeHtml(scenarioCase.label)}</option>`).join("");
  const doctrineId = doctrineIdForManifest(catalog, cloneManifest);
  const doctrineOptions = (catalog?.doctrines ?? []).map((doctrine) => `
    <option value="${escapeHtml(doctrine.doctrineId)}" ${selected(doctrine.doctrineId, doctrineId)}>${escapeHtml(doctrine.label)}</option>`).join("");
  const coordinationProfileId = cloneManifest?.coordinationProfileId ?? catalog?.playDefaults?.coordinationProfileId ?? "specialist-containment";
  const coordinationOptions = (catalog?.coordinationProfiles ?? []).map((profile) => `
    <option value="${escapeHtml(profile.profileId)}" ${selected(profile.profileId, coordinationProfileId)}>${escapeHtml(profile.label)}</option>`).join("");
  const doctrineDescription = (catalog?.doctrines ?? []).find((entry) => entry.doctrineId === doctrineId)?.description ?? "Routine work proceeds automatically; consequential actions return to Mission Control.";
  return `
    <main class="deployment-shell">
      ${renderProductNav()}
      ${errorBanner(error)}
      <section class="deployment-hero">
        <p class="eyebrow">STATION ZERO · PLAY MODE</p>
        <h1>${cloneManifest ? "Change the command doctrine. Compare the consequence." : "Command the emergency, not every Tick."}</h1>
        <p>${cloneManifest ? `The original Run remains retained for exact comparison with ${escapeHtml(compareBaseRunId ?? "the new deployment")}.` : "Set the mission and standing orders. The specialist team executes routine work and stops when Mission Control must make a consequential decision."}</p>
      </section>
      <section class="deployment-grid">
        <form id="deployment-form" class="panel deployment-form">
          <div class="section-heading"><div><p class="eyebrow">${cloneManifest ? "COMPARISON DEPLOYMENT" : "MISSION BRIEF"}</p><h2>Standing orders</h2></div><span>Station Zero</span></div>
          <label class="authority-field"><span>Emergency</span><select name="scenarioCaseId">${caseOptions}</select></label>
          <label class="authority-field"><span>Command doctrine</span><select name="doctrineId">${doctrineOptions}</select><small>${escapeHtml(doctrineDescription)}</small></label>
          <div class="configuration-note"><strong>Three persistent specialists</strong><p>Engineer Imani, Medic Reyes, and Security Chen retain their identities, tasks, and verified history across the mission.</p></div>
          <details class="advanced-deployment">
            <summary>Lab and model configuration</summary>
            <label class="authority-field"><span>Coordination fixture</span><select name="coordinationProfileId">${coordinationOptions}</select></label>
            <div class="provider-grid">${actorFields}</div>
            <details class="provider-preflight"><summary>Provider readiness</summary><ul>${providerReadiness(preflight)}</ul></details>
          </details>
          <input type="hidden" name="runId" value="${escapeHtml(selectedRunId ?? "")}" />
          <button class="primary deployment-start" type="submit">${cloneManifest ? "Start comparison mission" : "Begin emergency response"}</button>
        </form>
        <section class="panel retained-runs">
          <div class="section-heading"><div><p class="eyebrow">RETAINED MISSIONS</p><h2>Continue or inspect</h2></div><span>${runs.length}</span></div>
          <div class="resume-list">${runCards(runs)}</div>
        </section>
      </section>
    </main>`;
}

function resourceCards(view) {
  const forecast = new Map((view.experience?.passiveForecast?.resources ?? []).map((entry) => [entry.resourceId, entry]));
  return view.resources.map((resource) => {
    const suffix = resource.unit === "percent" || resource.unit === "health" ? "%" : "";
    const maximum = resource.maximum === null ? "" : `<small>/ ${resource.maximum}${suffix}</small>`;
    const next = forecast.get(resource.resourceId);
    const forecastLine = next && next.after !== next.before
      ? `<em class="resource-forecast">No-change next Tick: ${next.after}${suffix} <span>${next.delta > 0 ? "+" : ""}${next.delta}</span></em>`
      : `<em class="resource-forecast">No-change next Tick: stable</em>`;
    return `<article class="resource-card ${bandClass(resource.band)}"><span>${escapeHtml(resource.label)}</span><strong>${resource.current}${suffix}${maximum}</strong>${forecastLine}</article>`;
  }).join("");
}

function proposalForecast(actor) {
  if (!actor.forecast || actor.forecast.status !== "available") return "";
  const changed = actor.forecast.resources.filter((entry) => entry.delta !== 0).slice(0, 3);
  const lines = changed.map((entry) => `<li>${escapeHtml(entry.label)} ${entry.before} → ${entry.after}</li>`).join("");
  const effects = actor.forecast.irreversibleEffects.map((entry) => `<li>${escapeHtml(entry)}</li>`).join("");
  return lines || effects ? `<ul class="proposal-forecast">${lines}${effects}</ul>` : "";
}

function timeControl(view) {
  const round = view.currentRound;
  const proposals = round?.actors.length
    ? round.actors.map((actor) => `
      <article class="round-actor">
        <header><strong>${escapeHtml(humanize(actor.actorId))}</strong><small>${Math.round((actor.confidence ?? 0) * 100)}% confidence</small></header>
        <span>${escapeHtml(actor.action ?? "No proposal")}</span>
        ${actor.rationale ? `<p>${escapeHtml(actor.rationale)}</p>` : ""}
        ${proposalForecast(actor)}
      </article>`).join("")
    : '<p class="empty-label">The next proposal frontier will be prepared automatically.</p>';
  const decisionPending = Boolean(view.experience.activeInterventionId);
  return `
    <section class="panel time-control-panel">
      <div class="section-heading"><div><p class="eyebrow">TIME CONTROL</p><h2>${decisionPending ? "Mission Control decision required" : "Team ready to continue"}</h2></div><span>World revision ${view.generatedFrom.worldRevision}</span></div>
      ${round && ["proposal-review", "authority"].includes(round.phase) ? `<div class="round-actors">${proposals}</div>` : ""}
      ${round?.blocker ? `<p class="blocker">Operational blocker: ${escapeHtml(humanize(round.blocker))}</p>` : ""}
      <div class="mission-actions">
        <button class="primary" data-advance-mode="until-intervention" ${view.controls.canRun && !decisionPending ? "" : "disabled"}>Run until intervention</button>
        <button class="secondary" data-advance-mode="one-tick" ${view.controls.canAdvanceOne && !decisionPending ? "" : "disabled"}>Advance one Tick</button>
        <button class="secondary" data-advance-mode="three-ticks" ${view.controls.canRun && !decisionPending ? "" : "disabled"}>Advance up to three Ticks</button>
      </div>
      <p class="control-explainer">Routine verified actions continue automatically. Authority requests, conflicts, specialist failure, and terminal outcomes stop execution.</p>
    </section>`;
}

function terminalSummary(view, compareReady) {
  if (view.run.status === "running") return "";
  const outcome = view.experience.outcome;
  const facts = (outcome?.facts ?? []).map((fact) => `<li>${escapeHtml(fact)}</li>`).join("");
  const nearMisses = (outcome?.nearMisses ?? []).map((fact) => `<li>${escapeHtml(fact)}</li>`).join("");
  return `
    <section class="terminal-panel ${escapeHtml(view.run.status)}">
      <p class="eyebrow">VERIFIED MISSION OUTCOME</p>
      <h2>${escapeHtml(outcome?.headline ?? (view.run.status === "victory" ? "Rescue signal verified" : "Mission failed"))}</h2>
      <p>${escapeHtml(outcome?.summary ?? view.mission.reason ?? "The World reached a terminal state.")}</p>
      <div class="outcome-grid">
        <section><h3>What happened</h3><ul>${facts}</ul></section>
        <section><h3>Margins</h3>${nearMisses ? `<ul>${nearMisses}</ul>` : "<p>No critical terminal margin was recorded.</p>"}</section>
      </div>
      <div class="button-row">
        <button data-surface="replay">Open verified Replay</button>
        <button data-surface="diagnosis">Explain this outcome</button>
        ${compareReady ? '<button data-surface="compare">Compare with base Run</button>' : ""}
        <button data-clone-run="${escapeHtml(view.run.runId)}">Deploy again from this Run</button>
      </div>
    </section>`;
}

export function renderMission(view, { busy = false, error = null, catalog = null, compareReady = false } = {}) {
  return `
    <main class="mission-shell ${busy ? "busy" : ""}">
      ${renderProductNav({ surface: "mission", runId: view.run.runId, compareReady })}
      ${errorBanner(error)}
      <header class="mission-header">
        <div><p class="eyebrow">${escapeHtml(humanize(view.experience.doctrineId))} · ${escapeHtml(humanize(view.run.scenarioCaseId))}</p><h1>Station Zero</h1><p>${escapeHtml(view.mission.urgency)}</p></div>
        <div class="mission-state ${escapeHtml(view.run.status)}"><strong>${escapeHtml(humanize(view.run.status))}</strong><span>Tick ${view.run.turn} / ${view.run.turnLimit}</span></div>
      </header>
      <section class="resource-strip">${resourceCards(view)}</section>
      ${terminalSummary(view, compareReady)}
      ${renderMissionFronts(view)}
      <section class="primary-grid">${renderMap(view)}${renderInbox(view)}</section>
      ${view.run.status === "running" ? timeControl(view) : ""}
      ${renderActors(view, catalog)}
      <details class="secondary-system-panel"><summary>Technical objective graph</summary>${renderObjectives(view)}</details>
      <details class="secondary-system-panel"><summary>Recent verified timeline</summary>${renderTimeline(view)}</details>
      ${busy ? '<div class="busy-overlay"><span></span><strong>Specialists are reasoning or the World is committing verified actions…</strong><button type="button" disabled>Execution remains recoverable</button></div>' : ""}
    </main>`;
}

export function renderFatal(error) {
  return `<main class="boot-shell">${errorBanner(error)}<p class="eyebrow">STATION ZERO UNAVAILABLE</p><h1>Unable to load the first playable.</h1><button data-new-mission>Return to deployment</button></main>`;
}
