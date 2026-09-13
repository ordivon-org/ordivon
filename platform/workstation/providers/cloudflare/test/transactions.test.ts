import assert from "node:assert/strict";
import test from "node:test";

import { cleanupArtifacts, cleanupTaskKey } from "../src/cleanup.js";
import type {
  ArtifactReference,
  EdgeReceiptEnvelope,
  EdgeReceiptRecord
} from "../src/contracts.js";
import { EdgeError } from "../src/errors.js";
import {
  beginRequest,
  commitReceipt,
  loadReceiptRecord,
  requestStateKey
} from "../src/idempotency.js";
import { handleRequest } from "../src/index.js";
import { createReceipt } from "../src/receipts.js";
import { MemoryR2, makeEnv, signedRequest } from "./helpers.js";

const WORKER_VERSION: WorkerVersionMetadata = {
  id: "worker-version-test",
  tag: "test",
  timestamp: "2026-07-27T00:00:00.000Z"
};
const DIGEST = "c".repeat(64);
const NO_LOG = () => {};
const TEST_POLICY_VERSION = "test-policy-current";

function artifact(key: string): ArtifactReference {
  return {
    key,
    sha256: "d".repeat(64),
    bytes: 4,
    media_type: "application/octet-stream",
    etag: "artifact-etag"
  };
}

function errorCode(error: unknown): string | undefined {
  return error instanceof EdgeError ? error.code : undefined;
}

test("pending executions are queryable before final commit", async () => {
  const memory = new MemoryR2();
  const environment = makeEnv(memory);
  const requestId = "request_pending_001";
  const requestBody = JSON.stringify({
    url: "https://allowed.example.org/pending",
    maximum_bytes: 1024,
    timeout_ms: 2000
  });

  let resolveFetch: ((response: Response) => void) | undefined;
  const fetcherPromise = new Promise<Response>((resolve) => {
    resolveFetch = resolve;
  });
  const operation = handleRequest(
    signedRequest("https://edge.invalid/v1/fetch", {
      method: "POST",
      body: requestBody,
      requestId
    }),
    environment,
    {
      fetcher: async () => fetcherPromise,
      logWriter: NO_LOG
    }
  );

  await memory.waitForPut(requestStateKey(requestId));
  assert.ok(memory.objects.has(requestStateKey(requestId)));

  const pendingResponse = await handleRequest(
    signedRequest(`https://edge.invalid/v1/receipts/${requestId}`, {
      requestId: "request_pending_read_001"
    }),
    environment,
    { logWriter: NO_LOG }
  );
  assert.equal(pendingResponse.status, 202);
  const pending = (await pendingResponse.json()) as EdgeReceiptRecord;
  assert.equal(pending.status, "pending");
  if (pending.status !== "pending") assert.fail("expected pending receipt");
  assert.equal(pending.execution.lease_generation, 1);
  assert.equal(pending.execution.capability_version, "fetch.v2");

  resolveFetch?.(new Response("done", { status: 200 }));
  const completed = await operation;
  assert.equal(completed.status, 200);
  const envelope = (await completed.json()) as EdgeReceiptEnvelope;
  assert.equal(envelope.receipt.status, "succeeded");
  const serializedReceipt = JSON.stringify(envelope.receipt);
  assert.doesNotMatch(serializedReceipt, /lease_token|state_etag/);

  const final = await loadReceiptRecord(environment.ARTIFACTS, requestId);
  assert.equal(final?.status, "succeeded");
});

test("lease takeover increments generation and fences the stale executor", async () => {
  const memory = new MemoryR2();
  const bucket = memory.asBucket();
  const requestId = "request_fence_001";

  const first = await beginRequest({
    bucket,
    requestId,
    requestDigest: DIGEST,
    operation: "fetch",
    policyVersion: TEST_POLICY_VERSION,
    workerVersion: WORKER_VERSION,
    now: new Date("2026-07-27T00:00:00.000Z"),
    tokenFactory: () => "lease-one"
  });
  assert.equal(first.kind, "acquired");
  if (first.kind !== "acquired") assert.fail("expected first lease");

  const second = await beginRequest({
    bucket,
    requestId,
    requestDigest: DIGEST,
    operation: "fetch",
    policyVersion: TEST_POLICY_VERSION,
    workerVersion: WORKER_VERSION,
    now: new Date("2026-07-27T00:01:01.000Z"),
    tokenFactory: () => "lease-two"
  });
  assert.equal(second.kind, "acquired");
  if (second.kind !== "acquired") assert.fail("expected replacement lease");
  assert.equal(second.lease.lease_generation, 2);

  const staleKey = `fetch/v2/${requestId}/g1/body`;
  const currentKey = `fetch/v2/${requestId}/g2/body`;
  await bucket.put(staleKey, "old");
  await bucket.put(currentKey, "new");

  const staleReceipt = createReceipt({
    operation: "fetch",
    status: "succeeded",
    requestDigest: DIGEST,
    receiptId: requestId,
    startedAt: new Date(first.lease.acquired_at),
    completedAt: new Date("2026-07-27T00:01:02.000Z"),
    execution: first.lease,
    artifact: artifact(staleKey),
    artifacts: [artifact(staleKey)],
    fetch: {
      requested_url: "https://allowed.example.org/fenced",
      final_url: "https://allowed.example.org/fenced",
      http_status: 200,
      redirect_count: 0
    }
  });
  await assert.rejects(
    commitReceipt({
      bucket,
      lease: first.lease,
      receipt: staleReceipt,
      artifactKeys: [staleKey]
    }),
    (error: unknown) => errorCode(error) === "execution_lease_lost"
  );
  assert.equal(await bucket.get(staleKey), null);
  assert.notEqual(await bucket.get(currentKey), null);

  const currentReceipt = createReceipt({
    operation: "fetch",
    status: "succeeded",
    requestDigest: DIGEST,
    receiptId: requestId,
    startedAt: new Date(second.lease.acquired_at),
    completedAt: new Date("2026-07-27T00:01:03.000Z"),
    execution: second.lease,
    artifact: artifact(currentKey),
    artifacts: [artifact(currentKey)],
    fetch: {
      requested_url: "https://allowed.example.org/fenced",
      final_url: "https://allowed.example.org/fenced",
      http_status: 200,
      redirect_count: 0
    }
  });
  await commitReceipt({
    bucket,
    lease: second.lease,
    receipt: currentReceipt,
    artifactKeys: [currentKey]
  });
  const stored = await loadReceiptRecord(bucket, requestId);
  assert.equal(stored?.status, "succeeded");
  assert.equal(stored?.execution.lease_generation, 2);
});

test("commit failure removes newly written artifacts and preserves pending state", async () => {
  const memory = new MemoryR2();
  const environment = makeEnv(memory);
  const requestId = "request_commit_loss_001";
  const stateKey = requestStateKey(requestId);
  memory.faultPut(stateKey, 2, "return_null");

  const response = await handleRequest(
    signedRequest("https://edge.invalid/v1/fetch", {
      method: "POST",
      body: JSON.stringify({ url: "https://allowed.example.org/result" }),
      requestId
    }),
    environment,
    {
      fetcher: async () => new Response("result"),
      logWriter: NO_LOG
    }
  );
  assert.equal(response.status, 409);
  assert.equal(
    ((await response.json()) as { error: string }).error,
    "execution_lease_lost"
  );
  const artifactKey = `fetch/v2/${requestId}/g1/body`;
  assert.equal(await environment.ARTIFACTS.get(artifactKey), null);
  assert.ok(memory.deletedKeys.includes(artifactKey));
  const state = await loadReceiptRecord(environment.ARTIFACTS, requestId);
  assert.equal(state?.status, "pending");
});

test("ambiguous commit response is recovered by rereading committed state", async () => {
  const memory = new MemoryR2();
  const environment = makeEnv(memory);
  const requestId = "request_commit_ambiguous_001";
  memory.faultPut(requestStateKey(requestId), 2, "throw_after");

  const response = await handleRequest(
    signedRequest("https://edge.invalid/v1/fetch", {
      method: "POST",
      body: JSON.stringify({ url: "https://allowed.example.org/result" }),
      requestId
    }),
    environment,
    {
      fetcher: async () => new Response("result"),
      logWriter: NO_LOG
    }
  );
  assert.equal(response.status, 200);
  const envelope = (await response.json()) as EdgeReceiptEnvelope;
  assert.equal(envelope.receipt.status, "succeeded");
  assert.notEqual(
    await environment.ARTIFACTS.get(`fetch/v2/${requestId}/g1/body`),
    null
  );
});

test("expired requests cannot cross a policy version boundary", async () => {
  const memory = new MemoryR2();
  const bucket = memory.asBucket();
  const requestId = "request_old_policy_001";
  await bucket.put(
    requestStateKey(requestId),
    JSON.stringify({
      schema_version: 2,
      state: "pending",
      request_id: requestId,
      request_digest: DIGEST,
      operation: "fetch",
      execution: {
        policy_version: "2026-07-01.old",
        capability_version: "fetch.v1",
        worker_version_id: "old-worker",
        worker_version_tag: "old",
        worker_version_timestamp: "2026-07-01T00:00:00.000Z",
        lease_generation: 1
      },
      lease_token: "old-token",
      acquired_at: "2026-07-27T00:00:00.000Z",
      lease_expires_at: "2026-07-27T00:01:00.000Z"
    })
  );
  await assert.rejects(
    beginRequest({
      bucket,
      requestId,
      requestDigest: DIGEST,
      operation: "fetch",
      policyVersion: TEST_POLICY_VERSION,
    workerVersion: WORKER_VERSION,
      now: new Date("2026-07-27T00:02:00.000Z")
    }),
    (error: unknown) => errorCode(error) === "request_policy_changed"
  );
});

test("rate limited execution is receipted and replay bypasses the limiter", async () => {
  const memory = new MemoryR2();
  const environment = makeEnv(memory);
  const requestId = "request_budget_001";
  const body = JSON.stringify({ url: "https://allowed.example.org/budget" });
  let limitChecks = 0;
  let fetchCount = 0;
  const dependencies = {
    rateLimit: async () => {
      limitChecks += 1;
      return false;
    },
    fetcher: async () => {
      fetchCount += 1;
      return new Response("unexpected");
    },
    logWriter: NO_LOG
  };

  const first = await handleRequest(
    signedRequest("https://edge.invalid/v1/fetch", {
      method: "POST",
      body,
      requestId
    }),
    environment,
    dependencies
  );
  assert.equal(first.status, 429);
  assert.equal(first.headers.get("retry-after"), "60");
  const firstEnvelope = (await first.json()) as EdgeReceiptEnvelope;
  assert.equal(firstEnvelope.receipt.status, "failed");
  assert.equal(firstEnvelope.receipt.error_code, "fetch_rate_limited");
  assert.equal(limitChecks, 1);
  assert.equal(fetchCount, 0);

  const replay = await handleRequest(
    signedRequest("https://edge.invalid/v1/fetch", {
      method: "POST",
      body,
      requestId,
      timestamp: Math.floor(Date.now() / 1000) + 1
    }),
    environment,
    dependencies
  );
  assert.equal(replay.status, 200);
  const replayEnvelope = (await replay.json()) as EdgeReceiptEnvelope;
  assert.equal(replayEnvelope.replayed, true);
  assert.equal(replayEnvelope.receipt.error_code, "fetch_rate_limited");
  assert.equal(limitChecks, 1);
  assert.equal(fetchCount, 0);
});


test("failed Artifact deletion creates a bounded cleanup tombstone", async () => {
  const memory = new MemoryR2();
  const bucket = memory.asBucket();
  const requestId = "request_cleanup_001";
  const begin = await beginRequest({
    bucket,
    requestId,
    requestDigest: DIGEST,
    operation: "fetch",
    policyVersion: TEST_POLICY_VERSION,
    workerVersion: WORKER_VERSION,
    now: new Date("2026-07-27T00:00:00.000Z"),
    tokenFactory: () => "cleanup-lease"
  });
  assert.equal(begin.kind, "acquired");
  if (begin.kind !== "acquired") assert.fail("expected cleanup lease");
  const artifactKey = `fetch/v2/${requestId}/g1/body`;
  await bucket.put(artifactKey, "orphan");
  memory.failNextDelete();

  await cleanupArtifacts(
    bucket,
    begin.lease,
    [artifactKey],
    "test_cleanup_failure",
    new Date("2026-07-27T00:00:01.000Z")
  );

  assert.notEqual(await bucket.get(artifactKey), null);
  const tombstone = await bucket.get(cleanupTaskKey(begin.lease));
  assert.notEqual(tombstone, null);
  const task = JSON.parse(await tombstone!.text()) as {
    artifact_keys: string[];
    reason: string;
    lease_generation: number;
  };
  assert.deepEqual(task.artifact_keys, [artifactKey]);
  assert.equal(task.reason, "test_cleanup_failure");
  assert.equal(task.lease_generation, 1);
  assert.doesNotMatch(JSON.stringify(task), /lease_token|state_etag/);
});

test("structured logs contain execution identity but not request content", async () => {
  const environment = makeEnv();
  const entries: Readonly<Record<string, unknown>>[] = [];
  const secretUrl = "https://allowed.example.org/private-path?token=hidden";
  const response = await handleRequest(
    signedRequest("https://edge.invalid/v1/fetch", {
      method: "POST",
      body: JSON.stringify({ url: secretUrl }),
      requestId: "request_logs_001"
    }),
    environment,
    {
      fetcher: async () => new Response("result"),
      logWriter: (entry) => entries.push(entry)
    }
  );
  assert.equal(response.status, 200);
  assert.deepEqual(
    entries.map((entry) => entry.event),
    ["operation_acquired", "operation_completed"]
  );
  const serialized = JSON.stringify(entries);
  assert.doesNotMatch(serialized, /private-path|token=hidden|EDGE_HMAC/);
  assert.match(serialized, /p1\.6\.[a-f0-9]{16}/);
  assert.match(serialized, /test-worker-version/);
  assert.match(serialized, /lease_generation/);
});
