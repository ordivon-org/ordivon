import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import { RecoveryOperationProvider } from "../src/providers/fixture.ts";
import type { CompiledAgentContext } from "../src/host/context.ts";
import type { OperationDecision, OperationProvider } from "../src/providers/types.ts";
import { createGameServer, type AgentProviderName } from "../src/server.ts";

async function listen(game: ReturnType<typeof createGameServer>): Promise<string> {
  await new Promise<void>((resolve) => game.server.listen(0, "127.0.0.1", resolve));
  const address = game.server.address();
  if (!address || typeof address === "string") throw new Error("server did not expose a TCP address");
  return `http://127.0.0.1:${address.port}`;
}

async function json(base: string, path: string, options?: RequestInit): Promise<{ status: number; body: any }> {
  const response = await fetch(`${base}${path}`, options);
  return { status: response.status, body: await response.json() };
}

function post(base: string, path: string, body: unknown): Promise<{ status: number; body: any }> {
  return json(base, path, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
}

class NamedRecoveryProvider implements OperationProvider {
  readonly providerId: string;
  readonly delegate = new RecoveryOperationProvider();
  calls = 0;

  constructor(name: AgentProviderName) {
    this.providerId = `test-provider:${name}`;
  }

  async decide(context: CompiledAgentContext): Promise<OperationDecision> {
    this.calls += 1;
    const decision = await this.delegate.decide(context);
    return { ...decision, providerId: this.providerId };
  }

  evidenceMetadata(): Record<string, unknown> {
    return { providerId: this.providerId, calls: this.calls };
  }
}

test("Agent HTTP control surface initializes, steps, runs, exposes timeline, and reads Artifacts", async () => {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-agent-server-"));
  const providers: NamedRecoveryProvider[] = [];
  const game = createGameServer({
    dbPath: join(directory, "world.sqlite3"),
    agentProviderFactory(name) {
      const provider = new NamedRecoveryProvider(name);
      providers.push(provider);
      return provider;
    },
  });
  try {
    const base = await listen(game);
    const before = await json(base, "/api/agent/state?provider=fixture");
    assert.equal(before.status, 200);
    assert.equal(before.body.initialized, false);

    const initialized = await post(base, "/api/agent/initialize", { provider: "codex" });
    assert.equal(initialized.status, 201);
    assert.equal(initialized.body.provider, "codex");
    assert.equal(initialized.body.projection.task.phase, "ready");

    const firstStep = await post(base, "/api/agent/step", { provider: "codex" });
    assert.equal(firstStep.status, 200);
    assert.equal(firstStep.body.receipt.status, "context_compiled");
    assert.equal(firstStep.body.agent.initialized, true);
    assert.equal(firstStep.body.agent.projection.task.phase, "active");

    const secondStep = await post(base, "/api/agent/step", { provider: "hermes" });
    assert.equal(secondStep.body.receipt.status, "decision_recorded");
    assert.equal(secondStep.body.receipt.providerId, "test-provider:hermes");

    const completed = await post(base, "/api/agent/run", { provider: "codex-hermes", maximumSteps: 256 });
    assert.equal(completed.status, 200);
    assert.equal(completed.body.receipt.projection.goal.status, "succeeded");
    assert.equal(completed.body.receipt.projection.task.phase, "succeeded");
    assert.equal(completed.body.world.state.mission.status, "victory");
    assert.equal(completed.body.world.digest, "41d7bfd4c1b36f0a8e38533be7f7e9b48b1625608c76c5ced1ddd3d0952d02d2");
    assert.equal(completed.body.agent.effects.length, 25);
    assert.equal(completed.body.agent.dispatches.length, 25);

    const state = await json(base, "/api/agent/state?provider=hermes-codex");
    assert.equal(state.body.initialized, true);
    assert.equal(state.body.projection.attempts.length, 10);
    assert.equal(state.body.timeline.at(-1).eventType, "task_succeeded");

    const timeline = await json(base, "/api/agent/timeline");
    assert.ok(timeline.body.timeline.length >= 45);
    assert.ok(timeline.body.timeline.some((event: { eventType: string }) => event.eventType === "skill_step_verified"));
    assert.ok(timeline.body.timeline.every((event: { eventType: string }) => !event.eventType.startsWith("host-contract.")));

    const contextDigest = state.body.projection.attempts[0].contextDigest;
    const artifact = await json(base, `/api/agent/artifacts/${encodeURIComponent(contextDigest)}`);
    assert.equal(artifact.status, 200);
    assert.equal(artifact.body.kind, "agent-context-v2");
    assert.equal(artifact.body.digest, contextDigest);
    assert.ok(providers.some((provider) => provider.providerId === "test-provider:hermes" && provider.calls === 1));
  } finally {
    await game.close();
    rmSync(directory, { recursive: true, force: true });
  }
});

test("Agent API validates Provider names, body shapes, step budgets, Artifacts, and uninitialized timeline", async () => {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-agent-server-errors-"));
  const game = createGameServer({
    dbPath: join(directory, "world.sqlite3"),
    agentProviderFactory: (name) => new NamedRecoveryProvider(name),
  });
  try {
    const base = await listen(game);
    const timeline = await json(base, "/api/agent/timeline");
    assert.deepEqual(timeline.body.timeline, []);

    for (const [path, body] of [
      ["/api/agent/initialize", { provider: "unknown" }],
      ["/api/agent/step", []],
      ["/api/agent/run", { maximumSteps: 0 }],
      ["/api/agent/run", { maximumSteps: 513 }],
      ["/api/agent/run", { maximumSteps: 1.5 }],
    ] as const) {
      const response = await post(base, path, body);
      assert.equal(response.status, 400, path);
    }

    const missing = await json(base, "/api/agent/artifacts/sha256%3Amissing");
    assert.equal(missing.status, 404);
    assert.equal(missing.body.error, "artifact_not_found");

    const malformedJson = await fetch(`${base}/api/agent/initialize`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: "{",
    });
    assert.equal(malformedJson.status, 400);
    const notFound = await json(base, "/api/unknown");
    assert.equal(notFound.status, 404);
  } finally {
    await game.close();
    rmSync(directory, { recursive: true, force: true });
  }
});

test("Agent projections remain isolated across HTTP Runs and manual actions coexist", async () => {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-agent-server-runs-"));
  const game = createGameServer({
    dbPath: join(directory, "world.sqlite3"),
    agentProviderFactory: (name) => new NamedRecoveryProvider(name),
  });
  try {
    const base = await listen(game);
    const created = await post(base, "/api/runs", { runId: "run:http-second" });
    assert.equal(created.status, 201);
    assert.equal(created.body.run.runId, "run:http-second");

    await post(base, "/api/agent/initialize?runId=run:default", { provider: "fixture" });
    await post(base, "/api/agent/initialize?runId=run:http-second", { provider: "hermes" });
    await post(base, "/api/agent/step?runId=run:http-second", { provider: "hermes" });

    const first = await json(base, "/api/agent/state?runId=run:default&provider=fixture");
    const second = await json(base, "/api/agent/state?runId=run:http-second&provider=hermes");
    assert.equal(first.body.projection.attempts.length, 0);
    assert.equal(second.body.projection.attempts.length, 1);

    const world = await json(base, "/api/state?runId=run:default");
    const move = world.body.availableActions.find((action: { actionId: string }) => action.actionId === "move:power-junction");
    assert.ok(move);
    const manual = await post(base, "/api/actions?runId=run:default", { ...move.command, commandId: "http-manual" });
    assert.equal(manual.status, 200);
    const events = await json(base, "/api/events?runId=run:default");
    assert.equal(events.body.events.length, 1);
    const suggestion = await json(base, "/api/suggestion?runId=run:default");
    assert.equal(suggestion.status, 200);
    assert.equal(suggestion.body.runId, "run:default");

    const invalidCommand = await post(base, "/api/actions", { kind: "unknown" });
    assert.equal(invalidCommand.status, 400);
    const invalidRun = await fetch(`${base}/api/runs`, {
      method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify("bad"),
    });
    assert.equal(invalidRun.status, 400);
    const app = await fetch(`${base}/app.js`);
    assert.equal(app.status, 200);
    assert.match(await app.text(), /advanceMission|mission-control/);
    const debugApp = await fetch(`${base}/debug.js`);
    assert.equal(debugApp.status, 200);
    assert.match(await debugApp.text(), /Autonomous run|agent\/run/);
    const styles = await fetch(`${base}/styles.css`);
    assert.equal(styles.status, 200);
    const debugStyles = await fetch(`${base}/debug.css`);
    assert.equal(debugStyles.status, 200);
  } finally {
    await game.close();
    rmSync(directory, { recursive: true, force: true });
  }
});
