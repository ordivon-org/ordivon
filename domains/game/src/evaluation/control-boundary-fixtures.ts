import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { EmbeddedHostAuthority } from "../host-contract/embedded-authority.ts";
import { GameWorldExecutor } from "../host-contract/game-world-executor.ts";
import { protocolDigest, type ProtocolJson } from "../host-contract/canonical.ts";
import type {
  DispatchEnvelope,
  ObservationEnvelope,
  TaskDescriptor,
  VerificationReceipt,
} from "../host-contract/model.ts";
import { GameStore } from "../storage.ts";
import { listAvailableActions, materializeAction } from "../world.ts";
import type { BoundaryArmResult, BoundaryPhase } from "./control-boundary-types.ts";

export function result(
  shouldAct: boolean,
  acted: boolean,
  phase: BoundaryPhase,
  reasonCode: string,
  values: Partial<Omit<BoundaryArmResult, "shouldAct" | "acted" | "correct" | "phase" | "reasonCode">> = {},
): BoundaryArmResult {
  return {
    shouldAct,
    acted,
    correct: shouldAct === acted,
    phase,
    reasonCode,
    worldEvents: values.worldEvents ?? 0,
    hostEffects: values.hostEffects ?? 0,
    duplicateEffects: values.duplicateEffects ?? 0,
    modelCalls: values.modelCalls ?? 0,
    authorityChecks: values.authorityChecks ?? 0,
    operatorInterventions: values.operatorInterventions ?? 0,
    taskState: values.taskState ?? "unknown",
    details: values.details ?? {},
  };
}

export async function withGame<T>(
  prefix: string,
  operation: (game: GameStore) => Promise<T> | T,
): Promise<T> {
  const directory = mkdtempSync(join(tmpdir(), `${prefix}-`));
  const game = new GameStore(join(directory, "game.sqlite3"));
  try {
    return await operation(game);
  } finally {
    game.close();
    rmSync(directory, { recursive: true, force: true });
  }
}

export async function withTeamGame<T>(
  prefix: string,
  operation: (game: GameStore) => Promise<T> | T,
): Promise<T> {
  return withGame(prefix, async (game) => {
    const runId = `run:${prefix}`;
    game.createRun({ runId, scenarioVersion: 2, rulesetVersion: 3 });
    game.setActiveRun(runId);
    return await operation(game);
  });
}

function sha(value: string): `sha256:${string}` {
  return value.startsWith("sha256:") ? value as `sha256:${string}` : `sha256:${value}`;
}

export interface CompletionFixture {
  authority: EmbeddedHostAuthority;
  runId: string;
  taskId: string;
  goalId: string;
  dispatch: DispatchEnvelope;
  observation: ObservationEnvelope;
  verification: VerificationReceipt;
  worldEvents: number;
}

export function completionFixture(
  game: GameStore,
  suffix: string,
  accepted: boolean,
): CompletionFixture {
  const runId = game.activeRunId;
  const taskId = `task:control-completion:${suffix}`;
  const goalId = `goal:control-completion:${suffix}`;
  const before = game.verifyReplay(runId);
  const action = listAvailableActions(before.state)[0];
  assert.ok(action);
  const command = materializeAction(action, `command:control-completion:${suffix}`);
  const request = {
    schemaVersion: 1,
    kind: "ordivon.game.world-command-request",
    runId,
    commandId: command.commandId,
    command: command as unknown as ProtocolJson,
  } satisfies ProtocolJson;
  const descriptor: TaskDescriptor = {
    schemaVersion: 1,
    kind: "ordivon.host-task-descriptor",
    taskId,
    goalId,
    workloadId: "ordivon.game.control-boundary.v1",
    assigneeRef: `actor:${command.actorId}`,
    providerPolicyRef: "provider-policy:fixture",
    domainRef: `game-run:${runId}`,
    configurationDigests: [protocolDigest({ runId, suffix })],
  };
  const effect = {
    schemaVersion: 1,
    kind: "ordivon.game.world-effect",
    effectId: `effect:control-completion:${suffix}`,
    runId,
    commandId: command.commandId,
  } satisfies ProtocolJson;
  const dispatch: DispatchEnvelope = {
    schemaVersion: 1,
    kind: "ordivon.dispatch-envelope",
    dispatchId: `dispatch:control-completion:${suffix}`,
    effectId: String(effect.effectId),
    executorId: "executor:game-world-v1",
    requestDigest: protocolDigest(request),
    idempotencyKey: command.commandId,
    requiredStateRefs: [{ ref: `game-world:${runId}`, digest: sha(before.digest) }],
    expectedObservationKind: "ordivon.game.world-event-observation.v1",
  };
  const authority = new EmbeddedHostAuthority(game);
  authority.ensureTask(runId, descriptor);
  authority.prepare(runId, taskId, effect, request as Record<string, ProtocolJson>, dispatch);
  const world = new GameWorldExecutor(game).deliverCommand(command, runId);
  assert.equal(world.status, "succeeded");
  const payload = {
    schemaVersion: 1,
    kind: "ordivon.game.world-event-observation.v1",
    runId,
    commandId: command.commandId,
    commandSequence: world.commandSequence,
    worldEventId: world.worldEventId,
    worldAfterDigest: sha(world.worldAfterDigest!),
  } satisfies ProtocolJson;
  const observation: ObservationEnvelope = {
    schemaVersion: 1,
    kind: "ordivon.observation-envelope",
    dispatchId: dispatch.dispatchId,
    executorId: dispatch.executorId,
    status: "succeeded",
    payloadDigest: protocolDigest(payload),
    evidenceRefs: [{ ref: world.worldEventId!, kind: "game-world-event", digest: protocolDigest(payload) }],
  };
  authority.recordObservation(runId, taskId, observation);
  const verification: VerificationReceipt = {
    schemaVersion: 1,
    kind: "ordivon.verification-receipt",
    dispatchId: dispatch.dispatchId,
    method: "control-boundary-independent.v1",
    accepted,
    observationDigest: protocolDigest(observation),
    resultItems: [{
      subjectRef: taskId,
      decisionDigest: protocolDigest({ accepted, suffix }),
      status: accepted ? "succeeded" : "failed",
      reason: accepted ? null : "independent acceptance rejected the completion claim",
      evidenceDigest: observation.payloadDigest,
    }],
  };
  return {
    authority,
    runId,
    taskId,
    goalId,
    dispatch,
    observation,
    verification,
    worldEvents: game.eventCount(runId),
  };
}
