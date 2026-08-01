import assert from "node:assert/strict";
import test from "node:test";

import { GameStore } from "../src/storage.ts";
import {
  evaluateStationZeroCoordination,
  STATION_ZERO_COORDINATION_POLICY_ID,
  STATION_ZERO_SPECIALIST_LIMIT,
} from "../src/team/coordination-policy.ts";
import { TeamHost } from "../src/team/engine.ts";
import { teamCognitionStarted } from "../src/team/execution-store.ts";
import type { ActionProposal } from "../src/team/model.ts";
import { FixtureTeamProvider } from "../src/team/providers.ts";
import { teamRunInitialized, TeamStore } from "../src/team/store.ts";

async function proposalFixture() {
  const game = new GameStore(":memory:");
  const runId = "run:coordination-policy";
  game.createRun({ runId, scenarioVersion: 2, rulesetVersion: 3 });
  const host = new TeamHost(game, new FixtureTeamProvider());
  for (let index = 0; index < 3; index += 1) await host.step(runId);
  const round = host.execution.listRounds(runId).at(-1);
  assert.ok(round);
  const proposals = host.execution.listProposals(round.roundId);
  assert.equal(proposals.length, STATION_ZERO_SPECIALIST_LIMIT);
  return { game, runId, round, proposals };
}

test("Station Zero coordination is an explicit bounded domain policy", async () => {
  const { game, runId, round, proposals } = await proposalFixture();
  try {
    const state = game.loadState(runId);
    const candidates = proposals.map((proposal) => ({
      proposal, authorityGrantAvailable: false,
    }));
    const forward = evaluateStationZeroCoordination(state, round, candidates);
    const reverse = evaluateStationZeroCoordination(state, round, [...candidates].reverse());
    assert.equal(forward.policyId, STATION_ZERO_COORDINATION_POLICY_ID);
    assert.deepEqual(
      forward.selected?.map((proposal) => proposal.proposalId).sort(),
      reverse.selected?.map((proposal) => proposal.proposalId).sort(),
    );
  } finally {
    game.close();
  }
});

test("Station Zero coordination rejects accidental promotion beyond three specialists", async () => {
  const { game, runId, round, proposals } = await proposalFixture();
  try {
    const first = proposals[0]!;
    const overflow: ActionProposal = {
      ...first,
      proposalId: `${first.proposalId}:overflow`,
      actorId: "unexpected-fourth-actor",
      command: {
        ...first.command,
        actorId: "unexpected-fourth-actor",
        commandId: `${first.command.commandId}:overflow`,
      },
    };
    assert.throws(
      () => evaluateStationZeroCoordination(
        game.loadState(runId),
        round,
        [...proposals, overflow].map((proposal) => ({
          proposal, authorityGrantAvailable: false,
        })),
      ),
      /at most 3 specialist Proposals/,
    );
  } finally {
    game.close();
  }
});

test("Team initialization queries stay inside the Team owner and do not create schema", () => {
  const game = new GameStore(":memory:");
  const runId = "run:team-initialization-query";
  game.createRun({ runId, scenarioVersion: 2, rulesetVersion: 3 });
  assert.equal(teamRunInitialized(game, runId), false);
  assert.equal(teamCognitionStarted(game, runId), false);
  const before = game.db.prepare(
    "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'team_actor_sessions'",
  ).get();
  assert.equal(before, undefined);
  const team = new TeamStore(game);
  assert.equal(team.isInitialized(runId), false);
  team.initialize(runId);
  assert.equal(teamRunInitialized(game, runId), true);
  game.close();
});


test("Team cognition detection is owner-local and begins with the first retained Round", async () => {
  const game = new GameStore(":memory:");
  const runId = "run:team-cognition-query";
  try {
    game.createRun({ runId, scenarioVersion: 2, rulesetVersion: 3 });
    assert.equal(teamCognitionStarted(game, runId), false);
    const host = new TeamHost(game, new FixtureTeamProvider());
    host.initialize(runId);
    assert.equal(teamCognitionStarted(game, runId), false);
    await host.step(runId);
    assert.equal(teamCognitionStarted(game, runId), true);
  } finally {
    game.close();
  }
});
