import {
  STATION_ZERO_V3_ABILITIES,
  STATION_ZERO_V3_COMMANDER_ABILITIES,
  STATION_ZERO_V3_EQUIPMENT,
  STATION_ZERO_V3_OBJECTIVES,
} from "./content.ts";
import type {
  StationZeroActorIntent,
  StationZeroCommanderAction,
  StationZeroFactionId,
  StationZeroFactionTurnPlan,
  StationZeroStandingOrder,
  StationZeroTurnBatch,
  StationZeroV3WorldState,
} from "./model.ts";
import { STATION_ZERO_FACTION_IDS } from "./model.ts";

function actorAbilityIds(state: StationZeroV3WorldState, actorId: string): Set<string> {
  const actor = state.actors[actorId];
  if (!actor) return new Set();
  return new Set(Object.values(actor.equipment).flatMap((equipmentId) =>
    STATION_ZERO_V3_EQUIPMENT.find((entry) => entry.equipmentId === equipmentId)?.grantedAbilityIds ?? []));
}

function commanderActionTargetKind(action: StationZeroCommanderAction): "actor" | "zone" | "passage" | "system" | "faction" | "none" {
  const targets = [
    action.targetActorId === null ? null : "actor" as const,
    action.targetZoneId === null ? null : "zone" as const,
    action.targetPassageId === null ? null : "passage" as const,
    action.targetSystemId === null ? null : "system" as const,
    action.targetFactionId === null ? null : "faction" as const,
  ].filter((entry): entry is Exclude<typeof entry, null> => entry !== null);
  if (targets.length > 1) throw new TypeError(`Commander Action ${action.commanderActionId} has multiple targets`);
  return targets[0] ?? "none";
}

function assertExpectedHead(
  state: StationZeroV3WorldState,
  value: { expectedWorldRevision: number; expectedTurn: number },
  label: string,
): void {
  if (value.expectedWorldRevision !== state.revision) {
    throw new TypeError(`${label} expected World revision ${value.expectedWorldRevision}, current revision is ${state.revision}`);
  }
  if (value.expectedTurn !== state.encounter.turn) {
    throw new TypeError(`${label} expected Turn ${value.expectedTurn}, current Turn is ${state.encounter.turn}`);
  }
}

function assertKnownActor(state: StationZeroV3WorldState, factionId: StationZeroFactionId, actorId: string, label: string): void {
  if (!state.factionKnowledge[factionId].knownActors[actorId]) {
    throw new TypeError(`${label} references Actor ${actorId} outside Faction knowledge`);
  }
}

function assertCommanderAction(
  state: StationZeroV3WorldState,
  factionId: StationZeroFactionId,
  action: StationZeroCommanderAction,
): number {
  assertExpectedHead(state, action, `Commander Action ${action.commanderActionId}`);
  if (action.factionId !== factionId) throw new TypeError(`Commander Action ${action.commanderActionId} belongs to another Faction`);
  const definition = STATION_ZERO_V3_COMMANDER_ABILITIES.find((entry) => entry.commanderAbilityId === action.commanderAbilityId);
  if (!definition || !definition.factionIds.includes(factionId)) {
    throw new TypeError(`Faction ${factionId} cannot use Commander Ability ${action.commanderAbilityId}`);
  }
  const faction = state.factions[factionId];
  const charges = faction.commanderAbilityCharges[action.commanderAbilityId];
  if (charges !== null && (charges === undefined || charges < 1)) {
    throw new TypeError(`Commander Ability ${action.commanderAbilityId} has no remaining charge`);
  }
  if ((faction.commanderAbilityCooldowns[action.commanderAbilityId] ?? 0) > 0) {
    throw new TypeError(`Commander Ability ${action.commanderAbilityId} is on cooldown`);
  }
  const targetKind = commanderActionTargetKind(action);
  if (!definition.targetKinds.includes(targetKind)) {
    throw new TypeError(`Commander Ability ${action.commanderAbilityId} does not accept ${targetKind} target`);
  }
  if (action.targetActorId !== null) {
    if (!state.actors[action.targetActorId]) throw new TypeError(`Commander Action targets unknown Actor ${action.targetActorId}`);
    assertKnownActor(state, factionId, action.targetActorId, `Commander Action ${action.commanderActionId}`);
  }
  if (action.targetZoneId !== null && !state.zones[action.targetZoneId]) throw new TypeError(`Commander Action targets unknown Zone ${action.targetZoneId}`);
  if (action.targetPassageId !== null && !state.passages[action.targetPassageId]) throw new TypeError(`Commander Action targets unknown Passage ${action.targetPassageId}`);
  if (action.targetSystemId !== null && !state.systems[action.targetSystemId]) throw new TypeError(`Commander Action targets unknown System ${action.targetSystemId}`);
  if (action.targetFactionId !== null && !STATION_ZERO_FACTION_IDS.includes(action.targetFactionId)) throw new TypeError(`Commander Action targets unknown Faction`);
  return definition.commandPointCost;
}

function actionPointCost(intent: StationZeroActorIntent): number {
  switch (intent.kind) {
    case "wait": return 0;
    case "move":
    case "interact":
    case "pickup":
    case "extract":
    case "guard": return 1;
    case "attack":
    case "use_ability": {
      const ability = STATION_ZERO_V3_ABILITIES.find((entry) => entry.abilityId === intent.abilityId);
      if (!ability) throw new TypeError(`Intent ${intent.intentId} references unknown Ability ${intent.abilityId}`);
      return ability.actionPointCost;
    }
  }
}

function actorAbilityTargetKind(
  state: StationZeroV3WorldState,
  factionId: StationZeroFactionId,
  intent: Extract<StationZeroActorIntent, { kind: "use_ability" }>,
): "ally" | "enemy" | "zone" | "system" | "hazard" {
  if (intent.targetActorId !== null) {
    return state.actors[intent.targetActorId]?.factionId === factionId ? "ally" : "enemy";
  }
  if (intent.targetZoneId !== null) return "zone";
  if (intent.targetSystemId !== null) return "system";
  if (intent.targetHazardId !== null) return "hazard";
  throw new TypeError(`Ability Intent ${intent.intentId} requires one target`);
}

function assertActorIntent(
  state: StationZeroV3WorldState,
  factionId: StationZeroFactionId,
  intent: StationZeroActorIntent,
): void {
  assertExpectedHead(state, intent, `Intent ${intent.intentId}`);
  if (intent.factionId !== factionId) throw new TypeError(`Intent ${intent.intentId} belongs to another Faction`);
  const actor = state.actors[intent.actorId];
  if (!actor || actor.factionId !== factionId) throw new TypeError(`Intent ${intent.intentId} references an Actor outside Faction ${factionId}`);
  if (actor.lifeState !== "active") throw new TypeError(`Intent ${intent.intentId} references inactive Actor ${intent.actorId}`);
  if (actionPointCost(intent) > actor.actionPoints) throw new TypeError(`Intent ${intent.intentId} exceeds ${intent.actorId} Action Points`);

  switch (intent.kind) {
    case "move":
      if (!state.zones[intent.targetZoneId]) throw new TypeError(`Move Intent targets unknown Zone ${intent.targetZoneId}`);
      return;
    case "attack": {
      const ability = STATION_ZERO_V3_ABILITIES.find((entry) => entry.abilityId === intent.abilityId);
      if (!ability || !ability.targetKinds.includes("enemy")) throw new TypeError(`Attack Intent ${intent.intentId} requires an enemy-targeting Ability`);
      if (!actorAbilityIds(state, actor.actorId).has(intent.abilityId)) throw new TypeError(`Actor ${actor.actorId} lacks Ability ${intent.abilityId}`);
      if ((actor.abilityCooldowns[intent.abilityId] ?? 0) > 0) throw new TypeError(`Ability ${intent.abilityId} is on cooldown`);
      const target = state.actors[intent.targetActorId];
      if (!target || target.factionId === factionId || target.lifeState !== "active") throw new TypeError(`Attack Intent has invalid target ${intent.targetActorId}`);
      assertKnownActor(state, factionId, target.actorId, `Attack Intent ${intent.intentId}`);
      return;
    }
    case "use_ability": {
      const ability = STATION_ZERO_V3_ABILITIES.find((entry) => entry.abilityId === intent.abilityId);
      if (!ability) throw new TypeError(`Ability Intent ${intent.intentId} references unknown Ability ${intent.abilityId}`);
      if (!actorAbilityIds(state, actor.actorId).has(intent.abilityId)) throw new TypeError(`Actor ${actor.actorId} lacks Ability ${intent.abilityId}`);
      if ((actor.abilityCooldowns[intent.abilityId] ?? 0) > 0) throw new TypeError(`Ability ${intent.abilityId} is on cooldown`);
      const targetCount = [intent.targetActorId, intent.targetZoneId, intent.targetSystemId, intent.targetHazardId].filter((entry) => entry !== null).length;
      if (targetCount !== 1) throw new TypeError(`Ability Intent ${intent.intentId} requires exactly one target`);
      if (intent.targetActorId !== null) {
        if (!state.actors[intent.targetActorId]) throw new TypeError(`Ability Intent targets unknown Actor ${intent.targetActorId}`);
        assertKnownActor(state, factionId, intent.targetActorId, `Ability Intent ${intent.intentId}`);
      }
      if (intent.targetZoneId !== null && !state.zones[intent.targetZoneId]) throw new TypeError(`Ability Intent targets unknown Zone ${intent.targetZoneId}`);
      if (intent.targetSystemId !== null && !state.systems[intent.targetSystemId]) throw new TypeError(`Ability Intent targets unknown System ${intent.targetSystemId}`);
      if (intent.targetHazardId !== null && !state.hazards[intent.targetHazardId]) throw new TypeError(`Ability Intent targets unknown Hazard ${intent.targetHazardId}`);
      const targetKind = actorAbilityTargetKind(state, factionId, intent);
      if (!ability.targetKinds.includes(targetKind)) throw new TypeError(`Ability ${intent.abilityId} does not accept ${targetKind} target`);
      return;
    }
    case "interact": {
      if (!intent.targetId.trim()) throw new TypeError(`Interaction Intent ${intent.intentId} requires a target`);
      switch (intent.operationId) {
        case "repair":
          if (!state.systems[intent.targetId]) throw new TypeError(`Repair Intent targets unknown System ${intent.targetId}`);
          break;
        case "hack":
          if (!state.systems[intent.targetId] && !state.passages[intent.targetId]) throw new TypeError(`Hack Intent targets unknown System or Passage ${intent.targetId}`);
          break;
        case "infect":
          if (!state.systems[intent.targetId]) throw new TypeError(`Infect Intent targets unknown System ${intent.targetId}`);
          break;
        case "stabilize":
        case "rescue":
        case "capture":
        case "devour":
          if (!state.actors[intent.targetId]) throw new TypeError(`${intent.operationId} Intent targets unknown Actor ${intent.targetId}`);
          assertKnownActor(state, factionId, intent.targetId, `Interaction Intent ${intent.intentId}`);
          break;
      }
      return;
    }
    case "pickup": {
      const groundItem = state.groundItems[intent.groundItemId];
      if (!groundItem || !Number.isSafeInteger(intent.quantity) || intent.quantity < 1 || intent.quantity > groundItem.quantity) {
        throw new TypeError(`Pickup Intent ${intent.intentId} is invalid`);
      }
      if (!state.factionKnowledge[factionId].knownGroundItemIds.includes(intent.groundItemId)) {
        throw new TypeError(`Pickup Intent ${intent.intentId} references Item outside Faction knowledge`);
      }
      return;
    }
    case "extract":
      if (!state.zones[actor.position.zoneId]?.tags.includes(`extraction:${factionId}`)) {
        throw new TypeError(`Actor ${actor.actorId} is not in a ${factionId} extraction Zone`);
      }
      if (!intent.extractionId.trim()) throw new TypeError(`Extract Intent ${intent.intentId} requires an extraction identity`);
      return;
    case "guard":
      if ((intent.protectedActorId === null) === (intent.watchedZoneId === null)) {
        throw new TypeError(`Guard Intent ${intent.intentId} requires exactly one protected Actor or watched Zone`);
      }
      if (intent.protectedActorId !== null && state.actors[intent.protectedActorId]?.factionId !== factionId) {
        throw new TypeError(`Guard Intent ${intent.intentId} protects an invalid Actor`);
      }
      if (intent.watchedZoneId !== null && !state.zones[intent.watchedZoneId]) throw new TypeError(`Guard Intent targets unknown Zone`);
      return;
    case "wait": return;
  }
}

export function assertStationZeroStandingOrder(
  state: StationZeroV3WorldState,
  order: StationZeroStandingOrder,
): void {
  const actor = state.actors[order.actorId];
  if (!actor || actor.factionId !== order.factionId) throw new TypeError(`Standing Order references an Actor outside its Faction`);
  const objective = STATION_ZERO_V3_OBJECTIVES.find((entry) => entry.objectiveId === order.objectiveId);
  if (!objective || objective.factionId !== order.factionId) throw new TypeError(`Standing Order references an Objective outside its Faction`);
  if (!Number.isSafeInteger(order.revision) || order.revision < 1) throw new TypeError(`Standing Order revision must be positive`);
  if (!Number.isFinite(order.retreatHealthThreshold) || order.retreatHealthThreshold < 0 || order.retreatHealthThreshold > 1) {
    throw new TypeError(`Standing Order retreat threshold must be between 0 and 1`);
  }
  if (order.priorityTargetActorId !== null) assertKnownActor(state, order.factionId, order.priorityTargetActorId, `Standing Order ${order.orderId}`);
  if (order.protectedActorId !== null && state.actors[order.protectedActorId]?.factionId !== order.factionId) {
    throw new TypeError(`Standing Order protects an Actor outside its Faction`);
  }
}

export function assertStationZeroFactionTurnPlan(
  state: StationZeroV3WorldState,
  plan: StationZeroFactionTurnPlan,
): void {
  assertExpectedHead(state, plan, `Faction Plan ${plan.planId}`);
  if (!STATION_ZERO_FACTION_IDS.includes(plan.factionId)) throw new TypeError(`Faction Plan ${plan.planId} has unknown Faction`);
  if (plan.standingOrderRevision !== state.encounter.activePlanRevision) {
    throw new TypeError(`Faction Plan ${plan.planId} was built from stale Standing Orders`);
  }
  const commanderActionIds = plan.commanderActions.map((action) => action.commanderActionId);
  if (new Set(commanderActionIds).size !== commanderActionIds.length) throw new TypeError(`Faction Plan ${plan.planId} duplicates Commander Actions`);
  const spentCommandPoints = plan.commanderActions.reduce((total, action) =>
    total + assertCommanderAction(state, plan.factionId, action), 0);
  if (spentCommandPoints > state.factions[plan.factionId].commandPoints) {
    throw new TypeError(`Faction Plan ${plan.planId} exceeds Command Points`);
  }
  const abilityUseCounts = new Map<string, number>();
  for (const action of plan.commanderActions) {
    abilityUseCounts.set(action.commanderAbilityId, (abilityUseCounts.get(action.commanderAbilityId) ?? 0) + 1);
  }
  for (const [abilityId, count] of abilityUseCounts) {
    const charges = state.factions[plan.factionId].commanderAbilityCharges[abilityId];
    if (charges !== null && charges !== undefined && count > charges) {
      throw new TypeError(`Faction Plan ${plan.planId} exceeds Commander Ability ${abilityId} charges`);
    }
  }
  const intentIds = plan.actorIntents.map((intent) => intent.intentId);
  if (new Set(intentIds).size !== intentIds.length) throw new TypeError(`Faction Plan ${plan.planId} duplicates Intent identities`);
  const actorIds = plan.actorIntents.map((intent) => intent.actorId);
  if (new Set(actorIds).size !== actorIds.length) throw new TypeError(`Faction Plan ${plan.planId} gives one Actor multiple Intents`);
  for (const intent of plan.actorIntents) assertActorIntent(state, plan.factionId, intent);
}

export function assertStationZeroTurnBatch(
  state: StationZeroV3WorldState,
  batch: StationZeroTurnBatch,
): void {
  assertExpectedHead(state, batch, `Turn Batch ${batch.turnBatchId}`);
  if (state.encounter.status !== "running") throw new TypeError(`Turn Batch cannot commit a terminal Encounter`);
  if (state.encounter.phase !== "commitment") throw new TypeError(`Turn Batch can commit only from commitment phase`);
  if (batch.factionPlans.length !== STATION_ZERO_FACTION_IDS.length) throw new TypeError(`Turn Batch requires exactly one Plan per Faction`);
  const factionIds = batch.factionPlans.map((plan) => plan.factionId);
  if (new Set(factionIds).size !== STATION_ZERO_FACTION_IDS.length ||
      STATION_ZERO_FACTION_IDS.some((factionId) => !factionIds.includes(factionId))) {
    throw new TypeError(`Turn Batch requires rescue, pirate, and swarm Plans`);
  }
  const planIds = batch.factionPlans.map((plan) => plan.planId);
  if (new Set(planIds).size !== planIds.length) throw new TypeError(`Turn Batch duplicates Plan identities`);
  const intentIds = batch.factionPlans.flatMap((plan) => plan.actorIntents.map((intent) => intent.intentId));
  if (new Set(intentIds).size !== intentIds.length) throw new TypeError(`Turn Batch duplicates Intent identities across Factions`);
  const commanderActionIds = batch.factionPlans.flatMap((plan) =>
    plan.commanderActions.map((action) => action.commanderActionId));
  if (new Set(commanderActionIds).size !== commanderActionIds.length) {
    throw new TypeError(`Turn Batch duplicates Commander Action identities across Factions`);
  }
  for (const plan of batch.factionPlans) assertStationZeroFactionTurnPlan(state, plan);
}
