import { sha256 } from "../digest.ts";
import { STATION_ZERO_V3_OBJECTIVES } from "./content.ts";
import { stationZeroV3ExpressionAssets, type StationZeroV3SpriteFrame } from "./expression-assets.ts";
import type { StationZeroFact, StationZeroV3WorldState } from "./model.ts";
import type {
  StationZeroV3PlayView,
  StationZeroV3TemporalExpression,
  StationZeroV3TemporalExpressionSprite,
  StationZeroV3TemporalExpressionTone,
} from "./p3-model.ts";

type SpatialMapView = StationZeroV3PlayView["map"];
type Point = { x: number; y: number };

function zoneView(map: SpatialMapView, zoneId: string) {
  return map.zones.find((zone) => zone.zoneId === zoneId) ?? null;
}

function zoneCenter(map: SpatialMapView, zoneId: string): Point | null {
  const retained = zoneView(map, zoneId);
  if (!retained) return null;
  return {
    x: retained.geometry.x + retained.geometry.width / 2,
    y: retained.geometry.y + retained.geometry.height / 2,
  };
}

function actorKnown(state: StationZeroV3WorldState, actorId: string): boolean {
  const actor = state.actors[actorId];
  return Boolean(actor && (actor.factionId === "rescue" || state.factionKnowledge.rescue.knownActors[actorId]));
}

function actorFactionIfKnown(state: StationZeroV3WorldState, actorId: string) {
  return actorKnown(state, actorId) ? state.actors[actorId]?.factionId : undefined;
}

function actorLabel(state: StationZeroV3WorldState, actorId: string): string {
  return actorKnown(state, actorId) ? (state.actors[actorId]?.name ?? "Unknown contact") : "Unknown contact";
}

function zoneLabel(map: SpatialMapView, zoneId: string): string {
  return zoneView(map, zoneId)?.name ?? "an uncharted sector";
}

function actorPoint(state: StationZeroV3WorldState, map: SpatialMapView, actorId: string): Point | null {
  if (!actorKnown(state, actorId)) return null;
  const actor = state.actors[actorId];
  if (!actor) return null;
  const zoneId = actor.factionId === "rescue"
    ? actor.position.zoneId
    : state.factionKnowledge.rescue.knownActors[actorId]?.lastKnownZoneId;
  return zoneId ? zoneCenter(map, zoneId) : null;
}

function objectiveLabel(objectiveId: string): string {
  return STATION_ZERO_V3_OBJECTIVES.find((objective) => objective.objectiveId === objectiveId)?.name ?? "Mission objective";
}

function knownPassageLabel(state: StationZeroV3WorldState, map: SpatialMapView, passageId: string): string {
  const passage = state.passages[passageId];
  if (!passage) return "Nearby access";
  const left = zoneView(map, passage.zoneAId);
  const right = zoneView(map, passage.zoneBId);
  if (left && right) return `${left.name} ↔ ${right.name} access`;
  return `${left?.name ?? right?.name ?? "Nearby"} access`;
}

function sprite(frame: StationZeroV3SpriteFrame): StationZeroV3TemporalExpressionSprite {
  const assets = stationZeroV3ExpressionAssets();
  return {
    kind: "sprite",
    src: assets.rescueSprite.src,
    sheetWidth: assets.rescueSprite.sheetWidth,
    sheetHeight: assets.rescueSprite.sheetHeight,
    frame: { ...frame },
  };
}

function rescueSprite(state: StationZeroV3WorldState, actorId: string, frame: "move" | "impact"): StationZeroV3TemporalExpressionSprite | null {
  if (state.actors[actorId]?.factionId !== "rescue") return null;
  const assets = stationZeroV3ExpressionAssets();
  return sprite(assets.rescueSprite[frame]);
}

function base(
  fact: StationZeroFact,
  sequence: number,
  kind: StationZeroV3TemporalExpression["kind"],
  tone: StationZeroV3TemporalExpressionTone,
  label: string,
  detail: string,
): Omit<StationZeroV3TemporalExpression, "map" | "visual"> {
  return {
    expressionId: `expression:${sha256({ factId: fact.factId, kind }).slice(0, 20)}`,
    factId: fact.factId,
    sequence,
    kind,
    tone,
    label,
    detail,
  };
}

function movementExpression(
  state: StationZeroV3WorldState,
  map: SpatialMapView,
  fact: Extract<StationZeroFact, { kind: "actor_moved" }>,
  sequence: number,
): StationZeroV3TemporalExpression {
  const from = zoneCenter(map, fact.fromZoneId);
  const to = zoneCenter(map, fact.toZoneId);
  const fromLabel = zoneLabel(map, fact.fromZoneId);
  const toLabel = zoneLabel(map, fact.toZoneId);
  const detail = from && to
    ? `Moved ${fromLabel} → ${toLabel}`
    : to
      ? `Entered ${toLabel} from an uncharted sector`
      : from
        ? `Left ${fromLabel} toward an uncharted sector`
        : "Movement observed outside confirmed station geometry";
  return {
    ...base(fact, sequence, "move", "neutral", actorLabel(state, fact.actorId), detail),
    map: from && to
      ? { from, to, point: null, points: [] }
      : { from: null, to: null, point: to ?? from, points: [] },
    visual: rescueSprite(state, fact.actorId, "move"),
  };
}

function impactTone(state: StationZeroV3WorldState, targetActorId: string, sourceActorId: string): StationZeroV3TemporalExpressionTone {
  const targetFaction = actorFactionIfKnown(state, targetActorId);
  const sourceFaction = actorFactionIfKnown(state, sourceActorId);
  const targetKind = actorKnown(state, targetActorId) ? state.actors[targetActorId]?.kind : undefined;
  if (targetFaction === "rescue" || targetKind === "civilian") return "danger";
  if (sourceFaction === "rescue" && targetFaction !== undefined) return "positive";
  return "warning";
}

function expressionForFact(
  state: StationZeroV3WorldState,
  map: SpatialMapView,
  fact: StationZeroFact,
  sequence: number,
): StationZeroV3TemporalExpression | null {
  const assets = stationZeroV3ExpressionAssets();
  switch (fact.kind) {
    case "actor_moved":
      return movementExpression(state, map, fact, sequence);
    case "damage_dealt": {
      const point = actorPoint(state, map, fact.targetActorId);
      return {
        ...base(
          fact,
          sequence,
          "impact",
          impactTone(state, fact.targetActorId, fact.sourceActorId),
          actorLabel(state, fact.targetActorId),
          `${actorLabel(state, fact.sourceActorId)} dealt ${fact.amount} damage`,
        ),
        map: point ? { from: null, to: null, point, points: [] } : null,
        visual: rescueSprite(state, fact.targetActorId, "impact"),
      };
    }
    case "actor_health_changed": {
      const point = actorPoint(state, map, fact.actorId);
      const delta = fact.after - fact.before;
      return {
        ...base(
          fact,
          sequence,
          "health",
          delta < 0 ? "warning" : delta > 0 ? "positive" : "neutral",
          actorLabel(state, fact.actorId),
          `Health ${fact.before} → ${fact.after}`,
        ),
        map: point ? { from: null, to: null, point, points: [] } : null,
        visual: delta < 0 ? rescueSprite(state, fact.actorId, "impact") : null,
      };
    }
    case "passage_changed": {
      const passage = state.passages[fact.passageId];
      const retained = map.passages.find((entry) => entry.passageId === fact.passageId);
      const point = passage
        ? zoneCenter(map, passage.zoneAId) ?? zoneCenter(map, passage.zoneBId)
        : null;
      return {
        ...base(fact, sequence, "passage", "warning", knownPassageLabel(state, map, fact.passageId), `Access ${fact.before} → ${fact.after}`),
        map: retained
          ? { from: null, to: null, point: null, points: retained.points.map((entry) => ({ ...entry })) }
          : point
            ? { from: null, to: null, point, points: [] }
            : null,
        visual: null,
      };
    }
    case "system_changed": {
      const system = state.systems[fact.systemId];
      if (!system || !state.factionKnowledge.rescue.knownSystemIds.includes(fact.systemId)) return null;
      const point = zoneCenter(map, system.zoneId);
      const integrityDelta = fact.integrityAfter - fact.integrityBefore;
      const tone: StationZeroV3TemporalExpressionTone =
        integrityDelta < 0 || (fact.poweredBefore && !fact.poweredAfter) ? "danger" :
        integrityDelta > 0 || (!fact.poweredBefore && fact.poweredAfter) ? "positive" : "neutral";
      return {
        ...base(
          fact,
          sequence,
          "system",
          tone,
          system.name,
          `Integrity ${Math.round(fact.integrityBefore * 100)}% → ${Math.round(fact.integrityAfter * 100)}% · power ${fact.poweredBefore ? "on" : "off"} → ${fact.poweredAfter ? "on" : "off"}`,
        ),
        map: point ? { from: null, to: null, point, points: [] } : null,
        visual: { kind: "icon", src: assets.systemSignalSrc },
      };
    }
    case "hazard_changed": {
      const hazard = state.hazards[fact.hazardId];
      if (!hazard || !state.factionKnowledge.rescue.knownHazardIds.includes(fact.hazardId)) return null;
      const point = zoneCenter(map, hazard.zoneId);
      const delta = fact.severityAfter - fact.severityBefore;
      return {
        ...base(
          fact,
          sequence,
          "hazard",
          fact.contained || delta < 0 ? "positive" : delta > 0 ? "danger" : "warning",
          hazard.name,
          `Severity ${fact.severityBefore} → ${fact.severityAfter}${fact.contained ? " · contained" : ""}`,
        ),
        map: point ? { from: null, to: null, point, points: [] } : null,
        visual: { kind: "icon", src: assets.hazardSignalSrc },
      };
    }
    case "objective_changed":
      if (fact.factionId !== "rescue") return null;
      return {
        ...base(
          fact,
          sequence,
          "objective",
          fact.after === "completed" ? "positive" : fact.after === "failed" ? "danger" : "neutral",
          objectiveLabel(fact.objectiveId),
          `Objective ${fact.before} → ${fact.after}`,
        ),
        map: null,
        visual: null,
      };
    default:
      return null;
  }
}

export function createStationZeroV3TemporalExpressions(
  state: StationZeroV3WorldState,
  visibleFacts: StationZeroFact[],
  map: SpatialMapView,
): StationZeroV3TemporalExpression[] {
  const retained: StationZeroV3TemporalExpression[] = [];
  for (const [factIndex, fact] of visibleFacts.entries()) {
    if (fact.kind === "actor_health_changed" && fact.after < fact.before) {
      const prior = visibleFacts[factIndex - 1];
      if (prior?.kind === "damage_dealt" && prior.targetActorId === fact.actorId && prior.amount === fact.before - fact.after) {
        continue;
      }
    }
    const expression = expressionForFact(state, map, fact, retained.length);
    if (expression) retained.push(expression);
  }
  return retained;
}

export function stationZeroV3BoundedFactSummary(
  state: StationZeroV3WorldState,
  fact: StationZeroFact,
  map: SpatialMapView,
): string {
  const actor = (actorId: string) => actorLabel(state, actorId);
  const zone = (zoneId: string) => zoneLabel(map, zoneId);
  const system = (systemId: string) => state.factionKnowledge.rescue.knownSystemIds.includes(systemId)
    ? (state.systems[systemId]?.name ?? "Known system")
    : "Known system";
  const hazard = (hazardId: string) => state.factionKnowledge.rescue.knownHazardIds.includes(hazardId)
    ? (state.hazards[hazardId]?.name ?? "Known hazard")
    : "Known hazard";
  switch (fact.kind) {
    case "commander_ability_used": return `Emergency Response Team used ${fact.commanderAbilityId}.`;
    case "actor_moved": return `${actor(fact.actorId)} moved from ${zone(fact.fromZoneId)} to ${zone(fact.toZoneId)}.`;
    case "actor_attacked": return `${actor(fact.actorId)} attacked ${actor(fact.targetActorId)} with ${fact.abilityId}.`;
    case "damage_dealt": return `${actor(fact.targetActorId)} took ${fact.amount} damage from ${actor(fact.sourceActorId)}.`;
    case "actor_health_changed": return `${actor(fact.actorId)} health changed from ${fact.before} to ${fact.after}.`;
    case "actor_life_state_changed": return `${actor(fact.actorId)} became ${fact.after}.`;
    case "actor_status_changed": return `${actor(fact.actorId)} ${fact.active ? "gained" : "lost"} ${fact.statusId}.`;
    case "ground_item_dropped": return `${actor(fact.actorId)} dropped an item in ${zone(fact.zoneId)}.`;
    case "ground_item_picked_up": return `${actor(fact.actorId)} picked up ${fact.quantity} item.`;
    case "item_consumed": return actorFactionIfKnown(state, fact.actorId) === "rescue"
      ? `${actor(fact.actorId)} consumed ${fact.quantity} ${fact.itemId} for ${fact.purpose}.`
      : `${actor(fact.actorId)} used an item.`;
    case "item_extracted": return fact.factionId === "rescue"
      ? `${actor(fact.actorId)} extracted ${fact.itemId}.`
      : `${actor(fact.actorId)} extracted an item.`;
    case "passage_changed": return `${knownPassageLabel(state, map, fact.passageId)} changed from ${fact.before} to ${fact.after}.`;
    case "system_changed": return `${system(fact.systemId)} changed integrity ${fact.integrityBefore} → ${fact.integrityAfter} and power ${fact.poweredBefore ? "on" : "off"} → ${fact.poweredAfter ? "on" : "off"}.`;
    case "hazard_changed": return `${hazard(fact.hazardId)} severity changed ${fact.severityBefore} → ${fact.severityAfter}.`;
    case "knowledge_revealed": {
      if (fact.factionId !== "rescue") return "Mission Control received new intelligence.";
      if (fact.subjectKind === "zone") return `Mission Control confirmed zone ${zone(fact.subjectId)}.`;
      if (fact.subjectKind === "room") return `Mission Control confirmed room ${state.factionKnowledge.rescue.discoveredRoomIds.includes(fact.subjectId) ? (state.rooms[fact.subjectId]?.name ?? fact.subjectId) : "unknown"}.`;
      if (fact.subjectKind === "actor") return `Mission Control confirmed contact ${actor(fact.subjectId)}.`;
      if (fact.subjectKind === "system") return `Mission Control confirmed system ${system(fact.subjectId)}.`;
      if (fact.subjectKind === "hazard") return `Mission Control confirmed hazard ${hazard(fact.subjectId)}.`;
      return "Mission Control confirmed a recoverable item.";
    }
    case "objective_changed": return `${objectiveLabel(fact.objectiveId)} became ${fact.after}.`;
    case "faction_outcome_changed": return `${state.factions[fact.factionId].name} outcome became ${fact.after}.`;
    case "environment_changed": return `${fact.resourceId} changed ${fact.before} → ${fact.after}.`;
  }
}
