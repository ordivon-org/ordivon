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

const ORDER_FIELDS = [
  "primaryObjectiveId",
  "posture",
  "formation",
  "commanderDirectiveId",
  "lethalForce",
  "lootPolicy",
  "retreatHealthThreshold",
  "protectedActorId",
];

const DESCRIPTION_CATALOG = {
  primaryObjectiveId: ["objectives", "objectiveId"],
  posture: ["postures", "posture"],
  formation: ["formations", "formation"],
  commanderDirectiveId: ["commanderDirectives", "directiveId"],
  lethalForce: ["lethalForce", "value"],
  lootPolicy: ["lootPolicies", "value"],
};

const CONTROL_LABELS = {
  primaryObjectiveId: "Primary objective",
  posture: "Posture",
  formation: "Formation",
  commanderDirectiveId: "Remote capability",
  lethalForce: "Lethal force",
  lootPolicy: "Loot policy",
  retreatHealthThreshold: "Retreat threshold",
  protectedActorId: "Protected specialist",
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
  if (!form) return null;
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

function retainedOrderMatches(order) {
  const retained = model.view?.experience?.order;
  if (!order || !retained) return true;
  return ORDER_FIELDS.every((field) => retained[field] === order[field]);
}

function catalogEntry(field, value) {
  const mapping = DESCRIPTION_CATALOG[field];
  if (!mapping || !model.catalog) return null;
  const [collection, key] = mapping;
  return model.catalog[collection]?.find((entry) => entry[key] === value) ?? null;
}

function guidanceFor(field, value) {
  const entry = catalogEntry(field, value);
  if (entry?.description) return entry.description;
  if (field === "retreatHealthThreshold") {
    return "When extraction is locally available, specialists at or below this health threshold strongly prefer leaving the station.";
  }
  if (field === "protectedActorId") {
    return value
      ? "Bias legal guard coverage toward this specialist's last known Zone."
      : "No specialist receives extra guard-location preference.";
  }
  return "This Commander choice is retained in the Order used to generate the team plan.";
}

function refreshGuidance(field, value) {
  const label = document.querySelector("[data-order-guidance-label]");
  const text = document.querySelector("[data-order-guidance-text]");
  if (label) label.textContent = CONTROL_LABELS[field] ?? field;
  if (text) text.textContent = guidanceFor(field, value);
}

function refreshContingencySummary(order) {
  const target = document.querySelector("[data-contingency-summary]");
  if (!target || !order) return;
  const lethal = catalogEntry("lethalForce", order.lethalForce)?.label ?? order.lethalForce;
  const loot = catalogEntry("lootPolicy", order.lootPolicy)?.label ?? order.lootPolicy;
  const protectedActor = model.view?.ownActors?.find((actor) => actor.actorId === order.protectedActorId);
  const protectedLabel = protectedActor ? `protect ${protectedActor.actorName ?? protectedActor.name}` : "no protection priority";
  target.textContent = `${lethal} · retreat ≤ ${Math.round(order.retreatHealthThreshold * 100)}% · ${loot} · ${protectedLabel}`;
}

function syncOrderDirtyState() {
  const form = document.querySelector("#order-form");
  if (!form) return;
  const order = collectOrder();
  const dirty = !retainedOrderMatches(order);
  form.dataset.dirty = dirty ? "true" : "false";
  const preview = document.querySelector('[data-testid="plan-preview"]');
  const commit = document.querySelector('[data-testid="commit-turn"]');
  const notice = document.querySelector("[data-order-dirty-notice]");
  const generate = document.querySelector('[data-testid="generate-preview"]');
  const stalePreview = Boolean(preview && dirty);
  preview?.classList.toggle("is-stale", stalePreview);
  if (commit) commit.disabled = stalePreview || !model.view?.experience?.canCommitPreview;
  if (notice) notice.hidden = !stalePreview;
  if (generate && model.view?.experience?.preview) generate.textContent = stalePreview ? "Regenerate team plan" : "Generate team plan";
  refreshContingencySummary(order);
}

function onOrderInput(event) {
  const field = event.target?.name;
  if (!field) return;
  if (field === "retreatHealthThreshold") {
    const output = document.querySelector("#retreat-output");
    if (output) output.textContent = `${Math.round(Number(event.target.value) * 100)}%`;
  }
  refreshGuidance(field, event.target.value);
  syncOrderDirtyState();
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
  document.querySelectorAll("#order-form select").forEach((control) => {
    control.addEventListener("change", onOrderInput);
    control.addEventListener("focus", () => refreshGuidance(control.name, control.value));
  });
  document.querySelectorAll("#order-form input").forEach((control) => {
    control.addEventListener("input", onOrderInput);
    control.addEventListener("change", onOrderInput);
    control.addEventListener("focus", () => refreshGuidance(control.name, control.value));
  });
  syncOrderDirtyState();
  document.querySelector('[data-action="save-order"]')?.addEventListener("click", () => {
    const order = collectOrder();
    if (!order) return;
    perform("Saving Commander Order…", async () => {
      const result = await stationZeroV3Api.saveOrder(model.runId, order);
      model.view = result.view;
    });
  });
  document.querySelector('[data-action="generate-preview"]')?.addEventListener("click", () => {
    const order = collectOrder();
    if (!order) return;
    perform("Agents are deliberating…", async () => {
      const saved = await stationZeroV3Api.saveOrder(model.runId, order);
      model.view = saved.view;
      const generated = await stationZeroV3Api.preview(model.runId);
      model.view = generated.view;
    });
  });
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
