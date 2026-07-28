import type { Inventory } from "../model.ts";
import type { AuthorityPolicyMode, TeamTaskControlMode } from "../team/model.ts";

export type EvidenceStage = "observed" | "assessed" | "proposed" | "executing" | "verified";
export type Severity = "info" | "warning" | "critical";

export interface MissionResourceView {
  resourceId: string;
  label: string;
  current: number;
  maximum: number | null;
  unit: "energy" | "percent" | "health" | "ticks";
  band: "stable" | "warning" | "critical" | "terminal";
  trend: "improving" | "stable" | "worsening" | "unknown";
}

export interface StationRoomView {
  roomId: string;
  name: string;
  x: number;
  y: number;
  neighbors: string[];
  inventory: Inventory;
  actorIds: string[];
  crewIds: string[];
  systemIds: string[];
  hazardIds: string[];
  systems: Array<{ systemId: string; name: string; integrity: number; powered: boolean }>;
  hazards: Array<{ hazardId: string; name: string; controlled: boolean }>;
  crew: Array<{ crewId: string; name: string; health: number; stabilized: boolean }>;
}

export interface EvidenceView {
  stage: EvidenceStage;
  label: string;
  items: string[];
  confidence: number | null;
}

export interface ActorMissionView {
  actorId: string;
  name: string;
  role: string;
  locationRoomId: string;
  locationName: string;
  health: number;
  inventory: Partial<Inventory>;
  riskPreferenceId: string;
  providerOrder: string[];
  taskState: string;
  controlMode: TeamTaskControlMode;
  activeObjectiveId: string | null;
  waitReason: string | null;
  evidence: EvidenceView[];
}

export interface ObjectiveMissionView {
  objectiveId: string;
  label: string;
  priority: string;
  status: "satisfied" | "superseded" | "active" | "available" | "blocked";
  dependencies: string[];
  alternatives: string[][];
  actorIds: string[];
}

export type InterventionKind =
  | "authority-request"
  | "resource-mismatch"
  | "proposal-conflict"
  | "redundant-action"
  | "task-wait"
  | "provider-failure"
  | "message-pending"
  | "mission-risk";

export interface PlayerCommandDescriptor {
  action: string;
  actorId?: string;
  proposalId?: string;
  objectiveId?: string;
}

export interface InterventionCard {
  cardId: string;
  kind: InterventionKind;
  severity: Severity;
  actorIds: string[];
  title: string;
  explanation: string;
  consequence: string;
  urgency: string;
  expiresAtTick: number | null;
  commands: PlayerCommandDescriptor[];
  evidenceRefs: string[];
}

export interface RoundActorEntry {
  actorId: string;
  proposalId: string | null;
  action: string | null;
  status: string;
  authority: string | null;
}

export interface CoordinationRoundView {
  roundId: string;
  worldRevision: number;
  phase: "preparing" | "proposal-review" | "authority" | "committing" | "verified" | "blocked";
  actors: RoundActorEntry[];
  selectedProposalIds: string[];
  rejectedProposalIds: string[];
  blocker: string | null;
}

export interface MissionTimelineItem {
  cursor: string;
  worldRevision: number;
  turn: number;
  status: "verified" | "blocked" | "terminal" | "in-progress";
  summary: string;
  actorActions: string[];
  facts: string[];
}

export interface MissionControlView {
  schemaVersion: 1;
  initialized: boolean;
  generatedFrom: {
    worldRevision: number;
    worldDigest: string;
    goalRevision: number;
    configurationRevision: number;
  };
  run: {
    runId: string;
    scenarioId: string;
    scenarioVersion: number;
    scenarioCaseId: string;
    rulesetVersion: number;
    genesisDigest: string;
    evaluatedInputsDigest: string;
    createdWithBuild: string;
    turn: number;
    turnLimit: number;
    status: "setup" | "running" | "victory" | "failure";
  };
  configuration: {
    authorityPolicyMode: AuthorityPolicyMode;
  } | null;
  mission: {
    title: string;
    reason: string | null;
    turnsRemaining: number;
    objectiveProgress: { resolved: number; satisfied: number; superseded: number; total: number };
    urgency: string;
    score: number | null;
    scoreComponents: Record<string, number> | null;
  };
  resources: MissionResourceView[];
  station: { rooms: StationRoomView[]; communicationAvailable: boolean };
  actors: ActorMissionView[];
  objectives: ObjectiveMissionView[];
  currentRound: CoordinationRoundView | null;
  inbox: InterventionCard[];
  timeline: MissionTimelineItem[];
  controls: {
    canPrepare: boolean;
    canCommit: boolean;
    canConfigure: boolean;
  };
}

export interface MissionControlAdvanceResult {
  boundary: "proposal-review" | "tick-verified" | "authority" | "blocked" | "terminal" | "step-limit";
  steps: string[];
  view: MissionControlView;
}
