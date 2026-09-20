import assert from "node:assert/strict";
import test from "node:test";

import type { WorldCommand, WorldState } from "../src/model.ts";
import {
  advanceEnvironment,
  assertWorldInvariants,
  evaluateMission,
  initialTeamWorld,
} from "../src/scenario.ts";
import { parseWorldCommand, shortestPath, validateWorldCommand } from "../src/world.ts";

function clone(): WorldState {
  return structuredClone(initialTeamWorld());
}

function expectInvariant(mutator: (state: WorldState) => void, pattern: RegExp): void {
  const state = clone();
  mutator(state);
  assert.throws(() => assertWorldInvariants(state), pattern);
}

test("world invariants reject malformed topology, objects, resources, inventory, and mission state", () => {
  const cases: Array<[(state: WorldState) => void, RegExp]> = [
    [(state) => { (state as { schemaVersion: number }).schemaVersion = 99; }, /unsupported world schema/],
    [(state) => { state.revision = -1; }, /invalid revision/],
    [(state) => { state.turn = -1; }, /invalid turn/],
    [(state) => { state.turn = 1; }, /turn and revision diverged/],
    [(state) => { state.rooms["command-center"]?.neighbors.push("missing"); }, /unknown room neighbor/],
    [(state) => { state.rooms["power-junction"]!.neighbors = state.rooms["power-junction"]!.neighbors.filter((id) => id !== "command-center"); }, /asymmetric room edge/],
    [(state) => { state.agents["engineer-01"]!.location = "missing"; }, /agent in unknown room/],
    [(state) => { state.agents["engineer-01"]!.health = 101; }, /invalid agent health/],
    [(state) => { state.crew["crew-01"]!.location = "missing"; }, /crew in unknown room/],
    [(state) => { state.crew["crew-01"]!.health = -1; }, /invalid crew health/],
    [(state) => { state.systems.cooling!.roomId = "missing"; }, /system in unknown room/],
    [(state) => { state.systems.cooling!.integrity = 2; }, /invalid integrity/],
    [(state) => { state.systems.cooling!.powerDraw = -1; }, /invalid power draw/],
    [(state) => { state.systems.cooling!.powered = true; }, /damaged system is powered/],
    [(state) => { state.hazards["maintenance-breach"]!.roomId = "missing"; }, /hazard in unknown room/],
    [(state) => { state.resources.batteryCharge = 57; }, /invalid battery charge/],
    [(state) => { state.resources.energyConsumed = -1; }, /invalid consumed energy/],
    [(state) => { state.resources.batteryCharge = 55; }, /energy ledger does not conserve/],
    [(state) => { state.resources.oxygen = 101; }, /invalid oxygen/],
    [(state) => { state.resources.reactorHeat = -1; }, /invalid reactor heat/],
    [(state) => { state.resources.initialItems.medkit = -1; }, /invalid initial item quantity/],
    [(state) => { state.resources.consumedItems.medkit = -1; }, /invalid consumed item quantity/],
    [(state) => { state.resources.initialItems.medkit = 2; }, /item ledger mismatch/],
    [(state) => { state.rooms.storage!.inventory.medkit = -1; state.resources.consumedItems.medkit = 1; }, /invalid room inventory/],
    [(state) => { state.agents["engineer-01"]!.inventory.medkit = -1; state.resources.consumedItems.medkit = 1; }, /invalid agent inventory/],
    [(state) => { state.mission.reason = "unexpected"; }, /running mission cannot have a terminal reason/],
    [(state) => { state.mission.status = "failure"; }, /terminal mission requires a reason/],
  ];
  for (const [mutator, pattern] of cases) expectInvariant(mutator, pattern);
});

test("environment covers brownout and low-oxygen health consequences", () => {
  const state = clone();
  for (const system of Object.values(state.systems)) {
    system.integrity = 0.9;
    system.powered = true;
  }
  state.resources.batteryCharge = 1;
  state.resources.energyConsumed = 55;
  state.resources.oxygen = 20;
  state.resources.reactorHeat = 90;
  state.agents["engineer-01"]!.location = "reactor";
  advanceEnvironment(state);
  assert.equal(state.resources.batteryCharge, 0);
  assert.equal(state.resources.energyConsumed, 56);
  assert.ok(Object.values(state.systems).every((system) => !system.powered));
  assert.equal(state.resources.oxygen, 16);
  assert.equal(state.resources.reactorHeat, 96);
  assert.equal(state.crew["crew-01"]?.health, 44);
  assert.equal(state.agents["engineer-01"]?.health, 87);
});

test("mission evaluation covers every terminal reason and critical-object failure", () => {
  const cases: Array<[(state: WorldState) => void, string]> = [
    [(state) => { state.resources.reactorHeat = 100; }, "reactor_meltdown"],
    [(state) => { state.resources.oxygen = 0; }, "station_asphyxiation"],
    [(state) => { state.crew["crew-01"]!.health = 0; }, "crew_lost"],
    [(state) => { for (const agent of Object.values(state.agents)) agent.health = 0; }, "team_incapacitated"],
    [(state) => { state.resources.batteryCharge = 0; state.resources.energyConsumed = 56; }, "power_exhausted"],
    [(state) => { state.turn = 22; state.revision = 22; }, "mission_timeout"],
  ];
  for (const [mutator, reason] of cases) {
    const state = clone();
    mutator(state);
    evaluateMission(state);
    assert.equal(state.mission.status, "failure");
    assert.equal(state.mission.reason, reason);
  }

  const victory = clone();
  victory.mission.distressSent = true;
  victory.crew["crew-01"]!.stabilized = true;
  victory.hazards["maintenance-breach"]!.sealed = true;
  victory.systems.cooling!.integrity = 0.9;
  victory.systems["life-support"]!.integrity = 0.9;
  victory.systems["life-support"]!.powered = true;
  victory.resources.oxygen = 50;
  victory.resources.reactorHeat = 70;
  evaluateMission(victory);
  assert.equal(victory.mission.status, "victory");
  assert.equal(victory.mission.reason, "rescue_signal_verified");

  const missing = clone();
  delete missing.systems.cooling;
  assert.throws(() => evaluateMission(missing), /critical objects are missing/);
});

test("command parser accepts every command kind and rejects malformed fields", () => {
  const base = { commandId: "parse", actorId: "engineer-01", expectedRevision: 0 };
  const inputs: unknown[] = [
    { ...base, kind: "move", targetRoomId: "power-junction" },
    { ...base, kind: "pickup_item", itemId: "medkit", quantity: 1 },
    { ...base, kind: "repair_system", targetSystemId: "cooling" },
    { ...base, kind: "set_power", targetSystemId: "cooling", enabled: true },
    { ...base, kind: "seal_hull", targetHazardId: "maintenance-breach" },
    { ...base, kind: "stabilize_crew", targetCrewId: "crew-01" },
    { ...base, kind: "send_distress", targetSystemId: "communications" },
    { ...base, kind: "wait" },
  ];
  assert.deepEqual(inputs.map((input) => parseWorldCommand(input).kind), [
    "move", "pickup_item", "repair_system", "set_power", "seal_hull",
    "stabilize_crew", "send_distress", "wait",
  ]);

  const invalid: Array<[unknown, RegExp]> = [
    [null, /command must be an object/],
    [{ ...base, commandId: "", kind: "wait" }, /commandId/],
    [{ ...base, expectedRevision: -1, kind: "wait" }, /expectedRevision/],
    [{ ...base, kind: "pickup_item", itemId: "unknown", quantity: 1 }, /unsupported itemId/],
    [{ ...base, kind: "pickup_item", itemId: "medkit", quantity: 0 }, /positive integer/],
    [{ ...base, kind: "set_power", targetSystemId: "cooling", enabled: "yes" }, /enabled must be boolean/],
    [{ ...base, kind: "unknown" }, /unsupported command kind/],
  ];
  for (const [input, pattern] of invalid) assert.throws(() => parseWorldCommand(input), pattern);
});

function code(state: WorldState, command: WorldCommand): string | null {
  return validateWorldCommand(state, command)?.code ?? null;
}

test("command admission returns explicit rejection codes across all action families", () => {
  const base = { commandId: "reject", actorId: "engineer-01", expectedRevision: 0 };
  const terminal = clone();
  terminal.mission.status = "failure";
  terminal.mission.reason = "test";
  assert.equal(code(terminal, { ...base, kind: "wait" }), "mission_not_running");
  assert.equal(code(clone(), { ...base, expectedRevision: 1, kind: "wait" }), "stale_revision");
  assert.equal(code(clone(), { ...base, actorId: "missing", kind: "wait" }), "unknown_actor");

  const noMove = clone();
  noMove.agents["engineer-01"]!.capabilities = [];
  assert.equal(code(noMove, { ...base, kind: "move", targetRoomId: "power-junction" }), "capability_missing");
  assert.equal(code(clone(), { ...base, kind: "move", targetRoomId: "missing" }), "unknown_target");
  assert.equal(code(clone(), { ...base, kind: "move", targetRoomId: "reactor" }), "not_adjacent");

  assert.equal(code(clone(), { ...base, kind: "pickup_item", itemId: "medkit", quantity: 1 }), "item_missing");
  assert.equal(code(clone(), { ...base, kind: "repair_system", targetSystemId: "missing" }), "unknown_target");
  assert.equal(code(clone(), { ...base, kind: "repair_system", targetSystemId: "cooling" }), "wrong_location");

  const reactor = clone();
  reactor.agents["engineer-01"]!.location = "reactor";
  reactor.systems.cooling!.integrity = 0.9;
  assert.equal(code(reactor, { ...base, kind: "repair_system", targetSystemId: "cooling" }), "already_complete");
  reactor.systems.cooling!.integrity = 0.35;
  reactor.agents["engineer-01"]!.inventory.toolkit = 0;
  assert.equal(code(reactor, { ...base, kind: "repair_system", targetSystemId: "cooling" }), "tool_missing");
  reactor.agents["engineer-01"]!.inventory.toolkit = 1;
  reactor.agents["engineer-01"]!.inventory["spare-parts"] = 0;
  assert.equal(code(reactor, { ...base, kind: "repair_system", targetSystemId: "cooling" }), "item_missing");

  const junction = clone();
  junction.agents["engineer-01"]!.location = "power-junction";
  assert.equal(code(junction, { ...base, kind: "set_power", targetSystemId: "missing", enabled: true }), "unknown_target");
  junction.agents["engineer-01"]!.inventory["breaker-key"] = 0;
  assert.equal(code(junction, { ...base, kind: "set_power", targetSystemId: "cooling", enabled: true }), "tool_missing");
  junction.agents["engineer-01"]!.inventory["breaker-key"] = 1;
  assert.equal(code(junction, { ...base, kind: "set_power", targetSystemId: "cooling", enabled: false }), "already_complete");
  assert.equal(code(junction, { ...base, kind: "set_power", targetSystemId: "cooling", enabled: true }), "system_damaged");
  junction.systems.cooling!.integrity = 0.9;
  junction.resources.batteryCharge = 1;
  junction.resources.energyConsumed = 55;
  assert.equal(code(junction, { ...base, kind: "set_power", targetSystemId: "cooling", enabled: true }), "insufficient_power");
  junction.resources.batteryCharge = junction.systems.cooling!.powerDraw;
  junction.resources.energyConsumed = junction.resources.batteryInitial - junction.resources.batteryCharge;
  assert.equal(code(junction, { ...base, kind: "set_power", targetSystemId: "cooling", enabled: true }), null);

  assert.equal(code(clone(), { ...base, kind: "seal_hull", targetHazardId: "missing" }), "unknown_target");
  const maintenance = clone();
  maintenance.agents["engineer-01"]!.location = "maintenance";
  maintenance.hazards["maintenance-breach"]!.sealed = true;
  assert.equal(code(maintenance, { ...base, kind: "seal_hull", targetHazardId: "maintenance-breach" }), "already_complete");
  maintenance.hazards["maintenance-breach"]!.sealed = false;
  maintenance.agents["engineer-01"]!.inventory.sealant = 0;
  assert.equal(code(maintenance, { ...base, kind: "seal_hull", targetHazardId: "maintenance-breach" }), "item_missing");

  const medicBase = { ...base, actorId: "medic-01" };
  assert.equal(code(clone(), { ...medicBase, kind: "stabilize_crew", targetCrewId: "missing" }), "unknown_target");
  const medical = clone();
  medical.agents["medic-01"]!.location = "medical-bay";
  medical.crew["crew-01"]!.stabilized = true;
  assert.equal(code(medical, { ...medicBase, kind: "stabilize_crew", targetCrewId: "crew-01" }), "already_complete");
  medical.crew["crew-01"]!.stabilized = false;
  medical.agents["medic-01"]!.inventory.medkit = 0;
  assert.equal(code(medical, { ...medicBase, kind: "stabilize_crew", targetCrewId: "crew-01" }), "item_missing");

  assert.equal(code(clone(), { ...base, kind: "send_distress", targetSystemId: "missing" }), "unknown_target");
  assert.equal(code(clone(), { ...base, kind: "send_distress", targetSystemId: "cooling" }), "invalid_command");
  const communications = clone();
  communications.agents["engineer-01"]!.location = "communications";
  assert.equal(code(communications, { ...base, kind: "send_distress", targetSystemId: "communications" }), "system_damaged");
  communications.systems.communications!.integrity = 0.9;
  communications.systems.communications!.powered = true;
  communications.mission.distressSent = true;
  assert.equal(code(communications, { ...base, kind: "send_distress", targetSystemId: "communications" }), "already_complete");
});

test("shortest path returns identity and null for unreachable targets", () => {
  const state = clone();
  assert.deepEqual(shortestPath(state, "reactor", "reactor"), ["reactor"]);
  assert.equal(shortestPath(state, "reactor", "missing"), null);
});
