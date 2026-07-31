import assert from "node:assert/strict";

import type { TaskOutcome } from "../host-contract/model.ts";
import type { BoundaryPairResult } from "./control-boundary-types.ts";
import { completionFixture, result, withGame } from "./control-boundary-fixtures.ts";

export async function falseCompletionPair(): Promise<BoundaryPairResult> {
  const act = await withGame("control-accepted-completion", (game) => {
    const fixture = completionFixture(game, "accepted", true);
    const verified = fixture.authority.recordVerification(fixture.runId, fixture.taskId, fixture.verification);
    const outcome: TaskOutcome = {
      schemaVersion: 1,
      kind: "ordivon.task-outcome",
      taskId: fixture.taskId,
      goalId: fixture.goalId,
      status: "completed",
      verificationDigest: verified.verificationDigest,
      artifactRefs: fixture.observation.evidenceRefs,
    };
    const completed = fixture.authority.complete(fixture.runId, fixture.taskId, outcome);
    return result(true, completed.state === "completed", "post-commit", "accepted-verification-completed", {
      worldEvents: fixture.worldEvents,
      hostEffects: fixture.authority.listEffects(fixture.runId).length,
      taskState: completed.state,
      details: { verificationAccepted: true },
    });
  });

  const hold = await withGame("control-false-completion", (game) => {
    const fixture = completionFixture(game, "rejected", false);
    const verified = fixture.authority.recordVerification(fixture.runId, fixture.taskId, fixture.verification);
    let falseCompletionAccepted = false;
    try {
      fixture.authority.complete(fixture.runId, fixture.taskId, {
        schemaVersion: 1,
        kind: "ordivon.task-outcome",
        taskId: fixture.taskId,
        goalId: fixture.goalId,
        status: "completed",
        verificationDigest: verified.verificationDigest,
        artifactRefs: fixture.observation.evidenceRefs,
      });
      falseCompletionAccepted = true;
    } catch (error) {
      assert.match(String(error), /requires an accepted VerificationReceipt/);
    }
    const failed = fixture.authority.complete(fixture.runId, fixture.taskId, {
      schemaVersion: 1,
      kind: "ordivon.task-outcome",
      taskId: fixture.taskId,
      goalId: fixture.goalId,
      status: "failed",
      verificationDigest: verified.verificationDigest,
      artifactRefs: fixture.observation.evidenceRefs,
    });
    return result(false, falseCompletionAccepted, "post-commit", "false-completion-refused", {
      worldEvents: fixture.worldEvents,
      hostEffects: fixture.authority.listEffects(fixture.runId).length,
      taskState: failed.state,
      details: { verificationAccepted: false, worldTickAlreadyCommitted: fixture.worldEvents === 1 },
    });
  });

  return {
    id: "false-completion",
    changedCondition: "accepted independent verification versus rejected verification after a committed World Tick",
    act,
    hold,
  };
}

export async function evidencePair(): Promise<BoundaryPairResult> {
  const act = await withGame("control-evidence-present", (game) => {
    const fixture = completionFixture(game, "evidence-present", true);
    const verified = fixture.authority.recordVerification(fixture.runId, fixture.taskId, fixture.verification);
    const completed = fixture.authority.complete(fixture.runId, fixture.taskId, {
      schemaVersion: 1,
      kind: "ordivon.task-outcome",
      taskId: fixture.taskId,
      goalId: fixture.goalId,
      status: "completed",
      verificationDigest: verified.verificationDigest,
      artifactRefs: fixture.observation.evidenceRefs,
    });
    return result(true, completed.state === "completed", "post-commit", "required-evidence-present", {
      worldEvents: fixture.worldEvents,
      hostEffects: fixture.authority.listEffects(fixture.runId).length,
      taskState: completed.state,
      details: { evidenceRefs: fixture.observation.evidenceRefs.length },
    });
  });

  const hold = await withGame("control-evidence-absent", (game) => {
    const fixture = completionFixture(game, "evidence-absent", true);
    let completed = false;
    try {
      fixture.authority.complete(fixture.runId, fixture.taskId, {
        schemaVersion: 1,
        kind: "ordivon.task-outcome",
        taskId: fixture.taskId,
        goalId: fixture.goalId,
        status: "completed",
        verificationDigest: null,
        artifactRefs: [],
      });
      completed = true;
    } catch (error) {
      assert.match(String(error), /missing ordivon.verification-receipt/);
    }
    return result(false, completed, "post-commit", "missing-verification-held", {
      worldEvents: fixture.worldEvents,
      hostEffects: fixture.authority.listEffects(fixture.runId).length,
      taskState: fixture.authority.projection(fixture.runId, fixture.taskId).state,
      details: { evidenceRefs: fixture.observation.evidenceRefs.length, verificationRecorded: false },
    });
  });

  return {
    id: "required-evidence",
    changedCondition: "required VerificationReceipt present versus absent",
    act,
    hold,
  };
}
