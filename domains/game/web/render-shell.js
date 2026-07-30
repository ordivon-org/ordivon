import { renderActors } from "./render-actors.js";
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
  if (!runs.length) {
    return '<p class="empty-label">No compatible Station Zero missions are retained.</p>';
  }
  return runs.slice(0, 8).map((run) => `
    <article class="resume-card">
      <div><strong>${escapeHtml(humanize(run.status))}</strong><span>${new Date(run.createdAt).toLocaleString()}</span><small>${escapeHtml(humanize(run.scenarioCaseId))}</small></div>
      <button data-resume-run="${escapeHtml(run.runId)}">${run.status === "running" ? "Resume mission" : "Open mission"}</button>
    </article>`).join("");
}

function selected(value, expected) {
  return value === expected ? "selected" : "";
}

function providerReadiness(preflight) {
  return (preflight?.providers ?? []).map((entry) => `
    <li class="${entry.ready ? "ready" : "unavailable"}"><strong>${escapeHtml(humanize(entry.providerId))}</strong><span>${escapeHtml(entry.summary)}</span></li>`).join("");
}

export function renderDeployment(
  runs,
  options = {},
  legacySelectedRunId = null,
  legacyCatalog = null,
) {
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
    return `
      <label class="provider-field"><span>${escapeHtml(actor.name)} · ${escapeHtml(humanize(actor.role))}</span><select name="${escapeHtml(actor.actorId)}">${providerOptions(catalog?.providers, provider, preflight)}</select></label>`;
  }).join("");
  const scenarioCaseId = cloneManifest?.scenarioCaseId ?? "baseline";
  const caseOptions = (catalog?.cases ?? []).map((scenarioCase) => `
    <option value="${escapeHtml(scenarioCase.caseId)}" ${selected(scenarioCase.caseId, scenarioCaseId)}>${escapeHtml(scenarioCase.label)}</option>`).join("");
  const authorityPolicyMode = cloneManifest?.authorityPolicyMode ?? "autonomous";
  const authorityOptions = (catalog?.authorityPolicies ?? []).map((policy) => `
    <option value="${escapeHtml(policy.policyMode)}" ${selected(policy.policyMode, authorityPolicyMode)}>${escapeHtml(policy.label)}</option>`).join("");
  const coordinationProfileId = cloneManifest?.coordinationProfileId ?? "specialist-containment";
  const coordinationOptions = (catalog?.coordinationProfiles ?? []).map((profile) => `
    <option value="${escapeHtml(profile.profileId)}" ${selected(profile.profileId, coordinationProfileId)}>${escapeHtml(profile.label)}</option>`).join("");
  return `
    <main class="deployment-shell">
      ${renderProductNav()}
      ${errorBanner(error)}
      <section class="deployment-hero">
        <p class="eyebrow">STATION ZERO · FIRST PLAYABLE</p>
        <h1>${cloneManifest ? "Change one verified deployment input." : "Direct an imperfect autonomous team."}</h1>
        <p>${cloneManifest ? `This new Run preserves ${escapeHtml(compareBaseRunId ?? "the base Run")} for exact comparison.` : "Configure three persistent specialists, review proposals before mutation, and commit one independently verified World Tick at a time."}</p>
      </section>
      <section class="deployment-grid">
        <form id="deployment-form" class="panel deployment-form">
          <div class="section-heading"><div><p class="eyebrow">${cloneManifest ? "CLONED DEPLOYMENT" : "NEW DEPLOYMENT"}</p><h2>Team configuration</h2></div><span>Scenario v2 · Ruleset v3</span></div>
          <label class="authority-field"><span>Scenario Case</span><select name="scenarioCaseId">${caseOptions}</select></label>
          <label class="authority-field"><span>Coordination profile</span><select name="coordinationProfileId">${coordinationOptions}</select></label>
          <div class="provider-grid">${actorFields}</div>
          <label class="authority-field"><span>Authority policy</span><select name="authorityPolicyMode">${authorityOptions}</select></label>
          <div class="configuration-note">
            <strong>${escapeHtml(catalog?.fixedLoadout?.label ?? "Standard emergency loadout")}</strong>
            <p>${escapeHtml(catalog?.fixedLoadout?.description ?? "The verified first-playable loadout is fixed.")}</p>
          </div>
          <details class="provider-preflight"><summary>Provider readiness</summary><ul>${providerReadiness(preflight)}</ul></details>
          <input type="hidden" name="runId" value="${escapeHtml(selectedRunId ?? "")}" />
          <button class="primary" type="submit">${cloneManifest ? "Start comparison Run" : "Start verified mission"}</button>
        </form>
        <section class="panel retained-runs">
          <div class="section-heading"><div><p class="eyebrow">RETAINED RUNS</p><h2>Resume after reload</h2></div><span>${runs.length}</span></div>
          <div class="resume-list">${runCards(runs)}</div>
        </section>
      </section>
    </main>`;
}

function resourceCards(view) {
  return view.resources.map((resource) => {
    const suffix = resource.unit === "percent" || resource.unit === "health" ? "%" : "";
    const maximum = resource.maximum === null ? "" : `<small>/ ${resource.maximum}${suffix}</small>`;
    return `<article class="resource-card ${bandClass(resource.band)}"><span>${escapeHtml(resource.label)}</span><strong>${resource.current}${suffix}${maximum}</strong><em>${escapeHtml(humanize(resource.trend))}</em></article>`;
  }).join("");
}

function roundReview(view) {
  const round = view.currentRound;
  const actors = round?.actors.length
    ? round.actors.map((actor) => `
      <article class="round-actor"><strong>${escapeHtml(humanize(actor.actorId))}</strong><span>${escapeHtml(actor.action ?? "No proposal")}</span><small>${escapeHtml(humanize(actor.status))} · ${escapeHtml(humanize(actor.authority ?? "none"))}</small></article>`).join("")
    : '<p class="empty-label">Prepare the next coordination Round to inspect proposals.</p>';
  return `
    <section class="panel round-panel">
      <div class="section-heading"><div><p class="eyebrow">COORDINATION FRONTIER</p><h2>${round ? escapeHtml(humanize(round.phase)) : "Ready for next Round"}</h2></div><span>World rev ${view.generatedFrom.worldRevision}</span></div>
      <div class="round-actors">${actors}</div>
      ${round?.blocker ? `<p class="blocker">Blocked: ${escapeHtml(humanize(round.blocker))}</p>` : ""}
      <div class="mission-actions">
        <button class="secondary" data-mission-action="prepare" ${view.controls.canPrepare ? "" : "disabled"}>Prepare proposals</button>
        <button class="primary" data-mission-action="commit" ${view.controls.canCommit ? "" : "disabled"}>Commit one verified Tick</button>
      </div>
      <p class="control-explainer">Prepare stops before World mutation. Commit admits a compatible proposal subset and stops after one independently verified Tick.</p>
    </section>`;
}

function terminalSummary(view, compareReady) {
  if (view.run.status === "running") return "";
  const components = Object.entries(view.mission.scoreComponents ?? {}).map(([name, value]) => `<div><dt>${escapeHtml(humanize(name))}</dt><dd>${value}</dd></div>`).join("");
  return `
    <section class="terminal-panel ${escapeHtml(view.run.status)}">
      <p class="eyebrow">VERIFIED TERMINAL OUTCOME</p>
      <h2>${view.run.status === "victory" ? "Rescue signal verified" : "Mission failed"}</h2>
      <p>${escapeHtml(view.mission.reason ?? "The World reached a terminal state.")}</p>
      <strong class="final-score">Score ${view.mission.score ?? 0}</strong>
      <dl class="score-grid">${components}</dl>
      <div class="button-row">
        <button data-surface="replay">Open verified Replay</button>
        <button data-surface="diagnosis">Explain this outcome</button>
        ${compareReady ? '<button data-surface="compare">Compare with base Run</button>' : ""}
        <button data-clone-run="${escapeHtml(view.run.runId)}">Deploy again from this Run</button>
      </div>
    </section>`;
}

export function renderMission(
  view,
  { busy = false, error = null, catalog = null, compareReady = false } = {},
) {
  return `
    <main class="mission-shell ${busy ? "busy" : ""}">
      ${renderProductNav({ surface: "mission", runId: view.run.runId, compareReady })}
      ${errorBanner(error)}
      <header class="mission-header">
        <div><p class="eyebrow">${escapeHtml(humanize(view.configuration?.authorityPolicyMode ?? "unconfigured"))} AUTHORITY · ${escapeHtml(humanize(view.run.scenarioCaseId))}</p><h1>Station Zero</h1><p>${escapeHtml(view.mission.urgency)}</p></div>
        <div class="mission-state ${escapeHtml(view.run.status)}"><strong>${escapeHtml(humanize(view.run.status))}</strong><span>Tick ${view.run.turn} / ${view.run.turnLimit}</span></div>
      </header>
      <section class="resource-strip">${resourceCards(view)}</section>
      ${terminalSummary(view, compareReady)}
      <section class="primary-grid">${renderMap(view)}${renderInbox(view)}</section>
      ${roundReview(view)}
      ${renderObjectives(view)}
      ${renderActors(view, catalog)}
      ${renderTimeline(view)}
      ${busy ? '<div class="busy-overlay"><span></span><strong>Provider cognition or verified execution in progress…</strong></div>' : ""}
    </main>`;
}

export function renderFatal(error) {
  return `<main class="boot-shell">${errorBanner(error)}<p class="eyebrow">STATION ZERO UNAVAILABLE</p><h1>Unable to load the first playable.</h1><button data-new-mission>Return to deployment</button></main>`;
}
