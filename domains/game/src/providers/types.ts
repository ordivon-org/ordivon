import { sha256 } from "../digest.ts";
import type { WorldState } from "../model.ts";
import type { CompiledAgentContext } from "../host/context.ts";
import type { OperationCandidate } from "../host/operations.ts";

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
): OperationCandidate | null {
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
