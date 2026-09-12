import { stationZeroV3Api } from "/v3/api.js";
import { renderStationZeroV3App } from "/v3/render.js";

const root = document.querySelector("#app");
const statusAnnouncer = document.querySelector("#status-announcer");
const mobileReadingOrder = matchMedia("(max-width: 600px)");
const AUDIO_STORAGE_KEY = "station-zero-v3-audio-muted";
const AUDIO_CUES = {
  "plan-ready": "/v3/assets/audio/plan-ready.ogg",
  commit: "/v3/assets/audio/commit.ogg",
  aftermath: "/v3/assets/audio/aftermath.ogg",
};

function storedAudioMuted() {
  try { return localStorage.getItem(AUDIO_STORAGE_KEY) === "1"; } catch { return false; }
}

const model = {
  catalog: null,
  runs: [],
  view: null,
  runId: new URL(location.href).searchParams.get("runId"),
  busy: null,
  error: null,
  expressionTurnSequence: null,
  audioMuted: storedAudioMuted(),
};

const ORDER_FIELDS = [
  "primaryObjectiveId",
  "posture",
  "formation",
  "commanderDirectiveId",
  "lethalForce",
  "retreatHealthThreshold",
  "protectedActorId",
];

const DESCRIPTION_CATALOG = {
  primaryObjectiveId: ["objectives", "objectiveId"],
  posture: ["postures", "posture"],
  formation: ["formations", "formation"],
  commanderDirectiveId: ["commanderDirectives", "directiveId"],
  lethalForce: ["lethalForce", "value"],
};

const CONTROL_LABELS = {
  primaryObjectiveId: "Primary objective",
  posture: "Posture",
  formation: "Formation",
  commanderDirectiveId: "Remote capability",
  lethalForce: "Lethal force",
  retreatHealthThreshold: "Retreat threshold",
  protectedActorId: "Protected specialist",
};

function announceStatus(message) {
  if (!statusAnnouncer) return;
  statusAnnouncer.textContent = "";
  requestAnimationFrame(() => { statusAnnouncer.textContent = message; });
}

function applyResponsiveReadingOrder() {
  const mission = root.querySelector(".mission");
  const situation = mission?.querySelector(":scope > .situation-grid");
  const planning = mission?.querySelector(":scope > .planning-grid");
  if (!mission || !situation || !planning) return;
  if (mobileReadingOrder.matches) mission.insertBefore(planning, situation);
  else mission.insertBefore(situation, planning);
}

function render() {
  const expressionTurnSequence = model.expressionTurnSequence;
  root.innerHTML = renderStationZeroV3App(model);
  applyResponsiveReadingOrder();
  bind();
  if (expressionTurnSequence !== null) {
    model.expressionTurnSequence = null;
    document.querySelector('[data-testid="aftermath"]')?.scrollIntoView({ behavior: "auto", block: "start" });
  }
}

let busyTimer = null;

function updateBusyElapsed() {
  const target = document.querySelector("[data-busy-elapsed]");
  if (!target || !model.busy?.startedAt) return;
  target.textContent = `${((performance.now() - model.busy.startedAt) / 1000).toFixed(1)}s`;
}

function startBusyClock() {
  clearInterval(busyTimer);
  updateBusyElapsed();
  busyTimer = setInterval(updateBusyElapsed, 100);
}

function stopBusyClock() {
  clearInterval(busyTimer);
  busyTimer = null;
}

function playCue(name) {
  if (model.audioMuted) return;
  const src = AUDIO_CUES[name];
  if (!src) return;
  try {
    const audio = new Audio(src);
    audio.volume = 0.34;
    audio.play().catch(() => {});
  } catch {}
}

function setAudioMuted(muted) {
  model.audioMuted = Boolean(muted);
  try { localStorage.setItem(AUDIO_STORAGE_KEY, model.audioMuted ? "1" : "0"); } catch {}
}

async function perform(label, operation, kind = "generic") {
  model.busy = { label, kind, startedAt: performance.now() };
  model.error = null;
  if (kind === "deliberation" && model.view) announceStatus(`Deliberation started. World paused at Turn ${model.view.run.turn}.`);
  if (kind === "resolution" && model.view) announceStatus(`Turn ${model.view.run.turn + 1} committed. Resolving all factions.`);
  render();
  startBusyClock();
  try {
    await operation();
  } catch (error) {
    console.error(error);
    model.error = error.message ?? String(error);
  } finally {
    stopBusyClock();
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
    lootPolicy: model.view?.experience?.order?.lootPolicy ?? "mission-only",
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
  if (field === "commanderDirectiveId" && value === "reroute-cooling") {
    const cooling = model.view?.known?.systems?.find((system) => system.systemId === "cooling");
    if (!cooling) return "Power Cooling during committed resolution. Effective cooling requires at least 60% integrity; current condition is not yet observed.";
    const integrity = Math.round(cooling.observedIntegrity * 100);
    const age = model.view.run.turn - cooling.observedAtTurn;
    const freshness = age === 0 ? "observed this Turn" : `last observed ${age} Turn${age === 1 ? "" : "s"} ago`;
    return cooling.observedIntegrity < 0.6
      ? `Cooling was ${integrity}% integrity and ${cooling.observedPowered ? "powered" : "unpowered"} when ${freshness}. Power alone will not reduce heat until a local repair raises integrity to 60%.`
      : `Cooling was ${integrity}% integrity and ${cooling.observedPowered ? "powered" : "unpowered"} when ${freshness}. Power can make it operational if that observed condition still holds.`;
  }
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
  const protectedActor = model.view?.ownActors?.find((actor) => actor.actorId === order.protectedActorId);
  const protectedLabel = protectedActor ? `protect ${protectedActor.actorName ?? protectedActor.name}` : "no protection priority";
  target.textContent = `${lethal} · retreat ≤ ${Math.round(order.retreatHealthThreshold * 100)}% · ${protectedLabel}`;
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
  document.querySelector('[data-action="toggle-audio"]')?.addEventListener("click", () => {
    setAudioMuted(!model.audioMuted);
    render();
  });
  document.querySelector("#new-run-form")?.addEventListener("submit", (event) => {
    event.preventDefault();
    const runId = document.querySelector("#new-run-id").value.trim();
    const scenarioCaseId = document.querySelector("#new-run-case")?.value || model.catalog?.defaultScenarioCaseId || "fixed-genesis";
    if (!runId) return;
    perform("Opening Station Zero…", async () => {
      model.view = await stationZeroV3Api.createRun(runId, scenarioCaseId);
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
    perform("Team deliberation", async () => {
      const saved = await stationZeroV3Api.saveOrder(model.runId, order);
      model.view = saved.view;
      const generated = await stationZeroV3Api.preview(model.runId);
      model.view = generated.view;
      announceStatus(`Plan ready for Turn ${model.view.run.turn + 1}. Review three Rescue intents before Commit.`);
      playCue("plan-ready");
    }, "deliberation");
  });
  document.querySelector('[data-action="commit-turn"]')?.addEventListener("click", (event) => {
    playCue("commit");
    perform("Resolving all factions", async () => {
      const committed = await stationZeroV3Api.commit(model.runId, event.currentTarget.dataset.previewId);
      model.view = committed.view;
      model.expressionTurnSequence = committed.view.aftermath?.turnSequence ?? null;
      model.runs = (await stationZeroV3Api.runs()).runs;
      announceStatus(`Turn ${model.view.run.turn} resolved. Review Aftermath and mission-front changes.`);
      playCue("aftermath");
    }, "resolution");
  });
  document.querySelector('[data-action="new-operation"]')?.addEventListener("click", () => {
    model.view = null;
    model.runId = null;
    model.expressionTurnSequence = null;
    updateUrl(null);
    render();
  });
}

mobileReadingOrder.addEventListener("change", applyResponsiveReadingOrder);

async function boot() {
  await perform("Loading Mission Control…", async () => {
    const [catalog, runs] = await Promise.all([stationZeroV3Api.catalog(), stationZeroV3Api.runs()]);
    model.catalog = catalog;
    model.runs = runs.runs;
    if (model.runId) model.view = await stationZeroV3Api.resume(model.runId);
  });
}

boot();
