import { sha256 } from "../digest.ts";
import { STATION_ZERO_V3_COMMANDER_ABILITIES } from "./content.ts";
import { createStationZeroV3MissionControlView, stationZeroV3PlayerObjectiveViews } from "./mission-control.ts";
import type { StationZeroFactionId, StationZeroV3WorldState } from "./model.ts";
import { createStationZeroV3OperationDebrief } from "./operation-debrief.ts";
import {
  assertStationZeroV3SpatialLayout,
  stationZeroV3PassageVisibleToRescueTopology,
  stationZeroV3SpatialLayout,
  type StationZeroV3SpatialPoint,
} from "./spatial-layout.ts";
import type {
  StationZeroV3AftermathView,
  StationZeroV3PlanPreview,
  StationZeroV3PlayView,
  StationZeroV3PlayerPlanView,
} from "./p3-model.ts";
import type { StationZeroV3PlanningStore } from "./planning-store.ts";
import { createStationZeroV3PlanImpact } from "./plan-impact.ts";
import type { StationZeroV3Store } from "./persistence.ts";
import { createStationZeroV3TemporalExpressions, stationZeroV3BoundedFactSummary } from "./temporal-expression.ts";
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

function playerPreview(
  state: StationZeroV3WorldState,
  preview: StationZeroV3PlanPreview,
  objectives: ReturnType<typeof createStationZeroV3MissionControlView>["objectives"],
): StationZeroV3PlayerPlanView {
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
    planImpact: createStationZeroV3PlanImpact(preview, objectives),
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
      responsibility: entry.responsibility ? structuredClone(entry.responsibility) : null,
      responsibilityFeedback: entry.responsibilityFeedback ? structuredClone(entry.responsibilityFeedback) : null,
    })),
    enemyPlansSealed: (["pirate", "swarm"] as const).map((factionId) => ({
      factionId,
      status: "sealed",
      planDigest: sha256(preview.factionPlans[factionId]),
    })),
    warnings: [...preview.warnings],
  };
}

function buildAftermath(
  store: StationZeroV3Store,
  planningStore: StationZeroV3PlanningStore,
  runId: string,
  state: StationZeroV3WorldState,
  map: StationZeroV3PlayView["map"],
): StationZeroV3AftermathView | null {
  const latest = store.latestTurnReceipt(runId);
  if (!latest) return null;
  const committedPreview = planningStore.currentPreview(runId, latest.planningId);
  if (!committedPreview) throw new TypeError(`Committed Turn lacks retained Plan Preview: ${latest.planningId}`);
  const sourceState = store.stateAtRevision(runId, latest.record.resolution.worldRevisionBefore);
  const beforeObjectives = stationZeroV3PlayerObjectiveViews(sourceState);
  const afterObjectives = stationZeroV3PlayerObjectiveViews(state);
  const afterById = new Map(afterObjectives.map((objective) => [objective.objectiveId, objective]));
  const plannedImpact = createStationZeroV3PlanImpact(committedPreview, beforeObjectives);
  const plannedActions = new Map(committedPreview.explanations.rescue.actorIntents.map((entry) => [entry.actorId, entry.label]));
  const committedIntentActors = new Map(committedPreview.factionPlans.rescue.actorIntents.map((intent) => [intent.intentId, intent.actorId]));
  const visible = new Set(latest.record.resolution.observations.rescue.visibleFactIds);
  const retainedFacts = latest.record.resolution.facts.filter((fact) => visible.has(fact.factId));
  return {
    turnSequence: latest.turnSequence,
    turnBatchId: latest.turnBatchId,
    planReview: {
      previewId: committedPreview.previewId,
      orderRevision: committedPreview.orderRevision,
      objectives: plannedImpact.map((impact) => {
        const after = afterById.get(impact.objectiveId);
        if (!after) throw new TypeError(`Plan Review objective left the player projection: ${impact.objectiveId}`);
        return {
          objectiveId: impact.objectiveId,
          name: impact.name,
          mandatory: impact.mandatory,
          selectedPriority: impact.selectedPriority,
          plannedImpact: impact.impact,
          supportingActorNames: [...impact.actorNames],
          beforeProgress: impact.progress,
          afterProgress: after.progress,
          target: impact.target,
          beforeStatus: impact.status,
          afterStatus: after.status,
        };
      }),
    },
    expressions: createStationZeroV3TemporalExpressions(state, retainedFacts, map),
    visibleFacts: retainedFacts.map((fact) => ({
      factId: fact.factId,
      kind: fact.kind,
      summary: stationZeroV3BoundedFactSummary(state, fact, map),
    })),
    ownIntentResults: latest.record.resolution.intentResolutions
      .filter((entry) => entry.factionId === "rescue")
      .map((entry) => {
        if (committedIntentActors.get(entry.intentId) !== entry.actorId) {
          throw new TypeError(`Rescue resolution is not bound to committed Preview intent: ${entry.intentId}`);
        }
        const plannedAction = plannedActions.get(entry.actorId);
        if (!plannedAction) throw new TypeError(`Committed Preview lacks Rescue explanation: ${entry.actorId}`);
        return {
          actorId: entry.actorId,
          actorName: state.actors[entry.actorId]?.name ?? entry.actorId,
          plannedAction,
          status: entry.status,
          reason: entry.reason,
        };
      }),
  };
}

function clippedPolyline(points: StationZeroV3SpatialPoint[], maximumLength: number): StationZeroV3SpatialPoint[] {
  if (points.length < 2) return points.map((point) => ({ ...point }));
  const retained: StationZeroV3SpatialPoint[] = [{ ...points[0]! }];
  let remaining = maximumLength;
  for (let index = 1; index < points.length && remaining > 0; index += 1) {
    const from = points[index - 1]!;
    const to = points[index]!;
    const dx = to.x - from.x;
    const dy = to.y - from.y;
    const length = Math.hypot(dx, dy);
    if (length === 0) continue;
    if (length <= remaining) {
      retained.push({ ...to });
      remaining -= length;
      continue;
    }
    const ratio = remaining / length;
    retained.push({ x: from.x + dx * ratio, y: from.y + dy * ratio });
    remaining = 0;
  }
  return retained;
}

function buildMap(state: StationZeroV3WorldState) {
  const layout = stationZeroV3SpatialLayout();
  assertStationZeroV3SpatialLayout(layout, state);
  const knowledge = state.factionKnowledge.rescue;
  const knownZones = new Set(knowledge.discoveredZoneIds);
  const contactByZone = new Map<string, string[]>();
  for (const contact of Object.values(knowledge.knownActors)) {
    if (state.actors[contact.actorId]?.factionId === "rescue" || !knownZones.has(contact.lastKnownZoneId)) continue;
    const list = contactByZone.get(contact.lastKnownZoneId) ?? [];
    list.push(contact.actorId);
    contactByZone.set(contact.lastKnownZoneId, list);
  }
  const ownByZone = new Map<string, string[]>();
  for (const actor of Object.values(state.actors).filter((entry) => entry.factionId === "rescue" && knownZones.has(entry.position.zoneId))) {
    const list = ownByZone.get(actor.position.zoneId) ?? [];
    list.push(actor.actorId);
    ownByZone.set(actor.position.zoneId, list);
  }

  const zoneRows = [...knownZones].sort().map((zoneId) => {
    const zoneState = state.zones[zoneId]!;
    const geometry = layout.zones[zoneId]!;
    return {
      zoneId,
      roomId: zoneState.roomId,
      roomName: state.rooms[zoneState.roomId]?.name ?? zoneState.roomId,
      name: zoneState.name,
      cover: zoneState.cover,
      geometry: { x: geometry.x, y: geometry.y, width: geometry.width, height: geometry.height },
      ownActorIds: [...(ownByZone.get(zoneId) ?? [])].sort(),
      contactActorIds: [...(contactByZone.get(zoneId) ?? [])].sort(),
      systemIds: Object.values(state.systems)
        .filter((entry) => entry.zoneId === zoneId && knowledge.knownSystemIds.includes(entry.systemId))
        .map((entry) => entry.systemId).sort(),
      hazardIds: Object.values(state.hazards)
        .filter((entry) => entry.zoneId === zoneId && knowledge.knownHazardIds.includes(entry.hazardId))
        .map((entry) => entry.hazardId).sort(),
      groundItemIds: Object.values(state.groundItems)
        .filter((entry) => entry.zoneId === zoneId && knowledge.knownGroundItemIds.includes(entry.groundItemId))
        .map((entry) => entry.groundItemId).sort(),
    };
  });

  const passageRows = Object.values(state.passages)
    .filter((passage) => knownZones.has(passage.zoneAId) && knownZones.has(passage.zoneBId) && stationZeroV3PassageVisibleToRescueTopology(passage))
    .sort((left, right) => left.passageId.localeCompare(right.passageId))
    .map((passage) => ({
      passageId: passage.passageId,
      zoneAId: passage.zoneAId,
      zoneBId: passage.zoneBId,
      points: layout.passages[passage.passageId]!.points.map((point) => ({ ...point })),
    }));

  const frontierRows = Object.values(state.passages)
    .filter((passage) => stationZeroV3PassageVisibleToRescueTopology(passage))
    .flatMap((passage) => {
      const aKnown = knownZones.has(passage.zoneAId);
      const bKnown = knownZones.has(passage.zoneBId);
      if (aKnown === bKnown) return [];
      const fromZoneId = aKnown ? passage.zoneAId : passage.zoneBId;
      const route = layout.passages[passage.passageId]!.points;
      const fromKnown = aKnown ? route : [...route].reverse();
      const points = clippedPolyline(fromKnown, 42);
      return [{
        frontierId: `frontier:${sha256({ fromZoneId, points }).slice(0, 12)}`,
        fromZoneId,
        points,
      }];
    })
    .sort((left, right) => left.frontierId.localeCompare(right.frontierId));

  const xValues: number[] = [];
  const yValues: number[] = [];
  for (const zone of zoneRows) {
    xValues.push(zone.geometry.x, zone.geometry.x + zone.geometry.width);
    yValues.push(zone.geometry.y, zone.geometry.y + zone.geometry.height);
  }
  for (const row of [...passageRows, ...frontierRows]) {
    for (const point of row.points) {
      xValues.push(point.x);
      yValues.push(point.y);
    }
  }
  if (xValues.length === 0 || yValues.length === 0) throw new TypeError("Player spatial projection has no known geometry");
  const padding = 48;
  const minimumX = Math.min(...xValues);
  const maximumX = Math.max(...xValues);
  const minimumY = Math.min(...yValues);
  const maximumY = Math.max(...yValues);
  const offsetX = padding - minimumX;
  const offsetY = padding - minimumY;
  const translatePoint = (point: StationZeroV3SpatialPoint) => ({ x: point.x + offsetX, y: point.y + offsetY });

  return {
    layoutDigest: layout.layoutDigest,
    width: maximumX - minimumX + padding * 2,
    height: maximumY - minimumY + padding * 2,
    zones: zoneRows.map((zone) => ({
      ...zone,
      geometry: { ...zone.geometry, x: zone.geometry.x + offsetX, y: zone.geometry.y + offsetY },
    })),
    passages: passageRows.map((passage) => ({ ...passage, points: passage.points.map(translatePoint) })),
    frontiers: frontierRows.map((frontier) => ({ ...frontier, points: frontier.points.map(translatePoint) })),
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
  const map = buildMap(state);
  return {
    ...base,
    experience: {
      order: order?.order ?? null,
      orderRevision: order?.orderRevision ?? null,
      orderDigest: order?.orderDigest ?? null,
      preview: preview ? playerPreview(state, preview, base.objectives) : null,
      canEditOrder: canEdit,
      canGeneratePreview: canEdit,
      canCommitPreview: canCommit,
    },
    map,
    aftermath: buildAftermath(store, planningStore, runId, state, map),
    debrief: createStationZeroV3OperationDebrief(store, planningStore, runId),
    outcomes: {
      rescue: state.factions.rescue.outcome,
      pirate: state.factions.pirate.outcome,
      swarm: state.factions.swarm.outcome,
      reason: state.encounter.reason,
    },
  };
}
