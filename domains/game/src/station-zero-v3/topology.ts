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
