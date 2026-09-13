import assert from "node:assert/strict";
import test from "node:test";

import { validateArtifactKey } from "../src/artifacts.js";
import { createBrowserManifest } from "../src/browser-manifest.js";
import { browserRunOptions, validateBrowserRunRequest } from "../src/browser-policy.js";
import { capabilitiesDocument } from "../src/contracts.js";
import { validateExternalUrl, validateFetchRequest } from "../src/fetch-policy.js";
import { effectivePolicyVersion } from "../src/policy.js";
import { createReceipt } from "../src/receipts.js";

const DIGEST = "a".repeat(64);
const EXECUTION = {
  policy_version: "test-policy",
  capability_version: "test-capability",
  worker_version_id: "test-worker-version",
  worker_version_tag: "test",
  worker_version_timestamp: "2026-07-27T00:00:00.000Z",
  lease_generation: 1
} as const;

test("capabilities expose only the Edge execution surface", () => {
  const document = capabilitiesDocument("test-policy");
  const states = new Map(
    document.capabilities.map((capability) => [capability.id, capability.state])
  );
  assert.ok(document.retention.artifact_days > document.retention.idempotency_days);
  assert.deepEqual(
    [...states.entries()],
    [
      ["artifact.get", "ready"],
      ["fetch", "ready"],
      ["browser.run", "ready"],
      ["receipt", "ready"]
    ]
  );
});

test("receipt timestamps, request digests, and evidence are explicit", () => {
  const artifact = {
    key: "fetch/v2/receipt-test/g1/body",
    sha256: "b".repeat(64),
    bytes: 12,
    media_type: "text/plain"
  };
  const receipt = createReceipt({
    operation: "fetch",
    status: "succeeded",
    requestDigest: DIGEST,
    startedAt: new Date("2026-07-27T00:00:00.000Z"),
    completedAt: new Date("2026-07-27T00:00:01.000Z"),
    receiptId: "receipt-test",
    execution: { ...EXECUTION, capability_version: "fetch.v2" },
    artifact,
    artifacts: [artifact],
    fetch: {
      requested_url: "https://allowed.example.org/",
      final_url: "https://allowed.example.org/",
      http_status: 200,
      redirect_count: 0
    }
  });
  assert.equal(receipt.receipt_id, "receipt-test");
  assert.equal(receipt.request_digest, DIGEST);
  assert.equal(receipt.duration_ms, 1_000);
  assert.deepEqual(receipt.artifacts, [artifact]);
});

test("receipt rejects invalid outcome combinations", () => {
  assert.throws(() =>
    createReceipt({
      operation: "fetch",
      status: "failed",
      requestDigest: DIGEST,
      receiptId: "receipt-test",
      startedAt: new Date("2026-07-27T00:00:01.000Z"),
      completedAt: new Date("2026-07-27T00:00:00.000Z"),
      errorCode: "timeout",
      execution: EXECUTION
    })
  );
  assert.throws(() =>
    createReceipt({
      operation: "fetch",
      status: "succeeded",
      requestDigest: DIGEST,
      receiptId: "receipt-test",
      startedAt: new Date("2026-07-27T00:00:00.000Z"),
      completedAt: new Date("2026-07-27T00:00:01.000Z"),
      errorCode: "unexpected",
      execution: EXECUTION
    })
  );
});

test("artifact keys are normalized and namespaced", () => {
  assert.equal(
    validateArtifactKey("artifacts/2026/receipt-test.json"),
    "artifacts/2026/receipt-test.json"
  );
  for (const key of [
    "/artifacts/a",
    "unknown/a",
    "artifacts/../secret",
    "artifacts\\secret",
    "artifacts/"
  ]) {
    assert.throws(() => validateArtifactKey(key));
  }
});

test("fetch policy is HTTPS-only, allowlisted, and bounded", () => {
  const environment = { FETCH_ALLOWED_HOSTS: "allowed.example.org,api.trusted.example.org" };
  assert.equal(
    validateExternalUrl("https://allowed.example.org/path#fragment", environment).toString(),
    "https://allowed.example.org/path"
  );
  assert.equal(
    validateExternalUrl("https://api.trusted.example.org/path", environment).hostname,
    "api.trusted.example.org"
  );
  for (const url of [
    "http://allowed.example.org/",
    "https://127.0.0.1/",
    "https://localhost/",
    "https://not-allowed.example.org/",
    "https://allowed.example.org:8443/"
  ]) {
    assert.throws(() => validateExternalUrl(url, environment));
  }

  const request = validateFetchRequest(
    { url: "https://allowed.example.org/data", maximum_bytes: 1024, timeout_ms: 2000 },
    environment
  );
  assert.equal(request.maximumBytes, 1024);
  assert.equal(request.timeoutMs, 2000);
  assert.throws(() =>
    validateFetchRequest(
      { url: "https://allowed.example.org/data", timeout_mss: 1 },
      environment
    )
  );
  assert.throws(() =>
    validateExternalUrl(
      "https://example.com/",
      { FETCH_ALLOWED_HOSTS: "*.com" }
    )
  );
  assert.throws(() =>
    validateExternalUrl(
      "https://api.trusted.example.org/",
      { FETCH_ALLOWED_HOSTS: "*.trusted.example.org" }
    )
  );
});


test("browser policy exposes only bounded navigation and same-origin resources", () => {
  const environment = { FETCH_ALLOWED_HOSTS: "allowed.example.org" };
  const request = validateBrowserRunRequest(
    {
      url: "https://allowed.example.org/page#section",
      viewport_width: 1280,
      viewport_height: 720,
      full_page: true,
      wait_until: "domcontentloaded",
      timeout_ms: 5000,
      wait_after_ms: 250
    },
    environment
  );
  const options = browserRunOptions(request);
  assert.equal(request.url.toString(), "https://allowed.example.org/page");
  assert.deepEqual(request.viewport, { width: 1280, height: 720 });
  assert.equal(options.setJavaScriptEnabled, true);
  assert.equal(options.cacheTTL, 0);
  assert.deepEqual(options.allowRequestPattern, [
    "^https://allowed\\.example\\.org(?::443)?(?:/|$)"
  ]);
  assert.equal(options.screenshotOptions?.fullPage, true);
  assert.throws(() =>
    validateBrowserRunRequest(
      { url: "https://allowed.example.org/", cookies: [] },
      environment
    )
  );
  assert.throws(() =>
    validateBrowserRunRequest(
      { url: "https://forbidden.example.org/" },
      environment
    )
  );
});


test("effective policy version is stable across host order and changes with policy inputs", async () => {
  const first = await effectivePolicyVersion({
    FETCH_ALLOWED_HOSTS: "b.example.org,a.example.org"
  });
  const reordered = await effectivePolicyVersion({
    FETCH_ALLOWED_HOSTS: "a.example.org,b.example.org"
  });
  const changed = await effectivePolicyVersion({
    FETCH_ALLOWED_HOSTS: "a.example.org,c.example.org"
  });
  assert.match(first, /^p1\.6\.[a-f0-9]{16}$/);
  assert.equal(first, reordered);
  assert.notEqual(first, changed);
});


test("Browser Manifest preserves execution, page, and Artifact order", () => {
  const screenshot = {
    key: "browser/v2/request_browser_manifest_001/g1/screenshot.png",
    sha256: "b".repeat(64),
    bytes: 8,
    media_type: "image/png",
    etag: '"screenshot"'
  };
  const content = {
    key: "browser/v2/request_browser_manifest_001/g1/content.html",
    sha256: "c".repeat(64),
    bytes: 64,
    media_type: "text/html; charset=utf-8",
    etag: '"content"'
  };
  const execution = {
    ...EXECUTION,
    capability_version: "browser.snapshot.v2"
  };
  const browser = {
    requested_url: "https://allowed.example.org/",
    final_url_observed: false,
    page_title: "Manifest Test",
    page_status: 200,
    browser_ms: 42,
    viewport: { width: 1280, height: 720 },
    full_page: false
  };
  const manifest = createBrowserManifest({
    receiptId: "request_browser_manifest_001",
    execution,
    browser,
    screenshot,
    content
  });
  assert.equal(manifest.schema_version, 2);
  assert.equal(manifest.receipt_id, "request_browser_manifest_001");
  assert.deepEqual(manifest.execution, execution);
  assert.deepEqual(manifest.browser, browser);
  assert.deepEqual(manifest.artifacts, [screenshot, content]);
});


test("receipt factory rejects evidence, status, and operation drift", () => {
  const artifact = {
    key: "fetch/v2/receipt-drift/g1/body",
    sha256: "d".repeat(64),
    bytes: 1,
    media_type: "text/plain"
  };
  const common = {
    requestDigest: DIGEST,
    receiptId: "receipt-drift",
    startedAt: new Date("2026-07-27T00:00:00.000Z"),
    completedAt: new Date("2026-07-27T00:00:01.000Z"),
    execution: { ...EXECUTION, capability_version: "fetch.v2" }
  };
  assert.throws(() =>
    createReceipt({
      ...common,
      operation: "fetch",
      status: "succeeded"
    })
  );
  assert.throws(() =>
    createReceipt({
      ...common,
      operation: "fetch",
      status: "failed",
      errorCode: "timeout",
      artifact,
      artifacts: [artifact]
    })
  );
  assert.throws(() =>
    createReceipt({
      ...common,
      operation: "browser.run",
      status: "succeeded",
      artifact,
      artifacts: [artifact],
      browser: {
        requested_url: "https://allowed.example.org/",
        final_url_observed: false,
        page_title: "Drift",
        page_status: 200,
        browser_ms: 1,
        viewport: { width: 1280, height: 720 },
        full_page: false
      }
    })
  );
});
