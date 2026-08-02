import {
  advanceMission,
  compareRuns,
  initializeMission,
  issueCommand,
  listRuns,
  loadCatalog,
  loadDeploymentManifest,
  loadMission,
  loadProviderPreflight,
  loadReplayFrame,
  loadReplayReport,
} from "./api.js";
import { renderCompare } from "./render-compare.js";
import { renderDiagnosis } from "./render-diagnosis.js";
import { renderReplay } from "./render-replay.js";
import { renderDeployment, renderFatal, renderMission } from "./render-shell.js";
import {
  compareRunIdFromUrl,
  compatibleRuns,
  createRunId,
  revisionFromUrl,
  runIdFromUrl,
  surfaceFromUrl,
  urlForState,
} from "./store.js";

const root = document.querySelector("#app");
let runs = [];
let catalog = null;
let preflight = null;
let view = null;
let replayReport = null;
let replayFrame = null;
let comparison = null;
let cloneManifest = null;
let busy = false;
let error = null;
let currentRunId = runIdFromUrl(window.location.href);
let surface = surfaceFromUrl(window.location.href);
let selectedRevision = revisionFromUrl(window.location.href);
let compareBaseRunId = compareRunIdFromUrl(window.location.href);

function compareReady() {
  return Boolean(compareBaseRunId && currentRunId && compareBaseRunId !== currentRunId && view?.run?.status !== "running");
}

function syncUrl() {
  history.replaceState({}, "", urlForState(window.location.href, {
    runId: currentRunId,
    surface,
    revision: selectedRevision,
    compareRunId: compareBaseRunId,
  }));
}

function draw() {
  if (!root) return;
  const ready = compareReady();
  if (!view?.initialized) {
    root.innerHTML = renderDeployment(runs, {
      error,
      selectedRunId: currentRunId,
      catalog,
      preflight,
      cloneManifest,
      compareBaseRunId,
    });
  } else if (surface === "replay" && replayReport && replayFrame) {
    root.innerHTML = renderReplay(replayReport, replayFrame, { compareReady: ready });
  } else if (surface === "diagnosis" && replayReport) {
    root.innerHTML = renderDiagnosis(replayReport, { compareReady: ready });
  } else if (surface === "compare" && comparison) {
    root.innerHTML = renderCompare(comparison);
  } else {
    root.innerHTML = renderMission(view, { busy, error, catalog, compareReady: ready });
  }
}

function resetDerived() {
  replayReport = null;
  replayFrame = null;
  comparison = null;
  selectedRevision = null;
}

function setRunId(runId) {
  currentRunId = runId;
  syncUrl();
}

async function perform(operation) {
  if (busy) return;
  busy = true;
  error = null;
  draw();
  try {
    await operation();
  } catch (caught) {
    error = caught;
    if (surface !== "mission") surface = "mission";
  } finally {
    busy = false;
    syncUrl();
    draw();
  }
}

async function refreshRuns() {
  const result = await listRuns();
  runs = compatibleRuns(result.runs ?? []);
}

async function ensureReplay(revision = selectedRevision) {
  if (!currentRunId) return;
  replayReport ??= await loadReplayReport(currentRunId);
  const maximum = replayReport.summary.terminalRevision;
  selectedRevision = revision === null ? maximum : Math.max(0, Math.min(maximum, Number(revision)));
  replayFrame = await loadReplayFrame(currentRunId, selectedRevision);
}

async function ensureComparison() {
  if (!compareReady()) throw new Error("Deploy again from a retained terminal Run before opening Compare.");
  comparison = await compareRuns(compareBaseRunId, currentRunId);
}

async function openSurface(next) {
  surface = next;
  error = null;
  if (next === "replay") await ensureReplay();
  else if (next === "diagnosis") {
    if (!currentRunId) return;
    replayReport ??= await loadReplayReport(currentRunId);
  } else if (next === "compare") await ensureComparison();
  syncUrl();
  draw();
}

async function bootFromUrl() {
  currentRunId = runIdFromUrl(window.location.href);
  surface = surfaceFromUrl(window.location.href);
  selectedRevision = revisionFromUrl(window.location.href);
  compareBaseRunId = compareRunIdFromUrl(window.location.href);
  resetDerived();
  if (currentRunId) {
    view = await loadMission(currentRunId);
    if (surface === "replay") await ensureReplay(selectedRevision);
    else if (surface === "diagnosis") replayReport = await loadReplayReport(currentRunId);
    else if (surface === "compare") await ensureComparison();
  } else view = null;
}

async function boot() {
  try {
    [catalog, preflight] = await Promise.all([loadCatalog(), loadProviderPreflight()]);
    await refreshRuns();
    await bootFromUrl();
    draw();
  } catch (caught) {
    error = caught;
    root.innerHTML = renderFatal(caught);
  }
}

root.addEventListener("submit", (event) => {
  if (event.target.id !== "deployment-form") return;
  event.preventDefault();
  const form = new FormData(event.target);
  const runId = String(form.get("runId") || createRunId());
  const providers = Object.fromEntries((catalog?.actors ?? []).map((actor) => [
    actor.actorId,
    String(form.get(actor.actorId) || actor.defaultProvider),
  ]));
  perform(async () => {
    view = await initializeMission({
      runId,
      scenarioCaseId: String(form.get("scenarioCaseId") || catalog?.playDefaults?.scenarioCaseId || "baseline"),
      doctrineId: String(form.get("doctrineId") || catalog?.playDefaults?.doctrineId || "critical-approval"),
      coordinationProfileId: String(form.get("coordinationProfileId") || catalog?.playDefaults?.coordinationProfileId || "specialist-containment"),
      providers,
    });
    cloneManifest = null;
    resetDerived();
    surface = "mission";
    setRunId(runId);
    await refreshRuns();
  });
});

root.addEventListener("click", (event) => {
  const target = event.target.closest("button, a");
  if (!target) return;
  if (target.dataset.resumeRun) {
    perform(async () => {
      cloneManifest = null;
      compareBaseRunId = null;
      resetDerived();
      surface = "mission";
      setRunId(target.dataset.resumeRun);
      view = await loadMission(currentRunId);
    });
    return;
  }
  if (target.hasAttribute("data-new-mission")) {
    view = null;
    cloneManifest = null;
    compareBaseRunId = null;
    error = null;
    resetDerived();
    surface = "mission";
    setRunId(null);
    draw();
    return;
  }
  if (target.dataset.cloneRun) {
    perform(async () => {
      cloneManifest = await loadDeploymentManifest(target.dataset.cloneRun);
      compareBaseRunId = target.dataset.cloneRun;
      currentRunId = null;
      view = null;
      resetDerived();
      surface = "mission";
    });
    return;
  }
  if (target.dataset.surface) {
    perform(async () => openSurface(target.dataset.surface));
    return;
  }
  if (target.dataset.replayJump !== undefined && currentRunId) {
    perform(async () => {
      surface = "replay";
      await ensureReplay(Number(target.dataset.replayJump));
    });
    return;
  }
  if (target.dataset.advanceMode && currentRunId) {
    perform(async () => {
      view = (await advanceMission(currentRunId, target.dataset.advanceMode)).view;
      resetDerived();
    });
    return;
  }
  if (target.dataset.command && currentRunId) {
    const command = JSON.parse(decodeURIComponent(target.dataset.command));
    perform(async () => {
      view = (await issueCommand(currentRunId, command)).view;
      resetDerived();
    });
  }
});

root.addEventListener("change", (event) => {
  const target = event.target;
  if (target.dataset.replayRevision !== undefined && currentRunId) {
    perform(async () => ensureReplay(Number(target.value)));
    return;
  }
  if (!currentRunId) return;
  if (target.dataset.objectiveActor) {
    perform(async () => {
      view = (await issueCommand(currentRunId, {
        action: "redirect-objective",
        actorId: target.dataset.objectiveActor,
        objectiveId: target.value,
      })).view;
      resetDerived();
    });
  }
});

window.addEventListener("popstate", () => perform(bootFromUrl));
boot();
