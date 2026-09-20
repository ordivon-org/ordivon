import assert from "node:assert/strict";
import test from "node:test";

import { describeFact, deriveFacts, enrichWorldEvent } from "../src/facts.ts";
import type { TeamTickCommand, WorldEvent } from "../src/model.ts";
import { initialTeamWorld } from "../src/scenario.ts";
import { parseWorldCommand } from "../src/world.ts";

test("team command parser accepts exact contain and team envelopes and rejects malformed nesting", () => {
  const contain = parseWorldCommand({
    kind: "contain_hazard",
    commandId: "contain-parse",
    actorId: "security-01",
    expectedRevision: 0,
    targetHazardId: "maintenance-breach",
  });
  assert.equal(contain.kind, "contain_hazard");
  const team = parseWorldCommand({
    kind: "team_tick",
    commandId: "team-parse",
    actorId: "team-coordinator",
    expectedRevision: 0,
    tickId: "tick-parse",
    intents: [contain],
  });
  assert.equal(team.kind, "team_tick");
  assert.equal(team.kind === "team_tick" ? team.intents.length : 0, 1);
  assert.throws(() => parseWorldCommand({
    kind: "team_tick", commandId: "empty", actorId: "team-coordinator", expectedRevision: 0, tickId: "empty", intents: [],
  }), /non-empty/);
  assert.throws(() => parseWorldCommand({
    kind: "team_tick", commandId: "nested", actorId: "team-coordinator", expectedRevision: 0, tickId: "nested",
    intents: [{ kind: "team_tick", commandId: "inner", actorId: "team-coordinator", expectedRevision: 0, tickId: "inner", intents: [contain] }],
  }), /nested/);
});

test("team_tick fact helpers remain total and hazard facts are readable", () => {
  const before = initialTeamWorld();
  const after = structuredClone(before);
  after.revision = 1;
  after.turn = 1;
  const command: TeamTickCommand = {
    kind: "team_tick",
    commandId: "fact-team",
    actorId: "team-coordinator",
    expectedRevision: 0,
    tickId: "fact-team",
    intents: [],
  };
  assert.deepEqual(deriveFacts(before, after, command), []);
  const event: WorldEvent = {
    eventId: "event:fact-team",
    commandId: command.commandId,
    commandKind: command.kind,
    actorId: command.actorId,
    worldRevision: 1,
    turn: 1,
    beforeDigest: "before",
    afterDigest: "after",
    changes: [],
    missionStatus: "running",
    missionReason: null,
  };
  assert.equal(enrichWorldEvent(before, after, command, event).verification?.success, true);
  assert.equal(describeFact({ kind: "hazard_contained", hazardId: "breach", actorId: "security-01" }), "breach contained by security-01");
});
