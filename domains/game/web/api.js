async function request(path, options) {
  const response = await fetch(path, options);
  const body = await response.json();
  if (!response.ok) {
    const error = new Error(body.message ?? body.error ?? `HTTP ${response.status}`);
    error.status = response.status;
    error.body = body;
    throw error;
  }
  return body;
}

function post(path, body) {
  return request(path, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
}

function query(runId) {
  return `?runId=${encodeURIComponent(runId)}`;
}

export function loadCatalog() {
  return request("/api/mission-control/catalog");
}

export function loadProviderPreflight() {
  return request("/api/providers/preflight");
}

export function listRuns() {
  return request("/api/runs");
}

export function loadMission(runId) {
  return request(`/api/mission-control/state${query(runId)}`);
}

export function initializeMission(input) {
  return post("/api/mission-control/initialize", input);
}

export function advanceMission(runId, until) {
  return post(`/api/mission-control/advance${query(runId)}`, { until });
}

export function issueCommand(runId, command) {
  return post(`/api/mission-control/command${query(runId)}`, command);
}

export function loadReplayReport(runId) {
  return request(`/api/replay/report${query(runId)}`);
}

export function loadReplayFrame(runId, revision) {
  return request(`/api/replay/frame${query(runId)}&revision=${encodeURIComponent(revision)}`);
}

export function loadDeploymentManifest(runId) {
  return request(`/api/deployments/manifest${query(runId)}`);
}

export function compareRuns(leftRunId, rightRunId) {
  return request(`/api/compare?leftRunId=${encodeURIComponent(leftRunId)}&rightRunId=${encodeURIComponent(rightRunId)}`);
}
