import assert from "node:assert/strict";
import test from "node:test";

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
      () => host.execution.saveRound({ ...round, worldRevision: round.worldRevision + 1 }, "conflict"),
      /identity changed/,
    );

    assert.deepEqual(host.execution.putProposal(proposal), proposal);
    assert.throws(
      () => host.execution.putProposal({ ...proposal, rationale: "different" }),
      (error: unknown) => error instanceof TeamStoreError && error.code === "team_conflict",
    );
    assert.throws(
      () => host.execution.saveProposal({ ...proposal, actorId: "different" }, "conflict"),
      /identity changed/,
    );
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
