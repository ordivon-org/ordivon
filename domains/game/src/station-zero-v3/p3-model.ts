import type {
  StationZeroActorIntent,
  StationZeroCommanderAction,
  StationZeroFactionId,
  StationZeroFactionTurnPlan,
  StationZeroIntentResolutionStatus,
  StationZeroStandingOrder,
  StationZeroV3WorldState,
} from "./model.ts";
import type {
  StationZeroV3MissionControlActorView,
  StationZeroV3MissionControlContactView,
  StationZeroV3MissionControlView,
  StationZeroV3PlanningStatus,
} from "./p2-model.ts";

export const STATION_ZERO_V3_COMMAND_POSTURES = ["cautious", "balanced", "aggressive"] as const;
export type StationZeroV3CommandPosture = (typeof STATION_ZERO_V3_COMMAND_POSTURES)[number];

export const STATION_ZERO_V3_FORMATIONS = ["cohesive", "split"] as const;
export type StationZeroV3Formation = (typeof STATION_ZERO_V3_FORMATIONS)[number];

export const STATION_ZERO_V3_COMMANDER_DIRECTIVE_IDS = [
  "hold-command",
  "scan-reactor",
  "scan-maintenance",
  "scan-life-support",
  "reroute-cooling",
  "lock-maintenance",
  "emergency-uplink",
  "call-extraction",
] as const;
export type StationZeroV3CommanderDirectiveId = (typeof STATION_ZERO_V3_COMMANDER_DIRECTIVE_IDS)[number];

export const STATION_ZERO_V3_PIRATE_DIRECTIVES = ["steal-core", "capture-prize", "extract-crew"] as const;
export type StationZeroV3PirateDirective = (typeof STATION_ZERO_V3_PIRATE_DIRECTIVES)[number];

export const STATION_ZERO_V3_SWARM_DIRECTIVES = ["hunt-biomass", "infect-life-support", "preserve-hive"] as const;
export type StationZeroV3SwarmDirective = (typeof STATION_ZERO_V3_SWARM_DIRECTIVES)[number];

export interface StationZeroV3CommanderOrder {
  schemaVersion: 1;
  kind: "ordivon.game.station-zero-v3-commander-order";
  runId: string;
  planningId: string;
  expectedWorldRevision: number;
  expectedTurn: number;
  primaryObjectiveId: "rescue-two-civilians" | "recover-research-core" | "eliminate-hive-alpha";
  posture: StationZeroV3CommandPosture;
  formation: StationZeroV3Formation;
  retreatHealthThreshold: number;
  lethalForce: "forbidden" | "permitted" | "preferred";
  collateralPolicy: "forbidden" | "limited" | "permitted";
  lootPolicy: "ignore" | "mission-only" | "opportunistic";
  protectedActorId: string | null;
  priorityTargetActorId: string | null;
  commanderDirectiveId: StationZeroV3CommanderDirectiveId;
  issuedBy: string;
}

export interface StationZeroV3OrderRevision {
  orderRevision: number;
  order: StationZeroV3CommanderOrder;
  orderDigest: string;
  createdAt: string;
}

export interface StationZeroV3OrderHead {
  schemaVersion: 1;
  kind: "ordivon.game.station-zero-v3-order-head";
  runId: string;
  planningId: string;
  orderRevision: number;
  orderDigest: string;
  status: "draft" | "previewed" | "committed";
  previewId: string | null;
  previewDigest: string | null;
  committedPreviewId: string | null;
  committedAt: string | null;
  updatedAt: string;
}

export interface StationZeroV3AgentKnownActor {
  actorId: string;
  name: string;
  roleId: string;
  factionId: StationZeroFactionId | null;
  lastKnownZoneId: string;
  observedLifeState: StationZeroV3WorldState["actors"][string]["lifeState"];
  observedHealthBand: "healthy" | "wounded" | "critical" | "unknown";
  confidence: "confirmed" | "estimated" | "stale";
  observedAtTurn: number;
}

export interface StationZeroV3AgentCandidate {
  candidateId: string;
  actorId: string;
  factionId: StationZeroFactionId;
  intent: StationZeroActorIntent;
  label: string;
  rationaleHint: string;
  tags: string[];
}

export interface StationZeroV3AgentResponsibility {
  responsibilityId: string;
  kind: "search-civilian" | "recover-civilian" | "support-civilian-recovery";
  objectiveId: "rescue-two-civilians";
  targetActorId: string | null;
  targetZoneId: string;
  blockerActorIds: string[];
}

export interface StationZeroV3AgentContext {
  schemaVersion: 1;
  kind: "ordivon.game.station-zero-v3-agent-context";
  contextId: string;
  planningId: string;
  worldRevision: number;
  worldDigest: string;
  factionId: StationZeroFactionId;
  actor: {
    actorId: string;
    name: string;
    roleId: string;
    zoneId: string;
    zoneName: string;
    lifeState: StationZeroV3WorldState["actors"][string]["lifeState"];
    health: number;
    maximumHealth: number;
    actionPoints: number;
    capabilityIds: string[];
    traitIds: string[];
    statusIds: string[];
    inventoryItemIds: string[];
  };
  environment: {
    batteryCharge: number;
    oxygen: number;
    reactorHeat: number;
    biomass: number;
    alertLevel: number;
  };
  known: {
    zoneIds: string[];
    frontierZoneIds: string[];
    actors: StationZeroV3AgentKnownActor[];
    systemIds: string[];
    hazardIds: string[];
    groundItemIds: string[];
    reportIds: string[];
  };
  objectiveIds: string[];
  playerOrder: StationZeroV3CommanderOrder | null;
  responsibility: StationZeroV3AgentResponsibility | null;
  allowedDirectiveIds: string[];
  candidates: StationZeroV3AgentCandidate[];
  contextDigest: string;
}

export interface StationZeroV3AgentDecision {
  schemaVersion: 1;
  kind: "ordivon.game.station-zero-v3-agent-decision";
  contextId: string;
  contextDigest: string;
  actorId: string;
  factionId: StationZeroFactionId;
  candidateId: string;
  directiveId: string | null;
  rationale: string;
  confidence: number;
  providerId: string;
}

export interface StationZeroV3PolicyDecision {
  policyDecisionId: string;
  actorId: string;
  factionId: StationZeroFactionId;
  leaderActorId: string;
  directiveId: string;
  candidateId: string;
  intent: StationZeroActorIntent;
  rationale: string;
}

export interface StationZeroV3FactionPlanExplanation {
  factionId: StationZeroFactionId;
  directiveId: string;
  summary: string;
  risks: string[];
  actorIntents: Array<{
    actorId: string;
    actorName: string;
    roleId: string;
    controllerKind: "agent" | "policy";
    intent: StationZeroActorIntent;
    label: string;
    rationale: string;
    confidence: number | null;
    responsibility: StationZeroV3AgentResponsibility | null;
  }>;
}

export interface StationZeroV3PlanPreview {
  schemaVersion: 1;
  kind: "ordivon.game.station-zero-v3-plan-preview";
  previewId: string;
  runId: string;
  planningId: string;
  worldRevision: number;
  worldDigest: string;
  orderRevision: number;
  orderDigest: string;
  providerId: string;
  generatedAt: string;
  playerOrder: StationZeroV3CommanderOrder;
  standingOrders: StationZeroStandingOrder[];
  commanderAction: StationZeroCommanderAction | null;
  contexts: StationZeroV3AgentContext[];
  agentDecisions: StationZeroV3AgentDecision[];
  policyDecisions: StationZeroV3PolicyDecision[];
  factionPlans: Record<StationZeroFactionId, StationZeroFactionTurnPlan>;
  explanations: Record<StationZeroFactionId, StationZeroV3FactionPlanExplanation>;
  warnings: string[];
  previewDigest: string;
}

export interface StationZeroV3PlayerPlanView {
  previewId: string;
  previewDigest: string;
  generatedAt: string;
  orderRevision: number;
  providerId: string;
  summary: string;
  risks: string[];
  commanderAction: {
    commanderAbilityId: string;
    label: string;
    targetLabel: string;
  } | null;
  actorIntents: Array<{
    actorId: string;
    actorName: string;
    roleId: string;
    action: string;
    rationale: string;
    confidence: number | null;
    responsibility: StationZeroV3AgentResponsibility | null;
  }>;
  enemyPlansSealed: Array<{
    factionId: "pirate" | "swarm";
    status: "sealed";
    planDigest: string;
  }>;
  warnings: string[];
}

export interface StationZeroV3AftermathView {
  turnSequence: number;
  turnBatchId: string;
  visibleFacts: Array<{
    factId: string;
    kind: string;
    summary: string;
  }>;
  ownIntentResults: Array<{
    actorId: string;
    actorName: string;
    status: StationZeroIntentResolutionStatus;
    reason: string;
  }>;
}

export interface StationZeroV3PlayView extends StationZeroV3MissionControlView {
  experience: {
    order: StationZeroV3CommanderOrder | null;
    orderRevision: number | null;
    orderDigest: string | null;
    preview: StationZeroV3PlayerPlanView | null;
    canEditOrder: boolean;
    canGeneratePreview: boolean;
    canCommitPreview: boolean;
  };
  map: {
    rooms: Array<{
      roomId: string;
      name: string;
      known: boolean;
      zones: Array<{
        zoneId: string;
        name: string;
        known: boolean;
        cover: "none" | "half" | "full" | "unknown";
        ownActorIds: string[];
        contactActorIds: string[];
        systemIds: string[];
        hazardIds: string[];
        groundItemIds: string[];
      }>;
    }>;
  };
  aftermath: StationZeroV3AftermathView | null;
  outcomes: {
    rescue: StationZeroV3WorldState["factions"]["rescue"]["outcome"];
    pirate: StationZeroV3WorldState["factions"]["pirate"]["outcome"];
    swarm: StationZeroV3WorldState["factions"]["swarm"]["outcome"];
    reason: string | null;
  };
}

export interface StationZeroV3PlayCatalog {
  schemaVersion: 1;
  kind: "ordivon.game.station-zero-v3-play-catalog";
  objectives: Array<{ objectiveId: StationZeroV3CommanderOrder["primaryObjectiveId"]; label: string; description: string }>;
  postures: Array<{ posture: StationZeroV3CommandPosture; label: string; description: string }>;
  formations: Array<{ formation: StationZeroV3Formation; label: string; description: string }>;
  commanderDirectives: Array<{ directiveId: StationZeroV3CommanderDirectiveId; label: string; description: string }>;
  lethalForce: Array<{ value: StationZeroV3CommanderOrder["lethalForce"]; label: string }>;
  lootPolicies: Array<{ value: StationZeroV3CommanderOrder["lootPolicy"]; label: string }>;
}

export interface StationZeroV3PlayRunSummary {
  runId: string;
  status: "running" | "terminal";
  turn: number;
  turnLimit: number;
  createdAt: string;
  outcome: StationZeroV3WorldState["factions"]["rescue"]["outcome"];
}

export interface StationZeroV3OrderSaveReceipt {
  runId: string;
  planningId: string;
  orderRevision: number;
  orderDigest: string;
  idempotent: boolean;
}

export interface StationZeroV3PreviewReceipt {
  preview: StationZeroV3PlanPreview;
  idempotent: boolean;
}

export interface StationZeroV3CommitReceipt {
  runId: string;
  planningId: string;
  previewId: string;
  turnSequence: number;
  worldRevision: number;
  hostState: string;
  nextPlanningId: string | null;
}

export type StationZeroV3AgentProviderFactory = (
  factionId: StationZeroFactionId,
  actorId: string,
) => StationZeroV3AgentProvider;

export interface StationZeroV3AgentProvider {
  readonly providerId: string;
  decide(context: StationZeroV3AgentContext): Promise<StationZeroV3AgentDecision>;
}

export type StationZeroV3PlanningLifecycle = StationZeroV3PlanningStatus;
export type StationZeroV3OwnActorView = StationZeroV3MissionControlActorView;
export type StationZeroV3KnownContactView = StationZeroV3MissionControlContactView;
