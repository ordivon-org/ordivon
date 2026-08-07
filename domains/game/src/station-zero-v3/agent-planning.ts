import { sha256 } from "../digest.ts";
import {
  STATION_ZERO_V3_ABILITIES,
  STATION_ZERO_V3_COMMANDER_ABILITIES,
  STATION_ZERO_V3_EQUIPMENT,
  STATION_ZERO_V3_OBJECTIVES,
} from "./content.ts";
import { assertStationZeroFactionTurnPlan, assertStationZeroStandingOrder } from "./contracts.ts";
import type {
  StationZeroActorIntent,
  StationZeroActorState,
  StationZeroCommanderAction,
  StationZeroFactionId,
  StationZeroFactionTurnPlan,
  StationZeroStandingOrder,
  StationZeroV3WorldState,
} from "./model.ts";
import { STATION_ZERO_FACTION_IDS } from "./model.ts";
import type { StationZeroV3PlanningHead } from "./p2-model.ts";
import type {
  StationZeroV3AgentCandidate,
  StationZeroV3AgentContext,
  StationZeroV3AgentDecision,
  StationZeroV3AgentProvider,
  StationZeroV3AgentProviderFactory,
  StationZeroV3AgentResponsibility,
  StationZeroV3CommanderDirectiveId,
  StationZeroV3CommanderOrder,
  StationZeroV3FactionPlanExplanation,
  StationZeroV3PlanPreview,
  StationZeroV3PlayCatalog,
  StationZeroV3PolicyDecision,
  StationZeroV3PirateDirective,
  StationZeroV3SwarmDirective,
} from "./p3-model.ts";
import {
  STATION_ZERO_V3_COMMANDER_DIRECTIVE_IDS,
  STATION_ZERO_V3_COMMAND_POSTURES,
  STATION_ZERO_V3_FORMATIONS,
} from "./p3-model.ts";
import {
  stationZeroAdjacentZones,
  stationZeroMovementStepToward,
  stationZeroShortestDistance,
} from "./topology.ts";

const AGENT_ACTOR_IDS = new Set([
  "engineer-imani",
  "medic-reyes",
  "security-chen",
  "pirate-captain-veyra",
  "hive-alpha",
]);

const RESCUE_OBJECTIVE_IDS = [
  "rescue-two-civilians",
  "recover-research-core",
  "eliminate-hive-alpha",
] as const;

function intentIdentity(planningId: string, actorId: string, suffix: string): string {
  return `intent:p3:${planningId}:${actorId}:${suffix}`;
}

function candidate(
  intent: StationZeroActorIntent,
  label: string,
  rationaleHint: string,
  tags: string[],
): StationZeroV3AgentCandidate {
  return {
    candidateId: `candidate:${intent.intentId}`,
    actorId: intent.actorId,
    factionId: intent.factionId,
    intent,
    label,
    rationaleHint,
    tags: [...new Set(tags)].sort(),
  };
}

function abilityIds(actor: StationZeroActorState): string[] {
  return [...new Set(Object.values(actor.equipment).flatMap((equipmentId) =>
    STATION_ZERO_V3_EQUIPMENT.find((entry) => entry.equipmentId === equipmentId)?.grantedAbilityIds ?? []))].sort();
}

function actorHealthBand(actor: StationZeroActorState): "healthy" | "wounded" | "critical" | "unknown" {
  if (actor.health >= actor.maximumHealth * 0.75) return "healthy";
  if (actor.health >= actor.maximumHealth * 0.35) return "wounded";
  return "critical";
}

function knownZoneIds(state: StationZeroV3WorldState, factionId: StationZeroFactionId): string[] {
  const knowledge = state.factionKnowledge[factionId];
  const ownZones = Object.values(state.actors)
    .filter((actor) => actor.factionId === factionId)
    .map((actor) => actor.position.zoneId);
  return [...new Set([...knowledge.discoveredZoneIds, ...ownZones])].sort();
}

function frontierZoneIds(state: StationZeroV3WorldState, factionId: StationZeroFactionId): string[] {
  const known = new Set(knownZoneIds(state, factionId));
  const frontier = new Set<string>();
  for (const zoneId of known) {
    for (const neighbor of stationZeroAdjacentZones(state, zoneId, factionId)) {
      if (!known.has(neighbor)) frontier.add(neighbor);
    }
  }
  return [...frontier].sort();
}

function actorKnownToFaction(
  state: StationZeroV3WorldState,
  factionId: StationZeroFactionId,
  actorId: string,
): boolean {
  return state.factionKnowledge[factionId].knownActors[actorId] !== undefined;
}

function confirmedCurrentContact(
  state: StationZeroV3WorldState,
  factionId: StationZeroFactionId,
  actorId: string,
): boolean {
  const known = state.factionKnowledge[factionId].knownActors[actorId];
  return Boolean(known && known.confidence === "confirmed" && known.observedAtTurn === state.encounter.turn);
}

function rescueResponsibilities(
  state: StationZeroV3WorldState,
  planning: StationZeroV3PlanningHead,
  order: StationZeroV3CommanderOrder | null,
): Map<string, StationZeroV3AgentResponsibility> {
  const responsibilities = new Map<string, StationZeroV3AgentResponsibility>();
  if (!order || order.primaryObjectiveId !== "rescue-two-civilians") return responsibilities;
  const knowledge = state.factionKnowledge.rescue;
  const knownCivilianContacts = Object.values(knowledge.knownActors)
    .filter((known) => state.actors[known.actorId]?.kind === "civilian")
    .sort((left, right) => left.actorId.localeCompare(right.actorId));
  const knownCivilians = knownCivilianContacts.filter((known) => known.observedLifeState === "active");
  const assignedTargets = new Set<string>();
  const assignedActors = new Set<string>();

  for (const known of knownCivilians) {
    const retained = state.actors[known.actorId]!;
    const escortStatus = retained.statusIds.find((statusId) => statusId.startsWith("escorted-by:"));
    const escortActorId = escortStatus?.slice("escorted-by:".length) ?? null;
    const escortActor = escortActorId ? state.actors[escortActorId] : null;
    if (!escortActorId || escortActor?.factionId !== "rescue" || escortActor.lifeState !== "active") continue;
    assignedTargets.add(known.actorId);
    assignedActors.add(escortActorId);
    responsibilities.set(escortActorId, {
      responsibilityId: `responsibility:p3:${planning.planningId}:${escortActorId}:recover:${known.actorId}`,
      kind: "recover-civilian",
      objectiveId: "rescue-two-civilians",
      targetActorId: known.actorId,
      targetZoneId: "rescue-airlock",
      blockerActorIds: [],
    });
  }

  const ownerPriority = ["medic-reyes", "engineer-imani", "security-chen"]
    .map((actorId) => state.actors[actorId])
    .filter((actor): actor is StationZeroActorState => Boolean(actor && actor.factionId === "rescue" && actor.lifeState === "active" && !assignedActors.has(actor.actorId)));
  for (const owner of ownerPriority) {
    const target = knownCivilians
      .filter((known) => !assignedTargets.has(known.actorId))
      .map((known) => ({ known, distance: stationZeroShortestDistance(state, owner.position.zoneId, known.lastKnownZoneId, "rescue") }))
      .sort((left, right) => (left.distance ?? Number.MAX_SAFE_INTEGER) - (right.distance ?? Number.MAX_SAFE_INTEGER) || left.known.actorId.localeCompare(right.known.actorId))[0];
    if (!target) break;
    assignedTargets.add(target.known.actorId);
    assignedActors.add(owner.actorId);
    responsibilities.set(owner.actorId, {
      responsibilityId: `responsibility:p3:${planning.planningId}:${owner.actorId}:recover:${target.known.actorId}`,
      kind: "recover-civilian",
      objectiveId: "rescue-two-civilians",
      targetActorId: target.known.actorId,
      targetZoneId: target.known.lastKnownZoneId,
      blockerActorIds: [],
    });
  }

  const knownCivilianRooms = new Set(knownCivilianContacts.map((known) => state.zones[known.lastKnownZoneId]?.roomId).filter((roomId): roomId is string => Boolean(roomId)));
  const searchFronts = knowledge.discoveredRoomIds
    .map((roomId) => state.rooms[roomId])
    .filter((room): room is NonNullable<typeof room> => Boolean(room?.tags.includes("civilian") && !knownCivilianRooms.has(room.roomId)))
    .map((room) => {
      const discoveredZones = room.zoneIds
        .map((zoneId) => state.zones[zoneId])
        .filter((zone): zone is NonNullable<typeof zone> => Boolean(zone && knowledge.discoveredZoneIds.includes(zone.zoneId)));
      return discoveredZones.find((zone) => zone.tags.includes("civilian"))
        ?? discoveredZones.find((zone) => zone.tags.includes("console"))
        ?? discoveredZones[0]
        ?? null;
    })
    .filter((zone): zone is NonNullable<typeof zone> => Boolean(zone))
    .sort((left, right) => left.zoneId.localeCompare(right.zoneId));
  const unassignedOwners = ownerPriority.filter((owner) => !assignedActors.has(owner.actorId));
  for (const owner of unassignedOwners) {
    const targetZone = searchFronts.splice(0, 1)[0];
    if (!targetZone) break;
    assignedActors.add(owner.actorId);
    responsibilities.set(owner.actorId, {
      responsibilityId: `responsibility:p3:${planning.planningId}:${owner.actorId}:search:${targetZone.zoneId}`,
      kind: "search-civilian",
      objectiveId: "rescue-two-civilians",
      targetActorId: null,
      targetZoneId: targetZone.zoneId,
      blockerActorIds: [],
    });
  }

  const blockersFor = (actor: StationZeroActorState, targetZoneId: string): string[] => {
    const step = stationZeroMovementStepToward(state, actor.position.zoneId, targetZoneId, "rescue", actor.movementRange);
    const relevantZones = new Set([targetZoneId, ...(step ? [step] : [])]);
    return Object.values(knowledge.knownActors)
      .filter((known) => {
        const retained = state.actors[known.actorId];
        return retained?.factionId !== null && retained?.factionId !== "rescue" && known.observedLifeState === "active" && relevantZones.has(known.lastKnownZoneId);
      })
      .map((known) => known.actorId)
      .sort();
  };
  for (const [actorId, responsibility] of responsibilities) {
    const actor = state.actors[actorId]!;
    responsibility.blockerActorIds = blockersFor(actor, responsibility.targetZoneId);
  }

  const security = state.actors["security-chen"];
  if (security?.lifeState === "active" && security.factionId === "rescue" && !responsibilities.has(security.actorId)) {
    const supported = [...responsibilities.entries()]
      .filter(([actorId, responsibility]) => actorId !== security.actorId && responsibility.kind === "recover-civilian")
      .sort(([leftId], [rightId]) => (leftId === "engineer-imani" ? -1 : rightId === "engineer-imani" ? 1 : leftId.localeCompare(rightId)))[0]?.[1];
    if (supported) {
      responsibilities.set(security.actorId, {
        responsibilityId: `responsibility:p3:${planning.planningId}:${security.actorId}:support:${supported.targetActorId ?? supported.targetZoneId}`,
        kind: "support-civilian-recovery",
        objectiveId: "rescue-two-civilians",
        targetActorId: supported.targetActorId,
        targetZoneId: supported.targetZoneId,
        blockerActorIds: blockersFor(security, supported.targetZoneId),
      });
    }
  }
  return responsibilities;
}

function moveCandidates(
  state: StationZeroV3WorldState,
  planning: StationZeroV3PlanningHead,
  actor: StationZeroActorState,
): StationZeroV3AgentCandidate[] {
  if (!actor.factionId) return [];
  const known = new Set(knownZoneIds(state, actor.factionId));
  const frontier = new Set(frontierZoneIds(state, actor.factionId));
  const routeTargetIds = [
    "rescue-airlock",
    "med-ward",
    "life-console",
    "reactor-console",
    "maintenance-nest",
    "cargo-airlock",
  ].filter((zoneId) => known.has(zoneId));
  const routeSteps = new Map(routeTargetIds.map((zoneId) => [
    zoneId,
    stationZeroMovementStepToward(
      state,
      actor.position.zoneId,
      zoneId,
      actor.factionId,
      actor.movementRange,
    ),
  ]));
  const escortedCivilianIds = Object.values(state.actors)
    .filter((entry) =>
      entry.kind === "civilian" &&
      entry.lifeState === "active" &&
      entry.position.zoneId === actor.position.zoneId &&
      entry.statusIds.includes(`escorted-by:${actor.actorId}`))
    .map((entry) => entry.actorId)
    .sort();
  return Object.values(state.zones)
    .filter((zone) => zone.zoneId !== actor.position.zoneId)
    .map((zone) => ({
      zone,
      distance: stationZeroShortestDistance(state, actor.position.zoneId, zone.zoneId, actor.factionId),
    }))
    .filter(({ zone, distance }) => distance !== null && distance <= actor.movementRange && (known.has(zone.zoneId) || frontier.has(zone.zoneId)))
    .sort((left, right) => left.zone.zoneId.localeCompare(right.zone.zoneId))
    .map(({ zone }) => candidate({
      intentId: intentIdentity(planning.planningId, actor.actorId, `move:${zone.zoneId}`),
      actorId: actor.actorId,
      factionId: actor.factionId!,
      expectedWorldRevision: planning.worldRevision,
      expectedTurn: planning.turn,
      kind: "move",
      targetZoneId: zone.zoneId,
    }, `Move to ${known.has(zone.zoneId) ? zone.name : "an uncharted adjacent sector"}`, "Reposition within current movement range.", [
      "move",
      known.has(zone.zoneId) ? "known-zone" : "frontier",
      `zone:${zone.zoneId}`,
      `room:${zone.roomId}`,
      ...(zone.tags.map((tag) => `zone-tag:${tag}`)),
      ...[...routeSteps.entries()].filter(([, stepZoneId]) => stepZoneId === zone.zoneId).map(([targetZoneId]) => `route:${targetZoneId}`),
      ...(escortedCivilianIds.length > 0 ? ["escorting-civilian"] : []),
      ...escortedCivilianIds.map((actorId) => `escort:${actorId}`),
    ]));
}

function attackCandidates(
  state: StationZeroV3WorldState,
  planning: StationZeroV3PlanningHead,
  actor: StationZeroActorState,
): StationZeroV3AgentCandidate[] {
  if (!actor.factionId) return [];
  const abilities = abilityIds(actor)
    .map((abilityId) => STATION_ZERO_V3_ABILITIES.find((entry) => entry.abilityId === abilityId))
    .filter((entry): entry is NonNullable<typeof entry> => Boolean(entry && entry.targetKinds.includes("enemy") && entry.damage > 0))
    .filter((entry) => (actor.abilityCooldowns[entry.abilityId] ?? 0) === 0 && entry.actionPointCost <= actor.actionPoints)
    .sort((left, right) => right.damage - left.damage || left.abilityId.localeCompare(right.abilityId));
  if (abilities.length === 0) return [];
  const candidates: StationZeroV3AgentCandidate[] = [];
  for (const [targetActorId, known] of Object.entries(state.factionKnowledge[actor.factionId].knownActors).sort(([left], [right]) => left.localeCompare(right))) {
    const target = state.actors[targetActorId];
    if (!target || target.factionId === actor.factionId || target.lifeState !== "active") continue;
    if (actor.factionId === "rescue" && target.factionId === null) continue;
    if (known.confidence === "stale") continue;
    const distance = stationZeroShortestDistance(state, actor.position.zoneId, known.lastKnownZoneId, actor.factionId);
    const selected = abilities.find((entry) => distance !== null && distance <= entry.range);
    if (!selected) continue;
    candidates.push(candidate({
      intentId: intentIdentity(planning.planningId, actor.actorId, `attack:${selected.abilityId}:${targetActorId}`),
      actorId: actor.actorId,
      factionId: actor.factionId,
      expectedWorldRevision: planning.worldRevision,
      expectedTurn: planning.turn,
      kind: "attack",
      abilityId: selected.abilityId,
      targetActorId,
    }, `${selected.name} against ${target.name}`, "Engage a currently known hostile contact.", [
      "combat",
      `ability:${selected.abilityId}`,
      `target:${targetActorId}`,
      `target-role:${target.roleId}`,
      ...(target.kind === "civilian" ? ["target-civilian"] : []),
      ...(target.actorId === "hive-alpha" ? ["objective:eliminate-hive-alpha"] : []),
      ...(target.actorId === "engineer-imani" ? ["objective:capture-engineer"] : []),
    ]));
  }
  return candidates;
}

function localInteractionCandidates(
  state: StationZeroV3WorldState,
  planning: StationZeroV3PlanningHead,
  actor: StationZeroActorState,
): StationZeroV3AgentCandidate[] {
  if (!actor.factionId) return [];
  const candidates: StationZeroV3AgentCandidate[] = [];
  const factionId = actor.factionId;
  const localActors = Object.values(state.actors)
    .filter((target) => target.position.zoneId === actor.position.zoneId)
    .sort((left, right) => left.actorId.localeCompare(right.actorId));
  const localSystems = Object.values(state.systems)
    .filter((system) => system.zoneId === actor.position.zoneId && state.factionKnowledge[factionId].knownSystemIds.includes(system.systemId))
    .sort((left, right) => left.systemId.localeCompare(right.systemId));
  const localHazards = Object.values(state.hazards)
    .filter((hazard) => hazard.zoneId === actor.position.zoneId && state.factionKnowledge[factionId].knownHazardIds.includes(hazard.hazardId))
    .sort((left, right) => left.hazardId.localeCompare(right.hazardId));

  if (actor.capabilityIds.includes("repair") && actor.inventoryItemIds.includes("spare-parts")) {
    for (const system of localSystems.filter((entry) => entry.integrity < 1)) {
      candidates.push(candidate({
        intentId: intentIdentity(planning.planningId, actor.actorId, `repair:${system.systemId}`),
        actorId: actor.actorId,
        factionId,
        expectedWorldRevision: planning.worldRevision,
        expectedTurn: planning.turn,
        kind: "interact",
        operationId: "repair",
        targetId: system.systemId,
      }, `Repair ${system.name}`, "Spend one set of Spare Parts to restore a local system.", ["interaction", "repair", `system:${system.systemId}`, ...(system.tags.map((tag) => `system-tag:${tag}`))]));
    }
  }

  if (actor.capabilityIds.includes("stabilize")) {
    for (const target of localActors.filter((entry) =>
      entry.actorId !== actor.actorId && actorKnownToFaction(state, factionId, entry.actorId) &&
      (entry.factionId === factionId || entry.factionId === null) &&
      entry.lifeState !== "dead" && (entry.lifeState === "incapacitated" || entry.health < entry.maximumHealth))) {
      candidates.push(candidate({
        intentId: intentIdentity(planning.planningId, actor.actorId, `stabilize:${target.actorId}`),
        actorId: actor.actorId,
        factionId,
        expectedWorldRevision: planning.worldRevision,
        expectedTurn: planning.turn,
        kind: "interact",
        operationId: "stabilize",
        targetId: target.actorId,
      }, `Stabilize ${target.name}`, "Restore a wounded or incapacitated local contact.", ["interaction", "medical", `target:${target.actorId}`, ...(target.kind === "civilian" ? ["objective:rescue-two-civilians"] : [])]));
    }
  }

  if (factionId === "rescue") {
    for (const target of localActors.filter((entry) =>
      entry.kind === "civilian" && entry.lifeState === "active" && actorKnownToFaction(state, factionId, entry.actorId) &&
      !entry.statusIds.some((statusId) => statusId.startsWith("escorted-by:")))) {
      candidates.push(candidate({
        intentId: intentIdentity(planning.planningId, actor.actorId, `rescue:${target.actorId}`),
        actorId: actor.actorId,
        factionId,
        expectedWorldRevision: planning.worldRevision,
        expectedTurn: planning.turn,
        kind: "interact",
        operationId: "rescue",
        targetId: target.actorId,
      }, `Take custody of ${target.name}`, "Bind the civilian to this specialist for escorted movement and extraction.", ["interaction", "rescue", "objective:rescue-two-civilians", `target:${target.actorId}`]));
    }
  }

  if (factionId === "pirate" && actor.capabilityIds.includes("capture")) {
    for (const target of localActors.filter((entry) =>
      entry.factionId !== factionId && entry.lifeState === "incapacitated" && actorKnownToFaction(state, factionId, entry.actorId))) {
      candidates.push(candidate({
        intentId: intentIdentity(planning.planningId, actor.actorId, `capture:${target.actorId}`),
        actorId: actor.actorId,
        factionId,
        expectedWorldRevision: planning.worldRevision,
        expectedTurn: planning.turn,
        kind: "interact",
        operationId: "capture",
        targetId: target.actorId,
      }, `Capture ${target.name}`, "Secure an incapacitated local prize.", ["interaction", "capture", `target:${target.actorId}`, ...(target.actorId === "engineer-imani" ? ["objective:capture-engineer"] : [])]));
    }
  }

  if (factionId === "swarm" && actor.capabilityIds.includes("devour")) {
    for (const target of localActors.filter((entry) =>
      entry.factionId !== factionId && ["incapacitated", "dead"].includes(entry.lifeState) && actorKnownToFaction(state, factionId, entry.actorId))) {
      candidates.push(candidate({
        intentId: intentIdentity(planning.planningId, actor.actorId, `devour:${target.actorId}`),
        actorId: actor.actorId,
        factionId,
        expectedWorldRevision: planning.worldRevision,
        expectedTurn: planning.turn,
        kind: "interact",
        operationId: "devour",
        targetId: target.actorId,
      }, `Devour ${target.name}`, "Convert a local casualty into Biomass.", ["interaction", "devour", "objective:swarm-gain-biomass", `target:${target.actorId}`, ...(target.kind === "specialist" ? ["objective:devour-specialist"] : [])]));
    }
  }

  if (factionId === "swarm" && actor.capabilityIds.includes("infect")) {
    for (const system of localSystems.filter((entry) => !entry.tags.includes("infected:swarm"))) {
      candidates.push(candidate({
        intentId: intentIdentity(planning.planningId, actor.actorId, `infect:${system.systemId}`),
        actorId: actor.actorId,
        factionId,
        expectedWorldRevision: planning.worldRevision,
        expectedTurn: planning.turn,
        kind: "interact",
        operationId: "infect",
        targetId: system.systemId,
      }, `Infect ${system.name}`, "Embed Swarm growth into a local station system.", ["interaction", "infect", `system:${system.systemId}`, ...(system.systemId === "life-support" ? ["objective:infect-life-support"] : [])]));
    }
  }

  if (factionId === "pirate" && actor.capabilityIds.includes("hack")) {
    for (const system of localSystems) {
      candidates.push(candidate({
        intentId: intentIdentity(planning.planningId, actor.actorId, `hack:${system.systemId}`),
        actorId: actor.actorId,
        factionId,
        expectedWorldRevision: planning.worldRevision,
        expectedTurn: planning.turn,
        kind: "interact",
        operationId: "hack",
        targetId: system.systemId,
      }, `Hack ${system.name}`, "Toggle a local station system to support the boarding operation.", ["interaction", "hack", `system:${system.systemId}`]));
    }
  }

  const abilities = new Set(abilityIds(actor));
  if (abilities.has("field-repair") && (actor.abilityCooldowns["field-repair"] ?? 0) === 0) {
    for (const system of localSystems.filter((entry) => entry.integrity < 1)) {
      candidates.push(candidate({
        intentId: intentIdentity(planning.planningId, actor.actorId, `field-repair:${system.systemId}`),
        actorId: actor.actorId,
        factionId,
        expectedWorldRevision: planning.worldRevision,
        expectedTurn: planning.turn,
        kind: "use_ability",
        abilityId: "field-repair",
        targetActorId: null,
        targetZoneId: null,
        targetSystemId: system.systemId,
        targetHazardId: null,
      }, `Field-repair ${system.name}`, "Apply the Engineering Kit without consuming Spare Parts.", ["interaction", "repair", "ability:field-repair", `system:${system.systemId}`]));
    }
  }
  if (abilities.has("combat-stabilize") && (actor.abilityCooldowns["combat-stabilize"] ?? 0) === 0) {
    for (const target of localActors.filter((entry) =>
      entry.actorId !== actor.actorId && entry.factionId === factionId &&
      entry.lifeState !== "dead" && (entry.lifeState === "incapacitated" || entry.health < entry.maximumHealth))) {
      candidates.push(candidate({
        intentId: intentIdentity(planning.planningId, actor.actorId, `combat-stabilize:${target.actorId}`),
        actorId: actor.actorId,
        factionId,
        expectedWorldRevision: planning.worldRevision,
        expectedTurn: planning.turn,
        kind: "use_ability",
        abilityId: "combat-stabilize",
        targetActorId: target.actorId,
        targetZoneId: null,
        targetSystemId: null,
        targetHazardId: null,
      }, `Deploy Medical Drone to ${target.name}`, "Use the medical utility on a local ally.", ["interaction", "medical", "ability:combat-stabilize", `target:${target.actorId}`]));
    }
  }
  if (abilities.has("system-intrusion") && (actor.abilityCooldowns["system-intrusion"] ?? 0) === 0) {
    for (const system of localSystems) {
      candidates.push(candidate({
        intentId: intentIdentity(planning.planningId, actor.actorId, `intrusion:${system.systemId}`),
        actorId: actor.actorId,
        factionId,
        expectedWorldRevision: planning.worldRevision,
        expectedTurn: planning.turn,
        kind: "use_ability",
        abilityId: "system-intrusion",
        targetActorId: null,
        targetZoneId: null,
        targetSystemId: system.systemId,
        targetHazardId: null,
      }, `Intrude into ${system.name}`, "Use the intrusion rig against a local system.", ["interaction", "hack", "ability:system-intrusion", `system:${system.systemId}`]));
    }
    for (const hazard of localHazards) {
      candidates.push(candidate({
        intentId: intentIdentity(planning.planningId, actor.actorId, `intrusion-hazard:${hazard.hazardId}`),
        actorId: actor.actorId,
        factionId,
        expectedWorldRevision: planning.worldRevision,
        expectedTurn: planning.turn,
        kind: "use_ability",
        abilityId: "system-intrusion",
        targetActorId: null,
        targetZoneId: null,
        targetSystemId: null,
        targetHazardId: hazard.hazardId,
      }, `Contain ${hazard.name}`, "Use control access to reduce a local hazard.", ["interaction", "contain", "ability:system-intrusion", `hazard:${hazard.hazardId}`]));
    }
  }
  if (abilities.has("brood-call") && (actor.abilityCooldowns["brood-call"] ?? 0) === 0 && state.environment.biomass >= 3) {
    candidates.push(candidate({
      intentId: intentIdentity(planning.planningId, actor.actorId, `brood-call:${actor.position.zoneId}`),
      actorId: actor.actorId,
      factionId,
      expectedWorldRevision: planning.worldRevision,
      expectedTurn: planning.turn,
      kind: "use_ability",
      abilityId: "brood-call",
      targetActorId: null,
      targetZoneId: actor.position.zoneId,
      targetSystemId: null,
      targetHazardId: null,
    }, "Call a new Brood", "Consume Biomass to spawn a deterministic policy creature.", ["cleanup", "spawn", "ability:brood-call"]));
  }

  return candidates;
}

function pickupAndExtractionCandidates(
  state: StationZeroV3WorldState,
  planning: StationZeroV3PlanningHead,
  actor: StationZeroActorState,
): StationZeroV3AgentCandidate[] {
  if (!actor.factionId) return [];
  const candidates: StationZeroV3AgentCandidate[] = [];
  const factionId = actor.factionId;
  for (const groundItemId of [...state.factionKnowledge[factionId].knownGroundItemIds].sort()) {
    const item = state.groundItems[groundItemId];
    if (!item || item.zoneId !== actor.position.zoneId) continue;
    candidates.push(candidate({
      intentId: intentIdentity(planning.planningId, actor.actorId, `pickup:${groundItemId}`),
      actorId: actor.actorId,
      factionId,
      expectedWorldRevision: planning.worldRevision,
      expectedTurn: planning.turn,
      kind: "pickup",
      groundItemId,
      quantity: 1,
    }, `Pick up ${item.itemId}`, "Acquire a known local item before another faction claims it.", [
      "interaction",
      "pickup",
      `item:${item.itemId}`,
      ...(item.itemId === "research-core" ? ["objective:recover-research-core", "objective:pirate-steal-core"] : []),
    ]));
  }
  if (state.zones[actor.position.zoneId]?.tags.includes(`extraction:${factionId}`)) {
    const escortedCivilianIds = Object.values(state.actors)
      .filter((entry) =>
        entry.kind === "civilian" &&
        entry.lifeState === "active" &&
        entry.position.zoneId === actor.position.zoneId &&
        entry.statusIds.includes(`escorted-by:${actor.actorId}`))
      .map((entry) => entry.actorId)
      .sort();
    candidates.push(candidate({
      intentId: intentIdentity(planning.planningId, actor.actorId, "extract"),
      actorId: actor.actorId,
      factionId,
      expectedWorldRevision: planning.worldRevision,
      expectedTurn: planning.turn,
      kind: "extract",
      extractionId: `extraction:p3:${planning.planningId}:${actor.actorId}`,
    }, "Extract from Station Zero", "Leave the encounter with carried items and escorted civilians.", [
      "interaction",
      "extract",
      `faction:${factionId}`,
      ...(escortedCivilianIds.length > 0 ? ["escorting-civilian", "objective:rescue-two-civilians"] : []),
      ...escortedCivilianIds.map((actorId) => `escort:${actorId}`),
    ]));
  }
  return candidates;
}

function guardCandidates(
  state: StationZeroV3WorldState,
  planning: StationZeroV3PlanningHead,
  actor: StationZeroActorState,
): StationZeroV3AgentCandidate[] {
  if (!actor.factionId || !abilityIds(actor).includes("overwatch") || (actor.abilityCooldowns.overwatch ?? 0) > 0) return [];
  const zones = [actor.position.zoneId, ...stationZeroAdjacentZones(state, actor.position.zoneId, actor.factionId)];
  return [...new Set(zones)].sort().map((zoneId) => candidate({
    intentId: intentIdentity(planning.planningId, actor.actorId, `guard:${zoneId}`),
    actorId: actor.actorId,
    factionId: actor.factionId!,
    expectedWorldRevision: planning.worldRevision,
    expectedTurn: planning.turn,
    kind: "guard",
    protectedActorId: null,
    watchedZoneId: zoneId,
  }, `Overwatch ${state.zones[zoneId]?.name ?? zoneId}`, "Interrupt the first hostile movement into the watched Zone.", ["reaction", "guard", `zone:${zoneId}`]));
}

export function stationZeroV3AgentCandidates(
  state: StationZeroV3WorldState,
  planning: StationZeroV3PlanningHead,
  actorId: string,
): StationZeroV3AgentCandidate[] {
  const actor = state.actors[actorId];
  if (!actor || !actor.factionId || actor.lifeState !== "active") return [];
  const wait = candidate({
    intentId: intentIdentity(planning.planningId, actor.actorId, "wait"),
    actorId: actor.actorId,
    factionId: actor.factionId,
    expectedWorldRevision: planning.worldRevision,
    expectedTurn: planning.turn,
    kind: "wait",
  }, "Hold position", "Take no material action this Turn.", ["wait"]);
  const candidates = [
    ...localInteractionCandidates(state, planning, actor),
    ...pickupAndExtractionCandidates(state, planning, actor),
    ...attackCandidates(state, planning, actor),
    ...guardCandidates(state, planning, actor),
    ...moveCandidates(state, planning, actor),
    wait,
  ];
  return [...new Map(candidates.map((entry) => [entry.candidateId, entry])).values()]
    .sort((left, right) => left.candidateId.localeCompare(right.candidateId));
}

function allowedDirectiveIds(factionId: StationZeroFactionId): string[] {
  if (factionId === "pirate") return ["steal-core", "capture-prize", "extract-crew"];
  if (factionId === "swarm") return ["hunt-biomass", "infect-life-support", "preserve-hive"];
  return [];
}

export function compileStationZeroV3AgentContext(
  state: StationZeroV3WorldState,
  planning: StationZeroV3PlanningHead,
  actorId: string,
  playerOrder: StationZeroV3CommanderOrder | null,
): StationZeroV3AgentContext {
  const actor = state.actors[actorId];
  if (!actor || !actor.factionId || actor.lifeState !== "active") throw new TypeError(`Cannot compile Agent Context for inactive or unknown Actor ${actorId}`);
  const factionId = actor.factionId;
  const knowledge = state.factionKnowledge[factionId];
  const actors = Object.values(knowledge.knownActors).sort((left, right) => left.actorId.localeCompare(right.actorId)).map((known) => {
    const retained = state.actors[known.actorId]!;
    return {
      actorId: known.actorId,
      name: retained.factionId === factionId || known.confidence === "confirmed" ? retained.name : `Contact ${known.actorId}`,
      roleId: retained.factionId === factionId || known.confidence === "confirmed" ? retained.roleId : "unknown",
      factionId: retained.factionId,
      lastKnownZoneId: known.lastKnownZoneId,
      observedLifeState: known.observedLifeState,
      observedHealthBand: known.observedHealthBand,
      confidence: known.confidence,
      observedAtTurn: known.observedAtTurn,
    };
  });
  const contextBase = {
    schemaVersion: 1 as const,
    kind: "ordivon.game.station-zero-v3-agent-context" as const,
    contextId: `context:p3:${planning.planningId}:${actorId}`,
    planningId: planning.planningId,
    worldRevision: planning.worldRevision,
    worldDigest: planning.worldDigest,
    factionId,
    actor: {
      actorId: actor.actorId,
      name: actor.name,
      roleId: actor.roleId,
      zoneId: actor.position.zoneId,
      zoneName: state.zones[actor.position.zoneId]?.name ?? actor.position.zoneId,
      lifeState: actor.lifeState,
      health: actor.health,
      maximumHealth: actor.maximumHealth,
      actionPoints: actor.actionPoints,
      capabilityIds: [...actor.capabilityIds].sort(),
      traitIds: [...actor.traitIds].sort(),
      statusIds: [...actor.statusIds].sort(),
      inventoryItemIds: [...actor.inventoryItemIds].sort(),
    },
    environment: {
      batteryCharge: state.environment.batteryCharge,
      oxygen: state.environment.oxygen,
      reactorHeat: state.environment.reactorHeat,
      biomass: state.environment.biomass,
      alertLevel: state.environment.alertLevel,
    },
    known: {
      zoneIds: knownZoneIds(state, factionId),
      frontierZoneIds: frontierZoneIds(state, factionId),
      actors,
      systemIds: [...knowledge.knownSystemIds].sort(),
      hazardIds: [...knowledge.knownHazardIds].sort(),
      groundItemIds: [...knowledge.knownGroundItemIds].filter((groundItemId) => state.groundItems[groundItemId] !== undefined).sort(),
      reportIds: [...knowledge.reportIds].sort(),
    },
    objectiveIds: STATION_ZERO_V3_OBJECTIVES.filter((objective) => objective.factionId === factionId).map((objective) => objective.objectiveId),
    playerOrder: factionId === "rescue" ? playerOrder : null,
    responsibility: factionId === "rescue" ? rescueResponsibilities(state, planning, playerOrder).get(actor.actorId) ?? null : null,
    allowedDirectiveIds: allowedDirectiveIds(factionId),
    candidates: stationZeroV3AgentCandidates(state, planning, actorId),
  };
  return { ...contextBase, contextDigest: sha256(contextBase) };
}

export function assertStationZeroV3AgentDecision(
  context: StationZeroV3AgentContext,
  decision: StationZeroV3AgentDecision,
): void {
  if (decision.schemaVersion !== 1 || decision.kind !== "ordivon.game.station-zero-v3-agent-decision") {
    throw new TypeError("Agent Decision contract identity mismatch");
  }
  if (
    decision.contextId !== context.contextId || decision.contextDigest !== context.contextDigest ||
    decision.actorId !== context.actor.actorId || decision.factionId !== context.factionId
  ) throw new TypeError("Agent Decision targets another Context or Actor");
  if (!context.candidates.some((entry) => entry.candidateId === decision.candidateId)) {
    throw new TypeError("Agent Decision invented a Candidate identity");
  }
  if ((decision.directiveId === null) !== (context.allowedDirectiveIds.length === 0)) {
    throw new TypeError("Agent Decision directive does not match Context requirements");
  }
  if (decision.directiveId !== null && !context.allowedDirectiveIds.includes(decision.directiveId)) {
    throw new TypeError("Agent Decision invented a Directive identity");
  }
  if (!Number.isFinite(decision.confidence) || decision.confidence < 0 || decision.confidence > 1) {
    throw new TypeError("Agent Decision confidence must be between zero and one");
  }
  if (!decision.rationale.trim() || !decision.providerId.trim()) throw new TypeError("Agent Decision rationale and Provider identity are required");
}

function candidateTag(candidate: StationZeroV3AgentCandidate, tag: string): boolean {
  return candidate.tags.includes(tag);
}

function moveTarget(candidate: StationZeroV3AgentCandidate): string | null {
  return candidate.intent.kind === "move" ? candidate.intent.targetZoneId : null;
}

function scoreRescueCandidate(context: StationZeroV3AgentContext, candidate: StationZeroV3AgentCandidate): number {
  const order = context.playerOrder!;
  const actor = context.actor;
  let score = candidateTag(candidate, "wait") ? 0 : 10;
  const healthRatio = actor.maximumHealth === 0 ? 0 : actor.health / actor.maximumHealth;
  if (candidateTag(candidate, "extract") && healthRatio <= order.retreatHealthThreshold) score += 900;
  if (candidateTag(candidate, `objective:${order.primaryObjectiveId}`)) score += 300;
  if (candidateTag(candidate, "objective:rescue-two-civilians")) score += order.primaryObjectiveId === "rescue-two-civilians" ? 350 : 180;
  if (candidateTag(candidate, "medical")) score += actor.roleId === "medic" ? 260 : 40;
  if (candidateTag(candidate, "repair")) {
    score += actor.roleId === "engineer" ? 180 : 20;
    if (context.environment.reactorHeat >= 78 && candidateTag(candidate, "system:cooling")) score += 420;
    if (context.environment.oxygen <= 45 && candidateTag(candidate, "system:life-support")) score += 420;
  }
  if (candidateTag(candidate, "combat")) {
    score += actor.roleId === "security" ? 120 : 40;
    score += order.posture === "aggressive" ? 220 : order.posture === "balanced" ? 100 : 10;
    if (order.lethalForce === "forbidden") score -= 500;
    if (order.priorityTargetActorId && candidateTag(candidate, `target:${order.priorityTargetActorId}`)) score += 260;
  }
  if (candidateTag(candidate, "guard")) {
    score += actor.roleId === "security" ? 180 : 20;
    score += order.posture === "cautious" ? 150 : 40;
  }
  if (candidateTag(candidate, "pickup")) {
    score += order.lootPolicy === "opportunistic" ? 100 : order.lootPolicy === "mission-only" ? 40 : -200;
    if (candidateTag(candidate, "item:research-core")) score += order.primaryObjectiveId === "recover-research-core" ? 500 : 80;
  }
  const targetZoneId = moveTarget(candidate);
  if (targetZoneId) {
    if (candidateTag(candidate, "frontier")) score += 55;
    if (candidateTag(candidate, "escorting-civilian") && candidateTag(candidate, "route:rescue-airlock")) score += 1_200;
    if (actor.roleId === "medic" && order.primaryObjectiveId === "rescue-two-civilians") {
      if (candidateTag(candidate, "route:med-ward")) score += 420;
      if (candidateTag(candidate, "route:life-console")) score += 360;
    }
    if (actor.roleId === "engineer") {
      if (context.environment.reactorHeat >= 72 && context.known.systemIds.includes("cooling") && candidateTag(candidate, "route:reactor-console")) score += 800;
      if (context.environment.oxygen <= 55 && context.known.systemIds.includes("life-support") && candidateTag(candidate, "route:life-console")) score += 700;
      if (order.primaryObjectiveId === "recover-research-core" && candidateTag(candidate, "route:reactor-console")) score += 650;
      if (order.primaryObjectiveId === "rescue-two-civilians" && context.known.systemIds.includes("life-support") &&
          context.environment.reactorHeat < 88 && candidateTag(candidate, "route:life-console")) score += 620;
      if (order.primaryObjectiveId === "eliminate-hive-alpha" && candidateTag(candidate, "route:maintenance-nest")) score += 650;
    }
    if (actor.roleId === "security" && order.primaryObjectiveId === "eliminate-hive-alpha" && candidateTag(candidate, "route:maintenance-nest")) score += 650;
    const roleTargets: Record<string, string[]> = {
      medic: order.primaryObjectiveId === "rescue-two-civilians"
        ? ["med-ward", "med-console", "life-console", "life-entry", "junction-cover", "command-deck"]
        : ["med-ward", "med-console", "junction-cover", "command-deck"],
      engineer: order.primaryObjectiveId === "recover-research-core"
        ? ["reactor-console", "reactor-entry", "command-deck", "junction-console"]
        : order.primaryObjectiveId === "eliminate-hive-alpha"
          ? ["maintenance-nest", "maintenance-entry", "storage-floor", "junction-cover"]
          : ["life-console", "life-entry", "maintenance-console", "maintenance-entry", "storage-floor", "junction-cover", "junction-console", "command-deck"],
      security: order.primaryObjectiveId === "eliminate-hive-alpha"
        ? ["maintenance-nest", "maintenance-entry", "storage-floor", "junction-cover"]
        : order.formation === "cohesive"
          ? ["command-deck", "junction-cover", "med-console", "storage-floor"]
          : ["reactor-entry", "maintenance-entry", "storage-floor", "junction-cover"],
    };
    const index = roleTargets[actor.roleId]?.indexOf(targetZoneId) ?? -1;
    if (index >= 0) score += 220 - index * 18;
    if (order.formation === "cohesive") {
      const nearbyOwn = context.known.actors.filter((known) => known.factionId === "rescue" && known.actorId !== actor.actorId)
        .some((known) => known.lastKnownZoneId === targetZoneId);
      if (nearbyOwn) score += 80;
    }
  }
  if (candidateTag(candidate, "extract") && actor.inventoryItemIds.includes("research-core")) score += 700;
  if (candidateTag(candidate, "extract") && candidateTag(candidate, "escorting-civilian")) score += 2_000;
  if (candidateTag(candidate, "escorting-civilian")) score += 1_000;
  return score;
}

function choosePirateDirective(context: StationZeroV3AgentContext): StationZeroV3PirateDirective {
  if (context.actor.inventoryItemIds.includes("research-core")) return "extract-crew";
  if (context.known.groundItemIds.includes("ground:research-core")) return "steal-core";
  if (context.known.actors.some((actor) => actor.actorId === "engineer-imani" && actor.observedLifeState === "incapacitated")) return "capture-prize";
  return "steal-core";
}

function scorePirateCandidate(context: StationZeroV3AgentContext, candidate: StationZeroV3AgentCandidate, directive: StationZeroV3PirateDirective): number {
  let score = candidateTag(candidate, "wait") ? 0 : 10;
  if (directive === "steal-core") {
    if (candidateTag(candidate, "item:research-core")) score += 600;
    if (moveTarget(candidate)) {
      const targets = ["reactor-console", "reactor-entry", "command-deck", "junction-cover", "storage-floor"];
      const index = targets.indexOf(moveTarget(candidate)!);
      if (index >= 0) score += 260 - index * 20;
    }
  }
  if (directive === "capture-prize" && candidateTag(candidate, "objective:capture-engineer")) score += 700;
  if (directive === "extract-crew" && candidateTag(candidate, "extract")) score += 800;
  if (candidateTag(candidate, "combat")) score += 120;
  if (candidateTag(candidate, "guard")) score += 100;
  if (candidateTag(candidate, "hack")) score += context.actor.roleId === "hacker" ? 180 : 30;
  return score;
}

function chooseSwarmDirective(context: StationZeroV3AgentContext): StationZeroV3SwarmDirective {
  if (context.actor.health / context.actor.maximumHealth < 0.4) return "preserve-hive";
  if (context.known.systemIds.includes("life-support")) return "infect-life-support";
  return "hunt-biomass";
}

function scoreSwarmCandidate(context: StationZeroV3AgentContext, candidate: StationZeroV3AgentCandidate, directive: StationZeroV3SwarmDirective): number {
  let score = candidateTag(candidate, "wait") ? 0 : 10;
  if (directive === "hunt-biomass") {
    if (candidateTag(candidate, "devour")) score += 700;
    if (candidateTag(candidate, "target-civilian")) score += 220;
    if (candidateTag(candidate, "combat")) score += 180;
  }
  if (directive === "infect-life-support" && candidateTag(candidate, "objective:infect-life-support")) score += 800;
  if (directive === "preserve-hive") {
    if (candidateTag(candidate, "guard")) score += 500;
    if (candidateTag(candidate, "combat")) score += 100;
  }
  const targetZoneId = moveTarget(candidate);
  if (targetZoneId) {
    const targets = directive === "infect-life-support"
      ? ["life-console", "life-entry", "life-duct", "maintenance-console"]
      : directive === "hunt-biomass"
        ? ["life-console", "med-ward", "life-entry", "maintenance-entry"]
        : ["maintenance-nest", "maintenance-entry", "life-duct"];
    const index = targets.indexOf(targetZoneId);
    if (index >= 0) score += 280 - index * 30;
  }
  if (candidateTag(candidate, "spawn")) score += context.environment.biomass >= 9 ? 180 : -120;
  return score;
}

export class FixtureStationZeroV3AgentProvider implements StationZeroV3AgentProvider {
  readonly providerId = "fixture-station-zero-v3-agent-v1";

  async decide(context: StationZeroV3AgentContext): Promise<StationZeroV3AgentDecision> {
    if (context.candidates.length === 0) throw new TypeError(`Agent Context has no Candidate: ${context.contextId}`);
    let directiveId: string | null = null;
    if (context.factionId === "pirate") directiveId = choosePirateDirective(context);
    if (context.factionId === "swarm") directiveId = chooseSwarmDirective(context);
    const scored = context.candidates.map((candidate) => ({
      candidate,
      score: context.factionId === "rescue"
        ? scoreRescueCandidate(context, candidate)
        : context.factionId === "pirate"
          ? scorePirateCandidate(context, candidate, directiveId as StationZeroV3PirateDirective)
          : scoreSwarmCandidate(context, candidate, directiveId as StationZeroV3SwarmDirective),
    })).sort((left, right) => right.score - left.score || left.candidate.candidateId.localeCompare(right.candidate.candidateId));
    const selected = scored[0]!;
    const decision: StationZeroV3AgentDecision = {
      schemaVersion: 1,
      kind: "ordivon.game.station-zero-v3-agent-decision",
      contextId: context.contextId,
      contextDigest: context.contextDigest,
      actorId: context.actor.actorId,
      factionId: context.factionId,
      candidateId: selected.candidate.candidateId,
      directiveId,
      rationale: `${selected.candidate.rationaleHint} Selected from ${context.candidates.length} admitted candidates under ${directiveId ?? context.playerOrder?.primaryObjectiveId ?? "specialist standing orders"}.`,
      confidence: Math.max(0.35, Math.min(0.95, 0.55 + Math.max(0, selected.score) / 2_000)),
      providerId: this.providerId,
    };
    assertStationZeroV3AgentDecision(context, decision);
    return decision;
  }
}

export const fixtureStationZeroV3AgentProviderFactory: StationZeroV3AgentProviderFactory = () =>
  new FixtureStationZeroV3AgentProvider();

function policyScore(
  context: StationZeroV3AgentContext,
  candidate: StationZeroV3AgentCandidate,
  directiveId: string,
): number {
  if (context.factionId === "pirate") return scorePirateCandidate(context, candidate, directiveId as StationZeroV3PirateDirective) +
    (context.actor.roleId === "hacker" && candidateTag(candidate, "hack") ? 220 : 0) +
    (context.actor.roleId === "raider" && candidateTag(candidate, "combat") ? 150 : 0);
  return scoreSwarmCandidate(context, candidate, directiveId as StationZeroV3SwarmDirective) +
    (context.actor.roleId === "stalker" && candidateTag(candidate, "combat") ? 180 : 0) +
    (context.actor.roleId === "drone" && candidateTag(candidate, "guard") ? 80 : 0);
}

function policyDecision(
  context: StationZeroV3AgentContext,
  leaderActorId: string,
  directiveId: string,
): StationZeroV3PolicyDecision {
  const selected = context.candidates.map((candidate) => ({ candidate, score: policyScore(context, candidate, directiveId) }))
    .sort((left, right) => right.score - left.score || left.candidate.candidateId.localeCompare(right.candidate.candidateId))[0];
  if (!selected) throw new TypeError(`Policy Actor ${context.actor.actorId} has no admitted Candidate`);
  return {
    policyDecisionId: `policy-decision:p3:${context.planningId}:${context.actor.actorId}`,
    actorId: context.actor.actorId,
    factionId: context.factionId,
    leaderActorId,
    directiveId,
    candidateId: selected.candidate.candidateId,
    intent: selected.candidate.intent,
    rationale: `${context.actor.roleId} policy expands leader directive ${directiveId} through the highest-ranked admitted local action.`,
  };
}

export function defaultStationZeroV3CommanderOrder(
  runId: string,
  planning: StationZeroV3PlanningHead,
  state: StationZeroV3WorldState,
): StationZeroV3CommanderOrder {
  const knowledge = state.factionKnowledge.rescue;
  let commanderDirectiveId: StationZeroV3CommanderDirectiveId = "hold-command";
  if (!knowledge.knownSystemIds.includes("cooling")) {
    commanderDirectiveId = "scan-reactor";
  } else if (!state.systems.cooling?.powered && (state.factions.rescue.commanderAbilityCooldowns["power-reroute"] ?? 0) === 0) {
    commanderDirectiveId = "reroute-cooling";
  } else if (!knowledge.discoveredZoneIds.includes("maintenance-entry")) {
    commanderDirectiveId = "scan-maintenance";
  } else if (!knowledge.knownSystemIds.includes("life-support")) {
    commanderDirectiveId = "scan-life-support";
  }
  return {
    schemaVersion: 1,
    kind: "ordivon.game.station-zero-v3-commander-order",
    runId,
    planningId: planning.planningId,
    expectedWorldRevision: planning.worldRevision,
    expectedTurn: planning.turn,
    primaryObjectiveId: "rescue-two-civilians",
    posture: "balanced",
    formation: "split",
    retreatHealthThreshold: 0.3,
    lethalForce: "permitted",
    collateralPolicy: "forbidden",
    lootPolicy: "mission-only",
    protectedActorId: "medic-reyes",
    priorityTargetActorId: null,
    commanderDirectiveId,
    issuedBy: "player:mission-control",
  };
}

export function assertStationZeroV3CommanderOrder(
  state: StationZeroV3WorldState,
  planning: StationZeroV3PlanningHead,
  order: StationZeroV3CommanderOrder,
): void {
  if (order.schemaVersion !== 1 || order.kind !== "ordivon.game.station-zero-v3-commander-order") {
    throw new TypeError("Commander Order contract identity mismatch");
  }
  if (
    order.runId !== planning.runId || order.planningId !== planning.planningId ||
    order.expectedWorldRevision !== planning.worldRevision || order.expectedTurn !== planning.turn
  ) throw new TypeError("Commander Order targets another Planning Head");
  if (!RESCUE_OBJECTIVE_IDS.includes(order.primaryObjectiveId)) throw new TypeError("Commander Order has unsupported primary Objective");
  if (!STATION_ZERO_V3_COMMAND_POSTURES.includes(order.posture)) throw new TypeError("Commander Order has unsupported posture");
  if (!STATION_ZERO_V3_FORMATIONS.includes(order.formation)) throw new TypeError("Commander Order has unsupported formation");
  if (!STATION_ZERO_V3_COMMANDER_DIRECTIVE_IDS.includes(order.commanderDirectiveId)) throw new TypeError("Commander Order has unsupported Commander directive");
  if (!Number.isFinite(order.retreatHealthThreshold) || order.retreatHealthThreshold < 0 || order.retreatHealthThreshold > 1) {
    throw new TypeError("Commander Order retreat threshold must be between zero and one");
  }
  if (order.protectedActorId !== null && state.actors[order.protectedActorId]?.factionId !== "rescue") {
    throw new TypeError("Commander Order protected Actor must belong to Rescue");
  }
  if (order.priorityTargetActorId !== null && !state.factionKnowledge.rescue.knownActors[order.priorityTargetActorId]) {
    throw new TypeError("Commander Order priority target is outside Rescue knowledge");
  }
  if (!order.issuedBy.trim()) throw new TypeError("Commander Order issuer is required");
}

export function createStationZeroV3PlayCatalog(): StationZeroV3PlayCatalog {
  return {
    schemaVersion: 1,
    kind: "ordivon.game.station-zero-v3-play-catalog",
    objectives: [
      { objectiveId: "rescue-two-civilians", label: "Rescue the crew", description: "Prioritize locating, escorting, and extracting both civilians." },
      { objectiveId: "recover-research-core", label: "Recover the Research Core", description: "Divert specialists toward the Reactor and extract the objective cargo." },
      { objectiveId: "eliminate-hive-alpha", label: "Hunt the Hive Alpha", description: "Accept higher combat exposure to break the Swarm leadership." },
    ],
    postures: [
      { posture: "cautious", label: "Cautious", description: "Prefer guard, stabilization, and survival over opportunistic combat." },
      { posture: "balanced", label: "Balanced", description: "Trade protection and tempo according to local evidence." },
      { posture: "aggressive", label: "Aggressive", description: "Prefer attacks and rapid objective pressure when legal." },
    ],
    formations: [
      { formation: "cohesive", label: "Cohesive team", description: "Prefer mutual support and shared Zones." },
      { formation: "split", label: "Split fronts", description: "Allow specialists to pursue different objectives concurrently." },
    ],
    commanderDirectives: [
      { directiveId: "hold-command", label: "Hold remote capability", description: "Spend no Commander Ability this Turn." },
      { directiveId: "scan-reactor", label: "Scan Reactor", description: "Reveal the Reactor Console sector." },
      { directiveId: "scan-maintenance", label: "Scan Maintenance", description: "Reveal the Maintenance Entry sector." },
      { directiveId: "scan-life-support", label: "Scan Life Support", description: "Reveal the Life Support Console sector." },
      { directiveId: "reroute-cooling", label: "Power Cooling", description: "Remotely power the Cooling system if available." },
      { directiveId: "lock-maintenance", label: "Lock Maintenance route", description: "Close the Storage–Maintenance bulkhead." },
      { directiveId: "emergency-uplink", label: "Emergency Uplink", description: "Share the current local visibility envelope across Rescue." },
      { directiveId: "call-extraction", label: "Call extraction", description: "Mark the Rescue Airlock as an extraction Zone." },
    ],
    lethalForce: [
      { value: "forbidden", label: "Avoid lethal force" },
      { value: "permitted", label: "Lethal force permitted" },
      { value: "preferred", label: "Lethal force preferred" },
    ],
    lootPolicies: [
      { value: "ignore", label: "Ignore loot" },
      { value: "mission-only", label: "Mission items only" },
      { value: "opportunistic", label: "Opportunistic recovery" },
    ],
  };
}

function commanderActionFromDirective(
  state: StationZeroV3WorldState,
  planning: StationZeroV3PlanningHead,
  order: StationZeroV3CommanderOrder,
): { action: StationZeroCommanderAction | null; warning: string | null } {
  const map: Record<Exclude<StationZeroV3CommanderDirectiveId, "hold-command">, {
    abilityId: string;
    targetActorId?: string;
    targetZoneId?: string;
    targetPassageId?: string;
    targetSystemId?: string;
    targetFactionId?: StationZeroFactionId;
  }> = {
    "scan-reactor": { abilityId: "orbital-scan", targetZoneId: "reactor-console" },
    "scan-maintenance": { abilityId: "orbital-scan", targetZoneId: "maintenance-entry" },
    "scan-life-support": { abilityId: "orbital-scan", targetZoneId: "life-console" },
    "reroute-cooling": { abilityId: "power-reroute", targetSystemId: "cooling" },
    "lock-maintenance": { abilityId: "bulkhead-lockdown", targetPassageId: "passage:storage-maintenance" },
    "emergency-uplink": { abilityId: "emergency-uplink", targetFactionId: "rescue" },
    "call-extraction": { abilityId: "rescue-extraction", targetZoneId: "rescue-airlock" },
  };
  if (order.commanderDirectiveId === "hold-command") return { action: null, warning: null };
  const selected = map[order.commanderDirectiveId];
  const definition = STATION_ZERO_V3_COMMANDER_ABILITIES.find((entry) => entry.commanderAbilityId === selected.abilityId)!;
  const faction = state.factions.rescue;
  const charges = faction.commanderAbilityCharges[selected.abilityId];
  if ((charges !== null && (charges === undefined || charges < 1)) || (faction.commanderAbilityCooldowns[selected.abilityId] ?? 0) > 0 || definition.commandPointCost > faction.commandPoints) {
    return { action: null, warning: `${definition.name} is unavailable; the Turn will retain Commander capacity.` };
  }
  return {
    action: {
      commanderActionId: `commander:p3:${planning.planningId}:rescue:${selected.abilityId}`,
      factionId: "rescue",
      commanderAbilityId: selected.abilityId,
      expectedWorldRevision: planning.worldRevision,
      expectedTurn: planning.turn,
      targetActorId: selected.targetActorId ?? null,
      targetZoneId: selected.targetZoneId ?? null,
      targetPassageId: selected.targetPassageId ?? null,
      targetSystemId: selected.targetSystemId ?? null,
      targetFactionId: selected.targetFactionId ?? null,
    },
    warning: null,
  };
}

function enemyCommanderActions(
  state: StationZeroV3WorldState,
  planning: StationZeroV3PlanningHead,
  factionId: "pirate" | "swarm",
  directiveId: string,
): StationZeroCommanderAction[] {
  if (factionId === "pirate") {
    const faction = state.factions.pirate;
    if (directiveId === "capture-prize" && confirmedCurrentContact(state, "pirate", "engineer-imani")) {
      return [{
        commanderActionId: `commander:p3:${planning.planningId}:pirate:mark-prize`,
        factionId: "pirate",
        commanderAbilityId: "mark-prize",
        expectedWorldRevision: planning.worldRevision,
        expectedTurn: planning.turn,
        targetActorId: "engineer-imani",
        targetZoneId: null,
        targetPassageId: null,
        targetSystemId: null,
        targetFactionId: null,
      }];
    }
    const charges = faction.commanderAbilityCharges["signal-jam"];
    if ((charges === null || (charges ?? 0) > 0) && (faction.commanderAbilityCooldowns["signal-jam"] ?? 0) === 0) {
      return [{
        commanderActionId: `commander:p3:${planning.planningId}:pirate:signal-jam`,
        factionId: "pirate",
        commanderAbilityId: "signal-jam",
        expectedWorldRevision: planning.worldRevision,
        expectedTurn: planning.turn,
        targetActorId: null,
        targetZoneId: null,
        targetPassageId: null,
        targetSystemId: null,
        targetFactionId: "rescue",
      }];
    }
    return [];
  }
  const faction = state.factions.swarm;
  const charges = faction.commanderAbilityCharges["pheromone-surge"];
  if ((charges === null || (charges ?? 0) > 0) && (faction.commanderAbilityCooldowns["pheromone-surge"] ?? 0) === 0) {
    const zoneId = directiveId === "infect-life-support" ? "life-entry" : "maintenance-entry";
    return [{
      commanderActionId: `commander:p3:${planning.planningId}:swarm:pheromone-surge`,
      factionId: "swarm",
      commanderAbilityId: "pheromone-surge",
      expectedWorldRevision: planning.worldRevision,
      expectedTurn: planning.turn,
      targetActorId: null,
      targetZoneId: zoneId,
      targetPassageId: null,
      targetSystemId: null,
      targetFactionId: null,
    }];
  }
  return [];
}

function standingOrders(
  state: StationZeroV3WorldState,
  planning: StationZeroV3PlanningHead,
  order: StationZeroV3CommanderOrder,
): StationZeroStandingOrder[] {
  return ["engineer-imani", "medic-reyes", "security-chen"].map((actorId) => {
    const standing: StationZeroStandingOrder = {
      orderId: `standing-order:p3:${planning.planningId}:${actorId}`,
      factionId: "rescue",
      actorId,
      objectiveId: order.primaryObjectiveId,
      priorityTargetActorId: order.priorityTargetActorId,
      protectedActorId: order.protectedActorId === actorId ? null : order.protectedActorId,
      retreatHealthThreshold: order.retreatHealthThreshold,
      lethalForce: order.lethalForce,
      collateralPolicy: order.collateralPolicy,
      lootPolicy: order.lootPolicy,
      revision: planning.standingOrderRevision + 1,
    };
    const validationState = structuredClone(state);
    validationState.encounter.activePlanRevision = standing.revision;
    assertStationZeroStandingOrder(validationState, standing);
    return standing;
  });
}

function explanation(
  state: StationZeroV3WorldState,
  factionId: StationZeroFactionId,
  directiveId: string,
  plan: StationZeroFactionTurnPlan,
  contexts: StationZeroV3AgentContext[],
  agentDecisions: StationZeroV3AgentDecision[],
  policyDecisions: StationZeroV3PolicyDecision[],
): StationZeroV3FactionPlanExplanation {
  const actorIntents = plan.actorIntents.map((intent) => {
    const context = contexts.find((entry) => entry.actor.actorId === intent.actorId);
    const agent = agentDecisions.find((entry) => entry.actorId === intent.actorId);
    const policy = policyDecisions.find((entry) => entry.actorId === intent.actorId);
    const candidate = context?.candidates.find((entry) => entry.candidateId === (agent?.candidateId ?? policy?.candidateId));
    const actor = state.actors[intent.actorId]!;
    return {
      actorId: actor.actorId,
      actorName: actor.name,
      roleId: actor.roleId,
      controllerKind: actor.controllerKind === "agent" ? "agent" as const : "policy" as const,
      intent,
      label: candidate?.label ?? intent.kind,
      rationale: agent?.rationale ?? policy?.rationale ?? "Deterministic faction policy selected this admitted action.",
      confidence: agent?.confidence ?? null,
      responsibility: context?.responsibility ? structuredClone(context.responsibility) : null,
    };
  });
  const risks: string[] = [];
  if (plan.actorIntents.filter((intent) => intent.kind === "move").length >= 2) risks.push("Several Actors are moving simultaneously; Zone capacity and reactions may interrupt the route.");
  if (plan.actorIntents.some((intent) => intent.kind === "attack")) risks.push("Combat can invalidate later actions if targets move, fall, or are captured first.");
  if (plan.commanderActions.length === 0) risks.push("No Commander Ability changes the World before movement.");
  return {
    factionId,
    directiveId,
    summary: `${state.factions[factionId].name} will pursue ${directiveId} through ${plan.actorIntents.length} Actor intents${plan.commanderActions.length ? " and one Commander action" : ""}.`,
    risks,
    actorIntents,
  };
}

export async function buildStationZeroV3PlanPreview(input: {
  state: StationZeroV3WorldState;
  planning: StationZeroV3PlanningHead;
  orderRevision: number;
  order: StationZeroV3CommanderOrder;
  orderDigest: string;
  providerFactory?: StationZeroV3AgentProviderFactory;
}): Promise<StationZeroV3PlanPreview> {
  const { state, planning, orderRevision, order, orderDigest } = input;
  assertStationZeroV3CommanderOrder(state, planning, order);
  const providerFactory = input.providerFactory ?? fixtureStationZeroV3AgentProviderFactory;
  const contexts: StationZeroV3AgentContext[] = [];
  const agentDecisions: StationZeroV3AgentDecision[] = [];
  const policyDecisions: StationZeroV3PolicyDecision[] = [];

  const highFidelityActors = [...AGENT_ACTOR_IDS].sort()
    .map((actorId) => state.actors[actorId])
    .filter((actor): actor is StationZeroActorState => Boolean(actor && actor.lifeState === "active"));
  const highFidelitySettled = await Promise.allSettled(highFidelityActors.map(async (actor) => {
    const context = compileStationZeroV3AgentContext(state, planning, actor.actorId, order);
    const provider = providerFactory(actor.factionId!, actor.actorId);
    const decision = await provider.decide(context);
    assertStationZeroV3AgentDecision(context, decision);
    return { context, decision };
  }));
  const rejected = highFidelitySettled.find((result) => result.status === "rejected");
  if (rejected?.status === "rejected") throw rejected.reason;
  for (const result of highFidelitySettled) {
    if (result.status !== "fulfilled") continue;
    contexts.push(result.value.context);
    agentDecisions.push(result.value.decision);
  }

  const pirateDirective = (agentDecisions.find((decision) => decision.actorId === "pirate-captain-veyra")?.directiveId ?? "steal-core") as StationZeroV3PirateDirective;
  const swarmDirective = (agentDecisions.find((decision) => decision.actorId === "hive-alpha")?.directiveId ?? "hunt-biomass") as StationZeroV3SwarmDirective;
  for (const actor of Object.values(state.actors).filter((entry) => entry.controllerKind === "policy" && entry.factionId !== null && entry.lifeState === "active")
    .sort((left, right) => left.actorId.localeCompare(right.actorId))) {
    const context = compileStationZeroV3AgentContext(state, planning, actor.actorId, order);
    contexts.push(context);
    policyDecisions.push(policyDecision(context, actor.leaderActorId!, actor.factionId === "pirate" ? pirateDirective : swarmDirective));
  }

  const intentForActor = (actorId: string): StationZeroActorIntent => {
    const agent = agentDecisions.find((decision) => decision.actorId === actorId);
    if (agent) {
      const context = contexts.find((entry) => entry.contextId === agent.contextId)!;
      return structuredClone(context.candidates.find((entry) => entry.candidateId === agent.candidateId)!.intent);
    }
    const policy = policyDecisions.find((decision) => decision.actorId === actorId);
    if (policy) return structuredClone(policy.intent);
    throw new Error(`No P3 planning decision exists for active Actor ${actorId}`);
  };

  const command = commanderActionFromDirective(state, planning, order);
  const rescuePlan: StationZeroFactionTurnPlan = {
    planId: `plan:p3:${planning.planningId}:rescue`,
    factionId: "rescue",
    expectedWorldRevision: planning.worldRevision,
    expectedTurn: planning.turn,
    standingOrderRevision: planning.standingOrderRevision,
    commanderActions: command.action ? [command.action] : [],
    actorIntents: Object.values(state.actors).filter((actor) => actor.factionId === "rescue" && actor.lifeState === "active")
      .sort((left, right) => left.actorId.localeCompare(right.actorId)).map((actor) => intentForActor(actor.actorId)),
    committedBy: `player:mission-control:${orderDigest}`,
  };
  const piratePlan: StationZeroFactionTurnPlan = {
    planId: `plan:p3:${planning.planningId}:pirate`,
    factionId: "pirate",
    expectedWorldRevision: planning.worldRevision,
    expectedTurn: planning.turn,
    standingOrderRevision: planning.standingOrderRevision,
    commanderActions: enemyCommanderActions(state, planning, "pirate", pirateDirective),
    actorIntents: Object.values(state.actors).filter((actor) => actor.factionId === "pirate" && actor.lifeState === "active")
      .sort((left, right) => left.actorId.localeCompare(right.actorId)).map((actor) => intentForActor(actor.actorId)),
    committedBy: `agent:pirate-captain-veyra:${agentDecisions.find((entry) => entry.actorId === "pirate-captain-veyra")?.providerId ?? "policy"}`,
  };
  const swarmPlan: StationZeroFactionTurnPlan = {
    planId: `plan:p3:${planning.planningId}:swarm`,
    factionId: "swarm",
    expectedWorldRevision: planning.worldRevision,
    expectedTurn: planning.turn,
    standingOrderRevision: planning.standingOrderRevision,
    commanderActions: enemyCommanderActions(state, planning, "swarm", swarmDirective),
    actorIntents: Object.values(state.actors).filter((actor) => actor.factionId === "swarm" && actor.lifeState === "active")
      .sort((left, right) => left.actorId.localeCompare(right.actorId)).map((actor) => intentForActor(actor.actorId)),
    committedBy: `agent:hive-alpha:${agentDecisions.find((entry) => entry.actorId === "hive-alpha")?.providerId ?? "policy"}`,
  };
  for (const plan of [rescuePlan, piratePlan, swarmPlan]) assertStationZeroFactionTurnPlan(state, plan);

  const retainedStandingOrders = standingOrders(state, planning, order);
  const warnings = [command.warning].filter((entry): entry is string => entry !== null);
  const providerIds = [...new Set(agentDecisions.map((entry) => entry.providerId))].sort();
  const factionPlans = { rescue: rescuePlan, pirate: piratePlan, swarm: swarmPlan };
  const explanations = {
    rescue: explanation(state, "rescue", order.primaryObjectiveId, rescuePlan, contexts, agentDecisions, policyDecisions),
    pirate: explanation(state, "pirate", pirateDirective, piratePlan, contexts, agentDecisions, policyDecisions),
    swarm: explanation(state, "swarm", swarmDirective, swarmPlan, contexts, agentDecisions, policyDecisions),
  };
  const base = {
    schemaVersion: 1 as const,
    kind: "ordivon.game.station-zero-v3-plan-preview" as const,
    runId: planning.runId,
    planningId: planning.planningId,
    worldRevision: planning.worldRevision,
    worldDigest: planning.worldDigest,
    orderRevision,
    orderDigest,
    providerId: providerIds.join("+") || "none",
    generatedAt: new Date().toISOString(),
    playerOrder: structuredClone(order),
    standingOrders: retainedStandingOrders,
    commanderAction: command.action,
    contexts,
    agentDecisions,
    policyDecisions,
    factionPlans,
    explanations,
    warnings,
  };
  const identityDigest = sha256({ ...base, generatedAt: "" });
  const previewId = `preview:p3:${planning.planningId}:${identityDigest}`;
  const previewDigest = sha256({ ...base, previewId });
  return { ...base, previewId, previewDigest };
}
