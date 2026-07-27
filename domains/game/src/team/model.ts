import type { PrimitiveWorldCommand, WorldFact } from "../model.ts";

export type ActorRole = "engineer" | "medic" | "security" | "coordinator";
export type TeamTaskState = "ready" | "running" | "waiting" | "completed" | "blocked" | "failed" | "cancelled";
export type TeamWaitKind = "message" | "authority" | "conflict" | "provider" | "dependency" | "replan";
export type AuthorityPolicyMode = "autonomous" | "supervised" | "locked";
export type AuthorityOutcome = "permit" | "require-human" | "deny";
export type MessageChannel = "local" | "station-radio";
export type MessageKind =
  | "fact-share"
  | "help-request"
  | "task-offer"
  | "task-accept"
  | "intent-announce"
  | "blocker-notice"
  | "status-update";
export type MessageStatus = "pending" | "delivered" | "expired";

export interface TeamGoal {
  goalId: string;
  runId: string;
  statement: string;
  objectiveGraphDigest: string;
  successPredicateId: string;
  status: "active" | "succeeded" | "failed";
  revision: number;
  createdAt: string;
  updatedAt: string;
}

export interface ActorProfile {
  actorId: string;
  role: ActorRole;
  providerOrder: string[];
  observationPolicyId: string;
  authorityPolicyId: string;
  riskPreferenceId: string;
}

export interface ObjectiveNode {
  objectiveId: string;
  label: string;
  visibility: "public" | "discovered";
  allOf: string[];
  anyOf: string[][];
  requiredCapabilities: string[];
  satisfactionPredicateId: string;
  priorityClass: "critical" | "high" | "normal" | "low";
}

export interface ObjectiveGraph {
  schemaVersion: 1;
  kind: "ordivon.game.objective-graph";
  rootObjectiveId: string;
  nodes: ObjectiveNode[];
}

export interface ObjectiveStatus {
  objectiveId: string;
  satisfied: boolean;
  visible: boolean;
}

export interface TeamWaitRecord {
  kind: TeamWaitKind;
  subjectId: string;
  reason: string;
  sinceTick: number;
}

export interface TeamTaskProjection {
  taskId: string;
  goalId: string;
  runId: string;
  actorId: string | null;
  role: ActorRole;
  state: TeamTaskState;
  revision: number;
  activeObjectiveId: string | null;
  preparedContextDigest: string | null;
  admittedProposalId: string | null;
  wait: TeamWaitRecord | null;
  lastWorldRevision: number;
  providerOrder: string[];
  createdAt: string;
  updatedAt: string;
}

export interface TeamTaskLease {
  taskId: string;
  ownerId: string;
  revision: number;
  expiresAtMs: number;
}

export interface TeamMessage {
  messageId: string;
  runId: string;
  senderActorId: string;
  recipientActorIds: string[];
  kind: MessageKind;
  referencedFactIds: string[];
  referencedArtifactDigests: string[];
  boundedSummary: string;
  channel: MessageChannel;
  createdTick: number;
  expiryTick: number;
  deliveredActorIds: string[];
  pendingActorIds: string[];
  status: MessageStatus;
  createdAt: string;
  updatedAt: string;
}

export interface AuthorityAttributes {
  subject: {
    actorId: string;
    role: ActorRole;
    capabilities: string[];
    mandate: string[];
  };
  action: {
    operationKind: PrimitiveWorldCommand["kind"];
    riskTags: string[];
  };
  target: {
    objectId: string;
    domain: "room" | "item" | "system" | "hazard" | "crew" | "mission" | "time";
    criticality: "routine" | "important" | "critical";
  };
  environment: {
    missionPhase: "running" | "terminal";
    oxygenBand: "critical" | "low" | "stable";
    reactorBand: "critical" | "high" | "stable";
    communicationAvailable: boolean;
  };
  policyId: string;
}

export interface AuthorityDecision {
  decisionId: string;
  runId: string;
  actorId: string;
  actionCandidateId: string;
  contextDigest: string;
  worldDigest: string;
  policyMode: AuthorityPolicyMode;
  policyRevision: number;
  attributes: AuthorityAttributes;
  outcome: AuthorityOutcome;
  reason: string;
  createdAt: string;
}

export interface AuthorityGrant {
  grantId: string;
  runId: string;
  actorId: string;
  proposalId: string;
  actionCandidateId: string;
  contextDigest: string;
  worldDigest: string;
  policyRevision: number;
  operationKind: PrimitiveWorldCommand["kind"];
  targetId: string;
  expiresAtTick: number;
  consumedAtTick: number | null;
  issuedBy: string;
  createdAt: string;
}

export type TeamContextBlockKind = "goal" | "task" | "world" | "local" | "objective" | "message" | "evidence" | "constraint";
export type TeamContextFreshness = "current" | "checkpoint" | "historical";

export interface TeamContextBlock {
  blockId: string;
  kind: TeamContextBlockKind;
  priority: number;
  required: boolean;
  freshness: TeamContextFreshness;
  sourceDigest: string;
  payload: unknown;
  estimatedTokens: number;
}

export interface TeamActionCandidate {
  actionCandidateId: string;
  actionId: string;
  label: string;
  actorId: string;
  worldDigest: string;
  worldRevision: number;
  command: PrimitiveWorldCommand;
  objectiveIds: string[];
  authorityOutcome: AuthorityOutcome;
  authorityDecisionId: string;
}

export interface TeamContextManifest {
  tokenBudget: number;
  estimatedTokens: number;
  selectedBlockIds: string[];
  omittedBlockIds: string[];
}

export interface CompiledTeamContext {
  schemaVersion: 1;
  kind: "ordivon.game.team-context";
  contextId: string;
  runId: string;
  taskId: string;
  actorId: string;
  worldDigest: string;
  worldRevision: number;
  blocks: TeamContextBlock[];
  allowedActions: TeamActionCandidate[];
  visibleFacts: WorldFact[];
  manifest: TeamContextManifest;
  byteLength: number;
}

export interface TeamProjection {
  goal: TeamGoal;
  profiles: ActorProfile[];
  tasks: TeamTaskProjection[];
  objectives: ObjectiveGraph;
  objectiveStatus: ObjectiveStatus[];
  messages: TeamMessage[];
  authorityDecisions: AuthorityDecision[];
  authorityGrants: AuthorityGrant[];
}
