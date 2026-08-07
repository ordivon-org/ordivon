import { sha256 } from "../digest.ts";
import {
  STATION_ZERO_V3_ABILITIES,
  STATION_ZERO_V3_COMMANDER_ABILITIES,
  STATION_ZERO_V3_EQUIPMENT,
  STATION_ZERO_V3_ITEMS,
  STATION_ZERO_V3_OBJECTIVES,
} from "./content.ts";
import { assertStationZeroTurnBatch } from "./contracts.ts";
import { assertStationZeroV3World } from "./genesis.ts";
import type {
  StationZeroActorIntent,
  StationZeroActorState,
  StationZeroFact,
  StationZeroFactionId,
  StationZeroFactionObservation,
  StationZeroFactionOutcome,
  StationZeroFactionTurnPlan,
  StationZeroGroundItemState,
  StationZeroIntentResolution,
  StationZeroIntentResolutionStatus,
  StationZeroResolutionPhase,
  StationZeroTurnApplyResult,
  StationZeroTurnBatch,
  StationZeroTurnRecord,
  StationZeroTurnResolution,
  StationZeroV3WorldState,
} from "./model.ts";
import { STATION_ZERO_FACTION_IDS, STATION_ZERO_RESOLUTION_PHASES } from "./model.ts";
import {
  stationZeroAdjacentZones,
  stationZeroShortestDistance,
  stationZeroVisibleZonesFrom,
} from "./topology.ts";

type StationZeroFactInput = StationZeroFact extends infer Fact
  ? Fact extends { factId: string }
    ? Omit<Fact, "factId">
    : never
  : never;

type MutableContext = {
  state: StationZeroV3WorldState;
  batch: StationZeroTurnBatch;
  facts: StationZeroFact[];
  resolutions: Map<string, StationZeroIntentResolution>;
  factSequence: number;
};

const FACTION_ORDER = new Map(STATION_ZERO_FACTION_IDS.map((factionId, index) => [factionId, index]));
const PHASE_ORDER = new Map(STATION_ZERO_RESOLUTION_PHASES.map((phase, index) => [phase, index]));

function clamp(value: number, minimum: number, maximum: number): number {
  return Math.max(minimum, Math.min(maximum, value));
}

function quantizeFraction(value: number): number {
  return Math.round(value * 1_000) / 1_000;
}

function sortedUnique(values: string[]): string[] {
  return [...new Set(values)].sort();
}

function addUnique(values: string[], value: string): boolean {
  if (values.includes(value)) return false;
  values.push(value);
  values.sort();
  return true;
}

function factionRank(factionId: StationZeroFactionId): number {
  return FACTION_ORDER.get(factionId) ?? Number.MAX_SAFE_INTEGER;
}

function actorInitiative(state: StationZeroV3WorldState, actorId: string): number {
  return state.actors[actorId]?.initiative ?? Number.MIN_SAFE_INTEGER;
}

function canonicalPlans(batch: StationZeroTurnBatch): StationZeroFactionTurnPlan[] {
  return [...batch.factionPlans]
    .sort((left, right) => factionRank(left.factionId) - factionRank(right.factionId))
    .map((plan) => ({
      ...structuredClone(plan),
      commanderActions: [...plan.commanderActions].sort((left, right) =>
        left.commanderActionId.localeCompare(right.commanderActionId)),
      actorIntents: [...plan.actorIntents].sort((left, right) =>
        left.actorId.localeCompare(right.actorId) || left.intentId.localeCompare(right.intentId)),
    }));
}

export function canonicalizeStationZeroV3TurnBatch(batch: StationZeroTurnBatch): StationZeroTurnBatch {
  return { ...structuredClone(batch), factionPlans: canonicalPlans(batch) };
}

function allIntents(batch: StationZeroTurnBatch): StationZeroActorIntent[] {
  return batch.factionPlans.flatMap((plan) => plan.actorIntents);
}

function ability(abilityId: string) {
  const retained = STATION_ZERO_V3_ABILITIES.find((entry) => entry.abilityId === abilityId);
  if (!retained) throw new Error(`Missing admitted Ability ${abilityId}`);
  return retained;
}

function intentPhase(intent: StationZeroActorIntent): StationZeroResolutionPhase {
  switch (intent.kind) {
    case "move": return "movement";
    case "guard": return "reaction";
    case "attack": return "combat";
    case "use_ability": return ability(intent.abilityId).resolutionPhase;
    case "interact":
    case "pickup":
    case "extract": return "interaction";
    case "wait": return "cleanup";
  }
}

function sortedIntents<T extends StationZeroActorIntent>(
  state: StationZeroV3WorldState,
  intents: T[],
): T[] {
  return [...intents].sort((left, right) =>
    (PHASE_ORDER.get(intentPhase(left)) ?? 99) - (PHASE_ORDER.get(intentPhase(right)) ?? 99) ||
    actorInitiative(state, right.actorId) - actorInitiative(state, left.actorId) ||
    left.actorId.localeCompare(right.actorId) ||
    left.intentId.localeCompare(right.intentId));
}

function emitFact(context: MutableContext, input: StationZeroFactInput): string {
  const factId = `fact:${context.batch.turnBatchId}:${String(context.factSequence).padStart(4, "0")}:${input.kind}`;
  context.factSequence += 1;
  context.facts.push({ factId, ...input } as StationZeroFact);
  return factId;
}

function resolveIntent(
  context: MutableContext,
  intent: StationZeroActorIntent,
  phase: StationZeroResolutionPhase,
  status: StationZeroIntentResolutionStatus,
  reason: string,
  factIds: string[] = [],
): void {
  if (context.resolutions.has(intent.intentId)) {
    throw new Error(`Intent ${intent.intentId} resolved more than once`);
  }
  context.resolutions.set(intent.intentId, {
    intentId: intent.intentId,
    actorId: intent.actorId,
    factionId: intent.factionId,
    resolutionPhase: phase,
    status,
    reason,
    verificationPassed: true,
    factIds: [...factIds],
  });
}

function healthBand(actor: StationZeroActorState): "healthy" | "wounded" | "critical" | "unknown" {
  if (actor.lifeState === "dead" || actor.lifeState === "captured") return "critical";
  if (actor.health >= actor.maximumHealth * 0.75) return "healthy";
  if (actor.health >= actor.maximumHealth * 0.35) return "wounded";
  return "critical";
}

function setActorStatus(context: MutableContext, actor: StationZeroActorState, statusId: string, active: boolean): string | null {
  const has = actor.statusIds.includes(statusId);
  if (active === has) return null;
  if (active) actor.statusIds = sortedUnique([...actor.statusIds, statusId]);
  else actor.statusIds = actor.statusIds.filter((entry) => entry !== statusId);
  return emitFact(context, { kind: "actor_status_changed", actorId: actor.actorId, statusId, active });
}

function equipmentItemId(equipmentId: string): string | null {
  return STATION_ZERO_V3_ITEMS.find((entry) => entry.equipmentId === equipmentId)?.itemId ?? null;
}

function addGroundItem(
  context: MutableContext,
  actorId: string,
  zoneId: string,
  itemId: string,
  quantity: number,
): string {
  const suffix = Object.keys(context.state.groundItems).filter((groundItemId) =>
    groundItemId.startsWith(`drop:${context.state.revision + 1}:${actorId}:${itemId}:`)).length;
  const groundItemId = `drop:${context.state.revision + 1}:${actorId}:${itemId}:${suffix}`;
  context.state.groundItems[groundItemId] = {
    groundItemId,
    itemId,
    zoneId,
    quantity,
    ownerFactionId: null,
  };
  return emitFact(context, { kind: "ground_item_dropped", groundItemId, actorId, zoneId });
}

function dropActorPossessions(context: MutableContext, actor: StationZeroActorState): string[] {
  const factIds: string[] = [];
  const counts = new Map<string, number>();
  for (const itemId of actor.inventoryItemIds) counts.set(itemId, (counts.get(itemId) ?? 0) + 1);
  for (const equipmentId of Object.values(actor.equipment)) {
    const itemId = equipmentItemId(equipmentId) ?? "alien-tissue";
    counts.set(itemId, (counts.get(itemId) ?? 0) + 1);
  }
  for (const [itemId, quantity] of [...counts].sort(([left], [right]) => left.localeCompare(right))) {
    factIds.push(addGroundItem(context, actor.actorId, actor.position.zoneId, itemId, quantity));
  }
  actor.inventoryItemIds = [];
  actor.equipment = {};
  actor.armor = 0;
  actor.abilityCooldowns = {};
  return factIds;
}

function changeLifeState(
  context: MutableContext,
  actor: StationZeroActorState,
  next: StationZeroActorState["lifeState"],
): string | null {
  if (actor.lifeState === next) return null;
  const before = actor.lifeState;
  actor.lifeState = next;
  return emitFact(context, { kind: "actor_life_state_changed", actorId: actor.actorId, before, after: next });
}

function applyDamage(
  context: MutableContext,
  sourceActorId: string,
  target: StationZeroActorState,
  amount: number,
  causes: string[],
): string[] {
  const factIds: string[] = [];
  if (amount <= 0 || target.lifeState === "dead" || target.lifeState === "extracted" || target.lifeState === "captured") {
    return factIds;
  }
  factIds.push(emitFact(context, {
    kind: "damage_dealt",
    sourceActorId,
    targetActorId: target.actorId,
    amount,
  }));
  const beforeHealth = target.health;
  target.health = Math.max(0, target.health - amount);
  factIds.push(emitFact(context, {
    kind: "actor_health_changed",
    actorId: target.actorId,
    before: beforeHealth,
    after: target.health,
    causes,
  }));
  if (target.health > 0) return factIds;

  if (target.lifeState === "incapacitated" || target.kind === "creature" || amount >= beforeHealth + 10) {
    const lifeFactId = changeLifeState(context, target, "dead");
    if (lifeFactId) factIds.push(lifeFactId);
    factIds.push(...dropActorPossessions(context, target));
  } else {
    const lifeFactId = changeLifeState(context, target, "incapacitated");
    if (lifeFactId) factIds.push(lifeFactId);
  }
  return factIds;
}

function coverReduction(state: StationZeroV3WorldState, zoneId: string): number {
  const cover = state.zones[zoneId]?.cover ?? "none";
  if (cover === "full") return 8;
  if (cover === "half") return 4;
  return 0;
}

function deterministicDamage(
  state: StationZeroV3WorldState,
  abilityId: string,
  target: StationZeroActorState,
  reaction = false,
): number {
  const definition = ability(abilityId);
  const effectiveArmor = Math.max(0, target.armor - definition.armorPiercing);
  const cover = reaction ? 0 : coverReduction(state, target.position.zoneId);
  return Math.max(0, definition.damage - effectiveArmor - cover);
}

function setAbilityCooldown(actor: StationZeroActorState, abilityId: string): void {
  const turns = ability(abilityId).cooldownTurns;
  actor.abilityCooldowns[abilityId] = turns > 0 ? turns + 1 : 0;
}

function knownActorSnapshot(actor: StationZeroActorState, turn: number) {
  return {
    actorId: actor.actorId,
    lastKnownZoneId: actor.position.zoneId,
    observedLifeState: actor.lifeState,
    observedHealthBand: healthBand(actor),
    observedAtTurn: turn,
    confidence: "confirmed" as const,
  };
}

function revealActor(context: MutableContext, factionId: StationZeroFactionId, actor: StationZeroActorState): void {
  const knowledge = context.state.factionKnowledge[factionId];
  const isNew = knowledge.knownActors[actor.actorId] === undefined;
  knowledge.knownActors[actor.actorId] = knownActorSnapshot(actor, context.state.encounter.turn);
  if (isNew) {
    emitFact(context, {
      kind: "knowledge_revealed",
      factionId,
      subjectId: actor.actorId,
      subjectKind: "actor",
    });
  }
}

function revealZone(context: MutableContext, factionId: StationZeroFactionId, zoneId: string): void {
  const zone = context.state.zones[zoneId];
  if (!zone) return;
  const knowledge = context.state.factionKnowledge[factionId];
  if (addUnique(knowledge.discoveredZoneIds, zoneId)) {
    emitFact(context, { kind: "knowledge_revealed", factionId, subjectId: zoneId, subjectKind: "zone" });
  }
  if (addUnique(knowledge.discoveredRoomIds, zone.roomId)) {
    emitFact(context, { kind: "knowledge_revealed", factionId, subjectId: zone.roomId, subjectKind: "room" });
  }
  for (const actor of Object.values(context.state.actors)
    .filter((entry) => entry.position.zoneId === zoneId)
    .sort((left, right) => left.actorId.localeCompare(right.actorId))) {
    revealActor(context, factionId, actor);
  }
  for (const system of Object.values(context.state.systems)
    .filter((entry) => entry.zoneId === zoneId)
    .sort((left, right) => left.systemId.localeCompare(right.systemId))) {
    if (addUnique(knowledge.knownSystemIds, system.systemId)) {
      emitFact(context, { kind: "knowledge_revealed", factionId, subjectId: system.systemId, subjectKind: "system" });
    }
  }
  for (const hazard of Object.values(context.state.hazards)
    .filter((entry) => entry.zoneId === zoneId)
    .sort((left, right) => left.hazardId.localeCompare(right.hazardId))) {
    if (addUnique(knowledge.knownHazardIds, hazard.hazardId)) {
      emitFact(context, { kind: "knowledge_revealed", factionId, subjectId: hazard.hazardId, subjectKind: "hazard" });
    }
  }
  for (const item of Object.values(context.state.groundItems)
    .filter((entry) => entry.zoneId === zoneId)
    .sort((left, right) => left.groundItemId.localeCompare(right.groundItemId))) {
    if (addUnique(knowledge.knownGroundItemIds, item.groundItemId)) {
      emitFact(context, { kind: "knowledge_revealed", factionId, subjectId: item.groundItemId, subjectKind: "item" });
    }
  }
}

function consumeCommanderResources(
  state: StationZeroV3WorldState,
  factionId: StationZeroFactionId,
  commanderAbilityId: string,
): void {
  const definition = STATION_ZERO_V3_COMMANDER_ABILITIES.find((entry) => entry.commanderAbilityId === commanderAbilityId);
  if (!definition) throw new Error(`Missing admitted Commander Ability ${commanderAbilityId}`);
  const faction = state.factions[factionId];
  faction.commandPoints -= definition.commandPointCost;
  const charges = faction.commanderAbilityCharges[commanderAbilityId];
  if (charges !== null && charges !== undefined) faction.commanderAbilityCharges[commanderAbilityId] = charges - 1;
  faction.commanderAbilityCooldowns[commanderAbilityId] = definition.cooldownTurns > 0
    ? definition.cooldownTurns + 1
    : 0;
}

function applyCommanderActions(context: MutableContext): void {
  for (const plan of canonicalPlans(context.batch)) {
    for (const action of plan.commanderActions) {
      consumeCommanderResources(context.state, action.factionId, action.commanderAbilityId);
      emitFact(context, {
        kind: "commander_ability_used",
        factionId: action.factionId,
        commanderAbilityId: action.commanderAbilityId,
      });
      switch (action.commanderAbilityId) {
        case "orbital-scan":
          if (action.targetZoneId) revealZone(context, action.factionId, action.targetZoneId);
          break;
        case "power-reroute": {
          const system = action.targetSystemId ? context.state.systems[action.targetSystemId] : null;
          if (!system) break;
          const integrityBefore = system.integrity;
          const poweredBefore = system.powered;
          system.powered = true;
          emitFact(context, {
            kind: "system_changed",
            systemId: system.systemId,
            integrityBefore,
            integrityAfter: system.integrity,
            poweredBefore,
            poweredAfter: system.powered,
          });
          break;
        }
        case "bulkhead-lockdown":
        case "door-spoof": {
          const passage = action.targetPassageId ? context.state.passages[action.targetPassageId] : null;
          if (!passage) break;
          const before = passage.state;
          passage.state = action.commanderAbilityId === "bulkhead-lockdown" ? "closed" : "open";
          if (before !== passage.state) {
            emitFact(context, { kind: "passage_changed", passageId: passage.passageId, before, after: passage.state });
          }
          break;
        }
        case "emergency-uplink": {
          const ownZones = Object.values(context.state.actors)
            .filter((actor) => actor.factionId === action.factionId && actor.lifeState === "active")
            .map((actor) => actor.position.zoneId);
          for (const zoneId of stationZeroVisibleZonesFrom(context.state, ownZones, action.factionId)) {
            revealZone(context, action.factionId, zoneId);
          }
          addUnique(context.state.factionKnowledge[action.factionId].reportIds, `uplink:${context.state.encounter.turn}`);
          break;
        }
        case "rescue-extraction":
        case "pirate-extraction": {
          const zone = action.targetZoneId ? context.state.zones[action.targetZoneId] : null;
          if (zone) addUnique(zone.tags, `extraction:${action.factionId}`);
          break;
        }
        case "signal-jam": {
          if (action.targetFactionId) {
            context.state.factions[action.targetFactionId].uplinkSlots = 0;
            addUnique(context.state.factionKnowledge[action.targetFactionId].reportIds, `jammed:${context.state.encounter.turn}`);
          }
          break;
        }
        case "mark-prize": {
          const target = action.targetActorId ? context.state.actors[action.targetActorId] : null;
          if (target) setActorStatus(context, target, "marked-prize:pirate", true);
          break;
        }
        case "pheromone-surge": {
          if (!action.targetZoneId) break;
          for (const actor of Object.values(context.state.actors)
            .filter((entry) => entry.factionId === "swarm" && entry.position.zoneId === action.targetZoneId)
            .sort((left, right) => left.actorId.localeCompare(right.actorId))) {
            setActorStatus(context, actor, `pheromone-surge:${context.state.encounter.turn}`, true);
          }
          break;
        }
        case "brood-awakening": {
          const nest = context.state.hazards["biomass-nest"];
          if (nest) {
            const severityBefore = nest.severity;
            const biomassBefore = context.state.environment.biomass;
            nest.severity = Math.min(5, nest.severity + 1);
            context.state.environment.biomass = Math.max(0, context.state.environment.biomass - 2);
            emitFact(context, {
              kind: "hazard_changed",
              hazardId: nest.hazardId,
              severityBefore,
              severityAfter: nest.severity,
              contained: nest.contained,
            });
            if (biomassBefore !== context.state.environment.biomass) {
              emitFact(context, {
                kind: "environment_changed",
                resourceId: "biomass",
                before: biomassBefore,
                after: context.state.environment.biomass,
                causes: ["brood_awakening"],
              });
            }
          }
          break;
        }
        case "vent-spread": {
          if (!action.targetZoneId) break;
          const hazardId = `vent-spread:${action.targetZoneId}`;
          const retained = context.state.hazards[hazardId];
          if (retained) {
            const severityBefore = retained.severity;
            retained.severity = Math.min(5, retained.severity + 1);
            emitFact(context, {
              kind: "hazard_changed",
              hazardId,
              severityBefore,
              severityAfter: retained.severity,
              contained: retained.contained,
            });
          } else {
            context.state.hazards[hazardId] = {
              hazardId,
              name: "Vent Biomass Spread",
              zoneId: action.targetZoneId,
              severity: 1,
              contained: false,
              tags: ["swarm", "infection", "vent"],
            };
            emitFact(context, {
              kind: "hazard_changed",
              hazardId,
              severityBefore: 0,
              severityAfter: 1,
              contained: false,
            });
          }
          break;
        }
      }
    }
  }
}

type ReactionIntent =
  | Extract<StationZeroActorIntent, { kind: "guard" }>
  | Extract<StationZeroActorIntent, { kind: "use_ability" }>;

type MoveCandidate = {
  intent: Extract<StationZeroActorIntent, { kind: "move" }>;
  actor: StationZeroActorState;
  escortedCivilians: StationZeroActorState[];
  footprint: number;
  fromZoneId: string;
  targetZoneId: string;
};

function resolveMovementAndReactions(context: MutableContext, intents: StationZeroActorIntent[]): void {
  const moveIntents = sortedIntents(context.state, intents.filter((intent): intent is Extract<StationZeroActorIntent, { kind: "move" }> =>
    intent.kind === "move"));
  const candidates: MoveCandidate[] = [];
  for (const intent of moveIntents) {
    const actor = context.state.actors[intent.actorId]!;
    if (actor.lifeState !== "active") {
      resolveIntent(context, intent, "movement", "interrupted", "actor_not_active");
      continue;
    }
    if (actor.position.zoneId === intent.targetZoneId) {
      resolveIntent(context, intent, "movement", "no_effect", "already_in_target_zone");
      continue;
    }
    const distance = stationZeroShortestDistance(context.state, actor.position.zoneId, intent.targetZoneId, actor.factionId);
    const movementBonus = actor.statusIds.includes(`pheromone-surge:${context.state.encounter.turn}`) ? 1 : 0;
    if (distance === null || distance > actor.movementRange + movementBonus) {
      resolveIntent(context, intent, "movement", "invalidated", "target_unreachable_in_committed_world");
      continue;
    }
    const escortedCivilians = Object.values(context.state.actors)
      .filter((candidate) =>
        candidate.kind === "civilian" &&
        candidate.lifeState === "active" &&
        candidate.position.zoneId === actor.position.zoneId &&
        candidate.statusIds.includes(`escorted-by:${actor.actorId}`))
      .sort((left, right) => left.actorId.localeCompare(right.actorId));
    candidates.push({
      intent,
      actor,
      escortedCivilians,
      footprint: 1 + escortedCivilians.length,
      fromZoneId: actor.position.zoneId,
      targetZoneId: intent.targetZoneId,
    });
  }

  const winnerIds = new Set<string>();
  for (const zoneId of sortedUnique(candidates.map((candidate) => candidate.targetZoneId))) {
    const zone = context.state.zones[zoneId]!;
    const occupied = Object.values(context.state.actors).filter((actor) =>
      actor.lifeState === "active" && actor.position.zoneId === zoneId).length;
    const available = Math.max(0, zone.capacity - occupied);
    const contenders = candidates
      .filter((candidate) => candidate.targetZoneId === zoneId)
      .sort((left, right) =>
        right.actor.initiative - left.actor.initiative ||
        left.actor.actorId.localeCompare(right.actor.actorId) ||
        left.intent.intentId.localeCompare(right.intent.intentId));
    let claimedCapacity = 0;
    for (const candidate of contenders) {
      if (claimedCapacity + candidate.footprint <= available) {
        claimedCapacity += candidate.footprint;
        winnerIds.add(candidate.intent.intentId);
      } else {
        resolveIntent(context, candidate.intent, "movement", "contested", "target_zone_capacity_lost");
      }
    }
  }

  const provisionalWinners = candidates
    .filter((candidate) => winnerIds.has(candidate.intent.intentId))
    .sort((left, right) =>
      right.actor.initiative - left.actor.initiative || left.actor.actorId.localeCompare(right.actor.actorId));
  const reactionIntents = sortedIntents(context.state, intents.filter((intent): intent is ReactionIntent =>
    intent.kind === "guard" || (intent.kind === "use_ability" && intentPhase(intent) === "reaction")));
  const reactedMoverIds = new Set<string>();
  for (const reactionIntent of reactionIntents) {
    const guard = context.state.actors[reactionIntent.actorId]!;
    if (guard.lifeState !== "active") {
      resolveIntent(context, reactionIntent, "reaction", "interrupted", "actor_not_active");
      continue;
    }
    const overwatchAbilityId = reactionIntent.kind === "guard" ? "overwatch" : reactionIntent.abilityId;
    if (!Object.values(guard.equipment).some((equipmentId) =>
      STATION_ZERO_V3_EQUIPMENT.find((entry) => entry.equipmentId === equipmentId)?.grantedAbilityIds.includes(overwatchAbilityId))) {
      resolveIntent(context, reactionIntent, "reaction", "invalidated", "actor_lacks_reaction_ability");
      continue;
    }
    if ((guard.abilityCooldowns[overwatchAbilityId] ?? 0) > 0) {
      resolveIntent(context, reactionIntent, "reaction", "invalidated", "reaction_ability_on_cooldown");
      continue;
    }
    const watchedZoneId = reactionIntent.kind === "guard"
      ? reactionIntent.watchedZoneId ??
        (reactionIntent.protectedActorId ? context.state.actors[reactionIntent.protectedActorId]?.position.zoneId : null)
      : reactionIntent.targetZoneId;
    const targetMove = provisionalWinners.find((candidate) =>
      !reactedMoverIds.has(candidate.intent.intentId) &&
      candidate.targetZoneId === watchedZoneId &&
      candidate.actor.factionId !== guard.factionId &&
      candidate.actor.lifeState === "active");
    if (!targetMove) {
      resolveIntent(context, reactionIntent, "reaction", "no_effect", "no_hostile_movement_triggered");
      continue;
    }
    reactedMoverIds.add(targetMove.intent.intentId);
    const factIds = [emitFact(context, {
      kind: "actor_attacked",
      actorId: guard.actorId,
      targetActorId: targetMove.actor.actorId,
      abilityId: overwatchAbilityId,
    })];
    const damage = deterministicDamage(context.state, overwatchAbilityId, targetMove.actor, true);
    factIds.push(...applyDamage(context, guard.actorId, targetMove.actor, damage, [overwatchAbilityId, "movement_reaction"]));
    setAbilityCooldown(guard, overwatchAbilityId);
    resolveIntent(context, reactionIntent, "reaction", "executed", "reaction_triggered", factIds);
  }

  for (const candidate of provisionalWinners) {
    if (candidate.actor.lifeState !== "active") {
      resolveIntent(context, candidate.intent, "movement", "interrupted", "movement_interrupted_by_reaction");
      continue;
    }
    const factIds: string[] = [];
    candidate.actor.position.zoneId = candidate.targetZoneId;
    factIds.push(emitFact(context, {
      kind: "actor_moved",
      actorId: candidate.actor.actorId,
      fromZoneId: candidate.fromZoneId,
      toZoneId: candidate.targetZoneId,
    }));
    for (const civilian of candidate.escortedCivilians) {
      civilian.position.zoneId = candidate.targetZoneId;
      factIds.push(emitFact(context, {
        kind: "actor_moved",
        actorId: civilian.actorId,
        fromZoneId: candidate.fromZoneId,
        toZoneId: candidate.targetZoneId,
      }));
    }
    resolveIntent(context, candidate.intent, "movement", "executed", "movement_completed", factIds);
  }
}

function resolveActorAttack(
  context: MutableContext,
  intent: Extract<StationZeroActorIntent, { kind: "attack" | "use_ability" }>,
  targetActorId: string,
): void {
  const attacker = context.state.actors[intent.actorId]!;
  const definition = ability(intent.abilityId);
  if (attacker.lifeState !== "active") {
    resolveIntent(context, intent, "combat", "interrupted", "actor_not_active");
    return;
  }
  const target = context.state.actors[targetActorId];
  if (!target || target.lifeState === "dead" || target.lifeState === "extracted" || target.lifeState === "captured") {
    resolveIntent(context, intent, "combat", "invalidated", "target_no_longer_attackable");
    return;
  }
  const distance = stationZeroShortestDistance(context.state, attacker.position.zoneId, target.position.zoneId, attacker.factionId);
  if (distance === null || distance > definition.range) {
    resolveIntent(context, intent, "combat", "invalidated", "target_out_of_range_after_movement");
    return;
  }
  const factIds = [emitFact(context, {
    kind: "actor_attacked",
    actorId: attacker.actorId,
    targetActorId: target.actorId,
    abilityId: definition.abilityId,
  })];
  if (target.lifeState === "incapacitated") {
    const lifeFactId = changeLifeState(context, target, "dead");
    if (lifeFactId) factIds.push(lifeFactId);
    factIds.push(...dropActorPossessions(context, target));
    setAbilityCooldown(attacker, definition.abilityId);
    resolveIntent(context, intent, "combat", "executed", "incapacitated_target_finished", factIds);
    return;
  }
  const damage = deterministicDamage(context.state, definition.abilityId, target);
  factIds.push(...applyDamage(context, attacker.actorId, target, damage, [definition.abilityId, "combat"]));
  setAbilityCooldown(attacker, definition.abilityId);
  resolveIntent(context, intent, "combat", damage > 0 ? "executed" : "no_effect", damage > 0 ? "attack_resolved" : "attack_absorbed", factIds);
}

function resolveCombat(context: MutableContext, intents: StationZeroActorIntent[]): void {
  const combatIntents = sortedIntents(context.state, intents.filter((intent) => intentPhase(intent) === "combat"));
  for (const intent of combatIntents) {
    if (intent.kind === "attack") {
      resolveActorAttack(context, intent, intent.targetActorId);
      continue;
    }
    if (intent.kind !== "use_ability") continue;
    if (intent.targetActorId !== null) {
      resolveActorAttack(context, intent, intent.targetActorId);
      continue;
    }
    const attacker = context.state.actors[intent.actorId]!;
    if (attacker.lifeState !== "active") {
      resolveIntent(context, intent, "combat", "interrupted", "actor_not_active");
      continue;
    }
    if (intent.targetSystemId !== null) {
      const system = context.state.systems[intent.targetSystemId]!;
      const distance = stationZeroShortestDistance(context.state, attacker.position.zoneId, system.zoneId, attacker.factionId);
      if (distance === null || distance > ability(intent.abilityId).range) {
        resolveIntent(context, intent, "combat", "invalidated", "system_out_of_range");
        continue;
      }
      const integrityBefore = system.integrity;
      const poweredBefore = system.powered;
      system.integrity = quantizeFraction(clamp(system.integrity - ability(intent.abilityId).damage / 100, 0, 1));
      if (system.integrity < 0.4) system.powered = false;
      const factId = emitFact(context, {
        kind: "system_changed",
        systemId: system.systemId,
        integrityBefore,
        integrityAfter: system.integrity,
        poweredBefore,
        poweredAfter: system.powered,
      });
      setAbilityCooldown(attacker, intent.abilityId);
      resolveIntent(context, intent, "combat", "executed", "system_attack_resolved", [factId]);
      continue;
    }
    resolveIntent(context, intent, "combat", "invalidated", "unsupported_combat_target");
  }
}

function sameZone(state: StationZeroV3WorldState, actorId: string, targetZoneId: string): boolean {
  return state.actors[actorId]?.position.zoneId === targetZoneId;
}

function consumeInventoryItem(actor: StationZeroActorState, itemId: string): boolean {
  const index = actor.inventoryItemIds.indexOf(itemId);
  if (index < 0) return false;
  actor.inventoryItemIds.splice(index, 1);
  return true;
}

function repairSystem(
  context: MutableContext,
  intent: StationZeroActorIntent,
  actor: StationZeroActorState,
  systemId: string,
  consumeParts: boolean,
): void {
  const system = context.state.systems[systemId];
  if (!system || !sameZone(context.state, actor.actorId, system.zoneId)) {
    resolveIntent(context, intent, "interaction", "invalidated", "repair_target_not_local");
    return;
  }
  const factIds: string[] = [];
  if (consumeParts) {
    if (!consumeInventoryItem(actor, "spare-parts")) {
      resolveIntent(context, intent, "interaction", "invalidated", "spare_parts_unavailable");
      return;
    }
    factIds.push(emitFact(context, {
      kind: "item_consumed",
      actorId: actor.actorId,
      itemId: "spare-parts",
      quantity: 1,
      purpose: `repair:${systemId}`,
    }));
  }
  const integrityBefore = system.integrity;
  const poweredBefore = system.powered;
  system.integrity = quantizeFraction(clamp(system.integrity + (consumeParts ? 0.3 : 0.2), 0, 1));
  factIds.push(emitFact(context, {
    kind: "system_changed",
    systemId,
    integrityBefore,
    integrityAfter: system.integrity,
    poweredBefore,
    poweredAfter: system.powered,
  }));
  resolveIntent(context, intent, "interaction", system.integrity === integrityBefore ? "no_effect" : "executed", "repair_resolved", factIds);
}

function stabilizeActor(
  context: MutableContext,
  intent: StationZeroActorIntent,
  actor: StationZeroActorState,
  targetActorId: string,
): void {
  const target = context.state.actors[targetActorId];
  if (!target || !sameZone(context.state, actor.actorId, target.position.zoneId) || target.lifeState === "dead") {
    resolveIntent(context, intent, "interaction", "invalidated", "stabilize_target_not_local_or_dead");
    return;
  }
  if (target.lifeState === "incapacitated") {
    const zone = context.state.zones[target.position.zoneId]!;
    const activeOccupants = Object.values(context.state.actors).filter((candidate) =>
      candidate.lifeState === "active" && candidate.position.zoneId === target.position.zoneId).length;
    if (activeOccupants >= zone.capacity) {
      resolveIntent(context, intent, "interaction", "contested", "stabilization_zone_capacity_lost");
      return;
    }
  }
  const factIds: string[] = [];
  const beforeHealth = target.health;
  target.health = Math.min(target.maximumHealth, Math.max(25, target.health + 30));
  if (beforeHealth !== target.health) {
    factIds.push(emitFact(context, {
      kind: "actor_health_changed",
      actorId: target.actorId,
      before: beforeHealth,
      after: target.health,
      causes: ["medical_stabilization"],
    }));
  }
  if (target.lifeState === "incapacitated") {
    const lifeFactId = changeLifeState(context, target, "active");
    if (lifeFactId) factIds.push(lifeFactId);
  }
  const statusFactId = setActorStatus(context, target, "stabilized", true);
  if (statusFactId) factIds.push(statusFactId);
  resolveIntent(context, intent, "interaction", factIds.length > 0 ? "executed" : "no_effect", "stabilization_resolved", factIds);
}

function resolveInteraction(context: MutableContext, intents: StationZeroActorIntent[]): void {
  const interactionIntents = sortedIntents(context.state, intents.filter((intent) => intentPhase(intent) === "interaction"));
  for (const intent of interactionIntents) {
    const actor = context.state.actors[intent.actorId]!;
    if (actor.lifeState !== "active") {
      resolveIntent(context, intent, "interaction", "interrupted", "actor_not_active");
      continue;
    }
    if (intent.kind === "pickup") {
      const groundItem = context.state.groundItems[intent.groundItemId];
      if (!groundItem || groundItem.quantity < intent.quantity || !sameZone(context.state, actor.actorId, groundItem.zoneId)) {
        resolveIntent(context, intent, "interaction", "contested", "ground_item_claim_lost_or_not_local");
        continue;
      }
      for (let index = 0; index < intent.quantity; index += 1) actor.inventoryItemIds.push(groundItem.itemId);
      actor.inventoryItemIds.sort();
      groundItem.quantity -= intent.quantity;
      if (groundItem.quantity === 0) delete context.state.groundItems[groundItem.groundItemId];
      const factId = emitFact(context, {
        kind: "ground_item_picked_up",
        groundItemId: intent.groundItemId,
        actorId: actor.actorId,
        quantity: intent.quantity,
      });
      resolveIntent(context, intent, "interaction", "executed", "ground_item_acquired", [factId]);
      continue;
    }
    if (intent.kind === "extract") {
      if (!context.state.zones[actor.position.zoneId]?.tags.includes(`extraction:${actor.factionId}`)) {
        resolveIntent(context, intent, "interaction", "invalidated", "extraction_zone_unavailable");
        continue;
      }
      const factIds: string[] = [];
      for (const itemId of [...actor.inventoryItemIds].sort()) {
        factIds.push(emitFact(context, { kind: "item_extracted", actorId: actor.actorId, factionId: actor.factionId!, itemId }));
      }
      const statusFactId = setActorStatus(context, actor, `extracted-by:${actor.factionId}`, true);
      if (statusFactId) factIds.push(statusFactId);
      const lifeFactId = changeLifeState(context, actor, "extracted");
      if (lifeFactId) factIds.push(lifeFactId);
      for (const civilian of Object.values(context.state.actors)
        .filter((entry) => entry.kind === "civilian" && entry.position.zoneId === actor.position.zoneId &&
          entry.statusIds.includes(`escorted-by:${actor.actorId}`))
        .sort((left, right) => left.actorId.localeCompare(right.actorId))) {
        const civilianStatusFactId = setActorStatus(context, civilian, `extracted-by:${actor.factionId}`, true);
        if (civilianStatusFactId) factIds.push(civilianStatusFactId);
        const civilianLifeFactId = changeLifeState(context, civilian, "extracted");
        if (civilianLifeFactId) factIds.push(civilianLifeFactId);
        revealActor(context, actor.factionId!, civilian);
      }
      resolveIntent(context, intent, "interaction", "executed", "actor_extracted", factIds);
      continue;
    }
    if (intent.kind === "use_ability") {
      switch (intent.abilityId) {
        case "field-repair":
          repairSystem(context, intent, actor, intent.targetSystemId!, false);
          setAbilityCooldown(actor, intent.abilityId);
          continue;
        case "combat-stabilize":
          stabilizeActor(context, intent, actor, intent.targetActorId!);
          setAbilityCooldown(actor, intent.abilityId);
          continue;
        case "system-intrusion": {
          const system = intent.targetSystemId ? context.state.systems[intent.targetSystemId] : null;
          const hazard = intent.targetHazardId ? context.state.hazards[intent.targetHazardId] : null;
          if (system && sameZone(context.state, actor.actorId, system.zoneId)) {
            const integrityBefore = system.integrity;
            const poweredBefore = system.powered;
            system.powered = !system.powered;
            const factId = emitFact(context, {
              kind: "system_changed",
              systemId: system.systemId,
              integrityBefore,
              integrityAfter: system.integrity,
              poweredBefore,
              poweredAfter: system.powered,
            });
            setAbilityCooldown(actor, intent.abilityId);
            resolveIntent(context, intent, "interaction", "executed", "system_intrusion_resolved", [factId]);
          } else if (hazard && sameZone(context.state, actor.actorId, hazard.zoneId)) {
            const severityBefore = hazard.severity;
            hazard.contained = true;
            hazard.severity = Math.max(0, hazard.severity - 1);
            const factId = emitFact(context, {
              kind: "hazard_changed",
              hazardId: hazard.hazardId,
              severityBefore,
              severityAfter: hazard.severity,
              contained: hazard.contained,
            });
            setAbilityCooldown(actor, intent.abilityId);
            resolveIntent(context, intent, "interaction", "executed", "hazard_intrusion_resolved", [factId]);
          } else {
            resolveIntent(context, intent, "interaction", "invalidated", "intrusion_target_not_local");
          }
          continue;
        }
        default:
          resolveIntent(context, intent, "interaction", "invalidated", "unsupported_interaction_ability");
          continue;
      }
    }
    if (intent.kind !== "interact") continue;
    switch (intent.operationId) {
      case "repair":
        repairSystem(context, intent, actor, intent.targetId, true);
        break;
      case "hack": {
        const system = context.state.systems[intent.targetId];
        const passage = context.state.passages[intent.targetId];
        if (system && sameZone(context.state, actor.actorId, system.zoneId)) {
          const integrityBefore = system.integrity;
          const poweredBefore = system.powered;
          system.powered = !system.powered;
          const factId = emitFact(context, {
            kind: "system_changed",
            systemId: system.systemId,
            integrityBefore,
            integrityAfter: system.integrity,
            poweredBefore,
            poweredAfter: system.powered,
          });
          resolveIntent(context, intent, "interaction", "executed", "system_hacked", [factId]);
        } else if (passage && (passage.zoneAId === actor.position.zoneId || passage.zoneBId === actor.position.zoneId)) {
          const before = passage.state;
          passage.state = passage.state === "open" ? "closed" : "open";
          const factId = emitFact(context, { kind: "passage_changed", passageId: passage.passageId, before, after: passage.state });
          resolveIntent(context, intent, "interaction", "executed", "passage_hacked", [factId]);
        } else {
          resolveIntent(context, intent, "interaction", "invalidated", "hack_target_not_local");
        }
        break;
      }
      case "stabilize":
        stabilizeActor(context, intent, actor, intent.targetId);
        break;
      case "rescue": {
        const target = context.state.actors[intent.targetId];
        if (!target || target.kind !== "civilian" || target.lifeState !== "active" || !sameZone(context.state, actor.actorId, target.position.zoneId)) {
          resolveIntent(context, intent, "interaction", "invalidated", "civilian_not_available_for_rescue");
          break;
        }
        const factId = setActorStatus(context, target, `escorted-by:${actor.actorId}`, true);
        resolveIntent(context, intent, "interaction", factId ? "executed" : "no_effect", "civilian_escort_bound", factId ? [factId] : []);
        break;
      }
      case "capture": {
        const target = context.state.actors[intent.targetId];
        if (!target || target.lifeState !== "incapacitated" || !sameZone(context.state, actor.actorId, target.position.zoneId)) {
          resolveIntent(context, intent, "interaction", "invalidated", "capture_target_not_incapacitated_and_local");
          break;
        }
        const factIds: string[] = [];
        const statusFactId = setActorStatus(context, target, `captured-by:${actor.factionId}`, true);
        if (statusFactId) factIds.push(statusFactId);
        const lifeFactId = changeLifeState(context, target, "captured");
        if (lifeFactId) factIds.push(lifeFactId);
        resolveIntent(context, intent, "interaction", "executed", "target_captured", factIds);
        break;
      }
      case "devour": {
        const target = context.state.actors[intent.targetId];
        if (!target || !["incapacitated", "dead"].includes(target.lifeState) || !sameZone(context.state, actor.actorId, target.position.zoneId)) {
          resolveIntent(context, intent, "interaction", "invalidated", "devour_target_not_available");
          break;
        }
        const factIds: string[] = [];
        if (target.lifeState !== "dead") {
          const lifeFactId = changeLifeState(context, target, "dead");
          if (lifeFactId) factIds.push(lifeFactId);
          factIds.push(...dropActorPossessions(context, target));
        }
        const statusFactId = setActorStatus(context, target, "devoured-by:swarm", true);
        if (statusFactId) factIds.push(statusFactId);
        const before = context.state.environment.biomass;
        context.state.environment.biomass += 4;
        factIds.push(emitFact(context, {
          kind: "environment_changed",
          resourceId: "biomass",
          before,
          after: context.state.environment.biomass,
          causes: ["devour"],
        }));
        resolveIntent(context, intent, "interaction", "executed", "target_devoured", factIds);
        break;
      }
      case "infect": {
        const system = context.state.systems[intent.targetId];
        if (!system || !sameZone(context.state, actor.actorId, system.zoneId)) {
          resolveIntent(context, intent, "interaction", "invalidated", "infect_target_not_local");
          break;
        }
        const integrityBefore = system.integrity;
        const poweredBefore = system.powered;
        system.integrity = quantizeFraction(clamp(system.integrity - 0.1, 0, 1));
        addUnique(system.tags, "infected:swarm");
        const factId = emitFact(context, {
          kind: "system_changed",
          systemId: system.systemId,
          integrityBefore,
          integrityAfter: system.integrity,
          poweredBefore,
          poweredAfter: system.powered,
        });
        resolveIntent(context, intent, "interaction", "executed", "system_infected", [factId]);
        break;
      }
    }
  }
}

function resolveCleanupAbilitiesAndWaits(context: MutableContext, intents: StationZeroActorIntent[]): void {
  const cleanupIntents = sortedIntents(context.state, intents.filter((intent) => intentPhase(intent) === "cleanup"));
  for (const intent of cleanupIntents) {
    const actor = context.state.actors[intent.actorId]!;
    if (intent.kind === "wait") {
      resolveIntent(context, intent, "cleanup", actor.lifeState === "active" ? "no_effect" : "interrupted", actor.lifeState === "active" ? "actor_waited" : "actor_not_active");
      continue;
    }
    if (intent.kind === "use_ability" && intent.abilityId === "brood-call") {
      if (actor.lifeState !== "active") {
        resolveIntent(context, intent, "cleanup", "interrupted", "actor_not_active");
        continue;
      }
      if (context.state.environment.biomass < 3 || intent.targetZoneId === null) {
        resolveIntent(context, intent, "cleanup", "invalidated", "insufficient_biomass_or_zone");
        continue;
      }
      const targetZone = context.state.zones[intent.targetZoneId];
      const occupied = Object.values(context.state.actors).filter((entry) =>
        entry.lifeState === "active" && entry.position.zoneId === intent.targetZoneId).length;
      if (!targetZone || occupied >= targetZone.capacity) {
        resolveIntent(context, intent, "cleanup", "contested", "brood_zone_at_capacity");
        continue;
      }
      const before = context.state.environment.biomass;
      context.state.environment.biomass -= 3;
      const actorId = `swarm-brood:${context.state.revision + 1}:${actor.actorId}`;
      context.state.actors[actorId] = {
        actorId,
        name: "Spawned Brood",
        factionId: "swarm",
        kind: "creature",
        roleId: "drone",
        controllerKind: "policy",
        leaderActorId: actor.actorId,
        position: { zoneId: intent.targetZoneId },
        lifeState: "active",
        health: 45,
        maximumHealth: 45,
        armor: 1,
        actionPoints: 0,
        maximumActionPoints: 2,
        initiative: 40,
        movementRange: 2,
        capabilityIds: ["guard", "devour"],
        traitIds: ["newborn", "expendable"],
        equipment: { biology: "drone-organs" },
        inventoryItemIds: [],
        abilityCooldowns: { pounce: 0 },
        statusIds: [],
      };
      const factIds = [emitFact(context, {
        kind: "environment_changed",
        resourceId: "biomass",
        before,
        after: context.state.environment.biomass,
        causes: ["brood_call"],
      })];
      setAbilityCooldown(actor, intent.abilityId);
      resolveIntent(context, intent, "cleanup", "executed", "brood_spawned", factIds);
      continue;
    }
    resolveIntent(context, intent, "cleanup", "invalidated", "unsupported_cleanup_ability");
  }
}

function advanceEnvironment(context: MutableContext): void {
  const powered = Object.values(context.state.systems)
    .filter((system) => system.powered)
    .sort((left, right) => left.systemId.localeCompare(right.systemId));
  const requestedPower = powered.reduce((total, system) => total + system.powerDraw, 0);
  const batteryBefore = context.state.environment.batteryCharge;
  const consumed = Math.min(batteryBefore, requestedPower);
  context.state.environment.batteryCharge -= consumed;
  context.state.environment.energyConsumed += consumed;
  if (consumed > 0) {
    emitFact(context, {
      kind: "environment_changed",
      resourceId: "battery",
      before: batteryBefore,
      after: context.state.environment.batteryCharge,
      causes: powered.filter((system) => system.powerDraw > 0).map((system) => `powered:${system.systemId}`),
    });
  }
  if (requestedPower > consumed) {
    for (const system of powered.filter((entry) => entry.powerDraw > 0)) {
      const integrityBefore = system.integrity;
      const poweredBefore = system.powered;
      system.powered = false;
      emitFact(context, {
        kind: "system_changed",
        systemId: system.systemId,
        integrityBefore,
        integrityAfter: system.integrity,
        poweredBefore,
        poweredAfter: false,
      });
    }
  }

  const oxygenBefore = context.state.environment.oxygen;
  const breach = context.state.hazards["maintenance-breach"];
  const lifeSupport = context.state.systems["life-support"];
  const oxygenDelta = -2 - (breach && !breach.contained ? breach.severity : 0) +
    (lifeSupport?.powered && lifeSupport.integrity >= 0.7 ? 4 : 0);
  context.state.environment.oxygen = clamp(oxygenBefore + oxygenDelta, 0, 100);
  if (context.state.environment.oxygen !== oxygenBefore) {
    emitFact(context, {
      kind: "environment_changed",
      resourceId: "oxygen",
      before: oxygenBefore,
      after: context.state.environment.oxygen,
      causes: [
        "baseline_consumption",
        ...(breach && !breach.contained ? ["maintenance_breach"] : []),
        ...(lifeSupport?.powered && lifeSupport.integrity >= 0.7 ? ["life_support"] : []),
      ],
    });
  }

  const heatBefore = context.state.environment.reactorHeat;
  const cooling = context.state.systems.cooling;
  const instability = context.state.hazards["reactor-instability"];
  const heatDelta = cooling?.powered && cooling.integrity >= 0.6
    ? -8
    : 6 + (instability && !instability.contained ? instability.severity : 0);
  context.state.environment.reactorHeat = clamp(heatBefore + heatDelta, 0, 100);
  if (context.state.environment.reactorHeat !== heatBefore) {
    emitFact(context, {
      kind: "environment_changed",
      resourceId: "reactor-heat",
      before: heatBefore,
      after: context.state.environment.reactorHeat,
      causes: cooling?.powered && cooling.integrity >= 0.6
        ? ["cooling_operational"]
        : ["cooling_unavailable", ...(instability && !instability.contained ? ["reactor_instability"] : [])],
    });
  }

  const alertBefore = context.state.environment.alertLevel;
  if (context.facts.some((fact) => fact.kind === "actor_attacked")) {
    context.state.environment.alertLevel = Math.min(5, alertBefore + 1);
  }
  if (alertBefore !== context.state.environment.alertLevel) {
    emitFact(context, {
      kind: "environment_changed",
      resourceId: "alert",
      before: alertBefore,
      after: context.state.environment.alertLevel,
      causes: ["combat_detected"],
    });
  }

  for (const actor of Object.values(context.state.actors).sort((left, right) => left.actorId.localeCompare(right.actorId))) {
    if (actor.lifeState !== "active") continue;
    if (context.state.environment.oxygen < 35) {
      applyDamage(context, "environment:oxygen", actor, 5, ["low_oxygen"]);
    }
    const roomId = context.state.zones[actor.position.zoneId]?.roomId;
    if (actor.lifeState === "active" && roomId === "reactor" && context.state.environment.reactorHeat > 85) {
      applyDamage(context, "environment:reactor", actor, 10, ["reactor_heat"]);
    }
  }
}

function objectiveValue(state: StationZeroV3WorldState, objectiveId: string): { progress: number; target: number } {
  const actors = Object.values(state.actors);
  switch (objectiveId) {
    case "rescue-two-civilians":
      return { progress: actors.filter((actor) => actor.kind === "civilian" && actor.statusIds.includes("extracted-by:rescue")).length, target: 2 };
    case "rescue-team-survives":
      return { progress: actors.filter((actor) => actor.kind === "specialist" && actor.factionId === "rescue" && actor.lifeState === "extracted").length, target: 1 };
    case "recover-research-core":
      return { progress: actors.some((actor) => actor.factionId === "rescue" && actor.lifeState === "extracted" && actor.inventoryItemIds.includes("research-core")) ? 1 : 0, target: 1 };
    case "eliminate-hive-alpha":
      return { progress: state.actors["hive-alpha"]?.lifeState === "dead" ? 1 : 0, target: 1 };
    case "pirate-steal-core":
      return { progress: actors.some((actor) => actor.factionId === "pirate" && actor.lifeState === "extracted" && actor.inventoryItemIds.includes("research-core")) ? 1 : 0, target: 1 };
    case "pirate-crew-survives":
      return { progress: actors.filter((actor) => actor.factionId === "pirate" && actor.lifeState === "extracted").length, target: 1 };
    case "capture-engineer":
      return { progress: state.actors["engineer-imani"]?.statusIds.includes("captured-by:pirate") ? 1 : 0, target: 1 };
    case "steal-medical-drone":
      return {
        progress: actors.some((actor) => actor.factionId === "pirate" && actor.lifeState === "extracted" &&
          (actor.inventoryItemIds.includes("medical-drone-item") || actor.equipment.utility === "medical-drone")) ? 1 : 0,
        target: 1,
      };
    case "swarm-gain-biomass": return { progress: state.environment.biomass, target: 12 };
    case "swarm-survives":
      return { progress: ["active", "extracted"].includes(state.actors["hive-alpha"]?.lifeState ?? "dead") ? 1 : 0, target: 1 };
    case "infect-life-support":
      return { progress: state.systems["life-support"]?.tags.includes("infected:swarm") ? 1 : 0, target: 1 };
    case "devour-specialist":
      return { progress: actors.some((actor) => actor.kind === "specialist" && actor.statusIds.includes("devoured-by:swarm")) ? 1 : 0, target: 1 };
    default: return { progress: 0, target: 1 };
  }
}

function updateObjectives(context: MutableContext): void {
  for (const objective of STATION_ZERO_V3_OBJECTIVES) {
    const progressState = context.state.factions[objective.factionId].objectiveProgress[objective.objectiveId]!;
    const before = progressState.status;
    const value = objectiveValue(context.state, objective.objectiveId);
    progressState.progress = value.progress;
    progressState.target = value.target;
    progressState.status = value.progress >= value.target ? "completed" : "active";
    progressState.reason = progressState.status === "completed" ? "world_requirement_satisfied" : null;
    if (before !== progressState.status) {
      emitFact(context, {
        kind: "objective_changed",
        factionId: objective.factionId,
        objectiveId: objective.objectiveId,
        before,
        after: progressState.status,
      });
    }
  }
}

function outcomeForFaction(state: StationZeroV3WorldState, factionId: StationZeroFactionId): StationZeroFactionOutcome {
  const definitions = STATION_ZERO_V3_OBJECTIVES.filter((objective) => objective.factionId === factionId);
  const mandatory = definitions.filter((objective) => objective.mandatory);
  const progress = state.factions[factionId].objectiveProgress;
  if (mandatory.every((objective) => progress[objective.objectiveId]?.status === "completed")) return "victory";
  const anyCompleted = definitions.some((objective) => progress[objective.objectiveId]?.status === "completed");
  const anyExtracted = Object.values(state.actors).some((actor) => actor.factionId === factionId && actor.lifeState === "extracted");
  return anyCompleted || anyExtracted ? "partial" : "failure";
}

function updateTerminalState(context: MutableContext): void {
  const activeCombatants = Object.values(context.state.actors).filter((actor) => actor.factionId !== null && actor.lifeState === "active");
  const terminalReason = context.state.encounter.turn >= context.state.encounter.turnLimit
    ? "turn_limit"
    : activeCombatants.length === 0
      ? "no_active_combatants"
      : null;
  if (!terminalReason) return;
  context.state.encounter.status = "terminal";
  context.state.encounter.reason = terminalReason;
  for (const factionId of STATION_ZERO_FACTION_IDS) {
    const faction = context.state.factions[factionId];
    const before = faction.outcome;
    faction.outcome = outcomeForFaction(context.state, factionId);
    faction.outcomeReason = terminalReason;
    if (before !== faction.outcome) {
      emitFact(context, {
        kind: "faction_outcome_changed",
        factionId,
        before,
        after: faction.outcome,
        reason: terminalReason,
      });
    }
  }
}

function refreshCooldownsAndBudgets(state: StationZeroV3WorldState): void {
  for (const actor of Object.values(state.actors)) {
    actor.abilityCooldowns = Object.fromEntries(Object.entries(actor.abilityCooldowns)
      .map(([abilityId, turns]) => [abilityId, Math.max(0, turns - 1)]));
    actor.actionPoints = actor.lifeState === "active" ? actor.maximumActionPoints : 0;
    actor.statusIds = actor.statusIds.filter((statusId) => !statusId.startsWith("pheromone-surge:"));
  }
  for (const factionId of STATION_ZERO_FACTION_IDS) {
    const faction = state.factions[factionId];
    faction.commanderAbilityCooldowns = Object.fromEntries(Object.entries(faction.commanderAbilityCooldowns)
      .map(([abilityId, turns]) => [abilityId, Math.max(0, turns - 1)]));
    faction.commandPoints = faction.maximumCommandPoints;
    faction.uplinkSlots = faction.maximumUplinkSlots;
  }
}

function refreshFactionKnowledge(context: MutableContext): void {
  for (const factionId of STATION_ZERO_FACTION_IDS) {
    const knowledge = context.state.factionKnowledge[factionId];
    for (const actor of Object.values(context.state.actors)
      .filter((entry) => entry.factionId === factionId)
      .sort((left, right) => left.actorId.localeCompare(right.actorId))) {
      knowledge.knownActors[actor.actorId] = knownActorSnapshot(actor, context.state.encounter.turn);
    }
    const originZones = Object.values(context.state.actors)
      .filter((actor) => actor.factionId === factionId && actor.lifeState === "active")
      .map((actor) => actor.position.zoneId);
    const visibleZones = stationZeroVisibleZonesFrom(context.state, originZones, factionId);
    for (const zoneId of visibleZones) revealZone(context, factionId, zoneId);
    for (const [actorId, known] of Object.entries(knowledge.knownActors)) {
      if (!visibleZones.includes(context.state.actors[actorId]?.position.zoneId ?? "") &&
          context.state.actors[actorId]?.factionId !== factionId) {
        known.confidence = "stale";
      }
    }
  }
}

function factVisibleToFaction(
  state: StationZeroV3WorldState,
  factionId: StationZeroFactionId,
  fact: StationZeroFact,
): boolean {
  const ownVisibleZones = stationZeroVisibleZonesFrom(
    state,
    Object.values(state.actors)
      .filter((actor) => actor.factionId === factionId && actor.lifeState === "active")
      .map((actor) => actor.position.zoneId),
    factionId,
  );
  const actorVisible = (actorId: string): boolean => {
    const actor = state.actors[actorId];
    return Boolean(actor && (actor.factionId === factionId || ownVisibleZones.includes(actor.position.zoneId)));
  };
  switch (fact.kind) {
    case "commander_ability_used": return fact.factionId === factionId;
    case "actor_moved": return actorVisible(fact.actorId) || ownVisibleZones.includes(fact.fromZoneId) || ownVisibleZones.includes(fact.toZoneId);
    case "actor_attacked": return actorVisible(fact.actorId) || actorVisible(fact.targetActorId);
    case "damage_dealt": return actorVisible(fact.sourceActorId) || actorVisible(fact.targetActorId);
    case "actor_health_changed":
    case "actor_life_state_changed":
    case "actor_status_changed": return actorVisible(fact.actorId);
    case "ground_item_dropped": return actorVisible(fact.actorId) || ownVisibleZones.includes(fact.zoneId);
    case "ground_item_picked_up":
    case "item_consumed": return actorVisible(fact.actorId);
    case "item_extracted": return fact.factionId === factionId || actorVisible(fact.actorId);
    case "passage_changed": {
      const passage = state.passages[fact.passageId];
      return Boolean(passage && (ownVisibleZones.includes(passage.zoneAId) || ownVisibleZones.includes(passage.zoneBId)));
    }
    case "system_changed": return state.factionKnowledge[factionId].knownSystemIds.includes(fact.systemId);
    case "hazard_changed": return state.factionKnowledge[factionId].knownHazardIds.includes(fact.hazardId);
    case "knowledge_revealed": return fact.factionId === factionId;
    case "objective_changed":
    case "faction_outcome_changed": return fact.factionId === factionId;
    case "environment_changed": return true;
  }
}

function buildObservations(context: MutableContext): Record<StationZeroFactionId, StationZeroFactionObservation> {
  return Object.fromEntries(STATION_ZERO_FACTION_IDS.map((factionId) => {
    const knowledge = context.state.factionKnowledge[factionId];
    const base = {
      factionId,
      worldRevision: context.state.revision,
      turn: context.state.encounter.turn,
      visibleFactIds: context.facts.filter((fact) => factVisibleToFaction(context.state, factionId, fact)).map((fact) => fact.factId),
      discoveredRoomIds: [...knowledge.discoveredRoomIds].sort(),
      discoveredZoneIds: [...knowledge.discoveredZoneIds].sort(),
      knownActorIds: Object.keys(knowledge.knownActors).sort(),
      knownSystemIds: [...knowledge.knownSystemIds].sort(),
      knownHazardIds: [...knowledge.knownHazardIds].sort(),
      knownGroundItemIds: [...knowledge.knownGroundItemIds].filter((groundItemId) => context.state.groundItems[groundItemId] !== undefined).sort(),
    };
    return [factionId, { ...base, observationDigest: sha256(base) }];
  })) as Record<StationZeroFactionId, StationZeroFactionObservation>;
}

export function prepareStationZeroV3Commitment(state: StationZeroV3WorldState): StationZeroV3WorldState {
  assertStationZeroV3World(state);
  if (state.encounter.status !== "running") throw new TypeError("Cannot prepare a terminal Encounter");
  if (!['situation', 'aftermath', 'commitment'].includes(state.encounter.phase)) {
    throw new TypeError(`Cannot prepare commitment from ${state.encounter.phase}`);
  }
  const next = structuredClone(state);
  next.encounter.phase = "commitment";
  return next;
}

export function applyStationZeroV3Turn(
  inputState: StationZeroV3WorldState,
  inputBatch: StationZeroTurnBatch,
): StationZeroTurnApplyResult {
  try {
    assertStationZeroV3World(inputState);
    assertStationZeroTurnBatch(inputState, inputBatch);
  } catch (error) {
    return {
      status: "rejected",
      code: "invalid_turn_batch",
      reason: error instanceof Error ? error.message : String(error),
    };
  }

  const stateDigestBefore = sha256(inputState);
  const batch = canonicalizeStationZeroV3TurnBatch(inputBatch);
  const context: MutableContext = {
    state: structuredClone(inputState),
    batch,
    facts: [],
    resolutions: new Map(),
    factSequence: 0,
  };
  context.state.encounter.phase = "resolution";
  const intents = allIntents(batch);

  applyCommanderActions(context);
  resolveMovementAndReactions(context, intents);
  resolveCombat(context, intents);
  resolveInteraction(context, intents);
  advanceEnvironment(context);
  resolveCleanupAbilitiesAndWaits(context, intents);
  refreshCooldownsAndBudgets(context.state);

  context.state.revision += 1;
  context.state.encounter.turn += 1;
  context.state.encounter.phase = "aftermath";
  context.state.encounter.activePlanRevision += 1;
  updateObjectives(context);
  updateTerminalState(context);
  refreshFactionKnowledge(context);

  for (const intent of sortedIntents(context.state, intents)) {
    if (!context.resolutions.has(intent.intentId)) {
      throw new Error(`Committed Intent ${intent.intentId} has no Resolution`);
    }
  }
  assertStationZeroV3World(context.state);

  const observations = buildObservations(context);
  const intentResolutions = [...context.resolutions.values()].sort((left, right) =>
    (PHASE_ORDER.get(left.resolutionPhase) ?? 99) - (PHASE_ORDER.get(right.resolutionPhase) ?? 99) ||
    actorInitiative(context.state, right.actorId) - actorInitiative(context.state, left.actorId) ||
    left.actorId.localeCompare(right.actorId) ||
    left.intentId.localeCompare(right.intentId));
  const resolutionBase = {
    turnBatchId: batch.turnBatchId,
    worldRevisionBefore: inputState.revision,
    worldRevisionAfter: context.state.revision,
    turnBefore: inputState.encounter.turn,
    turnAfter: context.state.encounter.turn,
    intentResolutions,
    facts: context.facts,
    observations,
  };
  const resolution: StationZeroTurnResolution = {
    ...resolutionBase,
    deterministicDigest: sha256(resolutionBase),
  };
  const stateDigestAfter = sha256(context.state);
  const recordBase = {
    schemaVersion: 1 as const,
    kind: "ordivon.game.station-zero-v3-turn-record" as const,
    stateDigestBefore,
    batch,
    resolution,
    stateDigestAfter,
  };
  const record: StationZeroTurnRecord = { ...recordBase, recordDigest: sha256(recordBase) };
  return { status: "accepted", state: context.state, resolution, record };
}

export function replayStationZeroV3Turn(
  inputState: StationZeroV3WorldState,
  record: StationZeroTurnRecord,
): Extract<StationZeroTurnApplyResult, { status: "accepted" }> {
  if (sha256(inputState) !== record.stateDigestBefore) throw new TypeError("Turn Record before-state digest mismatch");
  const recordBase = {
    schemaVersion: record.schemaVersion,
    kind: record.kind,
    stateDigestBefore: record.stateDigestBefore,
    batch: record.batch,
    resolution: record.resolution,
    stateDigestAfter: record.stateDigestAfter,
  };
  if (sha256(recordBase) !== record.recordDigest) throw new TypeError("Turn Record digest mismatch");
  const replay = applyStationZeroV3Turn(inputState, record.batch);
  if (replay.status !== "accepted") throw new TypeError(`Retained Turn Record no longer admits: ${replay.reason}`);
  if (replay.resolution.deterministicDigest !== record.resolution.deterministicDigest) {
    throw new TypeError("Turn Record Resolution digest mismatch");
  }
  if (sha256(replay.state) !== record.stateDigestAfter) throw new TypeError("Turn Record after-state digest mismatch");
  if (replay.record.recordDigest !== record.recordDigest) throw new TypeError("Turn Record replay identity mismatch");
  return replay;
}

export function replayStationZeroV3History(
  genesis: StationZeroV3WorldState,
  records: StationZeroTurnRecord[],
): {
  state: StationZeroV3WorldState;
  turns: Array<Extract<StationZeroTurnApplyResult, { status: "accepted" }>>;
} {
  if (records.length === 0) return { state: structuredClone(genesis), turns: [] };
  let state = prepareStationZeroV3Commitment(genesis);
  const turns: Array<Extract<StationZeroTurnApplyResult, { status: "accepted" }>> = [];
  for (const [index, record] of records.entries()) {
    const replay = replayStationZeroV3Turn(state, record);
    turns.push(replay);
    state = replay.state;
    if (index < records.length - 1) state = prepareStationZeroV3Commitment(state);
  }
  return { state, turns };
}
