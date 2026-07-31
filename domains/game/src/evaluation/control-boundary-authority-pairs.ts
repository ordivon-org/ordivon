import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { sha256 } from "../digest.ts";
import type { PrimitiveWorldCommand } from "../model.ts";
import { ENGINEER_ID } from "../scenario.ts";
import { evaluateAuthority, candidateAllowed, authorityTargetId } from "../team/authority.ts";
import type { TeamActionCandidate } from "../team/model.ts";
import { TeamStore, actorTaskId } from "../team/store.ts";
import { GameStore } from "../storage.ts";
import type { BoundaryPairResult } from "./control-boundary-types.ts";
import { result, withTeamGame } from "./control-boundary-fixtures.ts";

export async function authorityPair(): Promise<BoundaryPairResult> {
  return withTeamGame("control-authority", (game) => {
    const team = new TeamStore(game);
    const projection = team.initialize();
    const profile = projection.profiles.find((item) => item.actorId === ENGINEER_ID);
    assert.ok(profile);
    const state = game.loadState();
    const worldDigest = sha256(state);
    const contextDigest = sha256({ kind: "control-authority-context", worldDigest });
    const command: PrimitiveWorldCommand = {
      kind: "set_power",
      commandId: "command:control-authority-life-support-off",
      actorId: ENGINEER_ID,
      expectedRevision: state.revision,
      targetSystemId: "life-support",
      enabled: false,
    };
    const actionCandidateId = "candidate:control-authority";
    const decision = evaluateAuthority(
      game.activeRunId,
      profile,
      ["system-control"],
      actionCandidateId,
      contextDigest,
      worldDigest,
      state,
      command,
      "supervised",
      1,
    );
    team.putAuthorityDecision(decision);
    assert.equal(decision.outcome, "require-human");
    const candidate: TeamActionCandidate = {
      actionCandidateId,
      actionId: "action:control-authority",
      label: "Disable life support",
      actorId: ENGINEER_ID,
      worldDigest,
      worldRevision: state.revision,
      command,
      objectiveIds: ["verified-rescue"],
      authorityOutcome: decision.outcome,
      authorityDecisionId: decision.decisionId,
    };
    const hold = result(false, candidateAllowed(candidate, false), "pre-commit", "missing-authority-held", {
      authorityChecks: 1,
      taskState: team.getTask(actorTaskId(game.activeRunId, ENGINEER_ID)).state,
      details: { authorityOutcome: decision.outcome },
    });
    const proposalId = "proposal:control-authority";
    const grant = team.issueGrant({
      actorId: ENGINEER_ID,
      proposalId,
      actionCandidateId,
      contextDigest,
      worldDigest,
      policyRevision: decision.policyRevision,
      operationKind: command.kind,
      targetId: authorityTargetId(command),
      expiresAtTick: state.turn + 1,
      issuedBy: "operator:control-boundary",
    });
    const consumed = team.consumeGrant(grant.grantId, proposalId, contextDigest, worldDigest, state.turn);
    const exact =
      consumed.actionCandidateId === actionCandidateId
      && consumed.operationKind === command.kind
      && consumed.targetId === authorityTargetId(command)
      && consumed.consumedAtTick === state.turn;
    const act = result(true, candidateAllowed(candidate, exact), "pre-commit", "exact-authority-admitted", {
      authorityChecks: 1,
      operatorInterventions: 1,
      taskState: team.getTask(actorTaskId(game.activeRunId, ENGINEER_ID)).state,
      details: { authorityOutcome: decision.outcome, grantConsumed: exact },
    });
    return {
      id: "authority-binding",
      changedCondition: "missing human grant versus exact current single-use grant",
      act,
      hold,
    };
  });
}

export async function staleLeasePair(): Promise<BoundaryPairResult> {
  const directory = mkdtempSync(join(tmpdir(), "control-lease-reopen-"));
  const database = join(directory, "game.sqlite3");
  const runId = "run:control-lease";
  let first: GameStore | undefined;
  let reopened: GameStore | undefined;
  try {
    first = new GameStore(database);
    first.createRun({ runId, scenarioVersion: 2, rulesetVersion: 3 });
    first.setActiveRun(runId);
    const initialTeam = new TeamStore(first);
    initialTeam.initialize();
    const taskId = actorTaskId(runId, ENGINEER_ID);
    const currentLease = initialTeam.acquireLease(taskId, "worker:current", 1_000, 100);
    initialTeam.releaseLease(currentLease);
    const act = result(true, true, "pre-commit", "current-worker-lease-admitted", {
      taskState: initialTeam.getTask(taskId).state,
      details: { leaseRevision: currentLease.revision, hostReopened: false },
    });
    const staleLease = initialTeam.acquireLease(taskId, "worker:stale", 2_000, 100);
    first.close();
    first = undefined;

    reopened = new GameStore(database, { activeRunId: runId });
    const freshTeam = new TeamStore(reopened);
    const restored = freshTeam.projection();
    assert.equal(restored.goal.runId, runId);
    const replacement = freshTeam.acquireLease(taskId, "worker:replacement", 2_200, 100);
    let staleAccepted = false;
    try {
      freshTeam.releaseLease(staleLease);
      staleAccepted = true;
    } catch (error) {
      assert.match(String(error), /lease identity no longer matches/);
    }
    freshTeam.releaseLease(replacement);
    const hold = result(false, staleAccepted, "pre-commit", "stale-worker-held-after-host-reopen", {
      taskState: freshTeam.getTask(taskId).state,
      details: {
        staleRevision: staleLease.revision,
        replacementRevision: replacement.revision,
        hostReopened: true,
        restoredTaskCount: restored.tasks.length,
      },
    });
    return {
      id: "stale-worker-lease",
      changedCondition: "current lease versus stale result after closing and reopening the persisted Host/Game authority",
      act,
      hold,
    };
  } finally {
    first?.close();
    reopened?.close();
    rmSync(directory, { recursive: true, force: true });
  }
}

export async function waitTerminalPair(): Promise<BoundaryPairResult> {
  const act = await withTeamGame("control-recoverable-wait", (game) => {
    const team = new TeamStore(game);
    team.initialize();
    const taskId = actorTaskId(game.activeRunId, ENGINEER_ID);
    const waiting = team.setWait(taskId, {
      kind: "provider",
      subjectId: "provider:temporary",
      reason: "temporary provider unavailable",
      sinceTick: game.loadState().turn,
    });
    const ready = team.setWait(taskId, null);
    return result(true, ready.state === "ready", "terminal", "recoverable-wait-resumed", {
      taskState: ready.state,
      details: { waitingRevision: waiting.revision, readyRevision: ready.revision },
    });
  });

  const hold = await withTeamGame("control-terminal-task", (game) => {
    const team = new TeamStore(game);
    team.initialize();
    const taskId = actorTaskId(game.activeRunId, ENGINEER_ID);
    let sequence = 0;
    while (game.loadState().mission.status === "running") {
      const state = game.loadState();
      const command: PrimitiveWorldCommand = {
        kind: "wait",
        commandId: `command:control-terminal-wait:${sequence}`,
        actorId: ENGINEER_ID,
        expectedRevision: state.revision,
      };
      const applied = game.applyTeamTick({
        tickId: `tick:control-terminal:${sequence}`,
        expectedWorldRevision: state.revision,
        intents: [{ commandSequence: sequence, command }],
      });
      assert.equal(applied.result.status, "accepted");
      sequence += 1;
    }
    const synchronized = team.synchronizeTerminal();
    const failed = synchronized.tasks.find((item) => item.taskId === taskId);
    assert.equal(failed?.state, "failed");
    let reopened = false;
    try {
      reopened = team.setWait(taskId, null).state === "ready";
    } catch (error) {
      assert.match(String(error), /terminal Team Task cannot transition/);
    }
    return result(false, reopened, "terminal", "terminal-task-held", {
      worldEvents: game.eventCount(),
      taskState: team.getTask(taskId).state,
      details: { missionStatus: game.loadState().mission.status, ticks: sequence },
    });
  });

  return {
    id: "recoverable-versus-terminal",
    changedCondition: "temporary wait cleared versus mission-terminal failed Task",
    act,
    hold,
  };
}
