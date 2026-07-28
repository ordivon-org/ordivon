import { advanceMission, initializeMission, issueCommand, listRuns, loadMission } from "./api.js";
import { renderDeployment, renderFatal, renderMission } from "./render-shell.js";
import { compatibleRuns, createRunId, runIdFromUrl, urlForRun } from "./store.js";

const root = document.querySelector("#app");
let runs = [];
let view = null;
let busy = false;
let error = null;
let currentRunId = runIdFromUrl(window.location.href);

function draw() {
  if (!root) return;
  if (view?.initialized) root.innerHTML = renderMission(view, { busy, error });
  else root.innerHTML = renderDeployment(runs, error, currentRunId);
}

function setRunId(runId) {
  currentRunId = runId;
  history.replaceState({}, "", urlForRun(window.location.href, runId));
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
  } finally {
    busy = false;
    draw();
  }
}

async function refreshRuns() {
  const result = await listRuns();
  runs = compatibleRuns(result.runs ?? []);
}

async function boot() {
  try {
    await refreshRuns();
    if (currentRunId) view = await loadMission(currentRunId);
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
  const runId = String(form.get("runId") || currentRunId || createRunId());
  const providers = Object.fromEntries(["engineer-01", "medic-01", "security-01"].map((actorId) => [actorId, String(form.get(actorId) || "fixture")]));
  perform(async () => {
    view = await initializeMission({ runId, authorityPolicyMode: String(form.get("authorityPolicyMode") || "autonomous"), providers });
    setRunId(runId);
    await refreshRuns();
  });
});

root.addEventListener("click", (event) => {
  const target = event.target.closest("button, a");
  if (!target) return;
  if (target.dataset.resumeRun) {
    perform(async () => {
      setRunId(target.dataset.resumeRun);
      view = await loadMission(currentRunId);
    });
    return;
  }
  if (target.hasAttribute("data-new-mission")) {
    view = null;
    error = null;
    setRunId(null);
    draw();
    return;
  }
  if (target.dataset.missionAction && currentRunId) {
    const until = target.dataset.missionAction === "prepare" ? "proposal-review" : "tick-verified";
    perform(async () => { view = (await advanceMission(currentRunId, until)).view; });
    return;
  }
  if (target.dataset.command && currentRunId) {
    const command = JSON.parse(decodeURIComponent(target.dataset.command));
    perform(async () => { view = (await issueCommand(currentRunId, command)).view; });
  }
});

root.addEventListener("change", (event) => {
  const target = event.target;
  if (!currentRunId) return;
  if (target.dataset.providerActor) {
    perform(async () => {
      view = (await issueCommand(currentRunId, { action: "set-provider", actorId: target.dataset.providerActor, provider: target.value })).view;
    });
  } else if (target.dataset.objectiveActor) {
    perform(async () => {
      view = (await issueCommand(currentRunId, { action: "redirect-objective", actorId: target.dataset.objectiveActor, objectiveId: target.value })).view;
    });
  }
});

boot();
