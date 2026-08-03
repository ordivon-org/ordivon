async function request(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: {
      "content-type": "application/json",
      ...(options.headers ?? {}),
    },
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(body.message ?? body.error ?? `Request failed: ${response.status}`);
    error.code = body.error ?? "request_failed";
    error.status = response.status;
    throw error;
  }
  return body;
}

function runPath(path, runId) {
  return `${path}?runId=${encodeURIComponent(runId)}`;
}

export const stationZeroV3Api = {
  catalog: () => request("/api/station-zero-v3/catalog"),
  runs: () => request("/api/station-zero-v3/runs"),
  createRun: (runId) => request("/api/station-zero-v3/runs", {
    method: "POST",
    body: JSON.stringify({ runId }),
  }),
  resume: (runId) => request(runPath("/api/station-zero-v3/resume", runId), {
    method: "POST",
    body: "{}",
  }),
  state: (runId) => request(runPath("/api/station-zero-v3/state", runId)),
  saveOrder: (runId, patch) => request(runPath("/api/station-zero-v3/order", runId), {
    method: "POST",
    body: JSON.stringify(patch),
  }),
  preview: (runId) => request(runPath("/api/station-zero-v3/preview", runId), {
    method: "POST",
    body: "{}",
  }),
  commit: (runId, previewId) => request(runPath("/api/station-zero-v3/commit", runId), {
    method: "POST",
    body: JSON.stringify({ previewId }),
  }),
};
