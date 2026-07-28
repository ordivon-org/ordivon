import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import { GameStore } from "../src/storage.ts";
import { TeamHost } from "../src/team/engine.ts";
import { FixtureTeamProvider } from "../src/team/providers.ts";
import { MEDIC_ID, SECURITY_ID } from "../src/scenario.ts";

function fixture(runId: string) {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-m4-control-"));
  const dbPath = join(directory, "world.sqlite3");
  const game = new GameStore(dbPath, { activeRunId: runId });
  if (game.getRun(runId).scenarioVersion !== 2) {
    game.createRun({ runId, scenarioVersion: 2, rulesetVersion: 3 });
    game.setActiveRun(runId);
  }
  return { directory, dbPath, game };
}

function setControl(host: TeamHost, actorId: string, mode: "active" | "paused" | "cancelled") {
  const task = host.team.listTasks().find((candidate) => candidate.actorId === actorId);
  assert.ok(task);
  const tick = host.game.loadState().turn;
  return host.team.transitionTask(task.taskId, {
    state: mode === "active" ? "ready" : mode === "paused" ? "waiting" : "cancelled",
    control: { mode, reason: mode === "active" ? null : `test ${mode}`, issuedBy: "player:test", issuedAtTick: tick },
    preparedContextDigest: null,
    admittedProposalId: null,
    wait: mode === "paused" ? { kind: "replan", subjectId: "player:test", reason: "test paused", sinceTick: tick } : null,
  }, `team.task-test-${mode}`);
}

test("paused and cancelled Actors remain outside TeamHost eligibility until explicit resume", async () => {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-m4-control-"));
  const dbPath = join(directory, "world.sqlite3");
  const game = new GameStore(dbPath);
  try {
    const runId = "run:m4-control";
    game.createRun({ runId, scenarioVersion: 2, rulesetVersion: 3 });
    game.setActiveRun(runId);
    const host = new TeamHost(game, new FixtureTeamProvider());
    host.initialize(runId);

    setControl(host, MEDIC_ID, "paused");
    setControl(host, SECURITY_ID, "cancelled");
    assert.equal((await host.step(runId)).status, "initialized");
    assert.equal((await host.step(runId)).status, "contexts_prepared");
    const firstRound = host.execution.listRounds(runId)[0]!;
    const actorIds = host.execution.listContexts(firstRound.roundId).map((entry) => entry.actorId);
    assert.deepEqual(actorIds, ["engineer-01"]);
    assert.equal(host.team.listTasks(runId).find((task) => task.actorId === MEDIC_ID)?.control.mode, "paused");
    assert.equal(host.team.listTasks(runId).find((task) => task.actorId === SECURITY_ID)?.control.mode, "cancelled");

    setControl(host, MEDIC_ID, "active");
    assert.equal((await host.step(runId)).status, "contexts_prepared");
    const resumedActorIds = host.execution.listContexts(firstRound.roundId).map((entry) => entry.actorId);
    assert.deepEqual(resumedActorIds, ["engineer-01", "medic-01"]);
    assert.ok(!resumedActorIds.includes(SECURITY_ID));
  } finally {
    game.close();
    rmSync(directory, { recursive: true, force: true });
  }
});

test("rejected Proposals are excluded from legal subset selection", async () => {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-m4-deny-"));
  const game = new GameStore(join(directory, "world.sqlite3"));
  try {
    const runId = "run:m4-deny";
    game.createRun({ runId, scenarioVersion: 2, rulesetVersion: 3 });
    game.setActiveRun(runId);
    const host = new TeamHost(game, new FixtureTeamProvider(), { policyMode: "supervised" });
    const blocked = await host.run(runId, 128);
    assert.equal(blocked.steps.at(-1)?.status, "authority_required");
    const round = blocked.rounds.at(-1)!;
    const pending = host.execution.listProposals(round.roundId).find((proposal) => proposal.status === "proposed" && proposal.authorityOutcome === "require-human");
    assert.ok(pending);
    host.execution.saveProposal({ ...pending, status: "rejected", rejectionReason: "player_denied", updatedAt: new Date().toISOString() }, "team.proposal-player-denied");
    const next = await host.step(runId);
    assert.ok(["tick_plan_prepared", "authority_required", "blocked"].includes(next.status));
    const retained = host.execution.getProposal(pending.proposalId);
    assert.equal(retained.status, "rejected");
    const latest = host.execution.listRounds(runId).at(-1)!;
    if (latest.tickPlanId) {
      assert.ok(!host.execution.getTickPlan(latest.tickPlanId).selectedProposalIds.includes(pending.proposalId));
    }
  } finally {
    game.close();
    rmSync(directory, { recursive: true, force: true });
  }
});

test("Team authority and per-Actor Provider configuration survive a fresh process", () => {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-m4-config-"));
  const dbPath = join(directory, "world.sqlite3");
  const runId = "run:m4-config";
  let game = new GameStore(dbPath);
  try {
    game.createRun({ runId, scenarioVersion: 2, rulesetVersion: 3 });
    game.setActiveRun(runId);
    let host = new TeamHost(game, new FixtureTeamProvider());
    host.initialize(runId);
    const medic = host.team.listTasks(runId).find((task) => task.actorId === MEDIC_ID)!;
    host.team.transitionTask(medic.taskId, { providerOrder: ["hermes", "codex"] }, "team.task-provider-updated");
    host.team.saveConfiguration("locked", runId);
    game.close();

    game = new GameStore(dbPath, { activeRunId: runId });
    host = new TeamHost(game, new FixtureTeamProvider());
    assert.equal(host.team.getConfiguration(runId).authorityPolicyMode, "locked");
    assert.deepEqual(host.team.listTasks(runId).find((task) => task.actorId === MEDIC_ID)?.providerOrder, ["hermes", "codex"]);
    host.team.verify(runId);
  } finally {
    game.close();
    rmSync(directory, { recursive: true, force: true });
  }
});
