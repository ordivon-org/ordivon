import { stationZeroV3Api } from "/v3/api.js";
import { renderStationZeroV3App } from "/v3/render.js";

const root = document.querySelector("#app");
const model = {
  catalog: null,
  runs: [],
  view: null,
  runId: new URL(location.href).searchParams.get("runId"),
  busy: null,
  error: null,
  expressionTurnSequence: null,
};

function render() {
  const expressionTurnSequence = model.expressionTurnSequence;
  root.innerHTML = renderStationZeroV3App(model);
  bind();
  if (expressionTurnSequence !== null) {
    model.expressionTurnSequence = null;
    document.querySelector('[data-testid="aftermath"]')?.scrollIntoView({ behavior: "auto", block: "start" });
  }
}

async function perform(label, operation) {
  model.busy = label;
  model.error = null;
  render();
  try {
    await operation();
  } catch (error) {
    console.error(error);
    model.error = error.message ?? String(error);
  } finally {
    model.busy = null;
    render();
  }
}

function updateUrl(runId) {
  const url = new URL(location.href);
  if (runId) url.searchParams.set("runId", runId);
  else url.searchParams.delete("runId");
  history.replaceState({}, "", url);
}

function collectOrder() {
  const form = document.querySelector("#order-form");
  const data = new FormData(form);
  return {
    primaryObjectiveId: data.get("primaryObjectiveId"),
    posture: data.get("posture"),
    formation: data.get("formation"),
    commanderDirectiveId: data.get("commanderDirectiveId"),
    lethalForce: data.get("lethalForce"),
    lootPolicy: data.get("lootPolicy"),
    retreatHealthThreshold: Number(data.get("retreatHealthThreshold")),
    protectedActorId: data.get("protectedActorId") || null,
  };
}

function bind() {
  document.querySelector("#new-run-form")?.addEventListener("submit", (event) => {
    event.preventDefault();
    const runId = document.querySelector("#new-run-id").value.trim();
    if (!runId) return;
    perform("Opening Station Zero…", async () => {
      model.view = await stationZeroV3Api.createRun(runId);
      model.runId = runId;
      updateUrl(runId);
      model.runs = (await stationZeroV3Api.runs()).runs;
    });
  });
  document.querySelectorAll('[data-action="resume-run"]').forEach((button) => button.addEventListener("click", () => {
    const runId = button.dataset.runId;
    perform("Recovering retained evidence…", async () => {
      model.view = await stationZeroV3Api.resume(runId);
      model.runId = runId;
      updateUrl(runId);
    });
  }));
  document.querySelector('[name="retreatHealthThreshold"]')?.addEventListener("input", (event) => {
    const output = document.querySelector("#retreat-output");
    if (output) output.textContent = `${Math.round(Number(event.target.value) * 100)}%`;
  });
  document.querySelector('[data-action="save-order"]')?.addEventListener("click", () => perform("Saving Commander Order…", async () => {
    const result = await stationZeroV3Api.saveOrder(model.runId, collectOrder());
    model.view = result.view;
  }));
  document.querySelector('[data-action="generate-preview"]')?.addEventListener("click", () => perform("Agents are deliberating…", async () => {
    const saved = await stationZeroV3Api.saveOrder(model.runId, collectOrder());
    model.view = saved.view;
    const generated = await stationZeroV3Api.preview(model.runId);
    model.view = generated.view;
  }));
  document.querySelector('[data-action="commit-turn"]')?.addEventListener("click", (event) => perform("Resolving all factions…", async () => {
    const committed = await stationZeroV3Api.commit(model.runId, event.currentTarget.dataset.previewId);
    model.view = committed.view;
    model.expressionTurnSequence = committed.view.aftermath?.turnSequence ?? null;
    model.runs = (await stationZeroV3Api.runs()).runs;
  }));
  document.querySelector('[data-action="new-operation"]')?.addEventListener("click", () => {
    model.view = null;
    model.runId = null;
    model.expressionTurnSequence = null;
    updateUrl(null);
    render();
  });
}

async function boot() {
  await perform("Loading Mission Control…", async () => {
    const [catalog, runs] = await Promise.all([stationZeroV3Api.catalog(), stationZeroV3Api.runs()]);
    model.catalog = catalog;
    model.runs = runs.runs;
    if (model.runId) model.view = await stationZeroV3Api.resume(model.runId);
  });
}

boot();
