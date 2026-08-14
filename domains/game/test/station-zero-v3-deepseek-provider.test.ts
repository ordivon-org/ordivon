import assert from "node:assert/strict";
import { chmodSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import { ProviderAdapterError } from "../src/team/provider-runtime.ts";
import {
  FixtureStationZeroV3AgentProvider,
  StationZeroV3DeepSeekCredentialPool,
  StationZeroV3DeepSeekProviderPool,
  StationZeroV3PlayService,
  StationZeroV3Store,
  compileStationZeroV3AgentContext,
  type StationZeroV3AgentContext,
  type StationZeroV3AgentDecision,
  type StationZeroV3AgentProvider,
} from "../src/station-zero-v3/index.ts";

function secret(
  directory: string,
  name: string,
  apiKey: string,
  mode = 0o600,
  overrides: Record<string, unknown> = {},
): string {
  const path = join(directory, `${name}.json`);
  writeFileSync(path, JSON.stringify({
    schemaVersion: 1,
    apiKey,
    baseUrl: "https://api.deepseek.test",
    model: "deepseek-v4-flash",
    provider: "deepseek",
    ...overrides,
  }));
  chmodSync(path, mode);
  return path;
}

function contextFixture(): {
  store: StationZeroV3Store;
  context: StationZeroV3AgentContext;
} {
  const store = new StationZeroV3Store(":memory:");
  const play = new StationZeroV3PlayService(store);
  const runId = "run:deepseek-provider:test";
  play.initialize({ runId });
  const planning = store.latestPlanning(runId)!;
  const order = play.planning.currentOrder(runId, planning.planningId).order;
  return {
    store,
    context: compileStationZeroV3AgentContext(
      store.stateAtRevision(runId, planning.worldRevision),
      planning,
      "engineer-imani",
      order,
    ),
  };
}

function response(model: string, content: unknown, finishReason = "stop"): Response {
  return new Response(JSON.stringify({
    model,
    choices: [{
      finish_reason: finishReason,
      message: { content: typeof content === "string" ? content : JSON.stringify(content) },
    }],
    usage: {
      prompt_tokens: 100,
      completion_tokens: 20,
      total_tokens: 120,
      prompt_cache_hit_tokens: 32,
      completion_tokens_details: { reasoning_tokens: 0 },
    },
  }), { status: 200, headers: { "content-type": "application/json" } });
}

test("DeepSeek Provider loads only private credentials and returns one admitted Decision", async () => {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-v3-deepseek-valid-"));
  const { store, context } = contextFixture();
  let request: Record<string, unknown> | null = null;
  try {
    const path = secret(directory, "primary", "key-primary");
    const candidateId = context.candidates[0]!.candidateId;
    const pool = new StationZeroV3DeepSeekProviderPool({
      secretPaths: [path],
      thinkingMode: "disabled",
      fetchImplementation: async (_input, init) => {
        request = JSON.parse(String(init?.body));
        return response("deepseek-v4-flash", {
          candidateId,
          directiveId: null,
          rationale: "Choose the admitted engineering action.",
          confidence: 0.82,
        });
      },
    });
    const decision = await pool.decide(context);
    assert.equal(decision.candidateId, candidateId);
    assert.equal(decision.directiveId, null);
    assert.equal(decision.providerId, "deepseek-station-zero-v3-v1:deepseek/deepseek-v4-flash:disabled");
    const capturedRequest = request as unknown as Record<string, unknown>;
    const messages = capturedRequest.messages as Array<{ role: string; content: string }>;
    assert.match(messages[0]!.content, /Commander contingency semantics are exact/);
    assert.match(messages[0]!.content, /protectedActorId biases legal guard coverage/);
    assert.match(messages[0]!.content, /previousActionFeedback is present/);
    assert.deepEqual((capturedRequest.thinking as { type: string }).type, "disabled");
    assert.equal("reasoning_effort" in capturedRequest, false);
    assert.equal(capturedRequest.temperature, 0.1);
    const evidence = pool.evidenceSnapshot();
    assert.equal(evidence.calls.length, 1);
    assert.equal(evidence.calls[0]!.outcome, "success");
    assert.equal(evidence.calls[0]!.reasoningTokens, 0);
    assert.equal(JSON.stringify(evidence).includes("key-primary"), false);
  } finally {
    store.close();
    rmSync(directory, { recursive: true, force: true });
  }
});

test("DeepSeek Provider fails over from invalid output to another credential without weakening admission", async () => {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-v3-deepseek-fallback-"));
  const { store, context } = contextFixture();
  try {
    const first = secret(directory, "first", "key-first");
    const second = secret(directory, "second", "key-second");
    const candidateId = context.candidates[0]!.candidateId;
    const pool = new StationZeroV3DeepSeekProviderPool({
      secretPaths: [first, second],
      fetchImplementation: async (_input, init) => {
        const authorization = new Headers(init?.headers).get("authorization");
        return authorization === "Bearer key-first"
          ? response("deepseek-v4-flash", {
            candidateId: "candidate:invented",
            directiveId: null,
            rationale: "Invented output must be rejected.",
            confidence: 0.8,
          })
          : response("deepseek-v4-flash", {
            candidateId,
            directiveId: null,
            rationale: "Fallback selects an admitted Candidate.",
            confidence: 0.75,
          });
      },
    });
    const decision = await pool.decide(context);
    assert.equal(decision.candidateId, candidateId);
    const calls = pool.evidenceSnapshot().calls;
    assert.deepEqual(calls.map((call) => [call.credentialId, call.attempt, call.outcome]), [
      ["first", 1, "invalid_output"],
      ["second", 2, "success"],
    ]);
  } finally {
    store.close();
    rmSync(directory, { recursive: true, force: true });
  }
});

test("DeepSeek Provider rejects group-readable secret files before any network request", () => {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-v3-deepseek-permission-"));
  try {
    const path = secret(directory, "insecure", "key-insecure", 0o644);
    assert.throws(
      () => new StationZeroV3DeepSeekProviderPool({ secretPaths: [path] }),
      (error: unknown) => error instanceof ProviderAdapterError && error.code === "unavailable",
    );
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});

test("thinking mode sends explicit effort and omits ineffective temperature", async () => {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-v3-deepseek-thinking-"));
  const { store, context } = contextFixture();
  let request: Record<string, unknown> | null = null;
  try {
    const path = secret(directory, "thinking", "key-thinking");
    const pool = new StationZeroV3DeepSeekProviderPool({
      secretPaths: [path],
      thinkingMode: "enabled",
      reasoningEffort: "high",
      maxTokens: 2_048,
      fetchImplementation: async (_input, init) => {
        request = JSON.parse(String(init?.body));
        return response("deepseek-v4-flash", {
          candidateId: context.candidates[0]!.candidateId,
          directiveId: null,
          rationale: "Thinking-mode contract remains bounded.",
          confidence: 0.7,
        });
      },
    });
    await pool.decide(context);
    const capturedRequest = request as unknown as Record<string, unknown>;
    assert.deepEqual((capturedRequest.thinking as { type: string }).type, "enabled");
    assert.equal(capturedRequest.reasoning_effort, "high");
    assert.equal("temperature" in capturedRequest, false);
    assert.equal(pool.evidenceSnapshot().thinkingMode, "enabled");
  } finally {
    store.close();
    rmSync(directory, { recursive: true, force: true });
  }
});

test("high-fidelity Agent decisions are generated concurrently from one World snapshot", async () => {
  const store = new StationZeroV3Store(":memory:");
  const fixture = new FixtureStationZeroV3AgentProvider();
  let active = 0;
  let maximumActive = 0;
  const provider: StationZeroV3AgentProvider = {
    providerId: "delayed-concurrency-test",
    async decide(context): Promise<StationZeroV3AgentDecision> {
      active += 1;
      maximumActive = Math.max(maximumActive, active);
      await new Promise((resolve) => setTimeout(resolve, 80));
      try {
        return await fixture.decide(context);
      } finally {
        active -= 1;
      }
    },
  };
  try {
    const play = new StationZeroV3PlayService(store, { providerFactory: () => provider });
    const runId = "run:deepseek-provider:parallel";
    play.initialize({ runId });
    const started = performance.now();
    await play.generatePreview(runId);
    const elapsed = performance.now() - started;
    assert.equal(maximumActive, 5);
    assert.ok(elapsed < 300, `parallel Preview took ${elapsed} ms`);
  } finally {
    store.close();
  }
});

test("DeepSeek Provider retries across time after every credential shares a transient endpoint failure", async () => {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-v3-deepseek-time-retry-"));
  const { store, context } = contextFixture();
  let invocation = 0;
  try {
    const first = secret(directory, "first", "key-first");
    const second = secret(directory, "second", "key-second");
    const candidateId = context.candidates[0]!.candidateId;
    const pool = new StationZeroV3DeepSeekProviderPool({
      secretPaths: [first, second],
      maximumAttempts: 3,
      retryBaseDelayMs: 0,
      fetchImplementation: async () => {
        invocation += 1;
        if (invocation <= 2) throw new TypeError("fetch failed");
        return response("deepseek-v4-flash", {
          candidateId,
          directiveId: null,
          rationale: "The endpoint recovered and the admitted action remains valid.",
          confidence: 0.76,
        });
      },
    });
    const decision = await pool.decide(context);
    assert.equal(decision.candidateId, candidateId);
    assert.equal(invocation, 3);
    assert.deepEqual(pool.evidenceSnapshot().calls.map((call) => [call.credentialId, call.attempt, call.outcome]), [
      ["first", 1, "transport_error"],
      ["second", 2, "transport_error"],
      ["first", 3, "success"],
    ]);
  } finally {
    store.close();
    rmSync(directory, { recursive: true, force: true });
  }
});

test("directory sources hot-load additive deepseek files, retain existing identities, and skip duplicates", async () => {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-v3-deepseek-directory-"));
  const { store, context } = contextFixture();
  const authorizations: string[] = [];
  try {
    secret(directory, "deepseek", "key-primary", 0o600, { maximumConcurrency: 1 });
    secret(directory, "deepseek-disabled", "key-disabled", 0o600, { enabled: false });
    writeFileSync(join(directory, "unrelated.json"), "{}");
    chmodSync(join(directory, "unrelated.json"), 0o600);
    const pool = new StationZeroV3DeepSeekProviderPool({
      credentialSources: [directory],
      credentialReloadIntervalMs: 0,
      fetchImplementation: async (_input, init) => {
        authorizations.push(new Headers(init?.headers).get("authorization") ?? "");
        return response("deepseek-v4-flash", {
          candidateId: context.candidates[0]!.candidateId,
          directiveId: null,
          rationale: "Choose one admitted action from the current pool.",
          confidence: 0.8,
        });
      },
    });

    await pool.decide(context);
    assert.deepEqual(pool.evidenceSnapshot().credentials.map((entry) => entry.credentialId), ["deepseek"]);

    secret(directory, "deepseek2", "key-secondary", 0o600, {
      id: "secondary",
      maximumConcurrency: 2,
      weight: 3,
    });
    secret(directory, "deepseek-copy", "key-primary");
    await pool.decide(context);

    const snapshot = pool.evidenceSnapshot();
    assert.equal(snapshot.credentialPool.discoveredFiles, 4);
    assert.equal(snapshot.credentialPool.duplicateCredentialsSkipped, 1);
    assert.deepEqual(snapshot.credentials.map((entry) => entry.credentialId).sort(), ["deepseek", "secondary"]);
    assert.equal(snapshot.credentials.find((entry) => entry.credentialId === "deepseek")?.maximumConcurrency, 1);
    assert.equal(snapshot.credentials.find((entry) => entry.credentialId === "secondary")?.maximumConcurrency, 2);
    assert.equal(snapshot.credentials.find((entry) => entry.credentialId === "secondary")?.weight, 3);
    assert.ok(authorizations.includes("Bearer key-primary"));
    assert.ok(authorizations.includes("Bearer key-secondary"));
    assert.equal(JSON.stringify(snapshot).includes("key-primary"), false);
    assert.equal(JSON.stringify(snapshot).includes("key-secondary"), false);
  } finally {
    store.close();
    rmSync(directory, { recursive: true, force: true });
  }
});

test("an invalid newly added credential is reported without replacing the last-known-good pool", async () => {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-v3-deepseek-last-good-"));
  const { store, context } = contextFixture();
  try {
    secret(directory, "deepseek", "key-primary");
    const pool = new StationZeroV3DeepSeekProviderPool({
      credentialSources: [directory],
      credentialReloadIntervalMs: 0,
      fetchImplementation: async () => response("deepseek-v4-flash", {
        candidateId: context.candidates[0]!.candidateId,
        directiveId: null,
        rationale: "The retained credential remains usable.",
        confidence: 0.78,
      }),
    });
    await pool.decide(context);

    secret(directory, "deepseek-bad-permission", "key-bad", 0o644);
    secret(directory, "deepseek-wrong-model", "key-wrong", 0o600, { model: "another-model" });
    await pool.decide(context);

    const snapshot = pool.evidenceSnapshot();
    assert.deepEqual(snapshot.credentials.map((entry) => entry.credentialId), ["deepseek"]);
    assert.equal(snapshot.credentialPool.discoveryErrors.length, 2);
    assert.ok(snapshot.credentialPool.discoveryErrors.some((entry) => entry.sourceId === "deepseek-bad-permission.json"));
    assert.ok(snapshot.credentialPool.discoveryErrors.some((entry) => entry.sourceId === "deepseek-wrong-model.json"));
  } finally {
    store.close();
    rmSync(directory, { recursive: true, force: true });
  }
});

test("429 cools one credential while another credential completes the Decision", async () => {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-v3-deepseek-rate-limit-"));
  const { store, context } = contextFixture();
  try {
    const first = secret(directory, "deepseek-a", "key-a", 0o600, { id: "a" });
    const second = secret(directory, "deepseek-z", "key-z", 0o600, { id: "z" });
    const pool = new StationZeroV3DeepSeekProviderPool({
      credentialSources: [first, second],
      maximumAttempts: 2,
      retryBaseDelayMs: 1,
      credentialCooldownMaximumMs: 5_000,
      fetchImplementation: async (_input, init) => {
        const authorization = new Headers(init?.headers).get("authorization");
        if (authorization === "Bearer key-a") {
          return new Response(JSON.stringify({ error: { message: "rate limited" } }), {
            status: 429,
            headers: { "content-type": "application/json", "retry-after": "2" },
          });
        }
        return response("deepseek-v4-flash", {
          candidateId: context.candidates[0]!.candidateId,
          directiveId: null,
          rationale: "A healthy credential completed the bounded Decision.",
          confidence: 0.79,
        });
      },
    });

    await pool.decide(context);
    const snapshot = pool.evidenceSnapshot();
    assert.deepEqual(snapshot.calls.map((call) => [call.credentialId, call.outcome]), [
      ["a", "rate_limited"],
      ["z", "success"],
    ]);
    assert.notEqual(snapshot.credentials.find((entry) => entry.credentialId === "a")?.cooldownUntil, null);
    assert.equal(snapshot.credentials.find((entry) => entry.credentialId === "z")?.successes, 1);
  } finally {
    store.close();
    rmSync(directory, { recursive: true, force: true });
  }
});

test("401 quarantines only the rejected credential and does not poison the remaining pool", async () => {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-v3-deepseek-auth-"));
  const { store, context } = contextFixture();
  try {
    const first = secret(directory, "deepseek-a", "key-a", 0o600, { id: "a" });
    const second = secret(directory, "deepseek-z", "key-z", 0o600, { id: "z" });
    const pool = new StationZeroV3DeepSeekProviderPool({
      credentialSources: [first, second],
      maximumAttempts: 2,
      fetchImplementation: async (_input, init) => {
        const authorization = new Headers(init?.headers).get("authorization");
        if (authorization === "Bearer key-a") {
          return new Response(JSON.stringify({ error: { message: "invalid key" } }), {
            status: 401,
            headers: { "content-type": "application/json" },
          });
        }
        return response("deepseek-v4-flash", {
          candidateId: context.candidates[0]!.candidateId,
          directiveId: null,
          rationale: "The non-quarantined credential remains available.",
          confidence: 0.77,
        });
      },
    });

    const started = performance.now();
    await pool.decide(context);
    assert.ok(performance.now() - started < 500, "healthy fallback waited for a quarantined credential cycle");
    const firstSnapshot = pool.evidenceSnapshot();
    assert.equal(firstSnapshot.credentials.find((entry) => entry.credentialId === "a")?.quarantined, true);
    assert.equal(firstSnapshot.credentials.find((entry) => entry.credentialId === "a")?.quarantineReason, "authentication");
    await pool.decide(context);
    const calls = pool.evidenceSnapshot().calls;
    assert.equal(calls.filter((call) => call.credentialId === "a").length, 1);
    assert.equal(calls.filter((call) => call.credentialId === "z" && call.outcome === "success").length, 2);
  } finally {
    store.close();
    rmSync(directory, { recursive: true, force: true });
  }
});

test("a hot-added credential starts at the pool's current scheduling position instead of receiving a catch-up flood", async () => {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-v3-deepseek-fair-hot-add-"));
  try {
    secret(directory, "deepseek-old", "key-old", 0o600, { id: "old", maximumConcurrency: 1 });
    const pool = new StationZeroV3DeepSeekCredentialPool({
      sources: [directory],
      defaultMaximumConcurrency: 1,
      reloadIntervalMs: 0,
      cooldownBaseMs: 0,
    });
    for (let index = 0; index < 1_000; index += 1) {
      const handle = await pool.select();
      await handle.run(async () => undefined);
      pool.reportSuccess(handle, 1);
    }

    secret(directory, "deepseek-new", "key-new", 0o600, { id: "new", maximumConcurrency: 1 });
    pool.refresh(true);
    const selected: string[] = [];
    for (let index = 0; index < 20; index += 1) {
      const handle = await pool.select();
      selected.push(handle.credentialId);
      await handle.run(async () => undefined);
      pool.reportSuccess(handle, 1);
    }

    const counts = Object.groupBy(selected, (credentialId) => credentialId);
    assert.ok((counts.old?.length ?? 0) >= 8, selected.join(","));
    assert.ok((counts.new?.length ?? 0) >= 8, selected.join(","));
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});

test("a loaded credential fails closed when its file becomes insecure", async () => {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-v3-deepseek-permission-regression-"));
  try {
    const path = secret(directory, "deepseek", "key-primary");
    const pool = new StationZeroV3DeepSeekCredentialPool({
      sources: [directory],
      defaultMaximumConcurrency: 1,
      reloadIntervalMs: 0,
    });
    chmodSync(path, 0o644);

    assert.throws(
      () => pool.refresh(true),
      (error: unknown) => error instanceof ProviderAdapterError && error.code === "unavailable",
    );
    assert.equal(pool.size, 0);
    assert.equal(pool.snapshot().discoveryErrors[0]?.sourceId, "deepseek.json");
    await assert.rejects(
      () => pool.select(),
      (error: unknown) => error instanceof ProviderAdapterError && error.code === "unavailable",
    );
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});

test("the per-credential semaphore never exceeds its configured concurrency under queued handoff", async () => {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-v3-deepseek-concurrency-"));
  try {
    secret(directory, "deepseek", "key-primary", 0o600, { maximumConcurrency: 2 });
    const pool = new StationZeroV3DeepSeekCredentialPool({
      sources: [directory],
      defaultMaximumConcurrency: 1,
      reloadIntervalMs: 0,
    });
    let active = 0;
    let maximumActive = 0;
    await Promise.all(Array.from({ length: 40 }, async () => {
      const handle = await pool.select();
      await handle.run(async () => {
        active += 1;
        maximumActive = Math.max(maximumActive, active);
        await new Promise((resolve) => setTimeout(resolve, 4));
        active -= 1;
      });
      pool.reportSuccess(handle, 4);
    }));
    assert.equal(maximumActive, 2);
    const credential = pool.snapshot().credentials[0]!;
    assert.equal(credential.active, 0);
    assert.equal(credential.queued, 0);
    assert.equal(credential.reserved, 0);
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});

test("a concurrent success does not erase an active rate-limit cooldown", async () => {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-v3-deepseek-cooldown-race-"));
  try {
    secret(directory, "deepseek", "key-primary", 0o600, { maximumConcurrency: 2 });
    const pool = new StationZeroV3DeepSeekCredentialPool({
      sources: [directory],
      defaultMaximumConcurrency: 2,
      reloadIntervalMs: 0,
      cooldownBaseMs: 1,
      cooldownMaximumMs: 10_000,
    });
    const limited = await pool.select();
    const successful = await pool.select();
    await Promise.all([limited.run(async () => undefined), successful.run(async () => undefined)]);
    pool.reportFailure(limited, "rate_limit", 5_000);
    pool.reportSuccess(successful, 1);
    assert.notEqual(pool.snapshot().credentials[0]?.cooldownUntil, null);
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});

test("one missing credential source does not suppress valid credentials from another source", () => {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-v3-deepseek-multi-source-"));
  try {
    secret(directory, "deepseek", "key-primary");
    const missing = join(directory, "missing-directory");
    const pool = new StationZeroV3DeepSeekCredentialPool({
      sources: [missing, directory],
      defaultMaximumConcurrency: 1,
    });
    const snapshot = pool.snapshot();
    assert.equal(snapshot.credentials.length, 1);
    assert.ok(snapshot.discoveryErrors.some((entry) => entry.sourceId === missing));
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});

test("credential weight produces proportional sequential scheduling without bypassing concurrency", async () => {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-v3-deepseek-weight-"));
  try {
    secret(directory, "deepseek-a", "key-a", 0o600, { id: "a", weight: 1 });
    secret(directory, "deepseek-b", "key-b", 0o600, { id: "b", weight: 3 });
    const pool = new StationZeroV3DeepSeekCredentialPool({
      sources: [directory],
      defaultMaximumConcurrency: 1,
      reloadIntervalMs: 0,
    });
    const selected: string[] = [];
    for (let index = 0; index < 80; index += 1) {
      const handle = await pool.select();
      selected.push(handle.credentialId);
      await handle.run(async () => undefined);
      pool.reportSuccess(handle, 1);
    }
    const counts = Object.groupBy(selected, (credentialId) => credentialId);
    assert.equal(counts.a?.length, 20);
    assert.equal(counts.b?.length, 60);
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});
