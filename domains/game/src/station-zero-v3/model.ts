export const STATION_ZERO_V3_SCENARIO_ID = "station-zero" as const;
export const STATION_ZERO_V3_SCENARIO_VERSION = 3 as const;
export const STATION_ZERO_V3_RULESET_ID = "station-zero-core" as const;
export const STATION_ZERO_V3_RULESET_VERSION = 4 as const;
export const STATION_ZERO_V3_WORLD_SCHEMA_VERSION = 3 as const;
export const STATION_ZERO_V3_CONTRACT_VERSION = 1 as const;

export const STATION_ZERO_FACTION_IDS = ["rescue", "pirate", "swarm"] as const;
export type StationZeroFactionId = (typeof STATION_ZERO_FACTION_IDS)[number];

export const STATION_ZERO_TURN_PHASES = [
  "situation",
  "command",
  "deliberation",
  "commitment",
  "resolution",
  "aftermath",
] as const;
export type StationZeroTurnPhase = (typeof STATION_ZERO_TURN_PHASES)[number];

export const STATION_ZERO_RESOLUTION_PHASES = [
  "commander",
  "movement",
  "reaction",
  "combat",
  "interaction",
  "environment",
  "cleanup",
] as const;
export type StationZeroResolutionPhase = (typeof STATION_ZERO_RESOLUTION_PHASES)[number];

export const STATION_ZERO_INTENT_RESOLUTION_STATUSES = [
  "executed",
  "interrupted",
  "invalidated",
  "contested",
  "no_effect",
] as const;
export type StationZeroIntentResolutionStatus = (typeof STATION_ZERO_INTENT_RESOLUTION_STATUSES)[number];

export type StationZeroEncounterStatus = "running" | "terminal";
export type StationZeroFactionOutcome = "pending" | "victory" | "partial" | "failure";
export type StationZeroControllerKind = "player" | "agent" | "policy" | "none";
export type StationZeroActorKind = "specialist" | "pirate" | "creature" | "civilian";
export type StationZeroEquipmentSlot = "weapon" | "armor" | "utility" | "biology";
export type StationZeroItemCategory = "equipment" | "consumable" | "objective" | "material";
export type StationZeroCover = "none" | "half" | "full";
export type StationZeroPassageState = "open" | "closed" | "sealed";
export type StationZeroActorLifeState = "active" | "incapacitated" | "dead" | "extracted" | "captured";
export type StationZeroObjectiveStatus = "active" | "completed" | "failed";
export type StationZeroKnowledgeConfidence = "confirmed" | "estimated" | "stale";

export interface StationZeroDesignInfluence {
  influenceId: "roguelite" | "tactical-rpg" | "sandbox" | "systemic-sim" | "character-sim";
  retainedMechanics: string[];
  rejectedMechanics: string[];
}

export interface StationZeroP0Contract {
  schemaVersion: 1;
  kind: "ordivon.game.station-zero-v3-p0-contract";
  scenario: {
    id: typeof STATION_ZERO_V3_SCENARIO_ID;
    version: typeof STATION_ZERO_V3_SCENARIO_VERSION;
    rulesetId: typeof STATION_ZERO_V3_RULESET_ID;
    rulesetVersion: typeof STATION_ZERO_V3_RULESET_VERSION;
    worldSchemaVersion: typeof STATION_ZERO_V3_WORLD_SCHEMA_VERSION;
  };
  productForm: "single-player-asymmetric-turn-based-tactical-encounter";
  defaultPlayerFactionId: StationZeroFactionId;
  turnPhases: StationZeroTurnPhase[];
  resolutionPhases: StationZeroResolutionPhase[];
  playerResponsibilities: string[];
  agentResponsibilities: string[];
  randomnessPolicy: {
    setupMayVary: true;
    committedTurnIsDeterministic: true;
    hiddenHitRolls: false;
  };
  runBoundary: {
    turnLimit: number;
    encounterOwnsLoot: true;
    encounterOwnsFactionOutcomes: true;
    routeMapDeferred: true;
    metaProgressionDeferred: true;
  };
  influences: StationZeroDesignInfluence[];
  nonGoals: string[];
}

export interface StationZeroRoomState {
  roomId: string;
  name: string;
  zoneIds: string[];
  tags: string[];
}

export interface StationZeroZoneState {
  zoneId: string;
  roomId: string;
  name: string;
  cover: StationZeroCover;
  capacity: number;
  tags: string[];
}

export interface StationZeroPassageStateRecord {
  passageId: string;
  zoneAId: string;
  zoneBId: string;
  state: StationZeroPassageState;
  lockable: boolean;
  tags: string[];
}

export interface StationZeroEquipmentDefinition {
  equipmentId: string;
  name: string;
  slot: StationZeroEquipmentSlot;
  grantedAbilityIds: string[];
  armor: number;
  tags: string[];
}

export interface StationZeroItemDefinition {
  itemId: string;
  name: string;
  category: StationZeroItemCategory;
  equipmentId: string | null;
  stackLimit: number;
  tags: string[];
}

export interface StationZeroAbilityDefinition {
  abilityId: string;
  name: string;
  resolutionPhase: StationZeroResolutionPhase;
  actionPointCost: number;
  range: number;
  damage: number;
  armorPiercing: number;
  cooldownTurns: number;
  targetKinds: Array<"self" | "ally" | "enemy" | "zone" | "system" | "hazard" | "item">;
  tags: string[];
}

export interface StationZeroCommanderAbilityDefinition {
  commanderAbilityId: string;
  name: string;
  factionIds: StationZeroFactionId[];
  commandPointCost: number;
  maximumCharges: number | null;
  cooldownTurns: number;
  targetKinds: Array<"actor" | "zone" | "passage" | "system" | "faction" | "none">;
  tags: string[];
}

export interface StationZeroActorState {
  actorId: string;
  name: string;
  factionId: StationZeroFactionId | null;
  kind: StationZeroActorKind;
  roleId: string;
  controllerKind: StationZeroControllerKind;
  leaderActorId: string | null;
  position: { zoneId: string };
  lifeState: StationZeroActorLifeState;
  health: number;
  maximumHealth: number;
  armor: number;
  actionPoints: number;
  maximumActionPoints: number;
  initiative: number;
  movementRange: number;
  capabilityIds: string[];
  traitIds: string[];
  equipment: Partial<Record<StationZeroEquipmentSlot, string>>;
  inventoryItemIds: string[];
  abilityCooldowns: Record<string, number>;
  statusIds: string[];
}

export interface StationZeroGroundItemState {
  groundItemId: string;
  itemId: string;
  zoneId: string;
  quantity: number;
  ownerFactionId: StationZeroFactionId | null;
}

export interface StationZeroSystemState {
  systemId: string;
  name: string;
  zoneId: string;
  integrity: number;
  powered: boolean;
  powerDraw: number;
  tags: string[];
}

export interface StationZeroHazardState {
  hazardId: string;
  name: string;
  zoneId: string;
  severity: number;
  contained: boolean;
  tags: string[];
}

export interface StationZeroObjectiveDefinition {
  objectiveId: string;
  factionId: StationZeroFactionId;
  name: string;
  requirementId: string;
  mandatory: boolean;
  rewardTags: string[];
}

export interface StationZeroObjectiveProgress {
  objectiveId: string;
  status: StationZeroObjectiveStatus;
  progress: number;
  target: number;
  reason: string | null;
}

export interface StationZeroFactionState {
  factionId: StationZeroFactionId;
  name: string;
  controllerKind: Exclude<StationZeroControllerKind, "none">;
  commandPoints: number;
  maximumCommandPoints: number;
  uplinkSlots: number;
  maximumUplinkSlots: number;
  commanderAbilityCharges: Record<string, number | null>;
  commanderAbilityCooldowns: Record<string, number>;
  objectiveProgress: Record<string, StationZeroObjectiveProgress>;
  outcome: StationZeroFactionOutcome;
  outcomeReason: string | null;
}

export interface StationZeroKnownActorState {
  actorId: string;
  lastKnownZoneId: string;
  observedLifeState: StationZeroActorLifeState;
  observedHealthBand: "healthy" | "wounded" | "critical" | "unknown";
  observedAtTurn: number;
  confidence: StationZeroKnowledgeConfidence;
}

export interface StationZeroKnownSystemState {
  systemId: string;
  observedIntegrity: number;
  observedPowered: boolean;
  observedAtTurn: number;
}

export interface StationZeroFactionKnowledgeState {
  factionId: StationZeroFactionId;
  discoveredRoomIds: string[];
  discoveredZoneIds: string[];
  knownActors: Record<string, StationZeroKnownActorState>;
  knownSystemIds: string[];
  knownSystems: Record<string, StationZeroKnownSystemState>;
  knownHazardIds: string[];
  knownGroundItemIds: string[];
  reportIds: string[];
}

export interface StationZeroEnvironmentState {
  batteryInitial: number;
  batteryCharge: number;
  energyConsumed: number;
  oxygen: number;
  reactorHeat: number;
  biomass: number;
  alertLevel: number;
}

export interface StationZeroEncounterState {
  encounterId: string;
  title: string;
  playerFactionId: StationZeroFactionId;
  status: StationZeroEncounterStatus;
  reason: string | null;
  turn: number;
  turnLimit: number;
  phase: StationZeroTurnPhase;
  activePlanRevision: number;
}

export interface StationZeroV3WorldState {
  schemaVersion: typeof STATION_ZERO_V3_WORLD_SCHEMA_VERSION;
  scenarioId: typeof STATION_ZERO_V3_SCENARIO_ID;
  scenarioVersion: typeof STATION_ZERO_V3_SCENARIO_VERSION;
  rulesetId: typeof STATION_ZERO_V3_RULESET_ID;
  rulesetVersion: typeof STATION_ZERO_V3_RULESET_VERSION;
  seed: string;
  revision: number;
  rooms: Record<string, StationZeroRoomState>;
  zones: Record<string, StationZeroZoneState>;
  passages: Record<string, StationZeroPassageStateRecord>;
  actors: Record<string, StationZeroActorState>;
  groundItems: Record<string, StationZeroGroundItemState>;
  systems: Record<string, StationZeroSystemState>;
  hazards: Record<string, StationZeroHazardState>;
  factions: Record<StationZeroFactionId, StationZeroFactionState>;
  factionKnowledge: Record<StationZeroFactionId, StationZeroFactionKnowledgeState>;
  environment: StationZeroEnvironmentState;
  encounter: StationZeroEncounterState;
}

interface StationZeroIntentBase {
  intentId: string;
  actorId: string;
  factionId: StationZeroFactionId;
  expectedWorldRevision: number;
  expectedTurn: number;
}

export interface StationZeroMoveIntent extends StationZeroIntentBase {
  kind: "move";
  targetZoneId: string;
}

export interface StationZeroAttackIntent extends StationZeroIntentBase {
  kind: "attack";
  abilityId: string;
  targetActorId: string;
}

export interface StationZeroUseAbilityIntent extends StationZeroIntentBase {
  kind: "use_ability";
  abilityId: string;
  targetActorId: string | null;
  targetZoneId: string | null;
  targetSystemId: string | null;
  targetHazardId: string | null;
}

export interface StationZeroInteractIntent extends StationZeroIntentBase {
  kind: "interact";
  operationId: "repair" | "hack" | "stabilize" | "rescue" | "capture" | "devour" | "infect";
  targetId: string;
}

export interface StationZeroPickupIntent extends StationZeroIntentBase {
  kind: "pickup";
  groundItemId: string;
  quantity: number;
}

export interface StationZeroExtractIntent extends StationZeroIntentBase {
  kind: "extract";
  extractionId: string;
}

export interface StationZeroGuardIntent extends StationZeroIntentBase {
  kind: "guard";
  protectedActorId: string | null;
  watchedZoneId: string | null;
}

export interface StationZeroWaitIntent extends StationZeroIntentBase {
  kind: "wait";
}

export type StationZeroActorIntent =
  | StationZeroMoveIntent
  | StationZeroAttackIntent
  | StationZeroUseAbilityIntent
  | StationZeroInteractIntent
  | StationZeroPickupIntent
  | StationZeroExtractIntent
  | StationZeroGuardIntent
  | StationZeroWaitIntent;

export interface StationZeroCommanderAction {
  commanderActionId: string;
  factionId: StationZeroFactionId;
  commanderAbilityId: string;
  expectedWorldRevision: number;
  expectedTurn: number;
  targetActorId: string | null;
  targetZoneId: string | null;
  targetPassageId: string | null;
  targetSystemId: string | null;
  targetFactionId: StationZeroFactionId | null;
}

export interface StationZeroStandingOrder {
  orderId: string;
  factionId: StationZeroFactionId;
  actorId: string;
  objectiveId: string;
  priorityTargetActorId: string | null;
  protectedActorId: string | null;
  retreatHealthThreshold: number;
  lethalForce: "forbidden" | "permitted" | "preferred";
  collateralPolicy: "forbidden" | "limited" | "permitted";
  lootPolicy: "ignore" | "mission-only" | "opportunistic";
  revision: number;
}

export interface StationZeroFactionTurnPlan {
  planId: string;
  factionId: StationZeroFactionId;
  expectedWorldRevision: number;
  expectedTurn: number;
  standingOrderRevision: number;
  commanderActions: StationZeroCommanderAction[];
  actorIntents: StationZeroActorIntent[];
  committedBy: string;
}

export interface StationZeroTurnBatch {
  turnBatchId: string;
  expectedWorldRevision: number;
  expectedTurn: number;
  factionPlans: StationZeroFactionTurnPlan[];
}

export interface StationZeroIntentResolution {
  intentId: string;
  actorId: string;
  factionId: StationZeroFactionId;
  resolutionPhase: StationZeroResolutionPhase;
  status: StationZeroIntentResolutionStatus;
  reason: string;
  verificationPassed: boolean;
  factIds: string[];
}

export type StationZeroFact =
  | { factId: string; kind: "commander_ability_used"; factionId: StationZeroFactionId; commanderAbilityId: string }
  | { factId: string; kind: "actor_moved"; actorId: string; fromZoneId: string; toZoneId: string }
  | { factId: string; kind: "actor_attacked"; actorId: string; targetActorId: string; abilityId: string }
  | { factId: string; kind: "damage_dealt"; sourceActorId: string; targetActorId: string; amount: number }
  | { factId: string; kind: "actor_health_changed"; actorId: string; before: number; after: number; causes: string[] }
  | { factId: string; kind: "actor_life_state_changed"; actorId: string; before: StationZeroActorLifeState; after: StationZeroActorLifeState }
  | { factId: string; kind: "actor_status_changed"; actorId: string; statusId: string; active: boolean }
  | { factId: string; kind: "ground_item_dropped"; groundItemId: string; actorId: string; zoneId: string }
  | { factId: string; kind: "ground_item_picked_up"; groundItemId: string; actorId: string; quantity: number }
  | { factId: string; kind: "item_consumed"; actorId: string; itemId: string; quantity: number; purpose: string }
  | { factId: string; kind: "item_extracted"; actorId: string; factionId: StationZeroFactionId; itemId: string }
  | { factId: string; kind: "passage_changed"; passageId: string; before: StationZeroPassageState; after: StationZeroPassageState }
  | { factId: string; kind: "system_changed"; systemId: string; integrityBefore: number; integrityAfter: number; poweredBefore: boolean; poweredAfter: boolean }
  | { factId: string; kind: "hazard_changed"; hazardId: string; severityBefore: number; severityAfter: number; contained: boolean }
  | { factId: string; kind: "knowledge_revealed"; factionId: StationZeroFactionId; subjectId: string; subjectKind: "room" | "zone" | "actor" | "system" | "hazard" | "item" }
  | { factId: string; kind: "objective_changed"; factionId: StationZeroFactionId; objectiveId: string; before: StationZeroObjectiveStatus; after: StationZeroObjectiveStatus }
  | { factId: string; kind: "faction_outcome_changed"; factionId: StationZeroFactionId; before: StationZeroFactionOutcome; after: StationZeroFactionOutcome; reason: string }
  | { factId: string; kind: "environment_changed"; resourceId: "battery" | "oxygen" | "reactor-heat" | "biomass" | "alert"; before: number; after: number; causes: string[] };

export interface StationZeroFactionObservation {
  factionId: StationZeroFactionId;
  worldRevision: number;
  turn: number;
  visibleFactIds: string[];
  discoveredRoomIds: string[];
  discoveredZoneIds: string[];
  knownActorIds: string[];
  knownSystemIds: string[];
  knownSystems: StationZeroKnownSystemState[];
  knownHazardIds: string[];
  knownGroundItemIds: string[];
  observationDigest: string;
}

export interface StationZeroTurnResolution {
  turnBatchId: string;
  worldRevisionBefore: number;
  worldRevisionAfter: number;
  turnBefore: number;
  turnAfter: number;
  intentResolutions: StationZeroIntentResolution[];
  facts: StationZeroFact[];
  observations: Record<StationZeroFactionId, StationZeroFactionObservation>;
  deterministicDigest: string;
}

export interface StationZeroTurnRecord {
  schemaVersion: 1;
  kind: "ordivon.game.station-zero-v3-turn-record";
  stateDigestBefore: string;
  batch: StationZeroTurnBatch;
  resolution: StationZeroTurnResolution;
  stateDigestAfter: string;
  recordDigest: string;
}

export type StationZeroTurnApplyResult =
  | {
      status: "accepted";
      state: StationZeroV3WorldState;
      resolution: StationZeroTurnResolution;
      record: StationZeroTurnRecord;
    }
  | {
      status: "rejected";
      code: "invalid_turn_batch";
      reason: string;
    };
