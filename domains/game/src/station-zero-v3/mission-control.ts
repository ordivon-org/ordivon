import { STATION_ZERO_FACTION_IDS, type StationZeroV3WorldState } from "./model.ts";
import { STATION_ZERO_V3_OBJECTIVES } from "./content.ts";
import type { StationZeroV3MissionControlView } from "./p2-model.ts";
import type { StationZeroV3Store } from "./persistence.ts";

export function stationZeroV3PlayerObjectiveViews(
  state: StationZeroV3WorldState,
): StationZeroV3MissionControlView["objectives"] {
  const playerFactionId = state.encounter.playerFactionId;
  return STATION_ZERO_V3_OBJECTIVES
    .filter((objective) => objective.factionId === playerFactionId)
    .map((objective) => {
      const progress = state.factions[playerFactionId].objectiveProgress[objective.objectiveId];
      if (!progress) throw new Error(`Player Faction Objective progress is missing: ${objective.objectiveId}`);
      return {
        objectiveId: objective.objectiveId,
        name: objective.name,
        mandatory: objective.mandatory,
        status: progress.status,
        progress: progress.progress,
        target: progress.target,
        reason: progress.reason,
      };
    });
}

export function createStationZeroV3MissionControlView(
  store: StationZeroV3Store,
  runId: string,
): StationZeroV3MissionControlView {
  const head = store.loadWorldHead(runId);
  const state = head.state;
  const playerFactionId = state.encounter.playerFactionId;
  const knowledge = state.factionKnowledge[playerFactionId];
  const planning = store.latestPlanning(runId);
  const submittedFactions = planning
    ? STATION_ZERO_FACTION_IDS.filter((factionId) => planning.submittedPlanDigests[factionId] !== undefined)
    : [];
  const missingFactions = planning
    ? STATION_ZERO_FACTION_IDS.filter((factionId) => planning.submittedPlanDigests[factionId] === undefined)
    : [...STATION_ZERO_FACTION_IDS];
  const latestTurn = store.latestTurnReceipt(runId);

  const ownActors = Object.values(state.actors)
    .filter((actor) => actor.factionId === playerFactionId)
    .sort((left, right) => left.actorId.localeCompare(right.actorId))
    .map((actor) => ({
      actorId: actor.actorId,
      name: actor.name,
      roleId: actor.roleId,
      lifeState: actor.lifeState,
      health: actor.health,
      maximumHealth: actor.maximumHealth,
      zoneId: actor.position.zoneId,
      zoneName: state.zones[actor.position.zoneId]?.name ?? "Unknown",
      actionPoints: actor.actionPoints,
      statusIds: [...actor.statusIds].sort(),
      inventoryItemIds: [...actor.inventoryItemIds].sort(),
    }));

  const knownContacts = Object.values(knowledge.knownActors)
    .filter((known) => state.actors[known.actorId]?.factionId !== playerFactionId)
    .sort((left, right) => left.actorId.localeCompare(right.actorId))
    .map((known) => ({
      actorId: known.actorId,
      lastKnownZoneId: known.lastKnownZoneId,
      observedLifeState: known.observedLifeState,
      observedHealthBand: known.observedHealthBand,
      confidence: known.confidence,
      observedAtTurn: known.observedAtTurn,
    }));

  const objectives = stationZeroV3PlayerObjectiveViews(state);

  return {
    schemaVersion: 1,
    kind: "ordivon.game.station-zero-v3-mission-control-view",
    generatedFrom: {
      runId,
      worldRevision: head.revision,
      worldDigest: head.stateDigest,
      planningRevision: planning?.planningRevision ?? null,
    },
    run: {
      runId,
      turn: state.encounter.turn,
      turnLimit: state.encounter.turnLimit,
      status: state.encounter.status,
      reason: state.encounter.reason,
      playerFactionId,
    },
    planning: {
      planningId: planning?.planningId ?? null,
      status: planning?.status ?? null,
      submittedFactions,
      missingFactions,
      canSubmitPlans: state.encounter.status === "running" && planning?.status === "open",
      canCommit: state.encounter.status === "running" && planning?.status === "open" && missingFactions.length === 0,
      canExecute: state.encounter.status === "running" && planning?.status === "committed",
    },
    resources: {
      batteryCharge: state.environment.batteryCharge,
      batteryInitial: state.environment.batteryInitial,
      oxygen: state.environment.oxygen,
      reactorHeat: state.environment.reactorHeat,
      biomass: state.environment.biomass,
      alertLevel: state.environment.alertLevel,
    },
    ownActors,
    knownContacts,
    known: {
      roomIds: [...knowledge.discoveredRoomIds].sort(),
      zoneIds: [...knowledge.discoveredZoneIds].sort(),
      systemIds: [...knowledge.knownSystemIds].sort(),
      systems: [...knowledge.knownSystemIds].sort().map((systemId) => {
        const observed = knowledge.knownSystems[systemId];
        if (!observed) throw new Error(`Missing observed System state ${systemId}`);
        return {
          systemId,
          name: state.systems[systemId]?.name ?? systemId,
          observedIntegrity: observed.observedIntegrity,
          observedPowered: observed.observedPowered,
          observedAtTurn: observed.observedAtTurn,
        };
      }),
      hazardIds: [...knowledge.knownHazardIds].sort(),
      groundItemIds: [...knowledge.knownGroundItemIds]
        .filter((groundItemId) => state.groundItems[groundItemId] !== undefined)
        .sort(),
      reportIds: [...knowledge.reportIds].sort(),
    },
    objectives,
    latestTurn: latestTurn ? {
      turnSequence: latestTurn.turnSequence,
      turnBatchId: latestTurn.turnBatchId,
      eventId: latestTurn.event.eventId,
      eventDigest: latestTurn.eventDigest,
      recordDigest: latestTurn.recordDigest,
      visibleFactIds: [...latestTurn.record.resolution.observations[playerFactionId].visibleFactIds],
    } : null,
  };
}
