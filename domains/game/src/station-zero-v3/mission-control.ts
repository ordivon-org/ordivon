import { STATION_ZERO_FACTION_IDS } from "./model.ts";
import { STATION_ZERO_V3_OBJECTIVES } from "./content.ts";
import type { StationZeroV3MissionControlView } from "./p2-model.ts";
import type { StationZeroV3Store } from "./persistence.ts";
import type { StationZeroV3TurnService } from "./turn-service.ts";

export function createStationZeroV3MissionControlView(
  store: StationZeroV3Store,
  service: StationZeroV3TurnService,
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
  const hostExecution = planning?.taskId ? service.hostProjection(runId, planning.planningId) : null;
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

  const objectives = STATION_ZERO_V3_OBJECTIVES
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

  return {
    schemaVersion: 1,
    kind: "ordivon.game.station-zero-v3-mission-control-view",
    generatedFrom: {
      runId,
      worldRevision: head.revision,
      worldDigest: head.stateDigest,
      planningRevision: planning?.planningRevision ?? null,
      hostSequence: store.hostSequence(runId),
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
      canExecute: state.encounter.status === "running" && planning?.status === "committed" &&
        (hostExecution?.state === "reconciling" || hostExecution?.state === "ready"),
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
      hazardIds: [...knowledge.knownHazardIds].sort(),
      groundItemIds: [...knowledge.knownGroundItemIds]
        .filter((groundItemId) => state.groundItems[groundItemId] !== undefined)
        .sort(),
      reportIds: [...knowledge.reportIds].sort(),
    },
    objectives,
    hostExecution: hostExecution ? {
      taskId: hostExecution.taskId,
      dispatchId: planning?.dispatchId ?? "",
      state: hostExecution.state,
      hostRevision: hostExecution.revision,
      descriptorDigest: hostExecution.descriptorDigest,
      dispatchDigest: hostExecution.dispatchDigest,
      observationDigest: hostExecution.observationDigest,
      verificationDigest: hostExecution.verificationDigest,
      outcomeDigest: hostExecution.outcomeDigest,
    } : null,
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
