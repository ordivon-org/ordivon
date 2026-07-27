import assert from "node:assert/strict";
import test from "node:test";

import { sha256 } from "../src/digest.ts";
import { communicationsFirstPolicy, recoveryPolicy, runPolicy } from "../src/policies.ts";
import { initialWorld } from "../src/scenario.ts";
import { applyWorldCommand, listAvailableActions, materializeAction } from "../src/world.ts";

function applyActionId(state: ReturnType<typeof initialWorld>, actionId: string, commandId: string) {
  const action = listAvailableActions(state).find((candidate) => candidate.actionId === actionId);
  assert.ok(action, `missing action: ${actionId}`);
  const result = applyWorldCommand(state, materializeAction(action, commandId));
  if (result.status !== "accepted") throw new Error(`${result.code}: ${result.reason}`);
  assert.equal(result.status, "accepted");
  return result.state;
}

test("stale revisions and powering damaged systems fail atomically", () => {
  const initial = initialWorld();
  const initialDigest = sha256(initial);
  const stale = applyWorldCommand(initial, {
    kind: "move",
    commandId: "stale-contract",
    actorId: "engineer-01",
    targetRoomId: "power-junction",
    expectedRevision: 1,
  });
  assert.equal(stale.status, "rejected");
  assert.equal(stale.status === "rejected" ? stale.code : null, "stale_revision");
  assert.equal(sha256(initial), initialDigest);

  const atJunction = applyActionId(initial, "move:power-junction", "junction-contract");
  const beforePower = sha256(atJunction);
  const damagedPower = applyWorldCommand(atJunction, {
    kind: "set_power",
    commandId: "damaged-power-contract",
    actorId: "engineer-01",
    targetSystemId: "cooling",
    enabled: true,
    expectedRevision: atJunction.revision,
  });
  assert.equal(damagedPower.status, "rejected");
  assert.equal(damagedPower.status === "rejected" ? damagedPower.code : null, "system_damaged");
  assert.equal(sha256(atJunction), beforePower);
});

test("battery use is conserved after powering a repaired system", () => {
  let state = initialWorld();
  state = applyActionId(state, "move:power-junction", "energy-1");
  state = applyActionId(state, "move:reactor", "energy-2");
  state = applyActionId(state, "repair:cooling", "energy-3");
  state = applyActionId(state, "move:power-junction", "energy-4");
  state = applyActionId(state, "power:cooling:true", "energy-5");
  state = applyActionId(state, "wait", "energy-6");

  assert.equal(state.resources.batteryCharge, 52);
  assert.equal(state.resources.energyConsumed, 4);
  assert.equal(
    state.resources.batteryCharge + state.resources.energyConsumed,
    state.resources.batteryInitial,
  );
});

test("scripted scenario evidence covers every M1 command kind", () => {
  const events = [
    ...runPolicy(recoveryPolicy).events,
    ...runPolicy(communicationsFirstPolicy).events,
  ];
  const kinds = new Set(events.map((event) => event.commandKind));
  assert.deepEqual([...kinds].sort(), [
    "move",
    "pickup_item",
    "repair_system",
    "seal_hull",
    "send_distress",
    "set_power",
    "stabilize_crew",
    "wait",
  ]);
});
