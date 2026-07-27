import { ITEM_IDS, inventory, type ItemId, type WorldState } from "./model.ts";

export const POWER_JUNCTION_ID = "power-junction";
export const ENGINEER_ID = "engineer-01";

export function initialWorld(): WorldState {
  const initialItems = inventory({
    toolkit: 1,
    "breaker-key": 1,
    "spare-parts": 3,
    sealant: 1,
    medkit: 1,
  });

  return {
    schemaVersion: 2,
    scenarioId: "station-zero-m1",
    seed: "station-zero-fixed-seed-01",
    revision: 0,
    turn: 0,
    rooms: {
      "command-center": {
        id: "command-center",
        name: "Command Center",
        neighbors: [POWER_JUNCTION_ID],
        inventory: inventory(),
      },
      [POWER_JUNCTION_ID]: {
        id: POWER_JUNCTION_ID,
        name: "Power Junction",
        neighbors: [
          "command-center",
          "storage",
          "medical-bay",
          "reactor",
          "communications",
          "life-support",
        ],
        inventory: inventory(),
      },
      storage: {
        id: "storage",
        name: "Storage",
        neighbors: [POWER_JUNCTION_ID, "maintenance"],
        inventory: inventory({ "spare-parts": 2, sealant: 1 }),
      },
      maintenance: {
        id: "maintenance",
        name: "Maintenance Bay",
        neighbors: ["storage", "life-support"],
        inventory: inventory(),
      },
      "medical-bay": {
        id: "medical-bay",
        name: "Medical Bay",
        neighbors: [POWER_JUNCTION_ID],
        inventory: inventory({ medkit: 1 }),
      },
      reactor: {
        id: "reactor",
        name: "Reactor Room",
        neighbors: [POWER_JUNCTION_ID],
        inventory: inventory(),
      },
      communications: {
        id: "communications",
        name: "Communications",
        neighbors: [POWER_JUNCTION_ID],
        inventory: inventory(),
      },
      "life-support": {
        id: "life-support",
        name: "Life Support",
        neighbors: [POWER_JUNCTION_ID, "maintenance"],
        inventory: inventory(),
      },
    },
    agents: {
      [ENGINEER_ID]: {
        id: ENGINEER_ID,
        name: "Engineer Imani",
        location: "command-center",
        health: 100,
        capabilities: [
          "move",
          "pickup_item",
          "repair_system",
          "set_power",
          "seal_hull",
          "basic_first_aid",
          "send_distress",
          "wait",
        ],
        inventory: inventory({ toolkit: 1, "breaker-key": 1, "spare-parts": 1 }),
      },
    },
    crew: {
      "crew-01": {
        id: "crew-01",
        name: "Navigator Sato",
        location: "medical-bay",
        health: 50,
        stabilized: false,
      },
    },
    systems: {
      cooling: {
        id: "cooling",
        name: "Reactor Cooling",
        roomId: "reactor",
        integrity: 0.35,
        powered: false,
        powerDraw: 2,
        repairParts: 1,
      },
      "life-support": {
        id: "life-support",
        name: "Life Support Circulation",
        roomId: "life-support",
        integrity: 0.35,
        powered: false,
        powerDraw: 2,
        repairParts: 1,
      },
      communications: {
        id: "communications",
        name: "Long-range Communications",
        roomId: "communications",
        integrity: 0.35,
        powered: false,
        powerDraw: 2,
        repairParts: 1,
      },
    },
    hazards: {
      "maintenance-breach": {
        id: "maintenance-breach",
        name: "Maintenance Hull Breach",
        roomId: "maintenance",
        sealed: false,
      },
    },
    resources: {
      batteryInitial: 56,
      batteryCharge: 56,
      energyConsumed: 0,
      oxygen: 78,
      reactorHeat: 40,
      initialItems,
      consumedItems: inventory(),
    },
    mission: {
      status: "running",
      reason: null,
      distressSent: false,
      turnLimit: 28,
    },
  };
}

export function isOperational(integrity: number): boolean {
  return integrity >= 0.8;
}

export function currentItemTotal(state: WorldState, itemId: ItemId): number {
  let total = state.resources.consumedItems[itemId];
  for (const room of Object.values(state.rooms)) total += room.inventory[itemId];
  for (const agent of Object.values(state.agents)) total += agent.inventory[itemId];
  return total;
}

export function assertWorldInvariants(state: WorldState): void {
  if (state.schemaVersion !== 2) throw new Error("unsupported world schema");
  if (!Number.isSafeInteger(state.revision) || state.revision < 0) throw new Error("invalid revision");
  if (!Number.isSafeInteger(state.turn) || state.turn < 0) throw new Error("invalid turn");
  if (state.turn !== state.revision) throw new Error("turn and revision diverged");

  for (const room of Object.values(state.rooms)) {
    for (const neighborId of room.neighbors) {
      const neighbor = state.rooms[neighborId];
      if (!neighbor) throw new Error(`unknown room neighbor: ${neighborId}`);
      if (!neighbor.neighbors.includes(room.id)) {
        throw new Error(`asymmetric room edge: ${room.id} -> ${neighborId}`);
      }
    }
  }

  for (const agent of Object.values(state.agents)) {
    if (!state.rooms[agent.location]) throw new Error(`agent in unknown room: ${agent.id}`);
    if (agent.health < 0 || agent.health > 100) throw new Error(`invalid agent health: ${agent.id}`);
  }

  for (const crew of Object.values(state.crew)) {
    if (!state.rooms[crew.location]) throw new Error(`crew in unknown room: ${crew.id}`);
    if (crew.health < 0 || crew.health > 100) throw new Error(`invalid crew health: ${crew.id}`);
  }

  for (const system of Object.values(state.systems)) {
    if (!state.rooms[system.roomId]) throw new Error(`system in unknown room: ${system.id}`);
    if (system.integrity < 0 || system.integrity > 1) throw new Error(`invalid integrity: ${system.id}`);
    if (system.powerDraw < 0) throw new Error(`invalid power draw: ${system.id}`);
    if (system.powered && !isOperational(system.integrity)) {
      throw new Error(`damaged system is powered: ${system.id}`);
    }
  }

  for (const hazard of Object.values(state.hazards)) {
    if (!state.rooms[hazard.roomId]) throw new Error(`hazard in unknown room: ${hazard.id}`);
  }

  const resources = state.resources;
  if (resources.batteryCharge < 0 || resources.batteryCharge > resources.batteryInitial) {
    throw new Error("invalid battery charge");
  }
  if (resources.energyConsumed < 0) throw new Error("invalid consumed energy");
  if (resources.batteryCharge + resources.energyConsumed !== resources.batteryInitial) {
    throw new Error("energy ledger does not conserve initial battery energy");
  }
  if (resources.oxygen < 0 || resources.oxygen > 100) throw new Error("invalid oxygen");
  if (resources.reactorHeat < 0 || resources.reactorHeat > 100) throw new Error("invalid reactor heat");

  for (const itemId of ITEM_IDS) {
    const expected = resources.initialItems[itemId];
    const consumed = resources.consumedItems[itemId];
    if (!Number.isSafeInteger(expected) || expected < 0) {
      throw new Error(`invalid initial item quantity for ${itemId}`);
    }
    if (!Number.isSafeInteger(consumed) || consumed < 0) {
      throw new Error(`invalid consumed item quantity for ${itemId}`);
    }
    const actual = currentItemTotal(state, itemId);
    if (actual !== expected) {
      throw new Error(`item ledger mismatch for ${itemId}: expected ${expected}, got ${actual}`);
    }

    for (const room of Object.values(state.rooms)) {
      if (!Number.isSafeInteger(room.inventory[itemId]) || room.inventory[itemId] < 0) {
        throw new Error(`invalid room inventory for ${itemId}`);
      }
    }
    for (const agent of Object.values(state.agents)) {
      if (!Number.isSafeInteger(agent.inventory[itemId]) || agent.inventory[itemId] < 0) {
        throw new Error(`invalid agent inventory for ${itemId}`);
      }
    }
  }

  if (state.mission.status === "running" && state.mission.reason !== null) {
    throw new Error("running mission cannot have a terminal reason");
  }
  if (state.mission.status !== "running" && state.mission.reason === null) {
    throw new Error("terminal mission requires a reason");
  }
}

function clamp(value: number, minimum: number, maximum: number): number {
  return Math.min(maximum, Math.max(minimum, value));
}

export function advanceEnvironment(state: WorldState): void {
  const poweredSystems = Object.values(state.systems).filter((system) => system.powered);
  const requestedDraw = poweredSystems.reduce((total, system) => total + system.powerDraw, 0);

  if (requestedDraw > state.resources.batteryCharge) {
    state.resources.energyConsumed += state.resources.batteryCharge;
    state.resources.batteryCharge = 0;
    for (const system of poweredSystems) system.powered = false;
  } else {
    state.resources.batteryCharge -= requestedDraw;
    state.resources.energyConsumed += requestedDraw;
  }

  const lifeSupport = state.systems["life-support"];
  const cooling = state.systems.cooling;
  const breach = state.hazards["maintenance-breach"];
  if (!lifeSupport || !cooling || !breach) throw new Error("scenario critical objects are missing");

  const oxygenDelta =
    -2 +
    (breach.sealed ? 0 : -2) +
    (lifeSupport.powered && isOperational(lifeSupport.integrity) ? 5 : 0);
  state.resources.oxygen = clamp(state.resources.oxygen + oxygenDelta, 0, 100);

  const heatDelta = cooling.powered && isOperational(cooling.integrity) ? -8 : 6;
  state.resources.reactorHeat = clamp(state.resources.reactorHeat + heatDelta, 0, 100);

  for (const crew of Object.values(state.crew)) {
    if (!crew.stabilized) crew.health = clamp(crew.health - 2, 0, 100);
    if (state.resources.oxygen < 25) crew.health = clamp(crew.health - 4, 0, 100);
  }

  for (const agent of Object.values(state.agents)) {
    if (state.resources.oxygen < 30) agent.health = clamp(agent.health - 8, 0, 100);
    else if (state.resources.oxygen < 45) agent.health = clamp(agent.health - 3, 0, 100);
    if (agent.location === "reactor" && state.resources.reactorHeat > 85) {
      agent.health = clamp(agent.health - 5, 0, 100);
    }
  }
}

export function evaluateMission(state: WorldState): void {
  const engineer = state.agents[ENGINEER_ID];
  const casualty = state.crew["crew-01"];
  const cooling = state.systems.cooling;
  const lifeSupport = state.systems["life-support"];
  const breach = state.hazards["maintenance-breach"];
  if (!engineer || !casualty || !cooling || !lifeSupport || !breach) {
    throw new Error("scenario critical objects are missing");
  }

  const fail = (reason: string): void => {
    state.mission.status = "failure";
    state.mission.reason = reason;
  };

  if (state.resources.reactorHeat >= 100) return fail("reactor_meltdown");
  if (state.resources.oxygen <= 0) return fail("station_asphyxiation");
  if (casualty.health <= 0) return fail("crew_lost");
  if (engineer.health <= 0) return fail("engineer_incapacitated");

  const victory =
    state.mission.distressSent &&
    casualty.stabilized &&
    breach.sealed &&
    isOperational(cooling.integrity) &&
    isOperational(lifeSupport.integrity) &&
    lifeSupport.powered &&
    state.resources.oxygen >= 35 &&
    state.resources.reactorHeat <= 80;

  if (victory) {
    state.mission.status = "victory";
    state.mission.reason = "rescue_signal_verified";
    return;
  }

  if (state.resources.batteryCharge <= 0) return fail("power_exhausted");
  if (state.turn >= state.mission.turnLimit) return fail("mission_timeout");
}
