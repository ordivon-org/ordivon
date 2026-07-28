export const TEAM_ACTORS = [
  { actorId: "engineer-01", role: "Engineer", defaultProvider: "fixture" },
  { actorId: "medic-01", role: "Medic", defaultProvider: "fixture" },
  { actorId: "security-01", role: "Security", defaultProvider: "fixture" },
];

export const PROVIDERS = [
  ["fixture", "Fixture baseline"],
  ["codex", "Codex"],
  ["hermes", "Hermes / DeepSeek"],
  ["codex-hermes", "Codex → Hermes"],
  ["hermes-codex", "Hermes → Codex"],
];

export const OBJECTIVES_BY_ROLE = {
  engineer: [
    "cooling-operational", "cooling-powered", "breach-sealed",
    "life-support-operational", "life-support-powered",
    "communications-operational", "communications-powered", "distress-sent",
  ],
  medic: ["crew-stabilized"],
  security: ["breach-contained"],
};

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
