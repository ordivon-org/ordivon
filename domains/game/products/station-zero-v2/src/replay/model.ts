import type { WorldFact, WorldState } from "../model.ts";
import type {
  ActionProposal,
  AuthorityDecision,
  AuthorityGrant,
  TeamContextReference,
  TeamDispatch,
  TeamEffect,
  TeamMessage,
  TeamObservation,
  TeamRound,
  TeamTickPlan,
} from "../team/model.ts";

export interface PointInTimeReplayResult {
  runId: string;
  revision: number;
  state: WorldState;
  digest: string;
  snapshotRevision: number;
  replayedCommandCount: number;
  verified: true;
}

export type EvidenceNodeKind =
  | "actor"
  | "world-state"
  | "world-event"
  | "team-round"
  | "team-context"
  | "team-proposal"
  | "team-tick-plan"
  | "team-message"
  | "authority-decision"
  | "authority-grant"
  | "host-contract"
  | "host-event"
  | "effect"
  | "dispatch"
  | "observation";

export type EvidenceEdgeKind =
  | "advances-from"
  | "produces-state"
  | "prepared-from"
  | "belongs-to"
  | "proposed-from"
  | "authorized-by"
  | "granted-for"
  | "selected-by"
  | "rejected-by"
  | "materializes"
  | "dispatches"
  | "observed-as"
  | "records"
  | "references"
  | "sent-by"
  | "addressed-to";

export interface EvidenceNode {
  nodeId: string;
  kind: EvidenceNodeKind;
  worldRevision: number | null;
  sequence: number | null;
  actorId: string | null;
  roundId: string | null;
  subjectId: string | null;
  payloadDigest: string;
  summary: string;
}

export interface EvidenceEdge {
  edgeId: string;
  kind: EvidenceEdgeKind;
  fromNodeId: string;
  toNodeId: string;
  required: boolean;
}

export interface RunEvidenceGraph {
  schemaVersion: 1;
  kind: "ordivon.game.run-evidence-graph";
  runId: string;
  terminalRevision: number;
  nodes: EvidenceNode[];
  edges: EvidenceEdge[];
  graphDigest: string;
}

export interface ReplayEvidenceReference {
  nodeId: string;
  kind: EvidenceNodeKind;
  payloadDigest: string;
  summary: string;
}

export interface ReplayFrame {
  schemaVersion: 1;
  kind: "ordivon.game.replay-frame";
  runId: string;
  revision: number;
  previousRevision: number | null;
  state: WorldState;
  digest: string;
  snapshotRevision: number;
  replayedCommandCount: number;
  worldEvent: ReplayEvidenceReference | null;
  round: TeamRound | null;
  contexts: TeamContextReference[];
  proposals: ActionProposal[];
  tickPlan: TeamTickPlan | null;
  effect: TeamEffect | null;
  dispatch: TeamDispatch | null;
  observation: TeamObservation | null;
  authorityDecisions: AuthorityDecision[];
  authorityGrants: AuthorityGrant[];
  messages: TeamMessage[];
  playerInterventions: ReplayEvidenceReference[];
  hostRecords: ReplayEvidenceReference[];
  facts: WorldFact[];
  evidenceNodeIds: string[];
  graphDigest: string;
  byteLength: number;
  verified: true;
}

export interface ReplaySummary {
  schemaVersion: 1;
  kind: "ordivon.game.replay-summary";
  runId: string;
  terminalRevision: number;
  terminalStatus: WorldState["mission"]["status"];
  terminalReason: string | null;
  terminalDigest: string;
  graphDigest: string;
  frameCount: number;
  nodeCounts: Record<EvidenceNodeKind, number>;
  edgeCount: number;
}

export interface ReplayFramePage {
  runId: string;
  fromRevision: number;
  limit: number;
  frames: ReplayFrame[];
  nextFromRevision: number | null;
  graphDigest: string;
}


export type DiagnosisEvidenceClass = "VERIFIED_DIRECT" | "VERIFIED_CONTRIBUTOR" | "COUNTERFACTUAL_SENSITIVE" | "CONTEXT_ONLY";
export interface NumericCurvePoint { revision: number; value: number; }
export interface BooleanCurvePoint { revision: number; value: boolean; }
export interface ItemLocationCurvePoint { revision: number; rooms: Record<string, number>; actors: Record<string, number>; consumed: number; total: number; }
export interface SystemCurvePoint { revision: number; integrity: number; powered: boolean; }
export interface ReplayCurves {
  schemaVersion: 1; kind: "ordivon.game.replay-curves"; runId: string; graphDigest: string; revisions: number[];
  battery: NumericCurvePoint[]; oxygen: NumericCurvePoint[]; reactorHeat: NumericCurvePoint[];
  actorHealth: Record<string, NumericCurvePoint[]>; crewHealth: Record<string, NumericCurvePoint[]>;
  systems: Record<string, SystemCurvePoint[]>; items: Record<string, ItemLocationCurvePoint[]>;
  objectives: Record<string, BooleanCurvePoint[]>; curvesDigest: string;
}
export type KeyTurnKind = "genesis" | "terminal" | "objective" | "resource-threshold" | "health-threshold" | "critical-item" | "authority" | "player" | "provider";
export interface ReplayKeyTurn { keyTurnId: string; revision: number; priority: number; kind: KeyTurnKind; title: string; detail: string; evidenceNodeIds: string[]; }
export interface DiagnosisClaim { claimId: string; evidenceClass: DiagnosisEvidenceClass; revision: number; title: string; explanation: string; evidenceNodeIds: string[]; }
export interface RunDiagnosis {
  schemaVersion: 1; kind: "ordivon.game.run-diagnosis"; runId: string;
  terminal: { status: WorldState["mission"]["status"]; reason: string | null; revision: number; digest: string; };
  graphDigest: string; curvesDigest: string; keyTurns: ReplayKeyTurn[]; claims: DiagnosisClaim[];
  unsupportedCounterfactualReason: string | null; diagnosisDigest: string;
}


export interface ReplayProjection {
  schemaVersion: 1;
  kind: "ordivon.game.replay-projection";
  runId: string;
  graph: RunEvidenceGraph;
  frames: ReplayFrame[];
  curves: ReplayCurves;
  keyTurns: ReplayKeyTurn[];
}

export interface ReplayReport {
  schemaVersion: 1;
  kind: "ordivon.game.replay-report";
  runId: string;
  summary: ReplaySummary;
  curves: ReplayCurves;
  keyTurns: ReplayKeyTurn[];
  diagnosis: RunDiagnosis;
}
