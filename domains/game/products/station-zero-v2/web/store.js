const SURFACES = new Set(["mission", "replay", "diagnosis", "compare"]);

export function runIdFromUrl(href) {
  return new URL(href).searchParams.get("runId");
}

export function surfaceFromUrl(href) {
  const value = new URL(href).searchParams.get("view") ?? "mission";
  return SURFACES.has(value) ? value : "mission";
}

export function revisionFromUrl(href) {
  const raw = new URL(href).searchParams.get("revision");
  if (raw === null) return null;
  const value = Number(raw);
  return Number.isSafeInteger(value) && value >= 0 ? value : null;
}

export function compareRunIdFromUrl(href) {
  return new URL(href).searchParams.get("compareRunId");
}

export function urlForState(href, { runId, surface = "mission", revision = null, compareRunId = null }) {
  const url = new URL(href);
  if (runId) url.searchParams.set("runId", runId);
  else url.searchParams.delete("runId");
  if (surface && surface !== "mission") url.searchParams.set("view", surface);
  else url.searchParams.delete("view");
  if (revision !== null && surface === "replay") url.searchParams.set("revision", String(revision));
  else url.searchParams.delete("revision");
  if (compareRunId) url.searchParams.set("compareRunId", compareRunId);
  else url.searchParams.delete("compareRunId");
  return `${url.pathname}${url.search}${url.hash}`;
}

export function urlForRun(href, runId) {
  return urlForState(href, { runId, surface: "mission" });
}

export function createRunId(now = Date.now(), random = crypto.randomUUID()) {
  return `run:web:${now}:${random}`;
}

export function compatibleRuns(runs) {
  return runs
    .filter((run) => run.scenarioVersion >= 2 && run.rulesetVersion >= 3)
    .sort((left, right) => right.createdAt.localeCompare(left.createdAt));
}
