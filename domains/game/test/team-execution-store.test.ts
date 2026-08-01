import assert from "node:assert/strict";
import test from "node:test";

import { canonicalJson } from "../src/digest.ts";
import { GameStore } from "../src/storage.ts";
import { TeamHost } from "../src/team/engine.ts";
import { FixtureTeamProvider } from "../src/team/providers.ts";
import { TeamStoreError } from "../src/team/store.ts";

async function setup(runId: string) {
  const game = new GameStore(":memory:");
  game.createRun({ runId, scenarioVersion: 2, rulesetVersion: 3 });
  game.setActiveRun(runId);
  const host = new TeamHost(game, new FixtureTeamProvider());
  await host.step(runId);
  await host.step(runId);
  await host.step(runId);
  const round = host.execution.listRounds(runId)[0]!;
  const proposal = host.execution.listProposals(round.roundId)[0]!;
  return { game, host, round, proposal };
}

test("Team Execution Store is idempotent and rejects conflicting semantic identities", async () => {
  const { game, host, round, proposal } = await setup("run:team-execution-identities");
  try {
    assert.deepEqual(host.execution.putRound(round), round);
    assert.throws(
      () => host.execution.putRound({ ...round, status: "blocked" }),
      (error: unknown) => error instanceof TeamStoreError && error.code === "team_conflict",
    );
    assert.throws(
      () => host.execution.saveRound(round, { ...round, worldRevision: round.worldRevision + 1 }, "conflict"),
      /identity changed/,
    );
    const advancedRound = host.execution.saveRound(
      round,
      { ...round, updatedAt: "2026-08-01T00:00:01.000Z" },
      "team.round-audit-advanced",
    );
    assert.throws(
      () => host.execution.saveRound(
        round,
        { ...round, status: "blocked", blocker: "stale-writer", updatedAt: "2026-08-01T00:00:02.000Z" },
        "team.round-stale-overwrite",
      ),
      (error: unknown) => error instanceof TeamStoreError && error.code === "team_conflict" && /superseded/.test(error.message),
    );
    assert.deepEqual(host.execution.getRound(round.roundId), advancedRound);

    assert.deepEqual(host.execution.putProposal(proposal), proposal);
    assert.throws(
      () => host.execution.putProposal({ ...proposal, rationale: "different" }),
      (error: unknown) => error instanceof TeamStoreError && error.code === "team_conflict",
    );
    assert.throws(
      () => host.execution.saveProposal(proposal, { ...proposal, actorId: "different" }, "conflict"),
      /identity changed/,
    );
    const selectedProposal = host.execution.saveProposal(
      proposal,
      { ...proposal, status: "selected", updatedAt: "2026-08-01T00:00:03.000Z" },
      "team.proposal-audit-selected",
    );
    assert.throws(
      () => host.execution.saveProposal(
        proposal,
        { ...proposal, status: "rejected", rejectionReason: "stale-writer", updatedAt: "2026-08-01T00:00:04.000Z" },
        "team.proposal-stale-overwrite",
      ),
      (error: unknown) => error instanceof TeamStoreError && error.code === "team_conflict" && /superseded/.test(error.message),
    );
    assert.deepEqual(host.execution.getProposal(proposal.proposalId), selectedProposal);
    assert.equal(host.execution.findProposalForActor(round.roundId, "missing"), null);
    assert.equal(host.execution.findObservationForRound(round.roundId), null);
  } finally { game.close(); }
});

test("Team Execution Store reports every missing typed object explicitly", async () => {
  const { game, host } = await setup("run:team-execution-missing");
  try {
    assert.throws(() => host.execution.getRound("team-round:missing"), /unknown Team Round/);
    assert.throws(() => host.execution.getProposal("team-proposal:missing"), /unknown Team Proposal/);
    assert.throws(() => host.execution.getTickPlan("team-tick-plan:missing"), /unknown Team TickPlan/);
    assert.throws(() => host.execution.getEffect("team-effect:missing"), /unknown Team Effect/);
    assert.throws(() => host.execution.getDispatch("team-dispatch:missing"), /unknown Team Dispatch/);
  } finally { game.close(); }
});

test("Team Execution Store rejects corrupt retained JSON", async () => {
  const { game, host, round } = await setup("run:team-execution-corrupt");
  try {
    game.db.prepare("UPDATE team_rounds SET value_json = ? WHERE round_id = ?").run("{", round.roundId);
    assert.throws(
      () => host.execution.getRound(round.roundId),
      (error: unknown) => error instanceof TeamStoreError && error.code === "team_corrupt",
    );
  } finally { game.close(); }
});


test("Team Execution verification rejects terminal events that differ from retained heads", async () => {
  const { game, host, round, proposal } = await setup("run:team-execution-terminal-heads");
  try {
    host.team.host.appendEvent(
      game.activeRunId,
      "team.round-completed",
      "host-event:audit:forged-round-completion",
      { round: { ...round, status: "completed", updatedAt: "2026-08-01T00:00:05.000Z" } },
    );
    assert.throws(
      () => host.execution.verify(game.activeRunId),
      (error: unknown) => error instanceof TeamStoreError && error.code === "team_corrupt" && /completed Team Round/.test(error.message),
    );

    const second = await setup("run:team-execution-terminal-proposal");
    try {
      second.host.team.host.appendEvent(
        second.game.activeRunId,
        "team.proposal-verified",
        "host-event:audit:forged-proposal-verification",
        { proposal: { ...second.proposal, status: "verified", updatedAt: "2026-08-01T00:00:06.000Z" } },
      );
      assert.throws(
        () => second.host.execution.verify(second.game.activeRunId),
        (error: unknown) => error instanceof TeamStoreError && error.code === "team_corrupt" && /terminal Team Proposal/.test(error.message),
      );
    } finally {
      second.game.close();
    }
    assert.equal(proposal.status, "proposed");
  } finally {
    game.close();
  }
});


test("a stale completed writer cannot complete Authority after another Round head wins", async () => {
  const game = new GameStore(":memory:");
  const runId = "run:team-execution-authority-race";
  try {
    game.createRun({ runId, scenarioVersion: 2, rulesetVersion: 3 });
    const host = new TeamHost(game, new FixtureTeamProvider());
    let round = null as ReturnType<typeof host.execution.listRounds>[number] | null;
    for (let index = 0; index < 12; index += 1) {
      await host.step(runId);
      round = host.execution.listRounds(runId)[0] ?? null;
      if (round?.status === "observed") break;
    }
    assert.ok(round);
    assert.equal(round.status, "observed");
    const taskId = `task:team-round:${round.roundId.slice("team-round:".length)}`;
    assert.equal(host.execution.authority.projection(runId, taskId).state, "verifying");
    const blocked = host.execution.saveRound(
      round,
      { ...round, status: "blocked", blocker: "audit-winner", updatedAt: "2026-08-01T00:00:07.000Z" },
      "team.round-audit-blocked",
    );
    assert.equal(blocked.status, "blocked");
    assert.throws(
      () => host.execution.saveRound(
        round!,
        { ...round!, status: "completed", blocker: null, updatedAt: "2026-08-01T00:00:08.000Z" },
        "team.round-audit-completed",
      ),
      (error: unknown) => error instanceof TeamStoreError && error.code === "team_conflict" && /superseded/.test(error.message),
    );
    assert.equal(host.execution.authority.projection(runId, taskId).state, "verifying");
  } finally {
    game.close();
  }
});

test("a retained completed Round reconciles missing Authority completion", async () => {
  const game = new GameStore(":memory:");
  const runId = "run:team-execution-authority-recovery";
  try {
    game.createRun({ runId, scenarioVersion: 2, rulesetVersion: 3 });
    const host = new TeamHost(game, new FixtureTeamProvider());
    let round = null as ReturnType<typeof host.execution.listRounds>[number] | null;
    for (let index = 0; index < 12; index += 1) {
      await host.step(runId);
      round = host.execution.listRounds(runId)[0] ?? null;
      if (round?.status === "observed") break;
    }
    assert.ok(round);
    assert.equal(round.status, "observed");
    const completed = {
      ...round,
      status: "completed" as const,
      blocker: null,
      updatedAt: "2026-08-01T00:00:09.000Z",
    };
    host.team.host.withTransaction(runId, () => {
      host.team.db.prepare(
        "UPDATE team_rounds SET status = ?, value_json = ? WHERE round_id = ? AND value_json = ?",
      ).run("completed", canonicalJson(completed), round!.roundId, canonicalJson(round));
      host.team.host.appendEventInTransaction(
        runId,
        "team.round-completed",
        `host-event:${round!.roundId}:team.round-completed:${completed.updatedAt}`,
        { round: completed },
        completed.updatedAt,
      );
    });
    const taskId = `task:team-round:${round.roundId.slice("team-round:".length)}`;
    assert.equal(host.execution.authority.projection(runId, taskId).state, "verifying");
    const receipt = await host.step(runId);
    assert.ok(["initialized", "stable"].includes(receipt.status));
    assert.equal(host.execution.authority.projection(runId, taskId).state, "completed");
    host.execution.verify(runId);
  } finally {
    game.close();
  }
});
