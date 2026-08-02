import assert from "node:assert/strict";
import test from "node:test";

import { sha256 } from "../src/digest.ts";
import { initialTeamWorld } from "../src/scenario.ts";
import { applyWorldTick, listAvailableActions, materializeAction } from "../src/world.ts";

test("one intent advances one simulation tick and one world revision", () => {
  const state = initialTeamWorld();
  const action = listAvailableActions(state).find((candidate) => candidate.actionId === "move:power-junction");
  assert.ok(action);
  const command = materializeAction(action, "tick-one");
  const result = applyWorldTick(state, {
    tickId: "tick:test:1",
    expectedWorldRevision: 0,
    intents: [{ commandSequence: 7, command }],
  });
  if (result.status !== "accepted") throw new Error(`${result.code}: ${result.reason}`);
  assert.equal(result.status, "accepted");
  assert.equal(result.state.revision, 1);
  assert.equal(result.state.turn, 1);
  assert.equal(result.journalEvents[0]?.commandSequence, 7);
  assert.equal(result.journalEvents[0]?.simulationTick, 1);
  assert.equal(result.journalEvents[0]?.worldRevision, 1);
  assert.equal(result.journalEvents[0]?.tickId, "tick:test:1");
});

test("conflicting multi-intent batches fail closed atomically", () => {
  const state = initialTeamWorld();
  const action = listAvailableActions(state).find((candidate) => candidate.actionId === "move:power-junction");
  assert.ok(action);
  const command = materializeAction(action, "tick-multi");
  const before = sha256(state);
  const result = applyWorldTick(state, {
    tickId: "tick:test:multi",
    expectedWorldRevision: 0,
    intents: [
      { commandSequence: 0, command },
      { commandSequence: 1, command: { ...command, commandId: "tick-multi-2" } },
    ],
  });
  assert.equal(result.status, "rejected");
  assert.equal(result.status === "rejected" ? result.code : null, "conflicting_intents");
  assert.equal(sha256(state), before);
});

test("tick and intent revisions must agree", () => {
  const state = initialTeamWorld();
  const action = listAvailableActions(state).find((candidate) => candidate.actionId === "move:power-junction");
  assert.ok(action);
  const command = materializeAction(action, "tick-stale");
  const result = applyWorldTick(state, {
    tickId: "tick:test:stale",
    expectedWorldRevision: 1,
    intents: [{ commandSequence: 0, command }],
  });
  assert.equal(result.status, "rejected");
  assert.equal(result.status === "rejected" ? result.code : null, "stale_revision");
});
