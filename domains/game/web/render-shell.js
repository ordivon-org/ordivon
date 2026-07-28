import { renderActors } from "./render-actors.js";
import { renderInbox } from "./render-inbox.js";
import { renderMap } from "./render-map.js";
import { renderObjectives } from "./render-objectives.js";
import { renderTimeline } from "./render-timeline.js";
import { TEAM_ACTORS } from "./store.js";
import { bandClass, escapeHtml, humanize, providerOptions } from "./render-utils.js";

function errorBanner(error) {
  return error ? `<div class="error-banner" role="alert"><strong>Mission Control error</strong><span>${escapeHtml(error.message ?? error)}</span></div>` : "";
}

function runCards(runs) {
  if (!runs.length) return '<p class="empty-label">No compatible Station Zero missions are retained.</p>';
  return runs.slice(0, 8).map((run) => `
    <article class="resume-card">
      <div><strong>${escapeHtml(humanize(run.status))}</strong><span>${new Date(run.createdAt).toLocaleString()}</span></div>
      <button data-resume-run="${escapeHtml(run.runId)}">Resume mission</button>
    </article>`).join("");
}

export function renderDeployment(runs, error = null, selectedRunId = null) {
  const actorFields = TEAM_ACTORS.map((actor) => `
    <label class="provider-field"><span>${escapeHtml(actor.role)}</span><select name="${escapeHtml(actor.actorId)}">${providerOptions(actor.defaultProvider)}</select></label>`).join("");
  return `
    <main class="deployment-shell">
      <nav class="top-nav"><span>ORDIVON GAME</span><a href="/debug.html">Engineering debug</a></nav>
      ${errorBanner(error)}
      <section class="deployment-hero">
        <p class="eyebrow">STATION ZERO · M4</p>
        <h1>Direct an imperfect autonomous team.</h1>
        <p>Configure three persistent specialists, inspect what each one knows, review their proposals before mutation, and commit one independently verified World Tick at a time.</p>
      </section>
      <section class="deployment-grid">
        <form id="deployment-form" class="panel deployment-form">
          <div class="section-heading"><div><p class="eyebrow">NEW DEPLOYMENT</p><h2>Team configuration</h2></div><span>Scenario v2 · Ruleset v3</span></div>
          <div class="provider-grid">${actorFields}</div>
          <label class="authority-field"><span>Authority policy</span><select name="authorityPolicyMode"><option value="autonomous">Autonomous</option><option value="supervised">Supervised</option><option value="locked">Locked</option></select></label>
          <div class="configuration-note">
            <strong>Fixed first-playable loadout</strong>
            <p>Engineer carries tools and one spare part; Medic begins near the medkit; Security can contain the breach. Risk preferences and equipment are visible but not cosmetic controls.</p>
          </div>
          <input type="hidden" name="runId" value="${escapeHtml(selectedRunId ?? "")}" />
          <button class="primary" type="submit">Start verified mission</button>
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
  const actors = round?.actors.length ? round.actors.map((actor) => `
    <article class="round-actor"><strong>${escapeHtml(humanize(actor.actorId))}</strong><span>${escapeHtml(actor.action ?? "No proposal")}</span><small>${escapeHtml(humanize(actor.status))} · ${escapeHtml(humanize(actor.authority ?? "none"))}</small></article>`).join("") : '<p class="empty-label">Prepare the next coordination Round to inspect proposals.</p>';
  return `
    <section class="panel round-panel">
      <div class="section-heading"><div><p class="eyebrow">COORDINATION FRONTIER</p><h2>${round ? escapeHtml(humanize(round.phase)) : "Ready for next Round"}</h2></div><span>World rev ${view.run.revision ?? view.generatedFrom.worldRevision}</span></div>
      <div class="round-actors">${actors}</div>
      ${round?.blocker ? `<p class="blocker">Blocked: ${escapeHtml(humanize(round.blocker))}</p>` : ""}
      <div class="mission-actions">
        <button class="secondary" data-mission-action="prepare" ${view.controls.canPrepare ? "" : "disabled"}>Prepare proposals</button>
        <button class="primary" data-mission-action="commit" ${view.controls.canCommit ? "" : "disabled"}>Commit one verified Tick</button>
      </div>
      <p class="control-explainer">Prepare stops before World mutation. Commit admits a compatible proposal subset and stops after one independently verified Tick.</p>
    </section>`;
}

function terminalSummary(view) {
  if (view.run.status === "running") return "";
  const components = Object.entries(view.mission.scoreComponents ?? {}).map(([name, value]) => `<div><dt>${escapeHtml(humanize(name))}</dt><dd>${value}</dd></div>`).join("");
  return `
    <section class="terminal-panel ${escapeHtml(view.run.status)}">
      <p class="eyebrow">VERIFIED TERMINAL OUTCOME</p>
      <h2>${view.run.status === "victory" ? "Rescue signal verified" : "Mission failed"}</h2>
      <p>${escapeHtml(view.mission.reason ?? "The World reached a terminal state.")}</p>
      <strong class="final-score">Score ${view.mission.score ?? 0}</strong>
      <dl class="score-grid">${components}</dl>
      <div class="button-row"><button data-new-mission>Configure another deployment</button><span>M5 will add full replay and causal diagnosis.</span></div>
    </section>`;
}

export function renderMission(view, { busy = false, error = null } = {}) {
  return `
    <main class="mission-shell ${busy ? "busy" : ""}">
      <nav class="top-nav"><span>ORDIVON GAME · MISSION CONTROL</span><div><button class="text-button" data-new-mission>New deployment</button><a href="/debug.html">Engineering debug</a></div></nav>
      ${errorBanner(error)}
      <header class="mission-header">
        <div><p class="eyebrow">${escapeHtml(humanize(view.configuration?.authorityPolicyMode ?? "unconfigured"))} AUTHORITY</p><h1>Station Zero</h1><p>${escapeHtml(view.mission.urgency)}</p></div>
        <div class="mission-state ${escapeHtml(view.run.status)}"><strong>${escapeHtml(humanize(view.run.status))}</strong><span>Tick ${view.run.turn} / ${view.run.turnLimit}</span></div>
      </header>
      <section class="resource-strip">${resourceCards(view)}</section>
      ${terminalSummary(view)}
      <section class="primary-grid">${renderMap(view)}${renderInbox(view)}</section>
      ${roundReview(view)}
      ${renderObjectives(view)}
      ${renderActors(view)}
      ${renderTimeline(view)}
      ${busy ? '<div class="busy-overlay"><span></span><strong>Provider cognition or verified execution in progress…</strong></div>' : ""}
    </main>`;
}

export function renderFatal(error) {
  return `<main class="boot-shell">${errorBanner(error)}<p class="eyebrow">MISSION CONTROL UNAVAILABLE</p><h1>Unable to load Station Zero.</h1><button data-new-mission>Return to deployment</button></main>`;
}
