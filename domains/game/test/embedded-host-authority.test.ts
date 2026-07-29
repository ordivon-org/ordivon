import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import { EmbeddedHostAuthority } from "../src/host-contract/embedded-authority.ts";
import { GameWorldExecutor } from "../src/host-contract/game-world-executor.ts";
import { protocolDigest, type ProtocolJson } from "../src/host-contract/canonical.ts";
import type { DispatchEnvelope, ObservationEnvelope, TaskDescriptor, TaskOutcome, VerificationReceipt } from "../src/host-contract/model.ts";
import { GameStore } from "../src/storage.ts";
import { listAvailableActions, materializeAction } from "../src/world.ts";

function sha(value: string): `sha256:${string}` {
  return value.startsWith("sha256:") ? value as `sha256:${string}` : `sha256:${value}`;
}

test("embedded authority owns one Task lifecycle while Game owns one recovered World Event", () => {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-game-embedded-host-"));
  const database = join(directory, "world.sqlite3");
  const runId = "run:embedded-authority";
  const taskId = "task:embedded-authority:r0";
  const goalId = "goal:embedded-authority";
  try {
    let game = new GameStore(database);
    game.createRun({ runId, scenarioVersion: 2, rulesetVersion: 3 });
    game.setActiveRun(runId);
    const before = game.verifyReplay(runId);
    const action = listAvailableActions(before.state)[0];
    assert.ok(action);
    const command = materializeAction(action, "command:embedded-authority:r0");
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
      workloadId: "ordivon.game.actor-turn.v1",
      assigneeRef: `actor:${command.actorId}`,
      providerPolicyRef: "provider-policy:fixture",
      domainRef: `game-run:${runId}`,
      configurationDigests: [protocolDigest({ runId, actorId: command.actorId })],
    };
    const effect = {
      schemaVersion: 1,
      kind: "ordivon.game.world-effect",
      effectId: "effect:embedded-authority:r0",
      runId,
      commandId: command.commandId,
    } satisfies ProtocolJson;
    const dispatch: DispatchEnvelope = {
      schemaVersion: 1,
      kind: "ordivon.dispatch-envelope",
      dispatchId: "dispatch:embedded-authority:r0",
      effectId: "effect:embedded-authority:r0",
      executorId: "executor:game-world-v1",
      requestDigest: protocolDigest(request),
      idempotencyKey: command.commandId,
      requiredStateRefs: [{ ref: `game-world:${runId}`, digest: sha(before.digest) }],
      expectedObservationKind: "ordivon.game.world-event-observation.v1",
    };
    const authority = new EmbeddedHostAuthority(game);
    assert.equal(authority.ensureTask(runId, descriptor).revision, 1);
    assert.equal(authority.prepare(runId, taskId, effect, request as Record<string, ProtocolJson>, dispatch).revision, 2);

    const crashing = new GameWorldExecutor(game, {
      faultInjector() { throw new Error("injected:after_world_commit"); },
    });
    assert.throws(() => crashing.deliverCommand(command, runId), /injected:after_world_commit/);
    assert.equal(game.eventCount(runId), 1);
    game.close();

    game = new GameStore(database, { activeRunId: runId });
    const freshAuthority = new EmbeddedHostAuthority(game);
    assert.equal(freshAuthority.projection(runId, taskId).state, "reconciling");
    const recovered = new GameWorldExecutor(game).observeCommand(command, runId);
    assert.ok(recovered);
    const payload = {
      schemaVersion: 1,
      kind: "ordivon.game.world-event-observation.v1",
      runId,
      commandId: command.commandId,
      commandSequence: recovered.commandSequence,
      worldEventId: recovered.worldEventId,
      worldAfterDigest: sha(recovered.worldAfterDigest!),
    } satisfies ProtocolJson;
    const observation: ObservationEnvelope = {
      schemaVersion: 1,
      kind: "ordivon.observation-envelope",
      dispatchId: dispatch.dispatchId,
      executorId: dispatch.executorId,
      status: "succeeded",
      payloadDigest: protocolDigest(payload),
      evidenceRefs: [{ ref: recovered.worldEventId!, kind: "game-world-event", digest: protocolDigest(payload) }],
    };
    assert.throws(
      () => freshAuthority.recordObservation(runId, taskId, { ...observation, dispatchId: "dispatch:wrong" }),
      /not bound to the prepared Dispatch/,
    );
    assert.throws(
      () => freshAuthority.recordObservation(runId, taskId, { ...observation, executorId: "executor:wrong" }),
      /not bound to the prepared Dispatch/,
    );
    assert.equal(freshAuthority.recordObservation(runId, taskId, observation).revision, 3);
    assert.equal(freshAuthority.recordObservation(runId, taskId, observation).revision, 3);
    const verification: VerificationReceipt = {
      schemaVersion: 1,
      kind: "ordivon.verification-receipt",
      dispatchId: dispatch.dispatchId,
      method: "game-world-event.v1",
      accepted: recovered.verificationSuccess,
      observationDigest: protocolDigest(observation),
      resultItems: [{
        subjectRef: taskId,
        decisionDigest: protocolDigest(command),
        status: "succeeded",
        reason: null,
        evidenceDigest: observation.payloadDigest,
      }],
    };
    assert.throws(
      () => freshAuthority.recordVerification(runId, taskId, { ...verification, dispatchId: "dispatch:wrong" }),
      /targets another Dispatch/,
    );
    assert.throws(
      () => freshAuthority.recordVerification(
        runId, taskId, { ...verification, observationDigest: `sha256:${"0".repeat(64)}` },
      ),
      /targets another Observation/,
    );
    const verified = freshAuthority.recordVerification(runId, taskId, verification);
    assert.equal(verified.revision, 4);
    const outcome: TaskOutcome = {
      schemaVersion: 1,
      kind: "ordivon.task-outcome",
      taskId,
      goalId,
      status: "completed",
      verificationDigest: verified.verificationDigest,
      artifactRefs: [],
    };
    assert.throws(
      () => freshAuthority.complete(runId, taskId, { ...outcome, goalId: "goal:wrong" }),
      /another Task or Goal/,
    );
    assert.throws(
      () => freshAuthority.complete(
        runId, taskId, { ...outcome, verificationDigest: `sha256:${"0".repeat(64)}` },
      ),
      /another VerificationReceipt/,
    );
    assert.equal(freshAuthority.complete(runId, taskId, outcome).state, "completed");
    assert.equal(freshAuthority.complete(runId, taskId, outcome).revision, 5);
    freshAuthority.verify(runId);
    assert.equal(game.eventCount(runId), 1);
    assert.equal(freshAuthority.contracts.transcript(runId).length, 5);
    assert.equal(game.db.prepare("SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?").get("host_goals"), undefined);
    assert.equal(game.db.prepare("SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?").get("host_tasks"), undefined);
    assert.equal(game.db.prepare("SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?").get("host_attempts"), undefined);
    game.close();
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});
