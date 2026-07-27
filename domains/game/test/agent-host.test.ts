import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import { sha256 } from "../src/digest.ts";
import { AgentHost, type HostFaultPoint } from "../src/host/engine.ts";
import { materializeSkillStep, compileOperationFrontier, compileSkillPlan } from "../src/host/operations.ts";
import { RecoveryOperationProvider } from "../src/providers/fixture.ts";
import {
  ProviderAdapterError,
  type OperationDecision,
  type OperationProvider,
} from "../src/providers/types.ts";
import { GameStore } from "../src/storage.ts";

function fixture(): { directory: string; game: GameStore } {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-game-agent-host-"));
  return { directory, game: new GameStore(join(directory, "world.sqlite3")) };
}

class CountingProvider implements OperationProvider {
  readonly providerId = "counting-recovery-v1";
  calls = 0;
  readonly delegate = new RecoveryOperationProvider();
  async decide(context: Parameters<OperationProvider["decide"]>[0]): Promise<OperationDecision> {
    this.calls += 1;
    const decision = await this.delegate.decide(context);
    return { ...decision, providerId: this.providerId };
  }
  evidenceMetadata(): Record<string, unknown> { return { calls: this.calls }; }
}

test("persistent Agent Host completes the frozen mission through 10 Decisions and 25 verified Dispatches", async () => {
  const { directory, game } = fixture();
  try {
    const provider = new CountingProvider();
    const agent = new AgentHost(game, provider);
    const result = await agent.run(game.activeRunId, 256);
    assert.equal(result.projection.goal.status, "succeeded");
    assert.equal(result.projection.task.phase, "succeeded");
    assert.equal(result.projection.attempts.length, 10);
    assert.ok(result.projection.attempts.every((attempt) => attempt.status === "succeeded"));
    assert.equal(provider.calls, 10);
    assert.equal(game.eventCount(), 25);
    assert.equal(agent.execution.listEffects(game.activeRunId).length, 25);
    assert.equal(agent.execution.listDispatches(game.activeRunId).length, 25);
    assert.ok(agent.execution.listDispatches(game.activeRunId).every((dispatch) => dispatch.status === "succeeded"));
    assert.equal(result.worldDigest, "41d7bfd4c1b36f0a8e38533be7f7e9b48b1625608c76c5ced1ddd3d0952d02d2");
    assert.equal(game.verifyReplay().digest, result.worldDigest);
    agent.host.verifyJournal(game.activeRunId);
    const eventTypes = new Set(agent.host.listJournal(game.activeRunId).map((event) => event.eventType));
    for (const expected of [
      "attempt_activated", "decision_recorded", "effect_proposed", "dispatch_prepared",
      "observation_recorded", "dispatch_succeeded", "effect_succeeded",
      "skill_step_verified", "attempt_succeeded", "task_succeeded",
    ]) assert.ok(eventTypes.has(expected), expected);
  } finally {
    game.close();
    rmSync(directory, { recursive: true, force: true });
  }
});

const faultPoints: HostFaultPoint[] = [
  "after_context_artifact",
  "after_provider_call",
  "after_decision_artifact",
  "after_dispatch_prepare",
  "after_world_apply",
  "after_observation",
  "before_attempt_advance",
];

test("every persisted interruption boundary converges to one world effect history", async () => {
  for (const point of faultPoints) {
    const { directory, game } = fixture();
    try {
      const provider = new CountingProvider();
      let injected = false;
      const crashing = new AgentHost(game, provider, {
        faultInjector(current) {
          if (!injected && current === point) {
            injected = true;
            throw new Error(`injected:${point}`);
          }
        },
      });
      for (let index = 0; index < 128 && !injected; index += 1) {
        try { await crashing.step(); }
        catch (error) { assert.match(String(error), new RegExp(`injected:${point}`)); }
      }
      assert.equal(injected, true, point);
      const eventsAtInterruption = game.eventCount();
      const fresh = new AgentHost(game, provider);
      const result = await fresh.run(game.activeRunId, 256);
      assert.equal(result.projection.task.phase, "succeeded", point);
      assert.equal(game.eventCount(), 25, point);
      assert.equal(new Set(fresh.execution.listEffects(game.activeRunId).map((effect) => effect.commandId)).size, 25, point);
      assert.equal(fresh.execution.listDispatches(game.activeRunId).length, 25, point);
      assert.equal(result.worldDigest, "41d7bfd4c1b36f0a8e38533be7f7e9b48b1625608c76c5ced1ddd3d0952d02d2", point);
      if (point === "after_world_apply") assert.ok(eventsAtInterruption >= 1);
      if (point === "after_provider_call" || point === "after_decision_artifact") assert.ok(provider.calls >= 11);
      fresh.host.verifyJournal(game.activeRunId);
    } finally {
      game.close();
      rmSync(directory, { recursive: true, force: true });
    }
  }
});

test("world change during cognition rejects the stale Decision without a Host Effect", async () => {
  const { directory, game } = fixture();
  try {
    const delegate = new RecoveryOperationProvider();
    const drifting: OperationProvider = {
      providerId: "drifting-provider",
      async decide(context) {
        const state = game.loadState();
        const wait = compileOperationFrontier(state).find((candidate) => candidate.kind === "wait");
        assert.ok(wait);
        const step = compileSkillPlan(state, wait).steps[0];
        assert.ok(step);
        const applied = game.apply(materializeSkillStep(state, step, "manual-drift-during-provider"));
        assert.equal(applied.result.status, "accepted");
        const decision = await delegate.decide(context);
        return { ...decision, providerId: "drifting-provider" };
      },
    };
    const agent = new AgentHost(game, drifting);
    assert.equal((await agent.step()).status, "context_compiled");
    const rejected = await agent.step();
    assert.equal(rejected.status, "decision_rejected");
    assert.equal(agent.projection().task.phase, "ready");
    assert.equal(agent.execution.listEffects(game.activeRunId).length, 0);
    assert.equal(game.eventCount(), 1);
    assert.equal(agent.projection().attempts[0]?.status, "failed");
  } finally {
    game.close();
    rmSync(directory, { recursive: true, force: true });
  }
});

test("technical Provider exhaustion blocks the Task without mutating the world", async () => {
  const { directory, game } = fixture();
  try {
    const failed: OperationProvider = {
      providerId: "failed-provider",
      async decide() { throw new ProviderAdapterError("unavailable", "offline"); },
    };
    const agent = new AgentHost(game, failed);
    await agent.step();
    const blocked = await agent.step();
    assert.equal(blocked.status, "blocked");
    assert.equal(agent.projection().task.phase, "blocked");
    assert.deepEqual(agent.projection().task.blockers, ["provider_unavailable"]);
    assert.equal(game.eventCount(), 0);
    assert.equal(agent.execution.listEffects(game.activeRunId).length, 0);
  } finally {
    game.close();
    rmSync(directory, { recursive: true, force: true });
  }
});

test("a prepared Dispatch observes manual world drift and rejects stale execution exactly once", async () => {
  const { directory, game } = fixture();
  try {
    const agent = new AgentHost(game, new RecoveryOperationProvider());
    assert.equal((await agent.step()).status, "context_compiled");
    assert.equal((await agent.step()).status, "decision_recorded");
    assert.equal((await agent.step()).status, "dispatch_prepared");
    const state = game.loadState();
    const wait = compileOperationFrontier(state).find((candidate) => candidate.kind === "wait");
    assert.ok(wait);
    const step = compileSkillPlan(state, wait).steps[0];
    assert.ok(step);
    game.apply(materializeSkillStep(state, step, "manual-after-dispatch"));
    const rejected = await agent.step();
    assert.equal(rejected.status, "decision_rejected");
    assert.equal(agent.projection().task.phase, "ready");
    assert.equal(agent.execution.listDispatches(game.activeRunId)[0]?.status, "rejected");
    assert.equal(agent.execution.listEffects(game.activeRunId)[0]?.status, "rejected");
    assert.equal(game.eventCount(), 1);
  } finally {
    game.close();
    rmSync(directory, { recursive: true, force: true });
  }
});

test("terminal worlds synchronize Goal and Task without a Provider call", async () => {
  for (const expected of ["victory", "failure"] as const) {
    const { directory, game } = fixture();
    try {
      const provider = new CountingProvider();
      const agent = new AgentHost(game, provider);
      agent.initialize();
      if (expected === "failure") {
        while (game.loadState().mission.status === "running") {
          const state = game.loadState();
          game.apply({ kind: "wait", commandId: `manual-fail:${state.revision}`, actorId: "engineer-01", expectedRevision: state.revision });
        }
      } else {
        const runner = new AgentHost(game, new RecoveryOperationProvider());
        await runner.run();
        const projection = runner.projection();
        assert.equal(projection.task.phase, "succeeded");
        continue;
      }
      const receipt = await agent.step();
      assert.equal(receipt.status, "task_failed");
      assert.equal(agent.projection().goal.status, "failed");
      assert.equal(provider.calls, 0);
    } finally {
      game.close();
      rmSync(directory, { recursive: true, force: true });
    }
  }
});

test("run validates its deterministic step budget", async () => {
  const { directory, game } = fixture();
  try {
    const agent = new AgentHost(game, new RecoveryOperationProvider());
    await assert.rejects(() => agent.run(game.activeRunId, 0), /maximumSteps/);
    const partial = await agent.run(game.activeRunId, 1);
    assert.equal(partial.steps.length, 1);
    assert.equal(partial.projection.task.phase, "active");
    assert.notEqual(partial.worldDigest, sha256({}));
  } finally {
    game.close();
    rmSync(directory, { recursive: true, force: true });
  }
});

test("Effect, Dispatch, and Observation identities are idempotent and conflicting reuse fails closed", async () => {
  const { directory, game } = fixture();
  try {
    const agent = new AgentHost(game, new RecoveryOperationProvider());
    await agent.step();
    await agent.step();
    await agent.step();
    const effect = agent.execution.listEffects(game.activeRunId)[0];
    const dispatch = agent.execution.listDispatches(game.activeRunId)[0];
    assert.ok(effect);
    assert.ok(dispatch);
    assert.deepEqual(agent.execution.putEffect(effect), effect);
    assert.deepEqual(agent.execution.putDispatch(dispatch), dispatch);
    assert.throws(
      () => agent.execution.putEffect({ ...effect, status: "rejected" }),
      /Effect identity is bound to different content/,
    );
    assert.throws(
      () => agent.execution.putDispatch({ ...dispatch, error: "different" }),
      /Dispatch identity is bound to different content/,
    );
    assert.throws(() => agent.execution.getEffect("effect:missing"), /Effect is missing/);
    assert.throws(() => agent.execution.getDispatch("dispatch:missing"), /Dispatch is missing/);

    await agent.step();
    const observation = agent.execution.findObservation(dispatch.dispatchId);
    assert.ok(observation);
    assert.deepEqual(agent.execution.putObservation(observation), observation);
    assert.throws(
      () => agent.execution.putObservation({ ...observation, worldAfterDigest: "different" }),
      /Observation identity is bound to different content/,
    );
  } finally {
    game.close();
    rmSync(directory, { recursive: true, force: true });
  }
});

test("blocked and already synchronized Tasks are stable without additional cognition", async () => {
  const { directory, game } = fixture();
  try {
    const failedProvider: OperationProvider = {
      providerId: "failed-provider",
      async decide() { throw new ProviderAdapterError("unavailable", "offline"); },
    };
    const agent = new AgentHost(game, failedProvider);
    await agent.step();
    await agent.step();
    const stable = await agent.step();
    assert.equal(stable.status, "blocked");
    assert.equal(stable.detail, "Task has no automatic progress");
  } finally {
    game.close();
    rmSync(directory, { recursive: true, force: true });
  }
});
