import assert from "node:assert/strict";
import test from "node:test";

import { sha256 } from "../src/digest.ts";
import {
  applyStationZeroV3Turn,
  createStationZeroV3Genesis,
  prepareStationZeroV3Commitment,
  type StationZeroActorIntent,
  type StationZeroFactionId,
  type StationZeroFactionTurnPlan,
  type StationZeroTurnBatch,
  type StationZeroV3WorldState,
} from "../src/station-zero-v3/index.ts";

function plan(
  state: StationZeroV3WorldState,
  factionId: StationZeroFactionId,
  actorIntents: StationZeroActorIntent[] = [],
): StationZeroFactionTurnPlan {
  return {
    planId: `plan:w4:${factionId}:${actorIntents[0]?.intentId ?? "empty"}`,
    factionId,
    expectedWorldRevision: state.revision,
    expectedTurn: state.encounter.turn,
    standingOrderRevision: state.encounter.activePlanRevision,
    commanderActions: [],
    actorIntents,
    committedBy: `w4-authority-test:${factionId}`,
  };
}

function batch(
  state: StationZeroV3WorldState,
  factionId: StationZeroFactionId,
  intent: StationZeroActorIntent,
): StationZeroTurnBatch {
  const plans: Record<StationZeroFactionId, StationZeroFactionTurnPlan> = {
    rescue: plan(state, "rescue"),
    pirate: plan(state, "pirate"),
    swarm: plan(state, "swarm"),
  };
  plans[factionId] = plan(state, factionId, [intent]);
  return {
    turnBatchId: `turn-batch:w4:${intent.intentId}`,
    expectedWorldRevision: state.revision,
    expectedTurn: state.encounter.turn,
    factionPlans: [plans.rescue, plans.pirate, plans.swarm],
  };
}

function interact(
  state: StationZeroV3WorldState,
  actorId: string,
  factionId: StationZeroFactionId,
  operationId: Extract<StationZeroActorIntent, { kind: "interact" }>["operationId"],
  targetId: string,
): StationZeroActorIntent {
  return {
    intentId: `intent:w4:${actorId}:${operationId}`,
    actorId,
    factionId,
    expectedWorldRevision: state.revision,
    expectedTurn: state.encounter.turn,
    kind: "interact",
    operationId,
    targetId,
  };
}

function revealActor(
  state: StationZeroV3WorldState,
  factionId: StationZeroFactionId,
  actorId: string,
): void {
  const actor = state.actors[actorId]!;
  state.factionKnowledge[factionId].knownActors[actorId] = {
    actorId,
    lastKnownZoneId: actor.position.zoneId,
    observedLifeState: actor.lifeState,
    observedHealthBand: "critical",
    observedAtTurn: state.encounter.turn,
    confidence: "confirmed",
  };
}

function assertRejectedWithoutMutation(
  state: StationZeroV3WorldState,
  factionId: StationZeroFactionId,
  intent: StationZeroActorIntent,
  reason: RegExp,
): void {
  const before = sha256(state);
  const result = applyStationZeroV3Turn(state, batch(state, factionId, intent));
  assert.equal(result.status, "rejected");
  assert.match(result.status === "rejected" ? result.reason : "", reason);
  assert.equal(sha256(state), before);
}

test("final Turn admission rechecks interaction capabilities instead of trusting planning", () => {
  {
    const state = prepareStationZeroV3Commitment(createStationZeroV3Genesis("w4-hack"));
    state.actors["engineer-imani"]!.position.zoneId = "junction-console";
    assertRejectedWithoutMutation(
      state,
      "rescue",
      interact(state, "engineer-imani", "rescue", "hack", "power-grid"),
      /lacks Capability hack/,
    );
  }
  {
    const state = prepareStationZeroV3Commitment(createStationZeroV3Genesis("w4-infect"));
    state.actors["swarm-drone-one"]!.position.zoneId = "life-console";
    assertRejectedWithoutMutation(
      state,
      "swarm",
      interact(state, "swarm-drone-one", "swarm", "infect", "life-support"),
      /lacks Capability infect/,
    );
  }
  {
    const state = prepareStationZeroV3Commitment(createStationZeroV3Genesis("w4-capture"));
    const actor = state.actors["pirate-hacker-nyx"]!;
    const target = state.actors["civilian-kade"]!;
    actor.position.zoneId = "life-console";
    target.position.zoneId = "life-console";
    target.lifeState = "incapacitated";
    target.health = 0;
    revealActor(state, "pirate", target.actorId);
    assertRejectedWithoutMutation(
      state,
      "pirate",
      interact(state, actor.actorId, "pirate", "capture", target.actorId),
      /lacks Capability capture/,
    );
  }
  {
    const state = prepareStationZeroV3Commitment(createStationZeroV3Genesis("w4-devour"));
    const actor = state.actors["swarm-drone-two"]!;
    const target = state.actors["civilian-kade"]!;
    actor.position.zoneId = "life-console";
    target.position.zoneId = "life-console";
    target.lifeState = "incapacitated";
    target.health = 0;
    revealActor(state, "swarm", target.actorId);
    assertRejectedWithoutMutation(
      state,
      "swarm",
      interact(state, actor.actorId, "swarm", "devour", target.actorId),
      /lacks Capability devour/,
    );
  }
  {
    const state = prepareStationZeroV3Commitment(createStationZeroV3Genesis("w4-stabilize"));
    const actor = state.actors["engineer-imani"]!;
    const target = state.actors["medic-reyes"]!;
    actor.position.zoneId = "rescue-airlock";
    target.position.zoneId = "rescue-airlock";
    target.lifeState = "incapacitated";
    target.health = 0;
    revealActor(state, "rescue", target.actorId);
    assertRejectedWithoutMutation(
      state,
      "rescue",
      interact(state, actor.actorId, "rescue", "stabilize", target.actorId),
      /lacks Capability stabilize/,
    );
  }
});

test("domain interaction authority also retains its faction scope", () => {
  const state = prepareStationZeroV3Commitment(createStationZeroV3Genesis("w4-faction"));
  const actor = state.actors["security-chen"]!;
  actor.capabilityIds.push("hack");
  actor.position.zoneId = "junction-console";
  assertRejectedWithoutMutation(
    state,
    "rescue",
    interact(state, actor.actorId, "rescue", "hack", "power-grid"),
    /Faction rescue cannot perform Interaction hack/,
  );
});

test("guard admission rechecks the equipment-granted overwatch ability", () => {
  const state = prepareStationZeroV3Commitment(createStationZeroV3Genesis("w4-guard"));
  const actor = state.actors["engineer-imani"]!;
  actor.equipment.weapon = "pirate-shock-baton";
  const intent: StationZeroActorIntent = {
    intentId: "intent:w4:engineer:guard",
    actorId: actor.actorId,
    factionId: "rescue",
    expectedWorldRevision: state.revision,
    expectedTurn: state.encounter.turn,
    kind: "guard",
    protectedActorId: null,
    watchedZoneId: actor.position.zoneId,
  };
  assertRejectedWithoutMutation(state, "rescue", intent, /lacks Ability overwatch/);
});
