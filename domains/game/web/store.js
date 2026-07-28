export function runIdFromUrl(href) {
  return new URL(href).searchParams.get("runId");
}

export function urlForRun(href, runId) {
  const url = new URL(href);
  if (runId) url.searchParams.set("runId", runId);
  else url.searchParams.delete("runId");
  return `${url.pathname}${url.search}${url.hash}`;
}

export function createRunId(now = Date.now(), random = crypto.randomUUID()) {
  return `run:web:${now}:${random}`;
}

export function compatibleRuns(runs) {
  return runs
    .filter((run) => run.scenarioVersion >= 2 && run.rulesetVersion >= 3)
    .sort((left, right) => right.createdAt.localeCompare(left.createdAt));
}
