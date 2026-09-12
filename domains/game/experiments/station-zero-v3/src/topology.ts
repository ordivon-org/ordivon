import type { StationZeroFactionId, StationZeroV3WorldState } from "./model.ts";

function passageAllowsFaction(
  passage: StationZeroV3WorldState["passages"][string],
  factionId: StationZeroFactionId | null,
): boolean {
  if (passage.state !== "open") return false;
  if (passage.tags.includes("swarm-route") || passage.tags.includes("vent")) {
    return factionId === "swarm";
  }
  return true;
}

export function stationZeroAdjacentZones(
  state: StationZeroV3WorldState,
  zoneId: string,
  factionId: StationZeroFactionId | null,
): string[] {
  if (!state.zones[zoneId]) return [];
  return Object.values(state.passages)
    .filter((passage) => passageAllowsFaction(passage, factionId))
    .flatMap((passage) => {
      if (passage.zoneAId === zoneId) return [passage.zoneBId];
      if (passage.zoneBId === zoneId) return [passage.zoneAId];
      return [];
    })
    .sort();
}

export function stationZeroShortestDistance(
  state: StationZeroV3WorldState,
  fromZoneId: string,
  toZoneId: string,
  factionId: StationZeroFactionId | null,
): number | null {
  if (!state.zones[fromZoneId] || !state.zones[toZoneId]) return null;
  if (fromZoneId === toZoneId) return 0;
  const visited = new Set([fromZoneId]);
  let frontier = [fromZoneId];
  let distance = 0;
  while (frontier.length > 0) {
    distance += 1;
    const next: string[] = [];
    for (const zoneId of frontier.sort()) {
      for (const neighbor of stationZeroAdjacentZones(state, zoneId, factionId)) {
        if (visited.has(neighbor)) continue;
        if (neighbor === toZoneId) return distance;
        visited.add(neighbor);
        next.push(neighbor);
      }
    }
    frontier = next;
  }
  return null;
}

export function stationZeroVisibleZonesFrom(
  state: StationZeroV3WorldState,
  originZoneIds: string[],
  factionId: StationZeroFactionId,
): string[] {
  const visible = new Set<string>();
  for (const zoneId of [...originZoneIds].sort()) {
    if (!state.zones[zoneId]) continue;
    visible.add(zoneId);
    for (const neighbor of stationZeroAdjacentZones(state, zoneId, factionId)) visible.add(neighbor);
  }
  return [...visible].sort();
}

export function stationZeroShortestPath(
  state: StationZeroV3WorldState,
  fromZoneId: string,
  toZoneId: string,
  factionId: StationZeroFactionId | null,
): string[] | null {
  if (!state.zones[fromZoneId] || !state.zones[toZoneId]) return null;
  if (fromZoneId === toZoneId) return [fromZoneId];
  const queue = [fromZoneId];
  const previous = new Map<string, string | null>([[fromZoneId, null]]);
  while (queue.length > 0) {
    const current = queue.shift()!;
    for (const neighbor of stationZeroAdjacentZones(state, current, factionId)) {
      if (previous.has(neighbor)) continue;
      previous.set(neighbor, current);
      if (neighbor === toZoneId) {
        const path = [toZoneId];
        let cursor: string | null = current;
        while (cursor !== null) {
          path.push(cursor);
          cursor = previous.get(cursor) ?? null;
        }
        return path.reverse();
      }
      queue.push(neighbor);
    }
  }
  return null;
}

export function stationZeroMovementStepToward(
  state: StationZeroV3WorldState,
  fromZoneId: string,
  toZoneId: string,
  factionId: StationZeroFactionId | null,
  movementRange: number,
): string | null {
  const path = stationZeroShortestPath(state, fromZoneId, toZoneId, factionId);
  if (!path || path.length < 2 || movementRange < 1) return null;
  return path[Math.min(movementRange, path.length - 1)] ?? null;
}
