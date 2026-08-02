import assert from "node:assert/strict";
import test from "node:test";

import { sha256 } from "../src/digest.ts";
import {
  STATION_ZERO_FACTION_IDS,
  STATION_ZERO_RESOLUTION_PHASES,
  STATION_ZERO_TURN_PHASES,
  STATION_ZERO_V3_ABILITIES,
  STATION_ZERO_V3_COMMANDER_ABILITIES,
  STATION_ZERO_V3_EQUIPMENT,
  STATION_ZERO_V3_ITEMS,
  STATION_ZERO_V3_OBJECTIVES,
  STATION_ZERO_V3_P0_CONTRACT,
  assertStationZeroFactionTurnPlan,
  assertStationZeroStandingOrder,
  assertStationZeroTurnBatch,
  assertStationZeroV3Content,
  assertStationZeroV3World,
  createStationZeroV3Genesis,
  stationZeroV3GenesisDigest,
  type StationZeroFactionTurnPlan,
  type StationZeroStandingOrder,
  type StationZeroTurnBatch,
} from "../src/station-zero-v3/index.ts";

function waitPlan(factionId: "rescue" | "pirate" | "swarm", actorId: string): StationZeroFactionTurnPlan {
  return {
    planId: `plan:${factionId}:0`,
    factionId,
    expectedWorldRevision: 0,
    expectedTurn: 0,
    standingOrderRevision: 0,
    commanderActions: [],
    actorIntents: [{
      intentId: `intent:${actorId}:wait`,
      actorId,
      factionId,
      expectedWorldRevision: 0,
      expectedTurn: 0,
      kind: "wait",
    }],
    committedBy: factionId === "rescue" ? "player:mission-control" : `agent:${factionId}`,
  };
}

test("P0 freezes one asymmetric deterministic tactical encounter rather than a general engine", () => {
  assert.equal(STATION_ZERO_V3_P0_CONTRACT.productForm, "single-player-asymmetric-turn-based-tactical-encounter");
  assert.equal(STATION_ZERO_V3_P0_CONTRACT.defaultPlayerFactionId, "rescue");
  assert.deepEqual(STATION_ZERO_V3_P0_CONTRACT.turnPhases, STATION_ZERO_TURN_PHASES);
  assert.deepEqual(STATION_ZERO_V3_P0_CONTRACT.resolutionPhases, STATION_ZERO_RESOLUTION_PHASES);
  assert.equal(STATION_ZERO_V3_P0_CONTRACT.randomnessPolicy.committedTurnIsDeterministic, true);
  assert.equal(STATION_ZERO_V3_P0_CONTRACT.randomnessPolicy.hiddenHitRolls, false);
  assert.equal(STATION_ZERO_V3_P0_CONTRACT.runBoundary.routeMapDeferred, true);
  assert.equal(STATION_ZERO_V3_P0_CONTRACT.runBoundary.metaProgressionDeferred, true);
  assert.ok(STATION_ZERO_V3_P0_CONTRACT.nonGoals.includes("a general RPG engine"));
  assert.deepEqual(
    STATION_ZERO_V3_P0_CONTRACT.influences.map((entry) => entry.influenceId),
    ["roguelite", "tactical-rpg", "sandbox", "systemic-sim", "character-sim"],
  );
});

test("content catalogs are closed, referenced, deterministic, and faction-distinct", () => {
  assert.doesNotThrow(() => assertStationZeroV3Content());
  assert.ok(STATION_ZERO_V3_ABILITIES.length >= 10);
  assert.ok(STATION_ZERO_V3_EQUIPMENT.length >= 10);
  assert.ok(STATION_ZERO_V3_ITEMS.some((entry) => entry.itemId === "research-core"));
  assert.ok(STATION_ZERO_V3_ITEMS.some((entry) => entry.equipmentId === "medical-drone"));
  assert.ok(STATION_ZERO_V3_ABILITIES.every((entry) => Number.isSafeInteger(entry.damage)));
  assert.ok(STATION_ZERO_V3_ABILITIES.every((entry) => !("accuracy" in entry)));
  for (const factionId of STATION_ZERO_FACTION_IDS) {
    assert.ok(STATION_ZERO_V3_COMMANDER_ABILITIES.some((entry) => entry.factionIds.includes(factionId)));
    const objectives = STATION_ZERO_V3_OBJECTIVES.filter((entry) => entry.factionId === factionId);
    assert.ok(objectives.some((entry) => entry.mandatory));
    assert.ok(objectives.some((entry) => !entry.mandatory));
  }
});

test("fixed Genesis contains the complete three-faction tactical problem and limited information", () => {
  const state = createStationZeroV3Genesis();
  assert.doesNotThrow(() => assertStationZeroV3World(state));
  assert.equal(state.schemaVersion, 3);
  assert.equal(state.scenarioVersion, 3);
  assert.equal(state.rulesetVersion, 4);
  assert.equal(state.encounter.turnLimit, 14);
  assert.equal(state.encounter.playerFactionId, "rescue");
  assert.equal(Object.keys(state.rooms).length, 8);
  assert.equal(Object.keys(state.zones).length, 20);
  assert.equal(Object.keys(state.actors).length, 12);
  assert.equal(Object.values(state.actors).filter((entry) => entry.factionId === "rescue").length, 3);
  assert.equal(Object.values(state.actors).filter((entry) => entry.factionId === "pirate").length, 3);
  assert.equal(Object.values(state.actors).filter((entry) => entry.factionId === "swarm").length, 4);
  assert.equal(Object.values(state.actors).filter((entry) => entry.kind === "civilian").length, 2);
  assert.equal(state.factions.rescue.controllerKind, "player");
  assert.equal(state.factions.pirate.controllerKind, "agent");
  assert.equal(state.factions.swarm.controllerKind, "agent");
  assert.equal(state.environment.batteryCharge + state.environment.energyConsumed, state.environment.batteryInitial);

  const rescueKnowledge = state.factionKnowledge.rescue;
  assert.deepEqual(Object.keys(rescueKnowledge.knownActors).sort(), ["engineer-imani", "medic-reyes", "security-chen"]);
  assert.equal(rescueKnowledge.knownActors["pirate-captain-veyra"], undefined);
  assert.equal(rescueKnowledge.knownActors["hive-alpha"], undefined);
  assert.equal(rescueKnowledge.knownGroundItemIds.includes("ground:research-core"), false);

  assert.equal(stationZeroV3GenesisDigest(), sha256(state));
  assert.equal(stationZeroV3GenesisDigest(), stationZeroV3GenesisDigest());
  assert.notEqual(stationZeroV3GenesisDigest("another-seed"), stationZeroV3GenesisDigest());
});

test("World validation rejects identity, capacity, knowledge, equipment, and ledger divergence", () => {
  const identity = createStationZeroV3Genesis();
  identity.rulesetVersion = 3 as never;
  assert.throws(() => assertStationZeroV3World(identity), /identity mismatch/);

  const capacity = createStationZeroV3Genesis();
  capacity.zones["rescue-airlock"]!.capacity = 1;
  assert.throws(() => assertStationZeroV3World(capacity), /above capacity/);

  const knowledge = createStationZeroV3Genesis();
  delete knowledge.factionKnowledge.rescue.knownActors["engineer-imani"];
  assert.throws(() => assertStationZeroV3World(knowledge), /does not know its own Actor/);

  const equipment = createStationZeroV3Genesis();
  equipment.actors["security-chen"]!.equipment.weapon = "invented-weapon";
  assert.throws(() => assertStationZeroV3World(equipment), /unknown Equipment/);

  const ledger = createStationZeroV3Genesis();
  ledger.environment.batteryCharge -= 1;
  assert.throws(() => assertStationZeroV3World(ledger), /not conserved/);
});

test("standing orders bind player strategy without granting direct World mutation", () => {
  const state = createStationZeroV3Genesis();
  const order: StationZeroStandingOrder = {
    orderId: "order:security:protect-engineer",
    factionId: "rescue",
    actorId: "security-chen",
    objectiveId: "rescue-team-survives",
    priorityTargetActorId: null,
    protectedActorId: "engineer-imani",
    retreatHealthThreshold: 0.3,
    lethalForce: "permitted",
    collateralPolicy: "forbidden",
    lootPolicy: "mission-only",
    revision: 1,
  };
  assert.doesNotThrow(() => assertStationZeroStandingOrder(state, order));

  const hiddenTarget = { ...order, orderId: "order:hidden-target", priorityTargetActorId: "hive-alpha" };
  assert.throws(() => assertStationZeroStandingOrder(state, hiddenTarget), /outside Faction knowledge/);

  const foreignObjective = { ...order, orderId: "order:foreign-objective", objectiveId: "pirate-steal-core" };
  assert.throws(() => assertStationZeroStandingOrder(state, foreignObjective), /outside its Faction/);
});

test("Turn Plan admission enforces faction knowledge, command budgets, one intent per Actor, and exact heads", () => {
  const state = createStationZeroV3Genesis();
  state.encounter.phase = "commitment";

  const rescue = waitPlan("rescue", "engineer-imani");
  rescue.commanderActions.push({
    commanderActionId: "commander:rescue:scan",
    factionId: "rescue",
    commanderAbilityId: "orbital-scan",
    expectedWorldRevision: 0,
    expectedTurn: 0,
    targetActorId: null,
    targetZoneId: "reactor-entry",
    targetPassageId: null,
    targetSystemId: null,
    targetFactionId: null,
  });
  assert.doesNotThrow(() => assertStationZeroFactionTurnPlan(state, rescue));

  const hiddenAttack = waitPlan("rescue", "security-chen");
  hiddenAttack.actorIntents = [{
    intentId: "intent:security:hidden-attack",
    actorId: "security-chen",
    factionId: "rescue",
    expectedWorldRevision: 0,
    expectedTurn: 0,
    kind: "attack",
    abilityId: "pulse-shot",
    targetActorId: "hive-alpha",
  }];
  assert.throws(() => assertStationZeroFactionTurnPlan(state, hiddenAttack), /outside Faction knowledge/);

  const duplicateActor = waitPlan("rescue", "engineer-imani");
  duplicateActor.actorIntents.push({
    intentId: "intent:engineer:move",
    actorId: "engineer-imani",
    factionId: "rescue",
    expectedWorldRevision: 0,
    expectedTurn: 0,
    kind: "move",
    targetZoneId: "command-deck",
  });
  assert.throws(() => assertStationZeroFactionTurnPlan(state, duplicateActor), /multiple Intents/);

  const inventedInteraction = waitPlan("rescue", "engineer-imani");
  inventedInteraction.actorIntents = [{
    intentId: "intent:engineer:invented-repair",
    actorId: "engineer-imani",
    factionId: "rescue",
    expectedWorldRevision: 0,
    expectedTurn: 0,
    kind: "interact",
    operationId: "repair",
    targetId: "invented-system",
  }];
  assert.throws(() => assertStationZeroFactionTurnPlan(state, inventedInteraction), /unknown System/);

  const hiddenPickup = waitPlan("rescue", "engineer-imani");
  hiddenPickup.actorIntents = [{
    intentId: "intent:engineer:hidden-pickup",
    actorId: "engineer-imani",
    factionId: "rescue",
    expectedWorldRevision: 0,
    expectedTurn: 0,
    kind: "pickup",
    groundItemId: "ground:research-core",
    quantity: 1,
  }];
  assert.throws(() => assertStationZeroFactionTurnPlan(state, hiddenPickup), /outside Faction knowledge/);

  const stale = waitPlan("rescue", "engineer-imani");
  stale.expectedWorldRevision = 1;
  assert.throws(() => assertStationZeroFactionTurnPlan(state, stale), /current revision/);

  const overBudget = waitPlan("rescue", "engineer-imani");
  overBudget.commanderActions = [0, 1, 2, 3].map((index) => ({
    commanderActionId: `commander:rescue:scan:${index}`,
    factionId: "rescue" as const,
    commanderAbilityId: "orbital-scan",
    expectedWorldRevision: 0,
    expectedTurn: 0,
    targetActorId: null,
    targetZoneId: "reactor-entry",
    targetPassageId: null,
    targetSystemId: null,
    targetFactionId: null,
  }));
  assert.throws(() => assertStationZeroFactionTurnPlan(state, overBudget), /exceeds Command Points/);

  const overCharges = waitPlan("rescue", "engineer-imani");
  overCharges.commanderActions = [0, 1].map((index) => ({
    commanderActionId: `commander:rescue:lockdown:${index}`,
    factionId: "rescue" as const,
    commanderAbilityId: "bulkhead-lockdown",
    expectedWorldRevision: 0,
    expectedTurn: 0,
    targetActorId: null,
    targetZoneId: null,
    targetPassageId: index === 0 ? "passage:deck-junction" : "passage:deck-reactor",
    targetSystemId: null,
    targetFactionId: null,
  }));
  assert.throws(() => assertStationZeroFactionTurnPlan(state, overCharges), /exceeds Commander Ability/);
});

test("one deterministic Turn Batch requires exactly one complete Plan from every faction", () => {
  const state = createStationZeroV3Genesis();
  state.encounter.phase = "commitment";
  const batch: StationZeroTurnBatch = {
    turnBatchId: "turn-batch:0",
    expectedWorldRevision: 0,
    expectedTurn: 0,
    factionPlans: [
      waitPlan("rescue", "engineer-imani"),
      waitPlan("pirate", "pirate-captain-veyra"),
      waitPlan("swarm", "hive-alpha"),
    ],
  };
  assert.doesNotThrow(() => assertStationZeroTurnBatch(state, batch));

  const missing = structuredClone(batch);
  missing.factionPlans.pop();
  assert.throws(() => assertStationZeroTurnBatch(state, missing), /exactly one Plan per Faction/);

  const duplicated = structuredClone(batch);
  duplicated.factionPlans[2] = waitPlan("pirate", "pirate-raider-holt");
  assert.throws(() => assertStationZeroTurnBatch(state, duplicated), /rescue, pirate, and swarm/);

  const wrongPhase = createStationZeroV3Genesis();
  assert.throws(() => assertStationZeroTurnBatch(wrongPhase, batch), /commitment phase/);
});
