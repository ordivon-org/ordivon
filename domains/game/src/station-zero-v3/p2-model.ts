import type {
  StationZeroFactionId,
  StationZeroFactionOutcome,
  StationZeroFactionTurnPlan,
  StationZeroTurnBatch,
  StationZeroTurnRecord,
  StationZeroV3WorldState,
} from "./model.ts";

export const STATION_ZERO_V3_PLANNING_STATUSES = ["open", "committed", "resolved"] as const;
export type StationZeroV3PlanningStatus = (typeof STATION_ZERO_V3_PLANNING_STATUSES)[number];

export interface StationZeroV3RunMetadata {
  runId: string;
  scenarioId: "station-zero";
  scenarioVersion: 3;
  scenarioCaseId: string;
  rulesetId: "station-zero-core";
  rulesetVersion: 4;
  stateSchemaVersion: 3;
  seed: string;
  genesisDigest: string;
  status: "running" | "terminal";
  createdAt: string;
  createdWithBuild: string;
}

export interface StationZeroV3WorldHead {
  runId: string;
  revision: number;
  turn: number;
  phase: StationZeroV3WorldState["encounter"]["phase"];
  status: StationZeroV3WorldState["encounter"]["status"];
  state: StationZeroV3WorldState;
  stateDigest: string;
  lastTurnSequence: number;
  updatedAt: string;
}

export interface StationZeroV3PlanningHead {
  schemaVersion: 1;
  kind: "ordivon.game.station-zero-v3-planning-head";
  planningId: string;
  runId: string;
  worldRevision: number;
  turn: number;
  worldDigest: string;
  commitmentDigest: string;
  standingOrderRevision: number;
  planningRevision: number;
  status: StationZeroV3PlanningStatus;
  submittedPlanDigests: Partial<Record<StationZeroFactionId, string>>;
  turnBatchId: string | null;
  batchDigest: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface StationZeroV3PlanReceipt {
  runId: string;
  planningId: string;
  factionId: StationZeroFactionId;
  planDigest: string;
  planningRevision: number;
  idempotent: boolean;
}

export interface StationZeroV3PreparedTurn {
  planning: StationZeroV3PlanningHead;
  batch: StationZeroTurnBatch;
  batchDigest: string;
}

export interface StationZeroV3WorldEvent {
  schemaVersion: 1;
  kind: "ordivon.game.station-zero-v3-world-event";
  eventId: string;
  runId: string;
  turnSequence: number;
  planningId: string;
  turnBatchId: string;
  worldRevisionBefore: number;
  worldRevisionAfter: number;
  turnBefore: number;
  turnAfter: number;
  worldDigestBefore: string;
  commitmentDigestBefore: string;
  worldDigestAfter: string;
  resolutionDigest: string;
  turnRecordDigest: string;
  intentResolutionCounts: Record<"executed" | "interrupted" | "invalidated" | "contested" | "no_effect", number>;
  encounterStatus: StationZeroV3WorldState["encounter"]["status"];
  encounterReason: string | null;
  factionOutcomes: Record<StationZeroFactionId, StationZeroFactionOutcome>;
}

export interface StationZeroV3TurnReceipt {
  runId: string;
  turnSequence: number;
  planningId: string;
  turnBatchId: string;
  batch: StationZeroTurnBatch;
  event: StationZeroV3WorldEvent;
  eventDigest: string;
  record: StationZeroTurnRecord;
  recordDigest: string;
  state: StationZeroV3WorldState;
  stateDigest: string;
  idempotent: boolean;
}

export interface StationZeroV3RecoveryResult {
  runId: string;
  state: StationZeroV3WorldState;
  stateDigest: string;
  turnCount: number;
  lastTurnSequence: number;
  verified: true;
  headRebuilt: boolean;
}

export interface StationZeroV3ExecutorObservation {
  schemaVersion: 1;
  kind: "ordivon.game.station-zero-v3-turn-observation";
  executorId: "executor:station-zero-v3-world-v1";
  runId: string;
  planningId: string;
  turnBatchId: string;
  status: "succeeded";
  idempotent: boolean;
  turnSequence: number;
  worldEventId: string;
  worldEventDigest: string;
  turnRecordDigest: string;
  worldAfterDigest: string;
  verificationPassed: true;
}

export interface StationZeroV3MissionControlActorView {
  actorId: string;
  name: string;
  roleId: string;
  lifeState: StationZeroV3WorldState["actors"][string]["lifeState"];
  health: number;
  maximumHealth: number;
  zoneId: string;
  zoneName: string;
  actionPoints: number;
  statusIds: string[];
  inventoryItemIds: string[];
}

export interface StationZeroV3MissionControlContactView {
  actorId: string;
  lastKnownZoneId: string;
  observedLifeState: StationZeroV3WorldState["actors"][string]["lifeState"];
  observedHealthBand: "healthy" | "wounded" | "critical" | "unknown";
  confidence: "confirmed" | "estimated" | "stale";
  observedAtTurn: number;
}

export interface StationZeroV3MissionControlView {
  schemaVersion: 1;
  kind: "ordivon.game.station-zero-v3-mission-control-view";
  generatedFrom: {
    runId: string;
    worldRevision: number;
    worldDigest: string;
    planningRevision: number | null;
  };
  run: {
    runId: string;
    scenarioCaseId: string;
    turn: number;
    turnLimit: number;
    status: StationZeroV3WorldState["encounter"]["status"];
    reason: string | null;
    playerFactionId: StationZeroFactionId;
  };
  planning: {
    planningId: string | null;
    status: StationZeroV3PlanningStatus | null;
    submittedFactions: StationZeroFactionId[];
    missingFactions: StationZeroFactionId[];
    canSubmitPlans: boolean;
    canCommit: boolean;
    canExecute: boolean;
  };
  resources: {
    batteryCharge: number;
    batteryInitial: number;
    oxygen: number;
    reactorHeat: number;
    biomass: number;
    alertLevel: number;
  };
  ownActors: StationZeroV3MissionControlActorView[];
  knownContacts: StationZeroV3MissionControlContactView[];
  known: {
    roomIds: string[];
    zoneIds: string[];
    systemIds: string[];
    systems: Array<{ systemId: string; name: string; observedIntegrity: number; observedPowered: boolean; observedAtTurn: number }>;
    hazardIds: string[];
    groundItemIds: string[];
    reportIds: string[];
  };
  objectives: Array<{
    objectiveId: string;
    name: string;
    mandatory: boolean;
    status: "active" | "completed" | "failed";
    progress: number;
    target: number;
    reason: string | null;
  }>;
  latestTurn: {
    turnSequence: number;
    turnBatchId: string;
    eventId: string;
    eventDigest: string;
    recordDigest: string;
    visibleFactIds: string[];
  } | null;
}

export interface StationZeroV3SubmittedPlanRecord {
  plan: StationZeroFactionTurnPlan;
  planDigest: string;
  submittedAt: string;
}
