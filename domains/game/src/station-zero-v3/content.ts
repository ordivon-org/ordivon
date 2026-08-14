import type {
  StationZeroAbilityDefinition,
  StationZeroCommanderAbilityDefinition,
  StationZeroEquipmentDefinition,
  StationZeroItemDefinition,
  StationZeroObjectiveDefinition,
} from "./model.ts";
export const STATION_ZERO_V3_TURN_LIMIT = 20 as const;

export const STATION_ZERO_V3_ABILITIES: StationZeroAbilityDefinition[] = [
  {
    abilityId: "pulse-shot",
    name: "Pulse Shot",
    resolutionPhase: "combat",
    actionPointCost: 1,
    range: 3,
    damage: 24,
    armorPiercing: 2,
    cooldownTurns: 0,
    targetKinds: ["enemy"],
    tags: ["ranged", "ballistic"],
  },
  {
    abilityId: "scatter-blast",
    name: "Scatter Blast",
    resolutionPhase: "combat",
    actionPointCost: 1,
    range: 1,
    damage: 32,
    armorPiercing: 1,
    cooldownTurns: 0,
    targetKinds: ["enemy"],
    tags: ["ranged", "close-range"],
  },
  {
    abilityId: "shock-strike",
    name: "Shock Strike",
    resolutionPhase: "combat",
    actionPointCost: 1,
    range: 0,
    damage: 16,
    armorPiercing: 4,
    cooldownTurns: 1,
    targetKinds: ["enemy"],
    tags: ["melee", "stun"],
  },
  {
    abilityId: "precision-burst",
    name: "Precision Burst",
    resolutionPhase: "combat",
    actionPointCost: 2,
    range: 4,
    damage: 38,
    armorPiercing: 3,
    cooldownTurns: 2,
    targetKinds: ["enemy"],
    tags: ["ranged", "high-value"],
  },
  {
    abilityId: "combat-stabilize",
    name: "Combat Stabilize",
    resolutionPhase: "interaction",
    actionPointCost: 1,
    range: 0,
    damage: 0,
    armorPiercing: 0,
    cooldownTurns: 1,
    targetKinds: ["ally"],
    tags: ["medical", "healing"],
  },
  {
    abilityId: "field-repair",
    name: "Field Repair",
    resolutionPhase: "interaction",
    actionPointCost: 1,
    range: 0,
    damage: 0,
    armorPiercing: 0,
    cooldownTurns: 0,
    targetKinds: ["system"],
    tags: ["engineering", "repair"],
  },
  {
    abilityId: "system-intrusion",
    name: "System Intrusion",
    resolutionPhase: "interaction",
    actionPointCost: 1,
    range: 1,
    damage: 0,
    armorPiercing: 0,
    cooldownTurns: 1,
    targetKinds: ["system", "hazard"],
    tags: ["hacking", "control"],
  },
  {
    abilityId: "overwatch",
    name: "Overwatch",
    resolutionPhase: "reaction",
    actionPointCost: 1,
    range: 3,
    damage: 18,
    armorPiercing: 1,
    cooldownTurns: 1,
    targetKinds: ["zone"],
    tags: ["reaction", "interrupt"],
  },
  {
    abilityId: "pounce",
    name: "Pounce",
    resolutionPhase: "combat",
    actionPointCost: 1,
    range: 1,
    damage: 28,
    armorPiercing: 2,
    cooldownTurns: 1,
    targetKinds: ["enemy"],
    tags: ["melee", "movement"],
  },
  {
    abilityId: "acid-spit",
    name: "Acid Spit",
    resolutionPhase: "combat",
    actionPointCost: 1,
    range: 3,
    damage: 20,
    armorPiercing: 5,
    cooldownTurns: 1,
    targetKinds: ["enemy", "system"],
    tags: ["ranged", "biological", "corrosive"],
  },
  {
    abilityId: "devour",
    name: "Devour",
    resolutionPhase: "interaction",
    actionPointCost: 1,
    range: 0,
    damage: 0,
    armorPiercing: 0,
    cooldownTurns: 0,
    targetKinds: ["enemy"],
    tags: ["biological", "biomass", "requires-incapacitated-target"],
  },
  {
    abilityId: "brood-call",
    name: "Brood Call",
    resolutionPhase: "cleanup",
    actionPointCost: 2,
    range: 0,
    damage: 0,
    armorPiercing: 0,
    cooldownTurns: 3,
    targetKinds: ["zone"],
    tags: ["biological", "spawn"],
  },
];

export const STATION_ZERO_V3_EQUIPMENT: StationZeroEquipmentDefinition[] = [
  {
    equipmentId: "rescue-pulse-rifle",
    name: "Rescue Pulse Rifle",
    slot: "weapon",
    grantedAbilityIds: ["pulse-shot", "overwatch"],
    armor: 0,
    tags: ["rescue", "ranged"],
  },
  {
    equipmentId: "security-burst-rifle",
    name: "Security Burst Rifle",
    slot: "weapon",
    grantedAbilityIds: ["pulse-shot", "precision-burst", "overwatch"],
    armor: 0,
    tags: ["rescue", "ranged"],
  },
  {
    equipmentId: "pirate-scattergun",
    name: "Pirate Scattergun",
    slot: "weapon",
    grantedAbilityIds: ["scatter-blast"],
    armor: 0,
    tags: ["pirate", "close-range"],
  },
  {
    equipmentId: "pirate-shock-baton",
    name: "Pirate Shock Baton",
    slot: "weapon",
    grantedAbilityIds: ["shock-strike"],
    armor: 0,
    tags: ["pirate", "capture"],
  },
  {
    equipmentId: "rescue-armor",
    name: "Rescue Armor",
    slot: "armor",
    grantedAbilityIds: [],
    armor: 4,
    tags: ["rescue", "vacuum-rated"],
  },
  {
    equipmentId: "boarding-armor",
    name: "Boarding Armor",
    slot: "armor",
    grantedAbilityIds: [],
    armor: 6,
    tags: ["pirate", "heavy"],
  },
  {
    equipmentId: "engineering-kit",
    name: "Engineering Kit",
    slot: "utility",
    grantedAbilityIds: ["field-repair"],
    armor: 0,
    tags: ["engineering", "tool"],
  },
  {
    equipmentId: "medical-drone",
    name: "Medical Drone",
    slot: "utility",
    grantedAbilityIds: ["combat-stabilize"],
    armor: 0,
    tags: ["medical", "tool"],
  },
  {
    equipmentId: "intrusion-rig",
    name: "Intrusion Rig",
    slot: "utility",
    grantedAbilityIds: ["system-intrusion"],
    armor: 0,
    tags: ["hacking", "tool"],
  },
  {
    equipmentId: "chitin-plates",
    name: "Chitin Plates",
    slot: "biology",
    grantedAbilityIds: [],
    armor: 5,
    tags: ["swarm", "biological"],
  },
  {
    equipmentId: "stalker-organs",
    name: "Stalker Organs",
    slot: "biology",
    grantedAbilityIds: ["pounce", "devour"],
    armor: 2,
    tags: ["swarm", "predator"],
  },
  {
    equipmentId: "drone-organs",
    name: "Drone Organs",
    slot: "biology",
    grantedAbilityIds: ["pounce"],
    armor: 1,
    tags: ["swarm", "drone"],
  },
  {
    equipmentId: "hive-alpha-organs",
    name: "Hive Alpha Organs",
    slot: "biology",
    grantedAbilityIds: ["pounce", "acid-spit", "devour", "brood-call"],
    armor: 6,
    tags: ["swarm", "leader", "spawn"],
  },
  {
    equipmentId: "acid-gland",
    name: "Acid Gland",
    slot: "biology",
    grantedAbilityIds: ["acid-spit"],
    armor: 0,
    tags: ["swarm", "corrosive"],
  },
  {
    equipmentId: "brood-organ",
    name: "Brood Organ",
    slot: "biology",
    grantedAbilityIds: ["brood-call"],
    armor: 0,
    tags: ["swarm", "spawn"],
  },
];

export const STATION_ZERO_V3_ITEMS: StationZeroItemDefinition[] = [
  { itemId: "research-core", name: "Reactor Research Core", category: "objective", equipmentId: null, stackLimit: 1, tags: ["high-value", "extractable"] },
  { itemId: "medkit", name: "Medkit", category: "consumable", equipmentId: null, stackLimit: 3, tags: ["medical"] },
  { itemId: "spare-parts", name: "Spare Parts", category: "material", equipmentId: null, stackLimit: 4, tags: ["engineering"] },
  { itemId: "sealant", name: "Hull Sealant", category: "material", equipmentId: null, stackLimit: 2, tags: ["engineering", "hazard"] },
  { itemId: "rescue-pulse-rifle-item", name: "Rescue Pulse Rifle", category: "equipment", equipmentId: "rescue-pulse-rifle", stackLimit: 1, tags: ["loot"] },
  { itemId: "security-burst-rifle-item", name: "Security Burst Rifle", category: "equipment", equipmentId: "security-burst-rifle", stackLimit: 1, tags: ["loot"] },
  { itemId: "pirate-scattergun-item", name: "Pirate Scattergun", category: "equipment", equipmentId: "pirate-scattergun", stackLimit: 1, tags: ["loot"] },
  { itemId: "pirate-shock-baton-item", name: "Pirate Shock Baton", category: "equipment", equipmentId: "pirate-shock-baton", stackLimit: 1, tags: ["loot"] },
  { itemId: "engineering-kit-item", name: "Engineering Kit", category: "equipment", equipmentId: "engineering-kit", stackLimit: 1, tags: ["loot", "tool"] },
  { itemId: "medical-drone-item", name: "Medical Drone", category: "equipment", equipmentId: "medical-drone", stackLimit: 1, tags: ["loot", "tool"] },
  { itemId: "intrusion-rig-item", name: "Intrusion Rig", category: "equipment", equipmentId: "intrusion-rig", stackLimit: 1, tags: ["loot"] },
  { itemId: "rescue-armor-item", name: "Rescue Armor", category: "equipment", equipmentId: "rescue-armor", stackLimit: 1, tags: ["loot", "armor"] },
  { itemId: "boarding-armor-item", name: "Boarding Armor", category: "equipment", equipmentId: "boarding-armor", stackLimit: 1, tags: ["loot", "armor"] },
  { itemId: "alien-tissue", name: "Alien Tissue", category: "material", equipmentId: null, stackLimit: 4, tags: ["biological", "loot"] },
];

export const STATION_ZERO_V3_COMMANDER_ABILITIES: StationZeroCommanderAbilityDefinition[] = [
  { commanderAbilityId: "orbital-scan", name: "Orbital Scan", factionIds: ["rescue"], commandPointCost: 1, maximumCharges: 2, cooldownTurns: 0, targetKinds: ["zone"], tags: ["reveal"] },
  { commanderAbilityId: "power-reroute", name: "Emergency Power Reroute", factionIds: ["rescue"], commandPointCost: 1, maximumCharges: 2, cooldownTurns: 1, targetKinds: ["system"], tags: ["system", "power"] },
  { commanderAbilityId: "bulkhead-lockdown", name: "Bulkhead Lockdown", factionIds: ["rescue"], commandPointCost: 1, maximumCharges: 1, cooldownTurns: 0, targetKinds: ["passage"], tags: ["space", "control"] },
  { commanderAbilityId: "emergency-uplink", name: "Emergency Uplink", factionIds: ["rescue"], commandPointCost: 2, maximumCharges: 1, cooldownTurns: 0, targetKinds: ["faction"], tags: ["knowledge", "coordination"] },
  { commanderAbilityId: "rescue-extraction", name: "Call Rescue Extraction", factionIds: ["rescue"], commandPointCost: 1, maximumCharges: 1, cooldownTurns: 0, targetKinds: ["zone"], tags: ["extraction"] },
  { commanderAbilityId: "signal-jam", name: "Signal Jam", factionIds: ["pirate"], commandPointCost: 1, maximumCharges: 2, cooldownTurns: 1, targetKinds: ["faction"], tags: ["knowledge", "disruption"] },
  { commanderAbilityId: "door-spoof", name: "Door Spoof", factionIds: ["pirate"], commandPointCost: 1, maximumCharges: 2, cooldownTurns: 0, targetKinds: ["passage"], tags: ["space", "hacking"] },
  { commanderAbilityId: "pirate-extraction", name: "Call Pirate Extraction", factionIds: ["pirate"], commandPointCost: 1, maximumCharges: 1, cooldownTurns: 0, targetKinds: ["zone"], tags: ["extraction"] },
  { commanderAbilityId: "mark-prize", name: "Mark Prize", factionIds: ["pirate"], commandPointCost: 1, maximumCharges: null, cooldownTurns: 0, targetKinds: ["actor"], tags: ["target", "capture"] },
  { commanderAbilityId: "pheromone-surge", name: "Pheromone Surge", factionIds: ["swarm"], commandPointCost: 1, maximumCharges: 2, cooldownTurns: 1, targetKinds: ["zone"], tags: ["movement", "coordination"] },
  { commanderAbilityId: "brood-awakening", name: "Brood Awakening", factionIds: ["swarm"], commandPointCost: 2, maximumCharges: 1, cooldownTurns: 0, targetKinds: ["zone"], tags: ["spawn", "biomass"] },
  { commanderAbilityId: "vent-spread", name: "Vent Spread", factionIds: ["swarm"], commandPointCost: 1, maximumCharges: 2, cooldownTurns: 0, targetKinds: ["zone"], tags: ["space", "infection"] },
];

export const STATION_ZERO_V3_OBJECTIVES: StationZeroObjectiveDefinition[] = [
  { objectiveId: "rescue-two-civilians", factionId: "rescue", name: "Extract two civilians", requirementId: "rescue:extract-civilians:2", mandatory: true, rewardTags: ["survivors"] },
  { objectiveId: "rescue-team-survives", factionId: "rescue", name: "Extract at least one specialist", requirementId: "rescue:extract-specialist:1", mandatory: true, rewardTags: ["continuity"] },
  { objectiveId: "recover-research-core", factionId: "rescue", name: "Recover the Research Core", requirementId: "rescue:extract-item:research-core", mandatory: false, rewardTags: ["technology", "loot"] },
  { objectiveId: "eliminate-hive-alpha", factionId: "rescue", name: "Eliminate the Hive Alpha", requirementId: "rescue:defeat-actor:hive-alpha", mandatory: false, rewardTags: ["alien-sample"] },
  { objectiveId: "pirate-steal-core", factionId: "pirate", name: "Extract the Research Core", requirementId: "pirate:extract-item:research-core", mandatory: true, rewardTags: ["credits", "technology"] },
  { objectiveId: "pirate-crew-survives", factionId: "pirate", name: "Extract at least one pirate", requirementId: "pirate:extract-actor:1", mandatory: true, rewardTags: ["continuity"] },
  { objectiveId: "capture-engineer", factionId: "pirate", name: "Capture Engineer Imani", requirementId: "pirate:capture-actor:engineer-imani", mandatory: false, rewardTags: ["ransom"] },
  { objectiveId: "steal-medical-drone", factionId: "pirate", name: "Steal the Medical Drone", requirementId: "pirate:extract-equipment:medical-drone", mandatory: false, rewardTags: ["loot"] },
  { objectiveId: "swarm-gain-biomass", factionId: "swarm", name: "Accumulate 12 Biomass", requirementId: "swarm:biomass:12", mandatory: true, rewardTags: ["evolution"] },
  { objectiveId: "swarm-survives", factionId: "swarm", name: "Preserve or extract the Hive Alpha", requirementId: "swarm:hive-alpha-survives", mandatory: true, rewardTags: ["continuity"] },
  { objectiveId: "infect-life-support", factionId: "swarm", name: "Infect Life Support", requirementId: "swarm:infect-system:life-support", mandatory: false, rewardTags: ["spread"] },
  { objectiveId: "devour-specialist", factionId: "swarm", name: "Devour a specialist", requirementId: "swarm:devour-kind:specialist", mandatory: false, rewardTags: ["adaptation"] },
];

function uniqueIds(values: string[], label: string): void {
  const unique = new Set(values);
  if (unique.size !== values.length) throw new Error(`${label} contains duplicate identities`);
}

export function assertStationZeroV3Content(): void {
  uniqueIds(STATION_ZERO_V3_ABILITIES.map((entry) => entry.abilityId), "Ability catalog");
  uniqueIds(STATION_ZERO_V3_EQUIPMENT.map((entry) => entry.equipmentId), "Equipment catalog");
  uniqueIds(STATION_ZERO_V3_ITEMS.map((entry) => entry.itemId), "Item catalog");
  uniqueIds(STATION_ZERO_V3_COMMANDER_ABILITIES.map((entry) => entry.commanderAbilityId), "Commander Ability catalog");
  uniqueIds(STATION_ZERO_V3_OBJECTIVES.map((entry) => entry.objectiveId), "Objective catalog");

  const abilityIds = new Set(STATION_ZERO_V3_ABILITIES.map((entry) => entry.abilityId));
  const equipmentIds = new Set(STATION_ZERO_V3_EQUIPMENT.map((entry) => entry.equipmentId));
  for (const equipment of STATION_ZERO_V3_EQUIPMENT) {
    for (const abilityId of equipment.grantedAbilityIds) {
      if (!abilityIds.has(abilityId)) throw new Error(`Equipment ${equipment.equipmentId} grants unknown Ability ${abilityId}`);
    }
  }
  for (const item of STATION_ZERO_V3_ITEMS) {
    if (item.category === "equipment" && (!item.equipmentId || !equipmentIds.has(item.equipmentId))) {
      throw new Error(`Equipment Item ${item.itemId} has no valid Equipment definition`);
    }
    if (item.category !== "equipment" && item.equipmentId !== null) {
      throw new Error(`Non-equipment Item ${item.itemId} must not bind Equipment`);
    }
  }
  for (const factionId of ["rescue", "pirate", "swarm"] as const) {
    if (!STATION_ZERO_V3_COMMANDER_ABILITIES.some((entry) => entry.factionIds.includes(factionId))) {
      throw new Error(`Faction ${factionId} has no Commander Ability`);
    }
    const factionObjectives = STATION_ZERO_V3_OBJECTIVES.filter((entry) => entry.factionId === factionId);
    if (!factionObjectives.some((entry) => entry.mandatory) || !factionObjectives.some((entry) => !entry.mandatory)) {
      throw new Error(`Faction ${factionId} requires mandatory and optional Objectives`);
    }
  }
  if (!STATION_ZERO_V3_ABILITIES.every((ability) => Number.isSafeInteger(ability.damage) && ability.damage >= 0)) {
    throw new Error("Abilities require deterministic non-negative integer damage");
  }
}

assertStationZeroV3Content();
