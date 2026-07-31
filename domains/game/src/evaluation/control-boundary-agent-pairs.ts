import assert from "node:assert/strict";

import { sha256 } from "../digest.ts";
import { AgentHost } from "../host/engine.ts";
import type { CompiledAgentContext } from "../host/context.ts";
import { ENGINEER_ID } from "../scenario.ts";
import { RecoveryOperationProvider } from "../providers/fixture.ts";
import type { OperationDecision, OperationProvider } from "../providers/types.ts";
import type { GameStore } from "../storage.ts";
import type { BoundaryPairResult } from "./control-boundary-types.ts";
import { result, withGame } from "./control-boundary-fixtures.ts";

class CountingRecoveryProvider extends RecoveryOperationProvider {
  calls = 0;

  override async decide(context: CompiledAgentContext): Promise<OperationDecision> {
    this.calls += 1;
    return await super.decide(context);
  }
}

async function runUntilWorldEvent(agent: AgentHost, game: GameStore, maximumSteps = 12): Promise<number> {
  let steps = 0;
  while (game.eventCount() === 0 && steps < maximumSteps) {
    await agent.step();
    steps += 1;
  }
  return steps;
}

export async function staleContextPair(): Promise<BoundaryPairResult> {
  const current = await withGame("control-current-context", async (game) => {
    const provider = new CountingRecoveryProvider();
    const agent = new AgentHost(game, provider);
    const steps = await runUntilWorldEvent(agent, game);
    return result(true, game.eventCount() === 1, "pre-commit", "current-context-admitted", {
      worldEvents: game.eventCount(),
      hostEffects: agent.authority.listEffects(game.activeRunId).length,
      modelCalls: provider.calls,
      taskState: agent.projection().task.phase,
      details: { hostSteps: steps },
    });
  });

  const stale = await withGame("control-stale-context", async (game) => {
    class DriftingProvider implements OperationProvider {
      readonly providerId = "fixture:drifting-context";
      calls = 0;

      async decide(context: CompiledAgentContext): Promise<OperationDecision> {
        this.calls += 1;
        const state = game.loadState();
        const applied = game.apply({
          kind: "wait",
          commandId: "command:control-context-drift",
          actorId: ENGINEER_ID,
          expectedRevision: state.revision,
        });
        assert.equal(applied.result.status, "accepted");
        return {
          providerId: this.providerId,
          contextId: context.contextId,
          selectedOperationCandidateId: context.payload.allowedOperations[0]?.operationCandidateId ?? null,
          riskLevel: "low",
          confidence: 1,
          rationale: "decision intentionally returned after World drift",
        };
      }
    }

    const provider = new DriftingProvider();
    const agent = new AgentHost(game, provider);
    await agent.step();
    const rejected = await agent.step();
    const effects = agent.authority.listEffects(game.activeRunId);
    return result(false, effects.length > 0, "pre-commit", "stale-context-held", {
      worldEvents: game.eventCount(),
      hostEffects: effects.length,
      modelCalls: provider.calls,
      taskState: agent.projection().task.phase,
      details: { hostStatus: rejected.status, externalDriftEvents: game.eventCount() },
    });
  });

  return {
    id: "stale-context",
    changedCondition: "current World/Context revision versus World mutation during model invocation",
    act: current,
    hold: stale,
  };
}

export async function preconditionPair(): Promise<BoundaryPairResult> {
  const current = await withGame("control-current-precondition", async (game) => {
    const provider = new CountingRecoveryProvider();
    const agent = new AgentHost(game, provider);
    const steps = await runUntilWorldEvent(agent, game);
    return result(true, game.eventCount() === 1, "pre-commit", "current-precondition-committed", {
      worldEvents: game.eventCount(),
      hostEffects: agent.authority.listEffects(game.activeRunId).length,
      modelCalls: provider.calls,
      taskState: agent.projection().task.phase,
      details: { hostSteps: steps },
    });
  });

  const stale = await withGame("control-stale-precondition", async (game) => {
    const provider = new CountingRecoveryProvider();
    const agent = new AgentHost(game, provider);
    let steps = 0;
    while (agent.authority.listDispatches(game.activeRunId).length === 0 && steps < 8) {
      await agent.step();
      steps += 1;
    }
    assert.equal(agent.authority.listDispatches(game.activeRunId).length, 1);
    assert.equal(game.eventCount(), 0);
    const before = game.loadState();
    const applied = game.apply({
      kind: "wait",
      commandId: "command:control-precondition-drift",
      actorId: ENGINEER_ID,
      expectedRevision: before.revision,
    });
    assert.equal(applied.result.status, "accepted");
    const rejected = await agent.step();
    const observations = agent.authority.listObservations(game.activeRunId);
    const successfulAgentObservation = observations.some((item) => item.status === "succeeded");
    return result(false, successfulAgentObservation, "pre-commit", "stale-precondition-held", {
      worldEvents: game.eventCount(),
      hostEffects: agent.authority.listEffects(game.activeRunId).length,
      modelCalls: provider.calls,
      taskState: agent.projection().task.phase,
      details: {
        hostStatus: rejected.status,
        hostStepsBeforeDrift: steps,
        observationStatus: observations.at(-1)?.status ?? null,
        worldDigestAfterDrift: sha256(game.loadState()),
      },
    });
  });

  return {
    id: "commit-precondition",
    changedCondition: "current required World revision versus revision changed after Dispatch preparation",
    act: current,
    hold: stale,
  };
}
