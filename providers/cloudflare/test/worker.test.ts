import assert from "node:assert/strict";
import test from "node:test";

import type { EdgeReceiptEnvelope } from "../src/contracts.js";
import { handleRequest } from "../src/index.js";
import { effectivePolicyVersion } from "../src/policy.js";
import { MemoryR2, makeEnv, signedRequest } from "./helpers.js";

test("unsigned requests are rejected before route handling", async () => {
  const response = await handleRequest(
    new Request("https://edge.invalid/health"),
    makeEnv()
  );
  assert.equal(response.status, 401);
  assert.match(response.headers.get("www-authenticate") ?? "", /Ordivon-HMAC/);
});

test("signed health and capabilities are minimal and non-cacheable", async () => {
  const environment = makeEnv();
  const health = await handleRequest(
    signedRequest("https://edge.invalid/health"),
    environment
  );
  assert.equal(health.status, 200);
  assert.equal(health.headers.get("cache-control"), "no-store");
  assert.deepEqual(await health.json(), {
    schema_version: 1,
    service: "ordivon-edge",
    status: "ok",
    policy_version: await effectivePolicyVersion(environment),
    worker_version: {
      id: "test-worker-version",
      tag: "test",
      timestamp: "2026-07-27T00:00:00.000Z"
    },
    deployment_identity: {
      source_commit: null,
      worker_release_digest: null
    }
  });

  const capabilities = await handleRequest(
    signedRequest("https://edge.invalid/v1/capabilities", {
      requestId: "request_caps_001"
    }),
    environment
  );
  const body = await capabilities.text();
  assert.equal(capabilities.status, 200);
  assert.doesNotMatch(body, /account_id|bucket_name|ordivon-artifacts/i);
  const document = JSON.parse(body) as {
    retention: { artifact_days: number; idempotency_days: number };
  };
  assert.ok(document.retention.artifact_days > document.retention.idempotency_days);
});

test("bounded fetch persists an artifact and receipt, then replays without refetching", async () => {
  const memory = new MemoryR2();
  const environment = makeEnv(memory);
  const requestId = "request_fetch_001";
  const signedAt = Math.floor(Date.now() / 1000);
  const requestBody = JSON.stringify({
    url: "https://allowed.example.org/data",
    maximum_bytes: 1024,
    timeout_ms: 2000
  });
  let fetchCount = 0;
  const fetcher = async () => {
    fetchCount += 1;
    return new Response("edge-result", {
      status: 200,
      headers: { "content-type": "text/plain; charset=utf-8" }
    });
  };

  const first = await handleRequest(
    signedRequest("https://edge.invalid/v1/fetch", {
      method: "POST",
      body: requestBody,
      requestId,
      timestamp: signedAt
    }),
    environment,
    { fetcher }
  );
  assert.equal(first.status, 200);
  const firstEnvelope = (await first.json()) as EdgeReceiptEnvelope;
  assert.equal(firstEnvelope.replayed, false);
  assert.equal(firstEnvelope.receipt.status, "succeeded");
  assert.equal(firstEnvelope.receipt.artifact?.key, `fetch/v2/${requestId}/g1/body`);
  assert.equal(fetchCount, 1);
  assert.ok(memory.objects.has(`receipts/v2/${requestId}.json`));
  assert.ok(memory.objects.has(`fetch/v2/${requestId}/g1/body`));

  const second = await handleRequest(
    signedRequest("https://edge.invalid/v1/fetch", {
      method: "POST",
      body: requestBody,
      requestId,
      timestamp: signedAt + 1
    }),
    environment,
    { fetcher }
  );
  const secondEnvelope = (await second.json()) as EdgeReceiptEnvelope;
  assert.equal(secondEnvelope.replayed, true);
  assert.equal(second.headers.get("x-ordivon-replayed"), "true");
  assert.equal(fetchCount, 1);
});

test("one request ID cannot be rebound to different content", async () => {
  const environment = makeEnv();
  const requestId = "request_conflict_001";
  const fetcher = async () => new Response("ok");
  const firstBody = JSON.stringify({ url: "https://allowed.example.org/one" });
  const secondBody = JSON.stringify({ url: "https://allowed.example.org/two" });

  const first = await handleRequest(
    signedRequest("https://edge.invalid/v1/fetch", {
      method: "POST",
      body: firstBody,
      requestId
    }),
    environment,
    { fetcher }
  );
  assert.equal(first.status, 200);

  const conflict = await handleRequest(
    signedRequest("https://edge.invalid/v1/fetch", {
      method: "POST",
      body: secondBody,
      requestId
    }),
    environment,
    { fetcher }
  );
  assert.equal(conflict.status, 409);
  assert.equal((await conflict.json() as { error: string }).error, "idempotency_conflict");
});

test("redirect destinations are revalidated before a second fetch", async () => {
  const environment = makeEnv();
  const requestId = "request_redirect_001";
  const calls: string[] = [];
  const fetcher = async (input: RequestInfo | URL) => {
    const url = input.toString();
    calls.push(url);
    if (calls.length === 1) {
      return new Response(null, {
        status: 302,
        headers: { location: "https://redirect.example.org/final" }
      });
    }
    return new Response("redirected");
  };
  const response = await handleRequest(
    signedRequest("https://edge.invalid/v1/fetch", {
      method: "POST",
      body: JSON.stringify({ url: "https://allowed.example.org/start" }),
      requestId
    }),
    environment,
    { fetcher }
  );
  assert.equal(response.status, 200);
  assert.deepEqual(calls, [
    "https://allowed.example.org/start",
    "https://redirect.example.org/final"
  ]);
});

test("unknown fetch fields are rejected and receipted", async () => {
  const memory = new MemoryR2();
  const environment = makeEnv(memory);
  const requestId = "request_fetch_unknown_field_001";
  const response = await handleRequest(
    signedRequest("https://edge.invalid/v1/fetch", {
      method: "POST",
      body: JSON.stringify({
        url: "https://allowed.example.org/data",
        timeout_mss: 1
      }),
      requestId
    }),
    environment
  );
  assert.equal(response.status, 422);
  const envelope = (await response.json()) as EdgeReceiptEnvelope;
  assert.equal(envelope.receipt.status, "rejected");
  assert.equal(envelope.receipt.error_code, "unsupported_fetch_option");
  assert.ok(memory.objects.has(`receipts/v2/${requestId}.json`));
});

test("rejected fetches receive persistent receipts", async () => {
  const memory = new MemoryR2();
  const environment = makeEnv(memory);
  const requestId = "request_reject_001";
  const body = JSON.stringify({ url: "https://forbidden.example.org/data" });
  const response = await handleRequest(
    signedRequest("https://edge.invalid/v1/fetch", {
      method: "POST",
      body,
      requestId
    }),
    environment
  );
  assert.equal(response.status, 403);
  const envelope = (await response.json()) as EdgeReceiptEnvelope;
  assert.equal(envelope.receipt.status, "rejected");
  assert.equal(envelope.receipt.error_code, "host_not_allowed");
  assert.ok(memory.objects.has(`receipts/v2/${requestId}.json`));
});

test("authenticated clients can retrieve persisted artifacts", async () => {
  const memory = new MemoryR2();
  const environment = makeEnv(memory);
  await environment.ARTIFACTS.put("fetch/v1/request_artifact_001.body", "artifact-body", {
    httpMetadata: { contentType: "text/plain" },
    customMetadata: { sha256: "b".repeat(64) }
  });
  const response = await handleRequest(
    signedRequest(
      "https://edge.invalid/v1/artifacts/fetch/v1/request_artifact_001.body",
      { requestId: "request_get_001" }
    ),
    environment
  );
  assert.equal(response.status, 200);
  assert.equal(await response.text(), "artifact-body");
  assert.equal(response.headers.get("content-type"), "application/octet-stream");
  assert.equal(response.headers.get("content-disposition"), "attachment; filename=artifact.bin");
  assert.equal(response.headers.get("cache-control"), "no-store, no-transform");
  assert.equal(response.headers.get("x-ordivon-media-type"), "text/plain");
  assert.equal(response.headers.get("content-length"), "13");
  assert.equal(response.headers.get("x-ordivon-sha256"), "b".repeat(64));
});


test("bounded browser run stores screenshot, content, manifest, and replays", async () => {
  const memory = new MemoryR2();
  const environment = makeEnv(memory);
  const requestId = "request_browser_001";
  const signedAt = Math.floor(Date.now() / 1000);
  const requestBody = JSON.stringify({
    url: "https://allowed.example.org/page",
    viewport_width: 1280,
    viewport_height: 720,
    full_page: false,
    timeout_ms: 5000
  });
  const screenshot = Uint8Array.from([137, 80, 78, 71, 13, 10, 26, 10]);
  let browserCount = 0;
  const browserRunner = {
    async quickAction(action: "snapshot", options: BrowserRunSnapshotOptions) {
      browserCount += 1;
      assert.equal(action, "snapshot");
      assert.equal("url" in options ? options.url : "", "https://allowed.example.org/page");
      assert.deepEqual(options.viewport, { width: 1280, height: 720 });
      assert.deepEqual(options.allowRequestPattern, [
        "^https://allowed\\.example\\.org(?::443)?(?:/|$)"
      ]);
      return new Response(
        JSON.stringify({
          success: true,
          result: {
            content: "<!doctype html><title>Browser Test</title><p>rendered</p>",
            screenshot: Buffer.from(screenshot).toString("base64")
          },
          meta: { status: 200, title: "Browser Test" }
        }),
        {
          status: 200,
          headers: {
            "content-type": "application/json",
            "x-browser-ms-used": "321"
          }
        }
      );
    }
  };

  const first = await handleRequest(
    signedRequest("https://edge.invalid/v1/browser/run", {
      method: "POST",
      body: requestBody,
      requestId,
      timestamp: signedAt
    }),
    environment,
    { browserRunner }
  );
  assert.equal(first.status, 200);
  const envelope = (await first.json()) as EdgeReceiptEnvelope;
  assert.equal(envelope.replayed, false);
  assert.equal(envelope.receipt.operation, "browser.run");
  assert.equal(envelope.receipt.status, "succeeded");
  assert.equal(envelope.receipt.browser?.page_title, "Browser Test");
  assert.equal(envelope.receipt.browser?.browser_ms, 321);
  assert.equal(envelope.receipt.browser?.final_url_observed, false);
  assert.equal(envelope.receipt.browser?.final_url, undefined);
  assert.equal(envelope.receipt.artifacts?.length, 3);
  assert.equal(
    envelope.receipt.artifact?.key,
    `browser/v2/${requestId}/g1/manifest.json`
  );
  assert.equal(browserCount, 1);

  const screenshotObject = await environment.ARTIFACTS.get(
    `browser/v2/${requestId}/g1/screenshot.png`
  );
  assert.notEqual(screenshotObject, null);
  assert.deepEqual(
    new Uint8Array(await screenshotObject!.arrayBuffer()),
    screenshot
  );
  assert.ok(memory.objects.has(`browser/v2/${requestId}/g1/content.html`));
  assert.ok(memory.objects.has(`browser/v2/${requestId}/g1/manifest.json`));
  assert.ok(memory.objects.has(`receipts/v2/${requestId}.json`));

  const replay = await handleRequest(
    signedRequest("https://edge.invalid/v1/browser/run", {
      method: "POST",
      body: requestBody,
      requestId,
      timestamp: signedAt + 1
    }),
    environment,
    { browserRunner }
  );
  const replayEnvelope = (await replay.json()) as EdgeReceiptEnvelope;
  assert.equal(replayEnvelope.replayed, true);
  assert.deepEqual(replayEnvelope.receipt, envelope.receipt);
  assert.equal(browserCount, 1);
});

test("browser policy rejection is receipted before Browser Run executes", async () => {
  const memory = new MemoryR2();
  const environment = makeEnv(memory);
  let browserCount = 0;
  const browserRunner = {
    async quickAction() {
      browserCount += 1;
      return new Response(null, { status: 500 });
    }
  };
  const requestId = "request_browser_reject_001";
  const response = await handleRequest(
    signedRequest("https://edge.invalid/v1/browser/run", {
      method: "POST",
      body: JSON.stringify({
        url: "https://forbidden.example.org/",
        add_script_tag: "not-allowed"
      }),
      requestId
    }),
    environment,
    { browserRunner }
  );
  assert.equal(response.status, 422);
  const envelope = (await response.json()) as EdgeReceiptEnvelope;
  assert.equal(envelope.receipt.status, "rejected");
  assert.equal(envelope.receipt.error_code, "unsupported_browser_option");
  assert.equal(browserCount, 0);
  assert.ok(memory.objects.has(`receipts/v2/${requestId}.json`));
});

test("Browser Run rate limits produce failed receipts without upstream details", async () => {
  const memory = new MemoryR2();
  const environment = makeEnv(memory);
  const requestId = "request_browser_rate_001";
  const browserRunner = {
    async quickAction() {
      return new Response(
        JSON.stringify({
          success: false,
          errors: [{ message: "internal provider detail" }]
        }),
        { status: 429, headers: { "content-type": "application/json" } }
      );
    }
  };
  const response = await handleRequest(
    signedRequest("https://edge.invalid/v1/browser/run", {
      method: "POST",
      body: JSON.stringify({ url: "https://allowed.example.org/" }),
      requestId
    }),
    environment,
    { browserRunner }
  );
  assert.equal(response.status, 429);
  const text = await response.text();
  assert.doesNotMatch(text, /internal provider detail/);
  const envelope = JSON.parse(text) as EdgeReceiptEnvelope;
  assert.equal(envelope.receipt.status, "failed");
  assert.equal(envelope.receipt.error_code, "browser_rate_limited");
});


test("non-PNG Browser output fails before Browser Artifacts commit", async () => {
  const memory = new MemoryR2();
  const environment = makeEnv(memory);
  const requestId = "request_browser_invalid_png_001";
  const browserRunner = {
    async quickAction() {
      return new Response(
        JSON.stringify({
          success: true,
          result: {
            content: "<!doctype html><title>Invalid Screenshot</title>",
            screenshot: Buffer.from("not-a-png").toString("base64")
          },
          meta: { status: 200, title: "Invalid Screenshot" }
        }),
        { status: 200, headers: { "content-type": "application/json" } }
      );
    }
  };
  const response = await handleRequest(
    signedRequest("https://edge.invalid/v1/browser/run", {
      method: "POST",
      body: JSON.stringify({ url: "https://allowed.example.org/" }),
      requestId
    }),
    environment,
    { browserRunner }
  );
  assert.equal(response.status, 502);
  const envelope = (await response.json()) as EdgeReceiptEnvelope;
  assert.equal(envelope.receipt.status, "failed");
  assert.equal(envelope.receipt.error_code, "invalid_browser_output");
  assert.equal(
    [...memory.objects].some(([key]) => key.startsWith(`browser/v2/${requestId}/`)),
    false
  );
  assert.ok(memory.objects.has(`receipts/v2/${requestId}.json`));
});
