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
  requestStateKey,
  receiptMirrorKey
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
  assert.equal(memory.deletedKeys.length, 1);
  const artifactKey = memory.deletedKeys[0]!;
  assert.ok(artifactKey.startsWith(`fetch/v2/${requestId}/g1/`));
  assert.match(artifactKey, /\/body$/);
  assert.equal(await environment.ARTIFACTS.get(artifactKey), null);
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
  assert.ok(envelope.receipt.artifact);
  assert.notEqual(await environment.ARTIFACTS.get(envelope.receipt.artifact.key), null);
});

for (const operation of ["fetch", "browser.run"] as const) {
  for (const observation of ["read-failed", "pending-before-late-commit"] as const) {
    test(`${operation}: uncertain commit ${observation} preserves evidence for original receipt`, async () => {
      const memory = new MemoryR2();
      const base = makeEnv(memory);
      const bucket = base.ARTIFACTS;
      const requestId = "request_uncertain_" + operation.replace(".", "_") + "_" + observation.replaceAll("-", "_");
      const key = requestStateKey(requestId);
      let lostReply = false;
      let recoveryRead = false;
      let finishLateCommit: (() => Promise<unknown>) | undefined;
      const environment = {
        ...base,
        ARTIFACTS: {
          ...bucket,
          async put(objectKey: string, value: Parameters<R2Bucket["put"]>[1], options?: R2PutOptions) {
            if (objectKey === key && memory.putCount(key) === 1 && !lostReply) {
              lostReply = true;
              if (observation === "read-failed") {
                await bucket.put(objectKey, value, options);
              } else {
                finishLateCommit = () => bucket.put(objectKey, value, options);
              }
              throw new Error("injected lost commit response");
            }
            return bucket.put(objectKey, value, options);
          },
          async get(objectKey: string) {
            if (objectKey === key && lostReply && !recoveryRead) {
              recoveryRead = true;
              if (observation === "read-failed") throw new Error("injected recovery read failure");
            }
            return bucket.get(objectKey);
          }
        } as R2Bucket
      };
      const url = operation === "fetch" ? "/v1/fetch" : "/v1/browser/run";
      const body = JSON.stringify({ url: "https://allowed.example.org/result" });
      let providerCalls = 0;
      const dependencies = {
        fetcher: async () => { providerCalls += 1; return new Response("result"); },
        browserRunner: {
          async quickAction() {
            providerCalls += 1;
            return new Response(JSON.stringify({
              success: true,
              result: {
                content: "<html>result</html>",
                screenshot: Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]).toString("base64")
              },
              meta: { status: 200, title: "result" }
            }), { headers: { "content-type": "application/json", "x-browser-ms-used": "123" } });
          }
        },
        logWriter: NO_LOG
      };
      const invoke = () => handleRequest(
        signedRequest("https://edge.invalid" + url, { method: "POST", body, requestId }),
        environment,
        dependencies
      );
      const response = await invoke();
      assert.equal(response.status, 503);
      assert.ok(recoveryRead);
      if (finishLateCommit !== undefined) assert.notEqual(await finishLateCommit(), null);
      const record = await loadReceiptRecord(bucket, requestId);
      assert.equal(record?.status, "succeeded");
      if (record?.status !== "succeeded") assert.fail("expected committed success");
      assert.equal(record.artifacts?.length, operation === "fetch" ? 1 : 3);
      for (const evidence of record.artifacts ?? []) {
        assert.notEqual(await bucket.get(evidence.key), null, evidence.key);
      }
      assert.equal(memory.deletedKeys.length, 0);
      const replay = await invoke();
      assert.equal(replay.status, 200);
      const envelope = await replay.json() as EdgeReceiptEnvelope;
      assert.equal(envelope.replayed, true);
      assert.deepEqual(envelope.receipt, record);
      assert.equal(providerCalls, 1);
    });
  }
}

test("an ambiguous commit cleans only an observed superseded generation", async () => {
  const memory = new MemoryR2();
  const bucket = memory.asBucket();
  const requestId = "request_ambiguous_takeover_001";
  const options = {
    bucket, requestId, requestDigest: DIGEST, operation: "fetch" as const,
    policyVersion: TEST_POLICY_VERSION, workerVersion: WORKER_VERSION
  };
  const first = await beginRequest({ ...options, now: new Date("2026-07-27T00:00:00Z") });
  if (first.kind !== "acquired") assert.fail("expected first lease");
  const oldKey = `fetch/v2/${requestId}/g1/body`;
  const newKey = `fetch/v2/${requestId}/g2/body`;
  await bucket.put(oldKey, "old");
  const receipt = createReceipt({
    operation: "fetch", status: "succeeded", receiptId: requestId,
    requestDigest: DIGEST, execution: first.lease,
    startedAt: new Date(first.lease.acquired_at), completedAt: new Date("2026-07-27T00:00:01Z"),
    artifact: artifact(oldKey), artifacts: [artifact(oldKey)],
    fetch: { requested_url: "https://allowed.example.org/result",
      final_url: "https://allowed.example.org/result", http_status: 200, redirect_count: 0 }
  });
  const ambiguousBucket = {
    ...bucket,
    async put(key: string, value: Parameters<R2Bucket["put"]>[1], opts?: R2PutOptions) {
      if (key === requestStateKey(requestId)) {
        const second = await beginRequest({ ...options, now: new Date("2026-07-27T00:01:01Z") });
        if (second.kind !== "acquired") assert.fail("expected takeover");
        assert.equal(second.lease.lease_generation, 2);
        await bucket.put(newKey, "new");
        throw new Error("commit response unavailable after takeover");
      }
      return bucket.put(key, value, opts);
    }
  } as R2Bucket;
  await assert.rejects(
    commitReceipt({ bucket: ambiguousBucket, lease: first.lease, receipt, artifactKeys: [oldKey] }),
    (error: unknown) => errorCode(error) === "receipt_commit_unavailable"
  );
  assert.equal(await bucket.get(oldKey), null);
  assert.notEqual(await bucket.get(newKey), null);
  assert.deepEqual(memory.deletedKeys, [oldKey]);
  const current = await loadReceiptRecord(bucket, requestId);
  assert.equal(current?.status, "pending");
  assert.equal(current?.execution.lease_generation, 2);
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

for (const fault of ["return_null", "throw_after"] as const) {
  test(`Browser commit ${fault} preserves the same recovery contract as Fetch`, async () => {
    const memory = new MemoryR2();
    const environment = makeEnv(memory);
    const requestId = "request_browser_commit_" + fault;
    const stateKey = requestStateKey(requestId);
    memory.faultPut(stateKey, 2, fault);
    const body = JSON.stringify({ url: "https://allowed.example.org/page" });
    let browserCalls = 0;
    let limitCalls = 0;
    const dependencies = {
      browserRunner: {
        async quickAction() {
          browserCalls += 1;
          return new Response(JSON.stringify({
            success: true,
            result: {
              content: "<html>browser result</html>",
              screenshot: Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]).toString("base64")
            },
            meta: { status: 200, title: "Browser result" }
          }), {
            headers: { "content-type": "application/json", "x-browser-ms-used": "123" }
          });
        }
      },
      rateLimit: async () => { limitCalls += 1; return true; },
      logWriter: NO_LOG
    };
    const invoke = () => handleRequest(
      signedRequest("https://edge.invalid/v1/browser/run", { method: "POST", body, requestId }),
      environment,
      dependencies
    );
    const response = await invoke();
    assert.equal(browserCalls, 1);
    assert.equal(limitCalls, 1);
    assert.equal(memory.putCount(stateKey), 2);
    if (fault === "return_null") {
      assert.equal(response.status, 409);
      assert.equal((await response.json() as { error: string }).error, "execution_lease_lost");
      assert.equal((await loadReceiptRecord(environment.ARTIFACTS, requestId))?.status, "pending");
      assert.equal(memory.deletedKeys.length, 3);
      for (const key of memory.deletedKeys) {
        assert.equal(await environment.ARTIFACTS.get(key), null);
      }
    } else {
      assert.equal(response.status, 200);
      const envelope = await response.json() as EdgeReceiptEnvelope;
      assert.equal(envelope.receipt.status, "succeeded");
      assert.equal(envelope.receipt.operation, "browser.run");
      assert.equal(envelope.receipt.artifacts?.length, 3);
      assert.equal(memory.deletedKeys.length, 0);
      for (const artifact of envelope.receipt.artifacts ?? []) {
        assert.notEqual(await environment.ARTIFACTS.get(artifact.key), null);
      }
      const replay = await invoke();
      assert.equal(replay.status, 200);
      const replayed = await replay.json() as EdgeReceiptEnvelope;
      assert.equal(replayed.replayed, true);
      assert.deepEqual(replayed.receipt, envelope.receipt);
      assert.equal(browserCalls, 1);
      assert.equal(limitCalls, 1);
      assert.equal(memory.putCount(stateKey), 2);
    }
  });
}

for (const operation of ["fetch", "browser.run"] as const) {
  test(`${operation}: expired intent cannot overwrite retained Artifact bytes`, async () => {
    const memory = new MemoryR2();
    const environment = makeEnv(memory);
    const requestId = "retention_epoch_r6_001";
    const route = operation === "fetch" ? "/v1/fetch" : "/v1/browser/run";
    let run = 0;
    const dependencies = {
      fetcher: async () => new Response("run-" + (++run)),
      browserRunner: { async quickAction() {
        ++run;
        return new Response(JSON.stringify({
          success: true,
          result: {
            content: "<html>run-" + run + "</html>",
            screenshot: Buffer.from([137,80,78,71,13,10,26,10,run]).toString("base64")
          },
          meta: { status: 200, title: "run-" + run }
        }), { headers: { "content-type": "application/json" } });
      }},
      logWriter: NO_LOG
    };
    const invoke = async (suffix: string) => {
      const body = JSON.stringify({ url: "https://allowed.example.org/" + suffix });
      const response = await handleRequest(signedRequest("https://edge.invalid" + route, {
        method: "POST", body, requestId
      }), environment, dependencies);
      assert.equal(response.status, 200);
      return (await response.json() as EdgeReceiptEnvelope).receipt;
    };
    const first = await invoke("first");
    assert.equal(first.execution.lease_generation, 1);
    const originals = (first.artifacts ?? []).map(ref => ({
      key: ref.key, bytes: memory.objects.get(ref.key)!.bytes.slice()
    }));
    assert.equal(originals.length, operation === "fetch" ? 1 : 3);
    // Model only state and mirror expiry; old Artifact bytes remain.
    memory.objects.delete(requestStateKey(requestId));
    memory.objects.delete(receiptMirrorKey(requestId));
    const second = await invoke("second");
    assert.equal(second.execution.lease_generation, 1);
    assert.equal(run, 2);
    for (const original of originals) {
      assert.deepEqual(memory.objects.get(original.key)?.bytes, original.bytes);
      assert.ok(!second.artifacts?.some(ref => ref.key === original.key));
    }
  });

  test(`${operation}: an existing bundle key is never overwritten by a new write`, async () => {
    const memory = new MemoryR2();
    const base = makeEnv(memory);
    const bucket = base.ARTIFACTS;
    const requestId = "retention_collision_r6_001";
    let collision: string | undefined;
    const environment = {
      ...base,
      ARTIFACTS: {
        ...bucket,
        async put(key: string, value: Parameters<R2Bucket["put"]>[1], options?: R2PutOptions) {
          if (key.startsWith(operation === "fetch" ? "fetch/v2/" : "browser/v2/")
              && key.endsWith(operation === "fetch" ? "/body" : "/content.html")) {
            assert.equal(collision, undefined);
            collision = key;
            await bucket.put(key, "previously retained bytes");
          }
          return bucket.put(key, value, options);
        }
      } as R2Bucket
    };
    const route = operation === "fetch" ? "/v1/fetch" : "/v1/browser/run";
    const response = await handleRequest(signedRequest("https://edge.invalid" + route, {
      method: "POST", body: JSON.stringify({ url: "https://allowed.example.org/result" }), requestId
    }), environment, {
      fetcher: async () => new Response("new"),
      browserRunner: { async quickAction() {
        return new Response(JSON.stringify({
          success: true, result: {
            content: "<html>new</html>",
            screenshot: Buffer.from([137,80,78,71,13,10,26,10]).toString("base64")
          }, meta: { status: 200, title: "new" }
        }), { headers: { "content-type": "application/json" } });
      }},
      logWriter: NO_LOG
    });
    assert.equal(response.status, 500);
    assert.ok(collision);
    assert.equal(await (await bucket.get(collision))?.text(), "previously retained bytes");
    assert.ok(!memory.deletedKeys.includes(collision));
    const final = await loadReceiptRecord(bucket, requestId);
    assert.equal(final?.status, "failed");
    if (operation === "browser.run") {
      assert.equal(memory.deletedKeys.length, 1);
      assert.match(memory.deletedKeys[0]!, /\/screenshot\.png$/);
    }
  });
}
