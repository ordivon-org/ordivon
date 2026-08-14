import { readFileSync } from "node:fs";

import { sha256 } from "../digest.ts";
import type { StationZeroV3WorldState } from "./model.ts";

export interface StationZeroV3SpatialPoint {
  x: number;
  y: number;
}

export interface StationZeroV3SpatialZoneGeometry {
  zoneId: string;
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface StationZeroV3SpatialPassageGeometry {
  passageId: string;
  zoneAId: string;
  zoneBId: string;
  points: StationZeroV3SpatialPoint[];
}

export interface StationZeroV3SpatialLayout {
  schemaVersion: 1;
  kind: "ordivon.game.station-zero-v3-spatial-layout";
  width: number;
  height: number;
  zones: Record<string, StationZeroV3SpatialZoneGeometry>;
  passages: Record<string, StationZeroV3SpatialPassageGeometry>;
  layoutDigest: string;
}

interface TiledProperty {
  name: string;
  type?: string;
  value: unknown;
}

interface TiledObject {
  id: number;
  name: string;
  class?: string;
  type?: string;
  x: number;
  y: number;
  width: number;
  height: number;
  rotation?: number;
  visible?: boolean;
  polyline?: StationZeroV3SpatialPoint[];
  properties?: TiledProperty[];
}

interface TiledObjectLayer {
  id: number;
  name: string;
  type: "objectgroup";
  objects: TiledObject[];
}

interface TiledMap {
  type: "map";
  orientation: "orthogonal";
  infinite: boolean;
  width: number;
  height: number;
  tilewidth: number;
  tileheight: number;
  layers: TiledObjectLayer[];
  properties?: TiledProperty[];
}

const LAYOUT_URL = new URL("../../assets/station-zero-v3/station-zero-layout.tmj", import.meta.url);
const MAP_PROPERTY_NAMES = new Set(["authority", "scenarioId", "scenarioVersion"]);
const ZONE_PROPERTY_NAMES = new Set(["zoneId"]);
const PASSAGE_PROPERTY_NAMES = new Set(["passageId", "zoneAId", "zoneBId"]);
const RESCUE_INACCESSIBLE_PASSAGE_TAGS = new Set(["vent", "swarm-route"]);

function assertFinite(value: number, label: string): void {
  if (!Number.isFinite(value)) throw new TypeError(`${label} must be finite`);
}

function assertPositive(value: number, label: string): void {
  assertFinite(value, label);
  if (value <= 0) throw new TypeError(`${label} must be positive`);
}

function propertyMap(properties: TiledProperty[] | undefined, allowed: Set<string>, label: string): Map<string, unknown> {
  const result = new Map<string, unknown>();
  for (const property of properties ?? []) {
    if (!allowed.has(property.name)) throw new TypeError(`${label} contains non-authoritative property ${property.name}`);
    if (result.has(property.name)) throw new TypeError(`${label} duplicates property ${property.name}`);
    result.set(property.name, property.value);
  }
  return result;
}

function requiredString(properties: Map<string, unknown>, name: string, label: string): string {
  const value = properties.get(name);
  if (typeof value !== "string" || value.length === 0) throw new TypeError(`${label} requires string property ${name}`);
  return value;
}

function pointInsideZone(point: StationZeroV3SpatialPoint, zone: StationZeroV3SpatialZoneGeometry): boolean {
  const epsilon = 0.01;
  return point.x >= zone.x - epsilon && point.x <= zone.x + zone.width + epsilon &&
    point.y >= zone.y - epsilon && point.y <= zone.y + zone.height + epsilon;
}

function parseSpatialLayout(raw: unknown): StationZeroV3SpatialLayout {
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) throw new TypeError("Station Zero spatial layout must be a Tiled map object");
  const map = raw as TiledMap;
  if (map.type !== "map" || map.orientation !== "orthogonal" || map.infinite !== false) {
    throw new TypeError("Station Zero spatial layout must be a finite orthogonal Tiled map");
  }
  assertPositive(map.width, "Tiled map width");
  assertPositive(map.height, "Tiled map height");
  assertPositive(map.tilewidth, "Tiled tile width");
  assertPositive(map.tileheight, "Tiled tile height");

  const mapProperties = propertyMap(map.properties, MAP_PROPERTY_NAMES, "Tiled map");
  if (mapProperties.get("authority") !== "non-authoritative-spatial-projection" ||
      mapProperties.get("scenarioId") !== "station-zero" || mapProperties.get("scenarioVersion") !== 3) {
    throw new TypeError("Station Zero spatial layout identity or authority boundary mismatch");
  }

  const layers = new Map(map.layers.map((layer) => [layer.name, layer]));
  if (layers.size !== 2 || !layers.has("Zones") || !layers.has("Passages")) {
    throw new TypeError("Station Zero spatial layout requires exactly Zones and Passages object layers");
  }
  for (const layer of layers.values()) {
    if (layer.type !== "objectgroup") throw new TypeError(`Tiled layer ${layer.name} must be an object layer`);
  }

  const zones: Record<string, StationZeroV3SpatialZoneGeometry> = {};
  for (const object of layers.get("Zones")!.objects) {
    if ((object.class ?? object.type) !== "zone") throw new TypeError(`Tiled Zone object ${object.name} must use class zone`);
    if ((object.rotation ?? 0) !== 0 || object.visible === false) throw new TypeError(`Tiled Zone object ${object.name} must be visible and axis-aligned`);
    const properties = propertyMap(object.properties, ZONE_PROPERTY_NAMES, `Tiled Zone ${object.name}`);
    const zoneId = requiredString(properties, "zoneId", `Tiled Zone ${object.name}`);
    if (object.name !== zoneId) throw new TypeError(`Tiled Zone object name must equal zoneId ${zoneId}`);
    if (zones[zoneId]) throw new TypeError(`Tiled spatial layout duplicates Zone ${zoneId}`);
    assertFinite(object.x, `${zoneId}.x`);
    assertFinite(object.y, `${zoneId}.y`);
    assertPositive(object.width, `${zoneId}.width`);
    assertPositive(object.height, `${zoneId}.height`);
    zones[zoneId] = { zoneId, x: object.x, y: object.y, width: object.width, height: object.height };
  }

  const passages: Record<string, StationZeroV3SpatialPassageGeometry> = {};
  for (const object of layers.get("Passages")!.objects) {
    if ((object.class ?? object.type) !== "passage") throw new TypeError(`Tiled Passage object ${object.name} must use class passage`);
    if ((object.rotation ?? 0) !== 0 || object.visible === false) throw new TypeError(`Tiled Passage object ${object.name} must be visible and unrotated`);
    const properties = propertyMap(object.properties, PASSAGE_PROPERTY_NAMES, `Tiled Passage ${object.name}`);
    const passageId = requiredString(properties, "passageId", `Tiled Passage ${object.name}`);
    const zoneAId = requiredString(properties, "zoneAId", `Tiled Passage ${object.name}`);
    const zoneBId = requiredString(properties, "zoneBId", `Tiled Passage ${object.name}`);
    if (object.name !== passageId) throw new TypeError(`Tiled Passage object name must equal passageId ${passageId}`);
    if (passages[passageId]) throw new TypeError(`Tiled spatial layout duplicates Passage ${passageId}`);
    if (!object.polyline || object.polyline.length < 2) throw new TypeError(`Tiled Passage ${passageId} requires a polyline`);
    assertFinite(object.x, `${passageId}.x`);
    assertFinite(object.y, `${passageId}.y`);
    const points = object.polyline.map((point, index) => {
      assertFinite(point.x, `${passageId}.polyline[${index}].x`);
      assertFinite(point.y, `${passageId}.polyline[${index}].y`);
      return { x: object.x + point.x, y: object.y + point.y };
    });
    passages[passageId] = { passageId, zoneAId, zoneBId, points };
  }

  const retained = {
    schemaVersion: 1 as const,
    kind: "ordivon.game.station-zero-v3-spatial-layout" as const,
    width: map.width * map.tilewidth,
    height: map.height * map.tileheight,
    zones,
    passages,
  };
  return { ...retained, layoutDigest: sha256(retained) };
}

export function assertStationZeroV3SpatialLayout(
  layout: StationZeroV3SpatialLayout,
  state: StationZeroV3WorldState,
): void {
  const layoutZoneIds = Object.keys(layout.zones).sort();
  const worldZoneIds = Object.keys(state.zones).sort();
  if (layoutZoneIds.length !== worldZoneIds.length || layoutZoneIds.some((zoneId, index) => zoneId !== worldZoneIds[index])) {
    throw new TypeError("Station Zero spatial layout Zone identities diverge from World authority");
  }
  const layoutPassageIds = Object.keys(layout.passages).sort();
  const worldPassageIds = Object.keys(state.passages).sort();
  if (layoutPassageIds.length !== worldPassageIds.length || layoutPassageIds.some((passageId, index) => passageId !== worldPassageIds[index])) {
    throw new TypeError("Station Zero spatial layout Passage identities diverge from World authority");
  }

  for (const zoneId of worldZoneIds) {
    const geometry = layout.zones[zoneId];
    if (!geometry) throw new TypeError(`Station Zero spatial layout lacks Zone ${zoneId}`);
    if (geometry.x < 0 || geometry.y < 0 || geometry.x + geometry.width > layout.width || geometry.y + geometry.height > layout.height) {
      throw new TypeError(`Station Zero spatial Zone ${zoneId} is outside map bounds`);
    }
  }

  for (const passageId of worldPassageIds) {
    const worldPassage = state.passages[passageId]!;
    const geometry = layout.passages[passageId]!;
    if (geometry.zoneAId !== worldPassage.zoneAId || geometry.zoneBId !== worldPassage.zoneBId) {
      throw new TypeError(`Station Zero spatial Passage ${passageId} endpoints diverge from World authority`);
    }
    const first = geometry.points[0];
    const last = geometry.points.at(-1);
    if (!first || !last || !pointInsideZone(first, layout.zones[worldPassage.zoneAId]!) || !pointInsideZone(last, layout.zones[worldPassage.zoneBId]!)) {
      throw new TypeError(`Station Zero spatial Passage ${passageId} does not connect its authoritative endpoint Zones`);
    }
  }
}

export function stationZeroV3SpatialLayout(): StationZeroV3SpatialLayout {
  return RETAINED_SPATIAL_LAYOUT;
}

export function stationZeroV3PassageVisibleToRescueTopology(
  passage: StationZeroV3WorldState["passages"][string],
): boolean {
  return !passage.tags.some((tag) => RESCUE_INACCESSIBLE_PASSAGE_TAGS.has(tag));
}

const RETAINED_SPATIAL_LAYOUT = parseSpatialLayout(JSON.parse(readFileSync(LAYOUT_URL, "utf8")));
