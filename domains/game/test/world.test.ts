import assert from "node:assert/strict";
import test from "node:test";

import { sha256 } from "../src/digest.ts";
import { ITEM_IDS } from "../src/model.ts";
import { assertWorldInvariants, currentItemTotal, initialWorld } from "../src/scenario.ts";
import { applyWorldCommand, listAvailableActions, materializeAction, shortestPath } from "../src/world.ts";

test("initial station graph and resource ledgers are valid", () => {
  const state = initialWorld();
  assertWorldInvariants(state);
  assert.equal(Object.keys(state.rooms).length, 8);
  assert.deepEqual(shortestPath(state, "command-center", "maintenance"), [
    "command-center",
    "power-junction",
    "storage",
    "maintenance",
  ]);
  for (const itemId of ITEM_IDS) {
    assert.equal(currentItemTotal(state, itemId), state.resources.initialItems[itemId]);
  }
});

test("non-adjacent movement is rejected without mutation", () => {
  const state = initialWorld();
  const before = sha256(state);
  const result = applyWorldCommand(state, {
    kind: "move",
    commandId: "invalid-move",
    actorId: "engineer-01",
    targetRoomId: "reactor",
    expectedRevision: 0,
  });
  assert.equal(result.status, "rejected");
  assert.equal(sha256(state), before);
  assert.equal(state.turn, 0);
});

test("repair consumes a spare part into the conserved resource ledger", () => {
  let state = initialWorld();
  for (const actionId of ["move:power-junction", "move:reactor", "repair:cooling"]) {
    const action = listAvailableActions(state).find((candidate) => candidate.actionId === actionId);
    assert.ok(action);
    const result = applyWorldCommand(state, materializeAction(action, `repair-route:${actionId}`));
    assert.equal(result.status, "accepted");
    if (result.status !== "accepted") return;
    state = result.state;
  }
  assert.equal(state.resources.consumedItems["spare-parts"], 1);
  assert.equal(currentItemTotal(state, "spare-parts"), 3);
  assertWorldInvariants(state);
});
