import type { ProtocolJson } from "./canonical.ts";

export interface StateRef {
  ref: string;
  digest: `sha256:${string}`;
}

export interface ArtifactRef {
  ref: string;
  kind: string;
  digest: `sha256:${string}`;
}

export interface TaskDescriptor {
  schemaVersion: 1;
  kind: "ordivon.host-task-descriptor";
  taskId: string;
  goalId: string;
  workloadId: string;
  assigneeRef: string | null;
  providerPolicyRef: string | null;
  domainRef: string | null;
  configurationDigests: `sha256:${string}`[];
}

export interface ContextBlock {
  blockId: string;
  kind: string;
  priority: number;
  required: boolean;
  freshness: "current" | "checkpoint" | "historical";
  sourceRef: string;
  sourceOwner: "host" | "runtime" | "domain" | "provider" | "human";
  sourceDigest: `sha256:${string}`;
  trust: "authoritative" | "verified" | "reported" | "inferred";
  validityRefs: StateRef[];
  payload: ProtocolJson;
}

export type DecisionCandidateKind =
  | "domain-action"
  | "propose-effect"
  | "observe-dispatch"
  | "request-human"
  | "wait"
  | "finish";

export interface DecisionCandidate {
  candidateId: string;
  kind: DecisionCandidateKind;
  summary: string;
  proposalDigest: `sha256:${string}` | null;
  effectId: string | null;
  dispatchId: string | null;
  requiredStateRefs: StateRef[];
}

export interface CompiledContextPayload {
  schemaVersion: 1;
  kind: "ordivon.compiled-context";
  taskId: string;
  workloadId: string;
  stateRefs: StateRef[];
  blocks: ContextBlock[];
  candidates: DecisionCandidate[];
  completedEffectIds: string[];
  unresolvedDispatchIds: string[];
  instruction: string;
}

export interface CompiledContextEnvelope {
  schemaVersion: 1;
  kind: "ordivon.compiled-context-envelope";
  digest: `sha256:${string}`;
  byteLength: number;
  manifest: {
    tokenBudget: number;
    estimatedTokens: number;
    selectedBlockIds: string[];
    omittedBlockIds: string[];
  };
  payload: CompiledContextPayload;
}

export interface ModelInvocationIntent {
  schemaVersion: 1;
  kind: "ordivon.model-invocation-intent";
  invocationId: string;
  taskId: string;
  contextDigest: `sha256:${string}`;
  contextObjectDigest: `sha256:${string}`;
  providerPolicyRef: string;
}

export interface ModelDecision {
  schemaVersion: 1;
  kind: "ordivon.model-decision";
  invocationId: string;
  contextDigest: `sha256:${string}`;
  candidateId: string | null;
  providerId: string;
  confidencePermille: number;
  rationale: string;
}

export interface AdmittedDecision {
  schemaVersion: 1;
  kind: "ordivon.admitted-decision";
  contextDigest: `sha256:${string}`;
  candidate: DecisionCandidate | null;
  providerId: string;
  confidencePermille: number;
  rationale: string;
}

export interface DispatchEnvelope {
  schemaVersion: 1;
  kind: "ordivon.dispatch-envelope";
  dispatchId: string;
  effectId: string;
  executorId: string;
  requestDigest: `sha256:${string}`;
  idempotencyKey: string;
  requiredStateRefs: StateRef[];
  expectedObservationKind: string;
}

export interface ObservationEnvelope {
  schemaVersion: 1;
  kind: "ordivon.observation-envelope";
  dispatchId: string;
  executorId: string;
  status: "accepted" | "running" | "succeeded" | "failed" | "rejected" | "unknown";
  payloadDigest: `sha256:${string}`;
  evidenceRefs: ArtifactRef[];
}

export interface VerificationResultItem {
  subjectRef: string;
  decisionDigest: `sha256:${string}`;
  status: "succeeded" | "failed" | "rejected" | "not-selected";
  reason: string | null;
  evidenceDigest: `sha256:${string}`;
}

export interface VerificationReceipt {
  schemaVersion: 1;
  kind: "ordivon.verification-receipt";
  dispatchId: string;
  method: string;
  accepted: boolean;
  observationDigest: `sha256:${string}`;
  resultItems: VerificationResultItem[];
}

export interface TaskOutcome {
  schemaVersion: 1;
  kind: "ordivon.task-outcome";
  taskId: string;
  goalId: string;
  status: "completed" | "failed" | "cancelled" | "blocked";
  verificationDigest: `sha256:${string}` | null;
  artifactRefs: ArtifactRef[];
}

export type HostWorkloadObject =
  | TaskDescriptor
  | CompiledContextEnvelope
  | ModelInvocationIntent
  | ModelDecision
  | AdmittedDecision
  | DispatchEnvelope
  | ObservationEnvelope
  | VerificationReceipt
  | TaskOutcome;
