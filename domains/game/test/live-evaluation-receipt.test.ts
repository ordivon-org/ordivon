import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import {
  captureLiveEvaluationReceipt,
  readLiveEvaluationReceipt,
  writeLiveEvaluationReceipt,
  type LiveEvaluationSpec,
} from "../src/evaluation/live-receipt.ts";
import { AgentHost } from "../src/host/engine.ts";
import { RecoveryOperationProvider } from "../src/providers/fixture.ts";
import { GameStore } from "../src/storage.ts";

test("partial live receipt binds provider-pending recovery without duplicate Effects", async () => {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-live-receipt-"));
  const databasePath = join(directory, "world.sqlite3");
  const partialPath = join(directory, "partial.json");
  const finalPath = join(directory, "final.json");
  const startedAt = new Date(0).toISOString();
  const spec = (recoveryOfReceiptDigest: string | null): LiveEvaluationSpec => ({
    evaluationId: "evaluation:test:timeout-recovery",
    mode: "fixture",
    sourceRevision: "test-revision",
    startedAt,
    wallClockLimitMs: 100,
    maximumSteps: 256,
    databasePath,
    databaseRetained: true,
    recoveryOfReceiptDigest,
  });
  try {
    const game = new GameStore(databasePath);
    const first = new AgentHost(game, new RecoveryOperationProvider());
    let hostStepCount = 0;
    for (;;) {
      const receipt = await first.step();
      hostStepCount += 1;
      const projection = first.projection();
      if (
        projection.task.completedAttemptIds.length === 1 &&
        projection.attempts.find((attempt) => attempt.attemptId === projection.task.activeAttemptId)?.status === "provider_pending"
      ) break;
      assert.ok(hostStepCount < 80, "fixture did not reach the second provider-pending Attempt");
    }
    const partial = captureLiveEvaluationReceipt({
      phase: "partial",
      spec: spec(null),
      game,
      agent: first,
      providerCalls: [{ status: "interrupted", code: "evaluation_timeout" }],
      hostStepCount,
      termination: {
        kind: "evaluation_timeout",
        reason: "wall-clock limit reached",
        errorName: "LiveEvaluationInterruption",
      },
      now: new Date(100),
    });
    const partialEnvelope = writeLiveEvaluationReceipt(partialPath, partial);
    assert.equal(partial.run.activeAttemptStatus, "provider_pending");
    assert.equal(partial.run.completedAttemptCount, 1);
    assert.ok(partial.authority.effectCount > 0);
    assert.equal(partial.authority.effectCount, partial.authority.dispatchCount);
    assert.equal(partial.authority.dispatchCount, partial.authority.observationCount);
    assert.equal(partial.replay.digest, partial.world.digest);
    assert.equal(readLiveEvaluationReceipt(partialPath).receiptDigest, partialEnvelope.receiptDigest);
    const beforeEffectIds = new Set(first.authority.listEffects(game.activeRunId).map((entry) => entry.effectId));
    game.close();

    const recoveredGame = new GameStore(databasePath);
    const recovered = new AgentHost(recoveredGame, new RecoveryOperationProvider());
    const run = await recovered.run(recoveredGame.activeRunId, 256);
    assert.equal(run.projection.task.phase, "succeeded");
    const final = captureLiveEvaluationReceipt({
      phase: "completed",
      spec: spec(partialEnvelope.receiptDigest),
      game: recoveredGame,
      agent: recovered,
      providerCalls: [],
      hostStepCount: run.steps.length,
      termination: { kind: "domain_terminal", reason: "rescue_signal_verified" },
      now: new Date(200),
    });
    const finalEnvelope = writeLiveEvaluationReceipt(finalPath, final);
    assert.equal(final.evaluation.recoveryOfReceiptDigest, partialEnvelope.receiptDigest);
    assert.equal(final.world.missionStatus, "victory");
    assert.equal(final.replay.digest, final.world.digest);
    const finalEffects = recovered.authority.listEffects(recoveredGame.activeRunId);
    assert.equal(new Set(finalEffects.map((entry) => entry.effectId)).size, finalEffects.length);
    assert.ok([...beforeEffectIds].every((effectId) => finalEffects.some((entry) => entry.effectId === effectId)));
    assert.equal(readLiveEvaluationReceipt(finalPath).receiptDigest, finalEnvelope.receiptDigest);
    recoveredGame.close();
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});
