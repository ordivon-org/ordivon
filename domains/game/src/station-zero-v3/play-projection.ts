import { sha256 } from "../digest.ts";
import { STATION_ZERO_V3_COMMANDER_ABILITIES } from "./content.ts";
import { createStationZeroV3MissionControlView } from "./mission-control.ts";
import type { StationZeroFact, StationZeroFactionId, StationZeroV3WorldState } from "./model.ts";
import type {
  StationZeroV3AftermathView,
  StationZeroV3PlanPreview,
  StationZeroV3PlayView,
  StationZeroV3PlayerPlanView,
} from "./p3-model.ts";
import type { StationZeroV3PlanningStore } from "./planning-store.ts";
import type { StationZeroV3Store } from "./persistence.ts";
import type { StationZeroV3TurnService } from "./turn-service.ts";

function targetLabel(state: StationZeroV3WorldState, preview: StationZeroV3PlanPreview): string {
  const action = preview.commanderAction;
  if (!action) return "No target";
  if (action.targetActorId) return state.actors[action.targetActorId]?.name ?? action.targetActorId;
  if (action.targetZoneId) return state.zones[action.targetZoneId]?.name ?? action.targetZoneId;
  if (action.targetPassageId) return action.targetPassageId;
  if (action.targetSystemId) return state.systems[action.targetSystemId]?.name ?? action.targetSystemId;
  if (action.targetFactionId) return state.factions[action.targetFactionId]?.name ?? action.targetFactionId;
  return "No target";
}

function playerPreview(state: StationZeroV3WorldState, preview: StationZeroV3PlanPreview): StationZeroV3PlayerPlanView {
  const rescue = preview.explanations.rescue;
  const commanderDefinition = preview.commanderAction
    ? STATION_ZERO_V3_COMMANDER_ABILITIES.find((entry) => entry.commanderAbilityId === preview.commanderAction!.commanderAbilityId)
    : null;
  return {
    previewId: preview.previewId,
    previewDigest: preview.previewDigest,
    generatedAt: preview.generatedAt,
    orderRevision: preview.orderRevision,
    providerId: preview.providerId,
    summary: rescue.summary,
    risks: [...rescue.risks],
    commanderAction: preview.commanderAction ? {
      commanderAbilityId: preview.commanderAction.commanderAbilityId,
      label: commanderDefinition?.name ?? preview.commanderAction.commanderAbilityId,
      targetLabel: targetLabel(state, preview),
    } : null,
    actorIntents: rescue.actorIntents.map((entry) => ({
      actorId: entry.actorId,
      actorName: entry.actorName,
      roleId: entry.roleId,
      action: entry.label,
      rationale: entry.rationale,
      confidence: entry.confidence,
    })),
    enemyPlansSealed: (["pirate", "swarm"] as const).map((factionId) => ({
      factionId,
      status: "sealed",
      planDigest: sha256(preview.factionPlans[factionId]),
    })),
    warnings: [...preview.warnings],
  };
}

function factSummary(state: StationZeroV3WorldState, fact: StationZeroFact): string {
  const actor = (actorId: string) => state.actors[actorId]?.name ?? actorId;
  const zone = (zoneId: string) => state.zones[zoneId]?.name ?? zoneId;
  const system = (systemId: string) => state.systems[systemId]?.name ?? systemId;
  switch (fact.kind) {
    case "commander_ability_used": return `${state.factions[fact.factionId].name} used ${fact.commanderAbilityId}.`;
    case "actor_moved": return `${actor(fact.actorId)} moved from ${zone(fact.fromZoneId)} to ${zone(fact.toZoneId)}.`;
    case "actor_attacked": return `${actor(fact.actorId)} attacked ${actor(fact.targetActorId)} with ${fact.abilityId}.`;
    case "damage_dealt": return `${actor(fact.targetActorId)} took ${fact.amount} damage from ${actor(fact.sourceActorId)}.`;
    case "actor_health_changed": return `${actor(fact.actorId)} health changed from ${fact.before} to ${fact.after}.`;
    case "actor_life_state_changed": return `${actor(fact.actorId)} became ${fact.after}.`;
    case "actor_status_changed": return `${actor(fact.actorId)} ${fact.active ? "gained" : "lost"} ${fact.statusId}.`;
    case "ground_item_dropped": return `${actor(fact.actorId)} dropped an item in ${zone(fact.zoneId)}.`;
    case "ground_item_picked_up": return `${actor(fact.actorId)} picked up ${fact.quantity} item.`;
    case "item_consumed": return `${actor(fact.actorId)} consumed ${fact.quantity} ${fact.itemId} for ${fact.purpose}.`;
    case "item_extracted": return `${actor(fact.actorId)} extracted ${fact.itemId}.`;
    case "passage_changed": return `${fact.passageId} changed from ${fact.before} to ${fact.after}.`;
    case "system_changed": return `${system(fact.systemId)} changed integrity ${fact.integrityBefore} → ${fact.integrityAfter} and power ${fact.poweredBefore ? "on" : "off"} → ${fact.poweredAfter ? "on" : "off"}.`;
    case "hazard_changed": return `${fact.hazardId} severity changed ${fact.severityBefore} → ${fact.severityAfter}.`;
    case "knowledge_revealed": return `Mission Control confirmed ${fact.subjectKind} ${fact.subjectId}.`;
    case "objective_changed": return `${fact.objectiveId} became ${fact.after}.`;
    case "faction_outcome_changed": return `${state.factions[fact.factionId].name} outcome became ${fact.after}.`;
    case "environment_changed": return `${fact.resourceId} changed ${fact.before} → ${fact.after}.`;
  }
}

function buildAftermath(store: StationZeroV3Store, runId: string, state: StationZeroV3WorldState): StationZeroV3AftermathView | null {
  const latest = store.latestTurnReceipt(runId);
  if (!latest) return null;
  const visible = new Set(latest.record.resolution.observations.rescue.visibleFactIds);
  const visibleFacts = latest.record.resolution.facts
    .filter((fact) => visible.has(fact.factId))
    .map((fact) => ({ factId: fact.factId, kind: fact.kind, summary: factSummary(state, fact) }));
  return {
    turnSequence: latest.turnSequence,
    turnBatchId: latest.turnBatchId,
    visibleFacts,
    ownIntentResults: latest.record.resolution.intentResolutions
      .filter((entry) => entry.factionId === "rescue")
      .map((entry) => ({
        actorId: entry.actorId,
        actorName: state.actors[entry.actorId]?.name ?? entry.actorId,
        status: entry.status,
        reason: entry.reason,
      })),
  };
}

function buildMap(state: StationZeroV3WorldState) {
  const knowledge = state.factionKnowledge.rescue;
  const knownZones = new Set(knowledge.discoveredZoneIds);
  const contactByZone = new Map<string, string[]>();
  for (const contact of Object.values(knowledge.knownActors)) {
    if (state.actors[contact.actorId]?.factionId === "rescue") continue;
    const list = contactByZone.get(contact.lastKnownZoneId) ?? [];
    list.push(contact.actorId);
    contactByZone.set(contact.lastKnownZoneId, list);
  }
  const ownByZone = new Map<string, string[]>();
  for (const actor of Object.values(state.actors).filter((entry) => entry.factionId === "rescue")) {
    const list = ownByZone.get(actor.position.zoneId) ?? [];
    list.push(actor.actorId);
    ownByZone.set(actor.position.zoneId, list);
  }
  const visibleRoomIds = new Set(knowledge.discoveredRoomIds);
  for (const zoneId of knownZones) {
    const roomId = state.zones[zoneId]?.roomId;
    if (roomId) visibleRoomIds.add(roomId);
  }
  return {
    rooms: Object.values(state.rooms)
      .filter((room) => visibleRoomIds.has(room.roomId))
      .sort((left, right) => left.roomId.localeCompare(right.roomId))
      .map((room) => ({
        roomId: room.roomId,
        name: room.name,
        known: true,
        zones: room.zoneIds.filter((zoneId) => knownZones.has(zoneId)).map((zoneId) => {
          const zoneState = state.zones[zoneId]!;
          return {
            zoneId,
            name: zoneState.name,
            known: true,
            cover: zoneState.cover,
            ownActorIds: [...(ownByZone.get(zoneId) ?? [])].sort(),
            contactActorIds: [...(contactByZone.get(zoneId) ?? [])].sort(),
            systemIds: Object.values(state.systems).filter((entry) => entry.zoneId === zoneId && knowledge.knownSystemIds.includes(entry.systemId)).map((entry) => entry.systemId).sort(),
            hazardIds: Object.values(state.hazards).filter((entry) => entry.zoneId === zoneId && knowledge.knownHazardIds.includes(entry.hazardId)).map((entry) => entry.hazardId).sort(),
            groundItemIds: Object.values(state.groundItems).filter((entry) => entry.zoneId === zoneId && knowledge.knownGroundItemIds.includes(entry.groundItemId)).map((entry) => entry.groundItemId).sort(),
          };
        }),
      })),
  };
}

export function createStationZeroV3PlayView(
  store: StationZeroV3Store,
  turnService: StationZeroV3TurnService,
  planningStore: StationZeroV3PlanningStore,
  runId: string,
): StationZeroV3PlayView {
  const base = createStationZeroV3MissionControlView(store, turnService, runId);
  const state = store.loadState(runId);
  const planning = store.latestPlanning(runId);
  const head = planning ? planningStore.headOrNull(runId, planning.planningId) : null;
  const order = planning && head ? planningStore.currentOrder(runId, planning.planningId) : null;
  const preview = planning && head?.previewId ? planningStore.currentPreview(runId, planning.planningId) : null;
  const canEdit = Boolean(planning && head && planning.status === "open" && head.status !== "committed" && Object.keys(planning.submittedPlanDigests).length === 0);
  const submittedPlansMatchPreview = Boolean(planning && preview && Object.entries(planning.submittedPlanDigests)
    .every(([factionId, digest]) => digest === sha256(preview.factionPlans[factionId as StationZeroFactionId])));
  const canCommit = Boolean(
    state.encounter.status === "running" &&
    planning &&
    head &&
    preview &&
    (planning.status === "open" || planning.status === "committed") &&
    (head.status === "previewed" || head.status === "committed") &&
    head.previewId === preview.previewId &&
    head.previewDigest === preview.previewDigest &&
    submittedPlansMatchPreview
  );
  return {
    ...base,
    experience: {
      order: order?.order ?? null,
      orderRevision: order?.orderRevision ?? null,
      orderDigest: order?.orderDigest ?? null,
      preview: preview ? playerPreview(state, preview) : null,
      canEditOrder: canEdit,
      canGeneratePreview: canEdit,
      canCommitPreview: canCommit,
    },
    map: buildMap(state),
    aftermath: buildAftermath(store, runId, state),
    outcomes: {
      rescue: state.factions.rescue.outcome,
      pirate: state.factions.pirate.outcome,
      swarm: state.factions.swarm.outcome,
      reason: state.encounter.reason,
    },
  };
}
