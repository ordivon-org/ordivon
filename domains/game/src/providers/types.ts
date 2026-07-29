import { sha256 } from "../digest.ts";
import type { WorldState } from "../model.ts";
import type { CompiledAgentContext, ContextOperationCandidate } from "../host/context.ts";

export type DecisionRiskLevel = "low" | "medium" | "high" | "critical";

export interface OperationDecision {
  providerId: string;
  contextId: string;
  selectedOperationCandidateId: string | null;
  riskLevel: DecisionRiskLevel;
  confidence: number;
  rationale: string;
}

export interface OperationProvider {
  readonly providerId: string;
  decide(context: CompiledAgentContext): Promise<OperationDecision>;
  evidenceMetadata?(): Record<string, unknown> | null;
}

export class DecisionAdmissionError extends Error {
  readonly code: "wrong_context" | "stale_world" | "invented_operation" | "invalid_decision";
  constructor(code: DecisionAdmissionError["code"], message: string) {
    super(message);
    this.name = "DecisionAdmissionError";
    this.code = code;
  }
}

export function validateOperationDecision(value: OperationDecision): void {
  if (!value.providerId || !value.rationale.trim()) {
    throw new DecisionAdmissionError("invalid_decision", "providerId and rationale are required");
  }
  if (!Number.isFinite(value.confidence) || value.confidence < 0 || value.confidence > 1) {
    throw new DecisionAdmissionError("invalid_decision", "confidence must be between 0 and 1");
  }
}

export function admitOperationDecision(
  context: CompiledAgentContext,
  currentState: WorldState,
  decision: OperationDecision,
): ContextOperationCandidate | null {
  validateOperationDecision(decision);
  if (decision.contextId !== context.contextId) {
    throw new DecisionAdmissionError("wrong_context", "Provider Decision targets another Context");
  }
  if (
    currentState.revision !== context.payload.run.worldRevision ||
    sha256(currentState) !== context.payload.run.worldDigest
  ) {
    throw new DecisionAdmissionError("stale_world", "Provider Decision targets a stale world");
  }
  if (decision.selectedOperationCandidateId === null) return null;
  const candidate = context.payload.allowedOperations.find(
    (operation) => operation.operationCandidateId === decision.selectedOperationCandidateId,
  );
  if (!candidate) {
    throw new DecisionAdmissionError("invented_operation", "Provider selected an Operation outside the admitted frontier");
  }
  return candidate;
}

export type ProviderAdapterErrorCode =
  | "unavailable"
  | "timeout"
  | "process_failed"
  | "invalid_output"
  | "invalid_usage";

export class ProviderAdapterError extends Error {
  readonly code: ProviderAdapterErrorCode;
  constructor(code: ProviderAdapterErrorCode, message: string, options?: ErrorOptions) {
    super(message, options);
    this.name = "ProviderAdapterError";
    this.code = code;
  }
}

interface ModelDecisionOutput {
  contextId: string;
  selectedOperationCandidateId: string | null;
  riskLevel: DecisionRiskLevel;
  confidence: number;
  rationale: string;
}

export function parseModelDecisionOutput(
  context: CompiledAgentContext,
  value: unknown,
  providerId: string,
): OperationDecision {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new ProviderAdapterError("invalid_output", "Provider Decision must be one JSON object");
  }
  const record = value as Record<string, unknown>;
  const expected = ["confidence", "contextId", "rationale", "riskLevel", "selectedOperationCandidateId"];
  if (Object.keys(record).sort().join("|") !== expected.join("|")) {
    throw new ProviderAdapterError("invalid_output", "Provider Decision fields differ from the contract");
  }
  const risks: DecisionRiskLevel[] = ["low", "medium", "high", "critical"];
  if (
    typeof record.contextId !== "string" ||
    (record.selectedOperationCandidateId !== null && typeof record.selectedOperationCandidateId !== "string") ||
    typeof record.riskLevel !== "string" || !risks.includes(record.riskLevel as DecisionRiskLevel) ||
    typeof record.confidence !== "number" ||
    typeof record.rationale !== "string"
  ) {
    throw new ProviderAdapterError("invalid_output", "Provider Decision field types are invalid");
  }
  const output = record as unknown as ModelDecisionOutput;
  const decision: OperationDecision = { providerId, ...output };
  try { validateOperationDecision(decision); }
  catch (error) { throw new ProviderAdapterError("invalid_output", "Provider Decision values are invalid", { cause: error }); }
  if (decision.contextId !== context.contextId) {
    throw new ProviderAdapterError("invalid_output", "Provider copied another Context identity");
  }
  if (
    decision.selectedOperationCandidateId !== null &&
    !context.payload.allowedOperations.some(
      (candidate) => candidate.operationCandidateId === decision.selectedOperationCandidateId,
    )
  ) {
    throw new ProviderAdapterError("invalid_output", "Provider invented an Operation identity");
  }
  return decision;
}
