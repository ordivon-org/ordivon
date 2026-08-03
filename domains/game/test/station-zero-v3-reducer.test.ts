import assert from "node:assert/strict";
import test from "node:test";

import { sha256 } from "../src/digest.ts";
import {
  applyStationZeroV3Turn,
  createStationZeroV3Genesis,
  prepareStationZeroV3Commitment,
  replayStationZeroV3History,
  replayStationZeroV3Turn,
  type StationZeroActorIntent,
  type StationZeroCommanderAction,
  type StationZeroFactionId,
  type StationZeroFactionTurnPlan,
  type StationZeroTurnApplyResult,
  type StationZeroTurnBatch,
  type StationZeroV3WorldState,
} from "../src/station-zero-v3/index.ts";

function waitIntent(
  state: StationZeroV3WorldState,
  factionId: StationZeroFactionId,
  actorId: string,
): StationZeroActorIntent {
  return {
    intentId: `intent:${state.encounter.turn}:${actorId}:wait`,
    actorId,
    factionId,
    expectedWorldRevision: state.revision,
    expectedTurn: state.encounter.turn,
    kind: "wait",
  };
}

function plan(
  state: StationZeroV3WorldState,
  factionId: StationZeroFactionId,
  actorIntents: StationZeroActorIntent[] = [],
  commanderActions: StationZeroCommanderAction[] = [],
): StationZeroFactionTurnPlan {
  return {
    planId: `plan:${state.encounter.turn}:${factionId}`,
    factionId,
    expectedWorldRevision: state.revision,
    expectedTurn: state.encounter.turn,
    standingOrderRevision: state.encounter.activePlanRevision,
    commanderActions,
    actorIntents,
    committedBy: factionId === "rescue" ? "player:mission-control" : `agent:${factionId}`,
  };
}

function batch(
  state: StationZeroV3WorldState,
  plans: Partial<Record<StationZeroFactionId, StationZeroFactionTurnPlan>> = {},
  turnBatchId = `turn-batch:${state.encounter.turn}`,
): StationZeroTurnBatch {
  return {
    turnBatchId,
    expectedWorldRevision: state.revision,
    expectedTurn: state.encounter.turn,
    factionPlans: [
      plans.rescue ?? plan(state, "rescue"),
      plans.pirate ?? plan(state, "pirate"),
      plans.swarm ?? plan(state, "swarm"),
    ],
  };
}

function accepted(result: StationZeroTurnApplyResult): Extract<StationZeroTurnApplyResult, { status: "accepted" }> {
  if (result.status === "rejected") throw new Error(result.reason);
  return result;
}

function resolution(result: Extract<StationZeroTurnApplyResult, { status: "accepted" }>, intentId: string) {
  const retained = result.resolution.intentResolutions.find((entry) => entry.intentId === intentId);
  assert.ok(retained, `missing Intent Resolution ${intentId}`);
  return retained;
}

function revealActor(state: StationZeroV3WorldState, factionId: StationZeroFactionId, actorId: string): void {
  const actor = state.actors[actorId]!;
  state.factionKnowledge[factionId].knownActors[actorId] = {
    actorId,
    lastKnownZoneId: actor.position.zoneId,
    observedLifeState: actor.lifeState,
    observedHealthBand: actor.health >= actor.maximumHealth * 0.75
      ? "healthy"
      : actor.health >= actor.maximumHealth * 0.35
        ? "wounded"
        : "critical",
    observedAtTurn: state.encounter.turn,
    confidence: "confirmed",
  };
}

function fullGenesisBatch(state: StationZeroV3WorldState): StationZeroTurnBatch {
  const engineerMove: StationZeroActorIntent = {
    intentId: "intent:engineer:move-command",
    actorId: "engineer-imani",
    factionId: "rescue",
    expectedWorldRevision: state.revision,
    expectedTurn: state.encounter.turn,
    kind: "move",
    targetZoneId: "command-deck",
  };
  const medicMove: StationZeroActorIntent = {
    intentId: "intent:medic:move-command",
    actorId: "medic-reyes",
    factionId: "rescue",
    expectedWorldRevision: state.revision,
    expectedTurn: state.encounter.turn,
    kind: "move",
    targetZoneId: "command-deck",
  };
  const securityGuard: StationZeroActorIntent = {
    intentId: "intent:security:guard-command",
    actorId: "security-chen",
    factionId: "rescue",
    expectedWorldRevision: state.revision,
    expectedTurn: state.encounter.turn,
    kind: "guard",
    protectedActorId: null,
    watchedZoneId: "command-deck",
  };
  const pirateMove: StationZeroActorIntent = {
    intentId: "intent:captain:move-crates",
    actorId: "pirate-captain-veyra",
    factionId: "pirate",
    expectedWorldRevision: state.revision,
    expectedTurn: state.encounter.turn,
    kind: "move",
    targetZoneId: "crate-cover",
  };
  const stalkerMove: StationZeroActorIntent = {
    intentId: "intent:stalker:move-life-entry",
    actorId: "swarm-stalker-kappa",
    factionId: "swarm",
    expectedWorldRevision: state.revision,
    expectedTurn: state.encounter.turn,
    kind: "move",
    targetZoneId: "life-entry",
  };
  const hiveWait = waitIntent(state, "swarm", "hive-alpha");
  return batch(state, {
    rescue: plan(state, "rescue", [medicMove, securityGuard, engineerMove]),
    pirate: plan(state, "pirate", [pirateMove]),
    swarm: plan(state, "swarm", [hiveWait, stalkerMove]),
  });
}

test("P1 resolves one complete three-faction Turn, advances environment once, and replays every Intent", () => {
  const state = prepareStationZeroV3Commitment(createStationZeroV3Genesis());
  const before = structuredClone(state);
  const result = accepted(applyStationZeroV3Turn(state, fullGenesisBatch(state)));

  assert.deepEqual(state, before, "the reducer must not mutate its input");
  assert.equal(result.state.revision, 1);
  assert.equal(result.state.encounter.turn, 1);
  assert.equal(result.state.encounter.phase, "aftermath");
  assert.equal(result.state.environment.batteryCharge, 46);
  assert.equal(result.state.environment.energyConsumed, 2);
  assert.equal(result.state.environment.oxygen, 67);
  assert.equal(result.state.environment.reactorHeat, 70);
  assert.equal(result.state.environment.batteryCharge + result.state.environment.energyConsumed, 48);
  assert.equal(result.resolution.intentResolutions.length, 6);
  assert.ok(result.resolution.intentResolutions.every((entry) => entry.verificationPassed));
  assert.equal(result.resolution.facts.filter((entry) => entry.kind === "environment_changed" && entry.resourceId === "battery").length, 1);
  assert.equal(result.resolution.facts.filter((entry) => entry.kind === "environment_changed" && entry.resourceId === "oxygen").length, 1);
  assert.equal(result.resolution.facts.filter((entry) => entry.kind === "environment_changed" && entry.resourceId === "reactor-heat").length, 1);
  assert.match(result.resolution.deterministicDigest, /^[a-f0-9]{64}$/);
  assert.match(result.record.recordDigest, /^[a-f0-9]{64}$/);

  const replay = replayStationZeroV3Turn(state, result.record);
  assert.deepEqual(replay.state, result.state);
  assert.deepEqual(replay.resolution, result.resolution);
  assert.equal(replay.record.recordDigest, result.record.recordDigest);
});

test("Turn result and record identity are independent from Faction Plan and Intent input order", () => {
  const state = prepareStationZeroV3Commitment(createStationZeroV3Genesis());
  const original = fullGenesisBatch(state);
  const reordered = structuredClone(original);
  reordered.factionPlans.reverse();
  for (const factionPlan of reordered.factionPlans) {
    factionPlan.actorIntents.reverse();
    factionPlan.commanderActions.reverse();
  }

  const left = accepted(applyStationZeroV3Turn(state, original));
  const right = accepted(applyStationZeroV3Turn(state, reordered));
  assert.deepEqual(right.state, left.state);
  assert.equal(right.resolution.deterministicDigest, left.resolution.deterministicDigest);
  assert.equal(right.record.recordDigest, left.record.recordDigest);
});

test("Zone contention deterministically awards limited capacity by initiative", () => {
  const state = prepareStationZeroV3Commitment(createStationZeroV3Genesis());
  state.actors["security-chen"]!.position.zoneId = "reactor-cover";
  state.actors["pirate-captain-veyra"]!.position.zoneId = "reactor-entry";
  state.zones["command-deck"]!.capacity = 1;

  const engineerMove: StationZeroActorIntent = {
    intentId: "intent:engineer:contend-command",
    actorId: "engineer-imani",
    factionId: "rescue",
    expectedWorldRevision: 0,
    expectedTurn: 0,
    kind: "move",
    targetZoneId: "command-deck",
  };
  const pirateMove: StationZeroActorIntent = {
    intentId: "intent:captain:contend-command",
    actorId: "pirate-captain-veyra",
    factionId: "pirate",
    expectedWorldRevision: 0,
    expectedTurn: 0,
    kind: "move",
    targetZoneId: "command-deck",
  };
  const result = accepted(applyStationZeroV3Turn(state, batch(state, {
    rescue: plan(state, "rescue", [engineerMove]),
    pirate: plan(state, "pirate", [pirateMove]),
    swarm: plan(state, "swarm", [waitIntent(state, "swarm", "hive-alpha")]),
  })));

  assert.equal(result.state.actors["pirate-captain-veyra"]!.position.zoneId, "command-deck");
  assert.equal(result.state.actors["engineer-imani"]!.position.zoneId, "rescue-airlock");
  assert.equal(resolution(result, pirateMove.intentId).status, "executed");
  assert.equal(resolution(result, engineerMove.intentId).status, "contested");
  assert.equal(resolution(result, engineerMove.intentId).reason, "target_zone_capacity_lost");
});

test("Overwatch is a reaction that can incapacitate and interrupt committed movement", () => {
  const state = prepareStationZeroV3Commitment(createStationZeroV3Genesis());
  state.actors["pirate-captain-veyra"]!.position.zoneId = "reactor-entry";
  state.actors["pirate-captain-veyra"]!.health = 8;

  const guard: StationZeroActorIntent = {
    intentId: "intent:security:overwatch-command",
    actorId: "security-chen",
    factionId: "rescue",
    expectedWorldRevision: 0,
    expectedTurn: 0,
    kind: "guard",
    protectedActorId: null,
    watchedZoneId: "command-deck",
  };
  const move: StationZeroActorIntent = {
    intentId: "intent:captain:breach-command",
    actorId: "pirate-captain-veyra",
    factionId: "pirate",
    expectedWorldRevision: 0,
    expectedTurn: 0,
    kind: "move",
    targetZoneId: "command-deck",
  };
  const result = accepted(applyStationZeroV3Turn(state, batch(state, {
    rescue: plan(state, "rescue", [guard]),
    pirate: plan(state, "pirate", [move]),
  })));

  assert.equal(resolution(result, guard.intentId).status, "executed");
  assert.equal(resolution(result, move.intentId).status, "interrupted");
  assert.equal(result.state.actors["pirate-captain-veyra"]!.position.zoneId, "reactor-entry");
  assert.equal(result.state.actors["pirate-captain-veyra"]!.lifeState, "incapacitated");
  assert.ok(result.resolution.facts.some((entry) => entry.kind === "actor_attacked" && entry.abilityId === "overwatch"));
});

test("multiple attackers may legally focus one target and both consequences remain in one Turn", () => {
  const state = prepareStationZeroV3Commitment(createStationZeroV3Genesis());
  const captain = state.actors["pirate-captain-veyra"]!;
  captain.position.zoneId = "command-deck";
  captain.health = 45;
  revealActor(state, "rescue", captain.actorId);

  const securityAttack: StationZeroActorIntent = {
    intentId: "intent:security:focus-captain",
    actorId: "security-chen",
    factionId: "rescue",
    expectedWorldRevision: 0,
    expectedTurn: 0,
    kind: "attack",
    abilityId: "precision-burst",
    targetActorId: captain.actorId,
  };
  const engineerAttack: StationZeroActorIntent = {
    intentId: "intent:engineer:focus-captain",
    actorId: "engineer-imani",
    factionId: "rescue",
    expectedWorldRevision: 0,
    expectedTurn: 0,
    kind: "attack",
    abilityId: "pulse-shot",
    targetActorId: captain.actorId,
  };
  const result = accepted(applyStationZeroV3Turn(state, batch(state, {
    rescue: plan(state, "rescue", [engineerAttack, securityAttack]),
  })));

  assert.equal(resolution(result, securityAttack.intentId).status, "executed");
  assert.equal(resolution(result, engineerAttack.intentId).status, "executed");
  assert.equal(result.state.actors[captain.actorId]!.health, 0);
  assert.equal(result.state.actors[captain.actorId]!.lifeState, "incapacitated");
  assert.equal(result.resolution.facts.filter((entry) => entry.kind === "actor_attacked" && entry.targetActorId === captain.actorId).length, 2);
});

test("a lethal earlier attack drops equipment while a later local attack invalidates without rolling back the Turn", () => {
  const state = prepareStationZeroV3Commitment(createStationZeroV3Genesis());
  const raider = state.actors["pirate-raider-holt"]!;
  raider.position.zoneId = "command-deck";
  raider.health = 10;
  revealActor(state, "rescue", raider.actorId);

  const securityAttack: StationZeroActorIntent = {
    intentId: "intent:security:kill-raider",
    actorId: "security-chen",
    factionId: "rescue",
    expectedWorldRevision: 0,
    expectedTurn: 0,
    kind: "attack",
    abilityId: "precision-burst",
    targetActorId: raider.actorId,
  };
  const engineerAttack: StationZeroActorIntent = {
    intentId: "intent:engineer:late-raider-shot",
    actorId: "engineer-imani",
    factionId: "rescue",
    expectedWorldRevision: 0,
    expectedTurn: 0,
    kind: "attack",
    abilityId: "pulse-shot",
    targetActorId: raider.actorId,
  };
  const result = accepted(applyStationZeroV3Turn(state, batch(state, {
    rescue: plan(state, "rescue", [engineerAttack, securityAttack]),
  })));

  assert.equal(result.state.revision, 1);
  assert.equal(result.state.actors[raider.actorId]!.lifeState, "dead");
  assert.deepEqual(result.state.actors[raider.actorId]!.equipment, {});
  assert.equal(resolution(result, securityAttack.intentId).status, "executed");
  assert.equal(resolution(result, engineerAttack.intentId).status, "invalidated");
  assert.equal(resolution(result, engineerAttack.intentId).reason, "target_no_longer_attackable");
  const droppedItems = Object.values(result.state.groundItems)
    .filter((entry) => entry.groundItemId.includes(raider.actorId))
    .map((entry) => entry.itemId)
    .sort();
  assert.deepEqual(droppedItems, ["boarding-armor-item", "pirate-scattergun-item"]);
  assert.equal(result.resolution.facts.filter((entry) => entry.kind === "ground_item_dropped" && entry.actorId === raider.actorId).length, 2);

  const rescueObservation = result.resolution.observations.rescue;
  const swarmObservation = result.resolution.observations.swarm;
  const attackFactIds = result.resolution.facts.filter((entry) => entry.kind === "actor_attacked").map((entry) => entry.factId);
  assert.ok(attackFactIds.every((factId) => rescueObservation.visibleFactIds.includes(factId)));
  assert.ok(attackFactIds.every((factId) => !swarmObservation.visibleFactIds.includes(factId)));
  assert.ok(result.resolution.facts.filter((entry) => entry.kind === "environment_changed").every((entry) =>
    swarmObservation.visibleFactIds.includes(entry.factId)));
});

test("ground loot can be picked up and objective cargo can be extracted on a later Turn", () => {
  const pickupState = prepareStationZeroV3Commitment(createStationZeroV3Genesis());
  pickupState.actors["pirate-hacker-nyx"]!.position.zoneId = "reactor-console";
  const pickup: StationZeroActorIntent = {
    intentId: "intent:hacker:pickup-core",
    actorId: "pirate-hacker-nyx",
    factionId: "pirate",
    expectedWorldRevision: 0,
    expectedTurn: 0,
    kind: "pickup",
    groundItemId: "ground:research-core",
    quantity: 1,
  };
  const picked = accepted(applyStationZeroV3Turn(pickupState, batch(pickupState, {
    pirate: plan(pickupState, "pirate", [pickup]),
  })));
  assert.equal(picked.state.groundItems["ground:research-core"], undefined);
  assert.ok(picked.state.actors["pirate-hacker-nyx"]!.inventoryItemIds.includes("research-core"));
  assert.equal(resolution(picked, pickup.intentId).status, "executed");

  const extractionState = prepareStationZeroV3Commitment(createStationZeroV3Genesis());
  extractionState.actors["pirate-captain-veyra"]!.inventoryItemIds.push("research-core");
  const extract: StationZeroActorIntent = {
    intentId: "intent:captain:extract-core",
    actorId: "pirate-captain-veyra",
    factionId: "pirate",
    expectedWorldRevision: 0,
    expectedTurn: 0,
    kind: "extract",
    extractionId: "pirate-shuttle-alpha",
  };
  const extracted = accepted(applyStationZeroV3Turn(extractionState, batch(extractionState, {
    pirate: plan(extractionState, "pirate", [extract]),
  })));
  assert.equal(extracted.state.actors["pirate-captain-veyra"]!.lifeState, "extracted");
  assert.equal(extracted.state.factions.pirate.objectiveProgress["pirate-steal-core"]!.status, "completed");
  assert.equal(extracted.state.factions.pirate.objectiveProgress["pirate-crew-survives"]!.status, "completed");
  assert.ok(extracted.resolution.facts.some((entry) => entry.kind === "item_extracted" && entry.itemId === "research-core"));
});

test("Commander power reroute and local repair alter the coupled deterministic environment", () => {
  const state = prepareStationZeroV3Commitment(createStationZeroV3Genesis());
  state.actors["engineer-imani"]!.position.zoneId = "reactor-console";
  const repair: StationZeroActorIntent = {
    intentId: "intent:engineer:repair-cooling",
    actorId: "engineer-imani",
    factionId: "rescue",
    expectedWorldRevision: 0,
    expectedTurn: 0,
    kind: "interact",
    operationId: "repair",
    targetId: "cooling",
  };
  const reroute: StationZeroCommanderAction = {
    commanderActionId: "commander:rescue:power-cooling",
    factionId: "rescue",
    commanderAbilityId: "power-reroute",
    expectedWorldRevision: 0,
    expectedTurn: 0,
    targetActorId: null,
    targetZoneId: null,
    targetPassageId: null,
    targetSystemId: "cooling",
    targetFactionId: null,
  };
  const result = accepted(applyStationZeroV3Turn(state, batch(state, {
    rescue: plan(state, "rescue", [repair], [reroute]),
  })));
  assert.equal(result.state.systems.cooling!.integrity, 0.88);
  assert.equal(result.state.systems.cooling!.powered, true);
  assert.equal(result.state.environment.batteryCharge, 43);
  assert.equal(result.state.environment.energyConsumed, 5);
  assert.equal(result.state.environment.reactorHeat, 54);
  assert.equal(resolution(result, repair.intentId).status, "executed");
});

test("invalid Turn admission rejects before mutation and retained records fail closed when tampered", () => {
  const state = prepareStationZeroV3Commitment(createStationZeroV3Genesis());
  const beforeDigest = sha256(state);
  const invalid = fullGenesisBatch(state);
  invalid.expectedWorldRevision = 99;
  const rejected = applyStationZeroV3Turn(state, invalid);
  assert.equal(rejected.status, "rejected");
  assert.equal(sha256(state), beforeDigest);

  const malformed = structuredClone(state);
  malformed.environment.batteryCharge -= 1;
  const malformedResult = applyStationZeroV3Turn(malformed, fullGenesisBatch(malformed));
  assert.equal(malformedResult.status, "rejected");
  assert.match(malformedResult.status === "rejected" ? malformedResult.reason : "", /Battery ledger/);

  const acceptedTurn = accepted(applyStationZeroV3Turn(state, fullGenesisBatch(state)));
  const tampered = structuredClone(acceptedTurn.record);
  tampered.stateDigestAfter = "0".repeat(64);
  assert.throws(() => replayStationZeroV3Turn(state, tampered), /Record digest mismatch/);
});


test("a multi-Turn history replays from raw Genesis through every retained Resolution", () => {
  const genesis = createStationZeroV3Genesis();
  const firstState = prepareStationZeroV3Commitment(genesis);
  const first = accepted(applyStationZeroV3Turn(firstState, fullGenesisBatch(firstState)));

  const secondState = prepareStationZeroV3Commitment(first.state);
  const second = accepted(applyStationZeroV3Turn(secondState, batch(secondState, {
    rescue: plan(secondState, "rescue", [waitIntent(secondState, "rescue", "engineer-imani")]),
    pirate: plan(secondState, "pirate", [waitIntent(secondState, "pirate", "pirate-captain-veyra")]),
    swarm: plan(secondState, "swarm", [waitIntent(secondState, "swarm", "hive-alpha")]),
  })));

  const replay = replayStationZeroV3History(genesis, [first.record, second.record]);
  assert.equal(replay.turns.length, 2);
  assert.deepEqual(replay.state, second.state);
  assert.deepEqual(
    replay.turns.flatMap((turn) => turn.resolution.intentResolutions.map((entry) => entry.intentId)),
    [first, second].flatMap((turn) => turn.resolution.intentResolutions.map((entry) => entry.intentId)),
  );
});


test("terminal evaluation assigns independent victory, partial, and failure outcomes", () => {
  const state = prepareStationZeroV3Commitment(createStationZeroV3Genesis());
  state.encounter.turnLimit = 1;
  state.actors["pirate-captain-veyra"]!.inventoryItemIds.push("research-core");
  const extract: StationZeroActorIntent = {
    intentId: "intent:captain:terminal-extract",
    actorId: "pirate-captain-veyra",
    factionId: "pirate",
    expectedWorldRevision: 0,
    expectedTurn: 0,
    kind: "extract",
    extractionId: "pirate-shuttle-terminal",
  };
  const result = accepted(applyStationZeroV3Turn(state, batch(state, {
    pirate: plan(state, "pirate", [extract]),
  })));

  assert.equal(result.state.encounter.status, "terminal");
  assert.equal(result.state.encounter.reason, "turn_limit");
  assert.equal(result.state.factions.pirate.outcome, "victory");
  assert.equal(result.state.factions.swarm.outcome, "partial");
  assert.equal(result.state.factions.rescue.outcome, "failure");
  assert.equal(result.resolution.facts.filter((entry) => entry.kind === "faction_outcome_changed").length, 3);
});

test("Cleanup Ability consumes Biomass and spawns a deterministic policy Actor", () => {
  const state = prepareStationZeroV3Commitment(createStationZeroV3Genesis());
  const broodCall: StationZeroActorIntent = {
    intentId: "intent:hive:brood-call",
    actorId: "hive-alpha",
    factionId: "swarm",
    expectedWorldRevision: 0,
    expectedTurn: 0,
    kind: "use_ability",
    abilityId: "brood-call",
    targetActorId: null,
    targetZoneId: "maintenance-nest",
    targetSystemId: null,
    targetHazardId: null,
  };
  const result = accepted(applyStationZeroV3Turn(state, batch(state, {
    swarm: plan(state, "swarm", [broodCall]),
  })));

  const spawnedId = "swarm-brood:1:hive-alpha";
  assert.equal(resolution(result, broodCall.intentId).status, "executed");
  assert.equal(result.state.environment.biomass, 1);
  assert.equal(result.state.actors[spawnedId]?.controllerKind, "policy");
  assert.equal(result.state.actors[spawnedId]?.position.zoneId, "maintenance-nest");
  assert.ok(result.state.factionKnowledge.swarm.knownActors[spawnedId]);
  assert.ok(result.resolution.facts.some((entry) => entry.kind === "environment_changed" && entry.resourceId === "biomass"));
});

test("stabilization cannot reactivate an Actor when the Zone has no active-unit capacity", () => {
  const state = prepareStationZeroV3Commitment(createStationZeroV3Genesis());
  state.actors["engineer-imani"]!.position.zoneId = "junction-console";
  state.actors["engineer-imani"]!.lifeState = "incapacitated";
  state.actors["engineer-imani"]!.health = 0;
  state.actors["medic-reyes"]!.position.zoneId = "junction-console";
  state.actors["security-chen"]!.position.zoneId = "junction-console";
  const stabilize: StationZeroActorIntent = {
    intentId: "intent:medic:stabilize-full-zone",
    actorId: "medic-reyes",
    factionId: "rescue",
    expectedWorldRevision: state.revision,
    expectedTurn: state.encounter.turn,
    kind: "interact",
    operationId: "stabilize",
    targetId: "engineer-imani",
  };

  const result = accepted(applyStationZeroV3Turn(state, batch(state, {
    rescue: plan(state, "rescue", [stabilize]),
  })));

  assert.equal(resolution(result, stabilize.intentId).status, "contested");
  assert.equal(resolution(result, stabilize.intentId).reason, "stabilization_zone_capacity_lost");
  assert.equal(result.state.actors["engineer-imani"]!.lifeState, "incapacitated");
  assert.equal(result.state.actors["engineer-imani"]!.health, 0);
});
