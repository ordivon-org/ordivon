import { sha256 } from "../digest.ts";
import {
  STATION_ZERO_V3_COMMANDER_ABILITIES,
  STATION_ZERO_V3_EQUIPMENT,
  STATION_ZERO_V3_P0_CONTRACT,
  STATION_ZERO_V3_ITEMS,
  STATION_ZERO_V3_OBJECTIVES,
} from "./content.ts";
import type {
  StationZeroActorState,
  StationZeroFactionId,
  StationZeroFactionKnowledgeState,
  StationZeroFactionState,
  StationZeroGroundItemState,
  StationZeroKnownActorState,
  StationZeroObjectiveProgress,
  StationZeroPassageStateRecord,
  StationZeroRoomState,
  StationZeroV3WorldState,
  StationZeroZoneState,
} from "./model.ts";
import {
  STATION_ZERO_FACTION_IDS,
  STATION_ZERO_V3_RULESET_ID,
  STATION_ZERO_V3_RULESET_VERSION,
  STATION_ZERO_V3_SCENARIO_ID,
  STATION_ZERO_V3_SCENARIO_VERSION,
  STATION_ZERO_V3_WORLD_SCHEMA_VERSION,
} from "./model.ts";

function room(roomId: string, name: string, zoneIds: string[], tags: string[] = []): StationZeroRoomState {
  return { roomId, name, zoneIds, tags };
}

function zone(
  zoneId: string,
  roomId: string,
  name: string,
  cover: StationZeroZoneState["cover"],
  capacity: number,
  tags: string[] = [],
): StationZeroZoneState {
  return { zoneId, roomId, name, cover, capacity, tags };
}

function passage(
  passageId: string,
  zoneAId: string,
  zoneBId: string,
  lockable = true,
  tags: string[] = [],
): StationZeroPassageStateRecord {
  return { passageId, zoneAId, zoneBId, state: "open", lockable, tags };
}

function equipmentArmor(equipmentIds: string[]): number {
  return equipmentIds.reduce((total, equipmentId) =>
    total + (STATION_ZERO_V3_EQUIPMENT.find((entry) => entry.equipmentId === equipmentId)?.armor ?? 0), 0);
}

function abilityCooldowns(equipmentIds: string[]): Record<string, number> {
  const abilities = equipmentIds.flatMap((equipmentId) =>
    STATION_ZERO_V3_EQUIPMENT.find((entry) => entry.equipmentId === equipmentId)?.grantedAbilityIds ?? []);
  return Object.fromEntries([...new Set(abilities)].sort().map((abilityId) => [abilityId, 0]));
}

interface ActorInput {
  actorId: string;
  name: string;
  factionId: StationZeroFactionId | null;
  kind: StationZeroActorState["kind"];
  roleId: string;
  controllerKind: StationZeroActorState["controllerKind"];
  leaderActorId?: string | null;
  zoneId: string;
  health: number;
  initiative: number;
  movementRange: number;
  capabilityIds?: string[];
  traitIds?: string[];
  equipment?: StationZeroActorState["equipment"];
  inventoryItemIds?: string[];
}

function actor(input: ActorInput): StationZeroActorState {
  const equipment = { ...(input.equipment ?? {}) };
  const equipmentIds = Object.values(equipment);
  return {
    actorId: input.actorId,
    name: input.name,
    factionId: input.factionId,
    kind: input.kind,
    roleId: input.roleId,
    controllerKind: input.controllerKind,
    leaderActorId: input.leaderActorId ?? null,
    position: { zoneId: input.zoneId },
    lifeState: "active",
    health: input.health,
    maximumHealth: input.health,
    armor: equipmentArmor(equipmentIds),
    actionPoints: 2,
    maximumActionPoints: 2,
    initiative: input.initiative,
    movementRange: input.movementRange,
    capabilityIds: [...(input.capabilityIds ?? [])],
    traitIds: [...(input.traitIds ?? [])],
    equipment,
    inventoryItemIds: [...(input.inventoryItemIds ?? [])],
    abilityCooldowns: abilityCooldowns(equipmentIds),
    statusIds: [],
  };
}

function objectiveProgress(factionId: StationZeroFactionId): Record<string, StationZeroObjectiveProgress> {
  return Object.fromEntries(STATION_ZERO_V3_OBJECTIVES
    .filter((objective) => objective.factionId === factionId)
    .map((objective) => [objective.objectiveId, {
      objectiveId: objective.objectiveId,
      status: "active" as const,
      progress: 0,
      target: objective.requirementId.endsWith(":2") ? 2 : objective.requirementId.endsWith(":12") ? 12 : 1,
      reason: null,
    }]));
}

function commanderCharges(factionId: StationZeroFactionId): Record<string, number | null> {
  return Object.fromEntries(STATION_ZERO_V3_COMMANDER_ABILITIES
    .filter((ability) => ability.factionIds.includes(factionId))
    .map((ability) => [ability.commanderAbilityId, ability.maximumCharges]));
}

function commanderCooldowns(factionId: StationZeroFactionId): Record<string, number> {
  return Object.fromEntries(STATION_ZERO_V3_COMMANDER_ABILITIES
    .filter((ability) => ability.factionIds.includes(factionId))
    .map((ability) => [ability.commanderAbilityId, 0]));
}

function faction(
  factionId: StationZeroFactionId,
  name: string,
  controllerKind: StationZeroFactionState["controllerKind"],
): StationZeroFactionState {
  return {
    factionId,
    name,
    controllerKind,
    commandPoints: 3,
    maximumCommandPoints: 3,
    uplinkSlots: factionId === "rescue" ? 2 : 1,
    maximumUplinkSlots: factionId === "rescue" ? 2 : 1,
    commanderAbilityCharges: commanderCharges(factionId),
    commanderAbilityCooldowns: commanderCooldowns(factionId),
    objectiveProgress: objectiveProgress(factionId),
    outcome: "pending",
    outcomeReason: null,
  };
}

function knownActor(actor: StationZeroActorState): StationZeroKnownActorState {
  return {
    actorId: actor.actorId,
    lastKnownZoneId: actor.position.zoneId,
    observedLifeState: actor.lifeState,
    observedHealthBand: actor.health >= actor.maximumHealth * 0.75
      ? "healthy"
      : actor.health >= actor.maximumHealth * 0.35
        ? "wounded"
        : "critical",
    observedAtTurn: 0,
    confidence: "confirmed",
  };
}

function knowledge(
  factionId: StationZeroFactionId,
  actors: Record<string, StationZeroActorState>,
  discoveredRoomIds: string[],
  discoveredZoneIds: string[],
  knownEnemyActorIds: string[],
  knownSystemIds: string[],
  knownHazardIds: string[],
  knownGroundItemIds: string[],
  reportIds: string[],
): StationZeroFactionKnowledgeState {
  const actorIds = Object.values(actors)
    .filter((candidate) => candidate.factionId === factionId)
    .map((candidate) => candidate.actorId)
    .concat(knownEnemyActorIds);
  const knownActors = Object.fromEntries([...new Set(actorIds)].sort().map((actorId) => {
    const retained = actors[actorId];
    if (!retained) throw new Error(`Knowledge references unknown Actor ${actorId}`);
    return [actorId, knownActor(retained)];
  }));
  return {
    factionId,
    discoveredRoomIds: [...discoveredRoomIds],
    discoveredZoneIds: [...discoveredZoneIds],
    knownActors,
    knownSystemIds: [...knownSystemIds],
    knownHazardIds: [...knownHazardIds],
    knownGroundItemIds: [...knownGroundItemIds],
    reportIds: [...reportIds],
  };
}

export function createStationZeroV3Genesis(seed = "station-zero-v3-fixed-encounter"): StationZeroV3WorldState {
  const rooms = Object.fromEntries([
    room("command-center", "Command Center", ["command-deck", "rescue-airlock"], ["rescue-entry"]),
    room("power-junction", "Power Junction", ["junction-console", "junction-cover"], ["power"]),
    room("storage", "Storage", ["storage-floor", "crate-cover", "cargo-airlock"], ["loot", "pirate-entry"]),
    room("maintenance", "Maintenance", ["maintenance-entry", "maintenance-console", "maintenance-nest"], ["hazard", "swarm-entry"]),
    room("medical-bay", "Medical Bay", ["med-ward", "med-console"], ["civilian"]),
    room("reactor", "Reactor", ["reactor-entry", "reactor-console", "reactor-cover"], ["critical", "objective"]),
    room("communications", "Communications", ["comms-entry", "comms-console"], ["communications"]),
    room("life-support", "Life Support", ["life-entry", "life-console", "life-duct"], ["critical", "civilian"]),
  ].map((entry) => [entry.roomId, entry]));

  const zones = Object.fromEntries([
    zone("command-deck", "command-center", "Command Deck", "half", 3, ["console"]),
    zone("rescue-airlock", "command-center", "Rescue Airlock", "none", 3, ["extraction:rescue"]),
    zone("junction-console", "power-junction", "Power Console", "half", 2, ["console", "power"]),
    zone("junction-cover", "power-junction", "Junction Machinery", "full", 2, ["cover"]),
    zone("storage-floor", "storage", "Storage Floor", "none", 4, ["loot"]),
    zone("crate-cover", "storage", "Cargo Crates", "full", 2, ["cover", "loot"]),
    zone("cargo-airlock", "storage", "Cargo Airlock", "half", 3, ["extraction:pirate"]),
    zone("maintenance-entry", "maintenance", "Maintenance Entry", "half", 2, ["chokepoint"]),
    zone("maintenance-console", "maintenance", "Maintenance Console", "half", 2, ["console"]),
    zone("maintenance-nest", "maintenance", "Biomass Nest", "full", 4, ["nest", "extraction:swarm"]),
    zone("med-ward", "medical-bay", "Medical Ward", "half", 4, ["civilian"]),
    zone("med-console", "medical-bay", "Medical Console", "full", 2, ["console"]),
    zone("reactor-entry", "reactor", "Reactor Entry", "half", 2, ["chokepoint"]),
    zone("reactor-console", "reactor", "Reactor Console", "none", 2, ["console", "objective"]),
    zone("reactor-cover", "reactor", "Shielded Machinery", "full", 2, ["cover"]),
    zone("comms-entry", "communications", "Communications Entry", "half", 2, ["chokepoint"]),
    zone("comms-console", "communications", "Communications Console", "full", 2, ["console"]),
    zone("life-entry", "life-support", "Life Support Entry", "half", 2, ["chokepoint"]),
    zone("life-console", "life-support", "Life Support Console", "none", 2, ["console", "critical"]),
    zone("life-duct", "life-support", "Ventilation Duct", "full", 2, ["vent", "swarm-route"]),
  ].map((entry) => [entry.zoneId, entry]));

  const passages = Object.fromEntries([
    passage("passage:rescue-deck", "rescue-airlock", "command-deck", false, ["internal"]),
    passage("passage:deck-junction", "command-deck", "junction-console"),
    passage("passage:deck-reactor", "command-deck", "reactor-entry"),
    passage("passage:junction-machinery", "junction-console", "junction-cover", false, ["internal"]),
    passage("passage:junction-storage", "junction-cover", "storage-floor"),
    passage("passage:junction-comms", "junction-console", "comms-entry"),
    passage("passage:junction-med", "junction-cover", "med-console"),
    passage("passage:storage-crates", "storage-floor", "crate-cover", false, ["internal"]),
    passage("passage:storage-airlock", "crate-cover", "cargo-airlock", false, ["internal"]),
    passage("passage:storage-maintenance", "storage-floor", "maintenance-entry"),
    passage("passage:maintenance-console", "maintenance-entry", "maintenance-console", false, ["internal"]),
    passage("passage:maintenance-nest", "maintenance-entry", "maintenance-nest", false, ["internal"]),
    passage("passage:maintenance-life", "maintenance-console", "life-entry"),
    passage("passage:med-ward", "med-console", "med-ward", false, ["internal"]),
    passage("passage:reactor-console", "reactor-entry", "reactor-console", false, ["internal"]),
    passage("passage:reactor-cover", "reactor-entry", "reactor-cover", false, ["internal"]),
    passage("passage:comms-console", "comms-entry", "comms-console", false, ["internal"]),
    passage("passage:life-console", "life-entry", "life-console", false, ["internal"]),
    passage("passage:life-duct", "life-entry", "life-duct", false, ["vent"]),
    passage("passage:duct-nest", "life-duct", "maintenance-nest", false, ["vent", "swarm-route"]),
  ].map((entry) => [entry.passageId, entry]));

  const actors = Object.fromEntries([
    actor({
      actorId: "engineer-imani",
      name: "Engineer Imani",
      factionId: "rescue",
      kind: "specialist",
      roleId: "engineer",
      controllerKind: "agent",
      zoneId: "rescue-airlock",
      health: 100,
      initiative: 55,
      movementRange: 2,
      capabilityIds: ["repair", "power-control", "seal-hazard"],
      traitIds: ["field-autonomy", "risk-aware"],
      equipment: { weapon: "rescue-pulse-rifle", armor: "rescue-armor", utility: "engineering-kit" },
      inventoryItemIds: ["spare-parts"],
    }),
    actor({
      actorId: "medic-reyes",
      name: "Medic Reyes",
      factionId: "rescue",
      kind: "specialist",
      roleId: "medic",
      controllerKind: "agent",
      zoneId: "rescue-airlock",
      health: 90,
      initiative: 60,
      movementRange: 2,
      capabilityIds: ["stabilize", "rescue-civilian"],
      traitIds: ["crew-first", "refuses-abandonment"],
      equipment: { weapon: "rescue-pulse-rifle", armor: "rescue-armor", utility: "medical-drone" },
      inventoryItemIds: ["medkit"],
    }),
    actor({
      actorId: "security-chen",
      name: "Security Chen",
      factionId: "rescue",
      kind: "specialist",
      roleId: "security",
      controllerKind: "agent",
      zoneId: "command-deck",
      health: 110,
      initiative: 65,
      movementRange: 2,
      capabilityIds: ["capture", "protect", "overwatch"],
      traitIds: ["containment-first", "disciplined"],
      equipment: { weapon: "security-burst-rifle", armor: "rescue-armor" },
    }),
    actor({
      actorId: "pirate-captain-veyra",
      name: "Captain Veyra",
      factionId: "pirate",
      kind: "pirate",
      roleId: "captain",
      controllerKind: "agent",
      zoneId: "cargo-airlock",
      health: 110,
      initiative: 62,
      movementRange: 2,
      capabilityIds: ["capture", "command-pirates", "loot"],
      traitIds: ["opportunist", "crew-preservation"],
      equipment: { weapon: "pirate-scattergun", armor: "boarding-armor" },
    }),
    actor({
      actorId: "pirate-hacker-nyx",
      name: "Hacker Nyx",
      factionId: "pirate",
      kind: "pirate",
      roleId: "hacker",
      controllerKind: "policy",
      leaderActorId: "pirate-captain-veyra",
      zoneId: "storage-floor",
      health: 80,
      initiative: 70,
      movementRange: 2,
      capabilityIds: ["hack", "loot"],
      traitIds: ["core-first", "avoids-melee"],
      equipment: { weapon: "pirate-shock-baton", armor: "boarding-armor", utility: "intrusion-rig" },
    }),
    actor({
      actorId: "pirate-raider-holt",
      name: "Raider Holt",
      factionId: "pirate",
      kind: "pirate",
      roleId: "raider",
      controllerKind: "policy",
      leaderActorId: "pirate-captain-veyra",
      zoneId: "crate-cover",
      health: 100,
      initiative: 58,
      movementRange: 2,
      capabilityIds: ["capture", "loot", "guard"],
      traitIds: ["aggressive", "vengeful"],
      equipment: { weapon: "pirate-scattergun", armor: "boarding-armor" },
    }),
    actor({
      actorId: "hive-alpha",
      name: "Hive Alpha",
      factionId: "swarm",
      kind: "creature",
      roleId: "hive-mind",
      controllerKind: "agent",
      zoneId: "maintenance-nest",
      health: 150,
      initiative: 50,
      movementRange: 2,
      capabilityIds: ["command-swarm", "devour", "infect", "spawn"],
      traitIds: ["biomass-hunger", "preserve-brood"],
      equipment: { biology: "hive-alpha-organs" },
    }),
    actor({
      actorId: "swarm-stalker-kappa",
      name: "Stalker Kappa",
      factionId: "swarm",
      kind: "creature",
      roleId: "stalker",
      controllerKind: "policy",
      leaderActorId: "hive-alpha",
      zoneId: "life-duct",
      health: 85,
      initiative: 75,
      movementRange: 3,
      capabilityIds: ["devour", "ambush"],
      traitIds: ["isolated-prey", "avoids-group-fire"],
      equipment: { biology: "stalker-organs" },
    }),
    actor({
      actorId: "swarm-drone-one",
      name: "Swarm Drone One",
      factionId: "swarm",
      kind: "creature",
      roleId: "drone",
      controllerKind: "policy",
      leaderActorId: "hive-alpha",
      zoneId: "maintenance-entry",
      health: 55,
      initiative: 45,
      movementRange: 2,
      capabilityIds: ["guard", "devour"],
      traitIds: ["expendable"],
      equipment: { biology: "drone-organs" },
    }),
    actor({
      actorId: "swarm-drone-two",
      name: "Swarm Drone Two",
      factionId: "swarm",
      kind: "creature",
      roleId: "drone",
      controllerKind: "policy",
      leaderActorId: "hive-alpha",
      zoneId: "maintenance-console",
      health: 55,
      initiative: 44,
      movementRange: 2,
      capabilityIds: ["guard", "infect"],
      traitIds: ["expendable"],
      equipment: { biology: "drone-organs" },
    }),
    actor({
      actorId: "civilian-sato",
      name: "Navigator Sato",
      factionId: null,
      kind: "civilian",
      roleId: "navigator",
      controllerKind: "none",
      zoneId: "med-ward",
      health: 45,
      initiative: 20,
      movementRange: 1,
      capabilityIds: [],
      traitIds: ["injured"],
    }),
    actor({
      actorId: "civilian-kade",
      name: "Researcher Kade",
      factionId: null,
      kind: "civilian",
      roleId: "researcher",
      controllerKind: "none",
      zoneId: "life-console",
      health: 65,
      initiative: 25,
      movementRange: 1,
      capabilityIds: ["identify-research-core"],
      traitIds: ["panicked"],
    }),
  ].map((entry) => [entry.actorId, entry]));

  const groundItemEntries: StationZeroGroundItemState[] = [
    { groundItemId: "ground:research-core", itemId: "research-core", zoneId: "reactor-console", quantity: 1, ownerFactionId: null },
    { groundItemId: "ground:medkit", itemId: "medkit", zoneId: "med-ward", quantity: 1, ownerFactionId: null },
    { groundItemId: "ground:spare-parts", itemId: "spare-parts", zoneId: "crate-cover", quantity: 2, ownerFactionId: null },
    { groundItemId: "ground:sealant", itemId: "sealant", zoneId: "maintenance-console", quantity: 1, ownerFactionId: null },
    { groundItemId: "ground:pirate-scattergun", itemId: "pirate-scattergun-item", zoneId: "storage-floor", quantity: 1, ownerFactionId: "pirate" },
  ];
  const groundItems = Object.fromEntries(groundItemEntries.map((entry) => [entry.groundItemId, entry]));

  const state: StationZeroV3WorldState = {
    schemaVersion: STATION_ZERO_V3_WORLD_SCHEMA_VERSION,
    scenarioId: STATION_ZERO_V3_SCENARIO_ID,
    scenarioVersion: STATION_ZERO_V3_SCENARIO_VERSION,
    rulesetId: STATION_ZERO_V3_RULESET_ID,
    rulesetVersion: STATION_ZERO_V3_RULESET_VERSION,
    seed,
    revision: 0,
    rooms,
    zones,
    passages,
    actors,
    groundItems,
    systems: {
      "power-grid": { systemId: "power-grid", name: "Power Grid", zoneId: "junction-console", integrity: 0.72, powered: true, powerDraw: 0, tags: ["power", "critical"] },
      cooling: { systemId: "cooling", name: "Cooling", zoneId: "reactor-console", integrity: 0.58, powered: false, powerDraw: 3, tags: ["reactor", "critical"] },
      communications: { systemId: "communications", name: "Communications", zoneId: "comms-console", integrity: 0.64, powered: false, powerDraw: 2, tags: ["knowledge", "extraction"] },
      "life-support": { systemId: "life-support", name: "Life Support", zoneId: "life-console", integrity: 0.7, powered: true, powerDraw: 2, tags: ["oxygen", "critical"] },
    },
    hazards: {
      "maintenance-breach": { hazardId: "maintenance-breach", name: "Hull Breach", zoneId: "maintenance-entry", severity: 3, contained: false, tags: ["oxygen", "passage"] },
      "biomass-nest": { hazardId: "biomass-nest", name: "Biomass Nest", zoneId: "maintenance-nest", severity: 2, contained: false, tags: ["swarm", "spawn"] },
      "reactor-instability": { hazardId: "reactor-instability", name: "Reactor Instability", zoneId: "reactor-console", severity: 2, contained: false, tags: ["heat", "critical"] },
    },
    factions: {
      rescue: faction("rescue", "Emergency Response Team", "player"),
      pirate: faction("pirate", "Veyra Boarding Crew", "agent"),
      swarm: faction("swarm", "Station Brood", "agent"),
    },
    factionKnowledge: {
      rescue: knowledge(
        "rescue",
        actors,
        ["command-center", "power-junction", "medical-bay"],
        ["rescue-airlock", "command-deck", "junction-console", "junction-cover", "med-console", "med-ward"],
        [],
        ["power-grid"],
        [],
        ["ground:medkit"],
        ["report:distress-signal", "report:unknown-life-signs"],
      ),
      pirate: knowledge(
        "pirate",
        actors,
        ["storage", "communications", "reactor"],
        ["cargo-airlock", "crate-cover", "storage-floor", "comms-entry", "comms-console", "reactor-entry", "reactor-console"],
        ["civilian-kade"],
        ["communications", "cooling"],
        ["reactor-instability"],
        ["ground:research-core", "ground:pirate-scattergun"],
        ["report:research-core-location", "report:rescue-ship-inbound"],
      ),
      swarm: knowledge(
        "swarm",
        actors,
        ["maintenance", "life-support"],
        ["maintenance-entry", "maintenance-console", "maintenance-nest", "life-entry", "life-console", "life-duct"],
        ["civilian-kade"],
        ["life-support"],
        ["maintenance-breach", "biomass-nest"],
        [],
        ["report:nearby-biomass", "report:metal-intruders"],
      ),
    },
    environment: {
      batteryInitial: 48,
      batteryCharge: 48,
      energyConsumed: 0,
      oxygen: 68,
      reactorHeat: 62,
      biomass: 4,
      alertLevel: 2,
    },
    encounter: {
      encounterId: "encounter:station-zero-v3:fixed",
      title: "Station Zero: Contested Signal",
      playerFactionId: "rescue",
      status: "running",
      reason: null,
      turn: 0,
      turnLimit: STATION_ZERO_V3_P0_CONTRACT.runBoundary.turnLimit,
      phase: "situation",
      activePlanRevision: 0,
    },
  };
  assertStationZeroV3World(state);
  return state;
}

function assertBounded(value: number, label: string, minimum: number, maximum: number): void {
  if (!Number.isFinite(value) || value < minimum || value > maximum) {
    throw new TypeError(`${label} must be between ${minimum} and ${maximum}`);
  }
}

function assertUnique(values: string[], label: string): void {
  if (new Set(values).size !== values.length) throw new TypeError(`${label} contains duplicate identities`);
}

export function assertStationZeroV3World(state: StationZeroV3WorldState): void {
  if (state.schemaVersion !== 3 || state.scenarioId !== "station-zero" || state.scenarioVersion !== 3 ||
      state.rulesetId !== "station-zero-core" || state.rulesetVersion !== 4) {
    throw new TypeError("Station Zero v3 contract identity mismatch");
  }
  if (!Number.isSafeInteger(state.revision) || state.revision < 0) throw new TypeError("World revision must be non-negative");
  if (!Number.isSafeInteger(state.encounter.turn) || state.encounter.turn < 0) throw new TypeError("Encounter turn must be non-negative");
  if (!Number.isSafeInteger(state.encounter.turnLimit) || state.encounter.turnLimit < 1) throw new TypeError("Encounter turn limit must be positive");
  if (state.encounter.playerFactionId !== "rescue") throw new TypeError("P0 fixed Encounter player faction must be rescue");

  assertUnique(Object.keys(state.rooms), "Room map");
  assertUnique(Object.keys(state.zones), "Zone map");
  assertUnique(Object.keys(state.passages), "Passage map");
  assertUnique(Object.keys(state.actors), "Actor map");
  assertUnique(Object.keys(state.groundItems), "Ground Item map");

  for (const roomState of Object.values(state.rooms)) {
    if (roomState.roomId.length === 0 || state.rooms[roomState.roomId] !== roomState) throw new TypeError("Room identity mismatch");
    if (roomState.zoneIds.length < 2) throw new TypeError(`Room ${roomState.roomId} requires at least two tactical Zones`);
    assertUnique(roomState.zoneIds, `Room ${roomState.roomId} Zones`);
    for (const zoneId of roomState.zoneIds) {
      if (state.zones[zoneId]?.roomId !== roomState.roomId) throw new TypeError(`Room ${roomState.roomId} references invalid Zone ${zoneId}`);
    }
  }
  for (const zoneState of Object.values(state.zones)) {
    if (!state.rooms[zoneState.roomId]?.zoneIds.includes(zoneState.zoneId)) throw new TypeError(`Zone ${zoneState.zoneId} has no owning Room`);
    if (!Number.isSafeInteger(zoneState.capacity) || zoneState.capacity < 1) throw new TypeError(`Zone ${zoneState.zoneId} capacity must be positive`);
  }
  for (const retained of Object.values(state.passages)) {
    if (!state.zones[retained.zoneAId] || !state.zones[retained.zoneBId] || retained.zoneAId === retained.zoneBId) {
      throw new TypeError(`Passage ${retained.passageId} references invalid Zones`);
    }
  }

  const equipmentIds = new Set(STATION_ZERO_V3_EQUIPMENT.map((entry) => entry.equipmentId));
  const itemIds = new Set(STATION_ZERO_V3_ITEMS.map((entry) => entry.itemId));
  for (const retained of Object.values(state.actors)) {
    if (!state.zones[retained.position.zoneId]) throw new TypeError(`Actor ${retained.actorId} has invalid position`);
    if (retained.factionId !== null && !STATION_ZERO_FACTION_IDS.includes(retained.factionId)) throw new TypeError(`Actor ${retained.actorId} has invalid Faction`);
    if (retained.kind === "civilian" && retained.factionId !== null) throw new TypeError(`Civilian ${retained.actorId} must be neutral in P0`);
    if (retained.factionId === null && retained.controllerKind !== "none") throw new TypeError(`Neutral Actor ${retained.actorId} must not have a controller`);
    if (retained.leaderActorId !== null && state.actors[retained.leaderActorId]?.factionId !== retained.factionId) {
      throw new TypeError(`Actor ${retained.actorId} has invalid leader`);
    }
    assertBounded(retained.health, `${retained.actorId}.health`, 0, retained.maximumHealth);
    if (!Number.isSafeInteger(retained.actionPoints) || retained.actionPoints < 0 || retained.actionPoints > retained.maximumActionPoints) {
      throw new TypeError(`Actor ${retained.actorId} Action Points are invalid`);
    }
    for (const equipmentId of Object.values(retained.equipment)) {
      if (!equipmentIds.has(equipmentId)) throw new TypeError(`Actor ${retained.actorId} has unknown Equipment ${equipmentId}`);
    }
    for (const itemId of retained.inventoryItemIds) {
      if (!itemIds.has(itemId)) throw new TypeError(`Actor ${retained.actorId} has unknown Item ${itemId}`);
    }
  }

  const occupiedByZone = new Map<string, number>();
  for (const retained of Object.values(state.actors).filter((candidate) => candidate.lifeState === "active")) {
    occupiedByZone.set(retained.position.zoneId, (occupiedByZone.get(retained.position.zoneId) ?? 0) + 1);
  }
  for (const [zoneId, count] of occupiedByZone) {
    if (count > (state.zones[zoneId]?.capacity ?? 0)) throw new TypeError(`Zone ${zoneId} starts above capacity`);
  }

  for (const retained of Object.values(state.groundItems)) {
    if (!state.zones[retained.zoneId]) throw new TypeError(`Ground Item ${retained.groundItemId} has invalid Zone`);
    if (!itemIds.has(retained.itemId)) throw new TypeError(`Ground Item ${retained.groundItemId} has unknown Item`);
    if (!Number.isSafeInteger(retained.quantity) || retained.quantity < 1) throw new TypeError(`Ground Item ${retained.groundItemId} quantity must be positive`);
  }
  for (const retained of Object.values(state.systems)) {
    if (!state.zones[retained.zoneId]) throw new TypeError(`System ${retained.systemId} has invalid Zone`);
    assertBounded(retained.integrity, `${retained.systemId}.integrity`, 0, 1);
    if (!Number.isSafeInteger(retained.powerDraw) || retained.powerDraw < 0) throw new TypeError(`System ${retained.systemId} power draw must be non-negative`);
  }
  for (const retained of Object.values(state.hazards)) {
    if (!state.zones[retained.zoneId]) throw new TypeError(`Hazard ${retained.hazardId} has invalid Zone`);
    if (!Number.isSafeInteger(retained.severity) || retained.severity < 0 || retained.severity > 5) throw new TypeError(`Hazard ${retained.hazardId} severity is invalid`);
  }

  for (const factionId of STATION_ZERO_FACTION_IDS) {
    const factionState = state.factions[factionId];
    const factionKnowledge = state.factionKnowledge[factionId];
    if (factionState.factionId !== factionId || factionKnowledge.factionId !== factionId) throw new TypeError(`Faction ${factionId} identity mismatch`);
    if (!Number.isSafeInteger(factionState.commandPoints) || factionState.commandPoints < 0 || factionState.commandPoints > factionState.maximumCommandPoints) {
      throw new TypeError(`Faction ${factionId} Command Points are invalid`);
    }
    if (!Number.isSafeInteger(factionState.uplinkSlots) || factionState.uplinkSlots < 0 || factionState.uplinkSlots > factionState.maximumUplinkSlots) {
      throw new TypeError(`Faction ${factionId} Uplink Slots are invalid`);
    }
    const objectives = STATION_ZERO_V3_OBJECTIVES.filter((entry) => entry.factionId === factionId);
    if (Object.keys(factionState.objectiveProgress).length !== objectives.length) throw new TypeError(`Faction ${factionId} Objective Progress is incomplete`);
    for (const objective of objectives) {
      if (!factionState.objectiveProgress[objective.objectiveId]) throw new TypeError(`Faction ${factionId} lacks Objective ${objective.objectiveId}`);
    }
    const ownActors = Object.values(state.actors).filter((retained) => retained.factionId === factionId);
    for (const ownActor of ownActors) {
      if (!factionKnowledge.knownActors[ownActor.actorId]) throw new TypeError(`Faction ${factionId} does not know its own Actor ${ownActor.actorId}`);
    }
    for (const roomId of factionKnowledge.discoveredRoomIds) if (!state.rooms[roomId]) throw new TypeError(`Faction ${factionId} knows invalid Room ${roomId}`);
    for (const zoneId of factionKnowledge.discoveredZoneIds) if (!state.zones[zoneId]) throw new TypeError(`Faction ${factionId} knows invalid Zone ${zoneId}`);
    for (const [actorId, known] of Object.entries(factionKnowledge.knownActors)) {
      if (!state.actors[actorId] || !state.zones[known.lastKnownZoneId]) throw new TypeError(`Faction ${factionId} knows invalid Actor state ${actorId}`);
    }
  }

  assertBounded(state.environment.oxygen, "oxygen", 0, 100);
  assertBounded(state.environment.reactorHeat, "reactorHeat", 0, 100);
  if (!Number.isSafeInteger(state.environment.batteryInitial) || state.environment.batteryInitial < 1) throw new TypeError("Battery initial must be positive");
  if (!Number.isSafeInteger(state.environment.batteryCharge) || state.environment.batteryCharge < 0) throw new TypeError("Battery charge must be non-negative");
  if (!Number.isSafeInteger(state.environment.energyConsumed) || state.environment.energyConsumed < 0) throw new TypeError("Energy consumed must be non-negative");
  if (state.environment.batteryCharge + state.environment.energyConsumed !== state.environment.batteryInitial) {
    throw new TypeError("Battery ledger is not conserved");
  }
  if (!Number.isSafeInteger(state.environment.biomass) || state.environment.biomass < 0) throw new TypeError("Biomass must be non-negative");
  if (!Number.isSafeInteger(state.environment.alertLevel) || state.environment.alertLevel < 0 || state.environment.alertLevel > 5) throw new TypeError("Alert Level is invalid");
}

export function stationZeroV3GenesisDigest(seed?: string): string {
  return sha256(createStationZeroV3Genesis(seed));
}
