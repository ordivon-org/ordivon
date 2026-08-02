import assert from "node:assert/strict";
import test from "node:test";

import { sha256 } from "../src/digest.ts";
import type { PrimitiveWorldCommand, TickBatch } from "../src/model.ts";
import { resolveRuleset, resolveScenario } from "../src/registry.ts";
import { ENGINEER_ID, MEDIC_ID, SECURITY_ID, evaluateMission, initialTeamWorld } from "../src/scenario.ts";
import { GameStore } from "../src/storage.ts";
import { applyWorldCommand, applyWorldTick, listAvailableActions, materializeAction, validateWorldCommand } from "../src/world.ts";

function command(state: ReturnType<typeof initialTeamWorld>, actorId: string, actionId: string, commandId: string): PrimitiveWorldCommand {
  const action = listAvailableActions(state, actorId).find((candidate) => candidate.actionId === actionId);
  assert.ok(action, `${actorId} missing ${actionId}`);
  const result = materializeAction(action, commandId);
  if (result.kind === "team_tick") throw new Error("available action produced team_tick");
  return result;
}

function movementBatch(state: ReturnType<typeof initialTeamWorld>, order = [ENGINEER_ID, MEDIC_ID, SECURITY_ID]): TickBatch {
  return {
    tickId: "team-move-power",
    expectedWorldRevision: state.revision,
    intents: order.map((actorId, index) => ({
      commandSequence: index,
      command: command(state, actorId, "move:power-junction", `move-power:${actorId}`),
    })),
  };
}

test("Scenario v2 exposes three persistent specialists with exclusive capabilities", () => {
  const state = initialTeamWorld();
  assert.deepEqual(Object.keys(state.agents).sort(), [ENGINEER_ID, MEDIC_ID, SECURITY_ID]);
  assert.ok(state.agents[ENGINEER_ID]?.capabilities.includes("repair_system"));
  assert.ok(!state.agents[MEDIC_ID]?.capabilities.includes("repair_system"));
  assert.ok(state.agents[MEDIC_ID]?.capabilities.includes("basic_first_aid"));
  assert.ok(!state.agents[SECURITY_ID]?.capabilities.includes("basic_first_aid"));
  assert.ok(state.agents[SECURITY_ID]?.capabilities.includes("contain_hazard"));
  assert.equal(state.hazards["maintenance-breach"]?.contained, false);
  assert.equal(resolveScenario("station-zero", 2).create().scenarioId, "station-zero");
  assert.equal(resolveRuleset("station-zero-core", 3).version, 3);
});

test("three compatible actor intents advance one simulation Tick and environment once", () => {
  const state = initialTeamWorld();
  const result = applyWorldTick(state, movementBatch(state));
  if (result.status !== "accepted") throw new Error(`${result.code}: ${result.reason}`);
  assert.equal(result.state.revision, 1);
  assert.equal(result.state.turn, 1);
  assert.equal(result.state.resources.oxygen, 74);
  assert.equal(result.state.resources.reactorHeat, 46);
  for (const actorId of [ENGINEER_ID, MEDIC_ID, SECURITY_ID]) {
    assert.equal(result.state.agents[actorId]?.location, "power-junction");
  }
  const event = result.journalEvents[0]?.event;
  assert.equal(event?.commandKind, "team_tick");
  assert.equal(event?.intentReceipts?.length, 3);
  assert.equal(event?.verification?.success, true);
});

test("TickBatch result is independent from actor intent order", () => {
  const state = initialTeamWorld();
  const forward = applyWorldTick(state, movementBatch(state));
  const reverse = applyWorldTick(state, movementBatch(state, [SECURITY_ID, MEDIC_ID, ENGINEER_ID]));
  assert.equal(forward.status, "accepted");
  assert.equal(reverse.status, "accepted");
  if (forward.status !== "accepted" || reverse.status !== "accepted") return;
  assert.equal(sha256(forward.state), sha256(reverse.state));
  assert.deepEqual(forward.journalEvents[0]?.event.intentReceipts, reverse.journalEvents[0]?.event.intentReceipts);
});

test("same mutable target and over-allocated shared inventory reject atomically", () => {
  const state = initialTeamWorld();
  for (const actor of Object.values(state.agents)) actor.location = "maintenance";
  const engineer = state.agents[ENGINEER_ID];
  assert.ok(engineer);
  engineer.inventory.sealant = 1;
  state.rooms.storage!.inventory.sealant = 0;
  const targetConflict = applyWorldTick(state, {
    tickId: "conflict-hazard",
    expectedWorldRevision: 0,
    intents: [
      { commandSequence: 0, command: command(state, ENGINEER_ID, "seal:maintenance-breach", "seal-conflict") },
      { commandSequence: 1, command: command(state, SECURITY_ID, "contain:maintenance-breach", "contain-conflict") },
    ],
  });
  assert.equal(targetConflict.status, "rejected");
  assert.equal(targetConflict.status === "rejected" ? targetConflict.code : null, "conflicting_intents");
  assert.equal(state.revision, 0);
  assert.equal(state.hazards["maintenance-breach"]?.sealed, false);
  assert.equal(state.hazards["maintenance-breach"]?.contained, false);

  const inventoryState = initialTeamWorld();
  inventoryState.agents[MEDIC_ID]!.location = "medical-bay";
  inventoryState.agents[SECURITY_ID]!.location = "medical-bay";
  const inventoryConflict = applyWorldTick(inventoryState, {
    tickId: "conflict-inventory",
    expectedWorldRevision: 0,
    intents: [
      { commandSequence: 0, command: command(inventoryState, MEDIC_ID, "pickup:medkit:1", "pickup-medic") },
      { commandSequence: 1, command: command(inventoryState, SECURITY_ID, "pickup:medkit:1", "pickup-security") },
    ],
  });
  assert.equal(inventoryConflict.status, "rejected");
  assert.equal(inventoryConflict.status === "rejected" ? inventoryConflict.code : null, "conflicting_intents");
  assert.equal(inventoryState.rooms["medical-bay"]?.inventory.medkit, 1);
});

test("GameStore persists one synthetic team_tick and replays the exact multi-Actor state", () => {
  const store = new GameStore(":memory:");
  const run = store.createRun({
    runId: "run:team-persistence",
    scenarioVersion: 2,
    rulesetVersion: 3,
  });
  const state = store.loadState(run.runId);
  const batch = movementBatch(state as ReturnType<typeof initialTeamWorld>);
  const first = store.applyTeamTick(batch, run.runId);
  assert.equal(first.result.status, "accepted");
  assert.equal(first.commandSequence, 0);
  assert.equal(store.eventCount(run.runId), 1);
  assert.equal(store.loadState(run.runId).revision, 1);
  assert.equal(store.events(run.runId)[0]?.intentReceipts?.length, 3);
  const repeated = store.applyTeamTick(batch, run.runId);
  assert.equal(repeated.idempotent, true);
  assert.equal(store.eventCount(run.runId), 1);
  const replay = store.verifyReplay(run.runId);
  assert.equal(replay.verified, true);
  assert.equal(replay.digest, sha256(store.loadState(run.runId)));
  store.close();
});

test("Ruleset v3 parses and verifies contain_hazard and synthetic team_tick commands", () => {
  const state = initialTeamWorld();
  state.agents[SECURITY_ID]!.location = "maintenance";
  const contain = command(state, SECURITY_ID, "contain:maintenance-breach", "contain-success");
  const result = applyWorldTick(state, {
    tickId: "contain-success",
    expectedWorldRevision: 0,
    intents: [{ commandSequence: 0, command: contain }],
  });
  if (result.status !== "accepted") throw new Error(result.reason);
  assert.equal(result.state.hazards["maintenance-breach"]?.contained, true);
  const receipt = result.journalEvents[0]?.event.intentReceipts?.[0];
  assert.equal(receipt?.verification.success, true);
  assert.ok(receipt?.facts.some((fact) => fact.kind === "hazard_contained"));
});

test("Ruleset v3 rejects malformed, stale, duplicate, nested, and illegal batches", () => {
  const state = initialTeamWorld();
  const moveEngineer = command(state, ENGINEER_ID, "move:power-junction", "edge-engineer");
  const moveMedic = command(state, MEDIC_ID, "move:power-junction", "edge-medic");
  const cases: TickBatch[] = [
    { tickId: "", expectedWorldRevision: 0, intents: [{ commandSequence: 0, command: moveEngineer }] },
    { tickId: "empty", expectedWorldRevision: 0, intents: [] },
    { tickId: "stale", expectedWorldRevision: 1, intents: [{ commandSequence: 0, command: moveEngineer }] },
    { tickId: "duplicate-sequence", expectedWorldRevision: 0, intents: [
      { commandSequence: 0, command: moveEngineer },
      { commandSequence: 0, command: moveMedic },
    ] },
    { tickId: "stale-intent", expectedWorldRevision: 0, intents: [
      { commandSequence: 0, command: { ...moveEngineer, expectedRevision: 1 } },
    ] },
    { tickId: "illegal-command", expectedWorldRevision: 0, intents: [
      { commandSequence: 0, command: { kind: "move", commandId: "illegal-move", actorId: ENGINEER_ID, expectedRevision: 0, targetRoomId: "reactor" } },
    ] },
    { tickId: "duplicate-actor", expectedWorldRevision: 0, intents: [
      { commandSequence: 0, command: moveEngineer },
      { commandSequence: 1, command: { ...moveEngineer, commandId: "edge-engineer-2" } },
    ] },
    { tickId: "duplicate-command-id", expectedWorldRevision: 0, intents: [
      { commandSequence: 0, command: moveEngineer },
      { commandSequence: 1, command: { ...moveMedic, commandId: moveEngineer.commandId } },
    ] },
  ];
  for (const batch of cases) {
    const before = sha256(state);
    const result = applyWorldTick(state, batch);
    assert.equal(result.status, "rejected", batch.tickId);
    assert.equal(sha256(state), before, batch.tickId);
  }

  const nested = {
    kind: "team_tick" as const,
    commandId: "nested",
    actorId: "team-coordinator",
    expectedRevision: 0,
    tickId: "nested",
    intents: [moveEngineer],
  };
  const nestedResult = applyWorldTick(state, {
    tickId: "nested-outer",
    expectedWorldRevision: 0,
    intents: [{ commandSequence: 0, command: nested }],
  });
  assert.equal(nestedResult.status, "accepted");

  const staleSynthetic = applyWorldTick(state, {
    tickId: "stale-synthetic",
    expectedWorldRevision: 0,
    intents: [{ commandSequence: 0, command: { ...nested, commandId: "stale-synthetic", expectedRevision: 1 } }],
  });
  assert.equal(staleSynthetic.status, "rejected");
});

test("v3 command wrapper preserves direct team admission and rejection boundaries", () => {
  const state = initialTeamWorld();
  const move = command(state, ENGINEER_ID, "move:power-junction", "wrapper-move");
  const direct = applyWorldCommand(state, move);
  assert.equal(direct.status, "accepted");

  const stale = applyWorldCommand(state, { ...move, commandId: "wrapper-stale", expectedRevision: 1 });
  assert.equal(stale.status, "rejected");
  assert.equal(stale.status === "rejected" ? stale.code : null, "stale_revision");

  const teamCommand = {
    kind: "team_tick" as const,
    commandId: "wrapper-team",
    actorId: "team-coordinator",
    expectedRevision: 0,
    tickId: "wrapper-team",
    intents: [
      move,
      command(state, MEDIC_ID, "move:power-junction", "wrapper-medic"),
    ],
  };
  assert.equal(validateWorldCommand(state, teamCommand)?.code, "invalid_command");
  const team = applyWorldCommand(state, teamCommand);
  assert.equal(team.status, "accepted");
  assert.equal(team.status === "accepted" ? team.event.intentReceipts?.length : 0, 2);
});

test("team scenario fails only after every specialist is incapacitated", () => {
  const state = initialTeamWorld();
  state.agents[ENGINEER_ID]!.health = 0;
  evaluateMission(state);
  assert.equal(state.mission.status, "running");
  state.agents[MEDIC_ID]!.health = 0;
  state.agents[SECURITY_ID]!.health = 0;
  evaluateMission(state);
  assert.equal(state.mission.status, "failure");
  assert.equal(state.mission.reason, "team_incapacitated");
});
