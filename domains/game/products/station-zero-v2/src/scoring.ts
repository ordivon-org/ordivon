import { isOperational } from "./scenario.ts";
import type { WorldState } from "./model.ts";

export interface MissionScore {
  total: number;
  components: {
    verifiedVictory: number;
    objectiveProgress: number;
    crewHealth: number;
    engineerHealth: number;
    oxygenReserve: number;
    batteryReserve: number;
    reactorSafety: number;
    operationalSystems: number;
    turnEfficiency: number;
  };
}

export function scoreMission(state: WorldState): MissionScore {
  const casualty = state.crew["crew-01"];
  const operationalCount = Object.values(state.systems).filter((system) =>
    isOperational(system.integrity),
  ).length;
  const objectiveCount = [
    state.hazards["maintenance-breach"]?.sealed ?? false,
    casualty?.stabilized ?? false,
    isOperational(state.systems.cooling?.integrity ?? 0),
    isOperational(state.systems["life-support"]?.integrity ?? 0),
    state.systems["life-support"]?.powered ?? false,
    isOperational(state.systems.communications?.integrity ?? 0),
    state.mission.distressSent,
  ].filter(Boolean).length;

  const components = {
    verifiedVictory: state.mission.status === "victory" ? 1_000 : 0,
    objectiveProgress: objectiveCount * 100,
    crewHealth: (casualty?.health ?? 0) * 2,
    engineerHealth: state.agents["engineer-01"]?.health ?? 0,
    oxygenReserve: state.resources.oxygen,
    batteryReserve: state.resources.batteryCharge * 2,
    reactorSafety: Math.max(0, 100 - state.resources.reactorHeat),
    operationalSystems: operationalCount * 75,
    turnEfficiency: Math.max(0, state.mission.turnLimit - state.turn) * 10,
  };

  return {
    total: Object.values(components).reduce((total, value) => total + value, 0),
    components,
  };
}
