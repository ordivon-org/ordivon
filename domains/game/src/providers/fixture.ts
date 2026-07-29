import type { CompiledAgentContext, ContextOperationCandidate } from "../host/context.ts";
import type { OperationDecision, OperationProvider } from "./types.ts";

function find(
  context: CompiledAgentContext,
  predicate: (candidate: ContextOperationCandidate) => boolean,
): ContextOperationCandidate | null {
  return context.payload.allowedOperations.find(predicate) ?? null;
}

export class RecoveryOperationProvider implements OperationProvider {
  readonly providerId = "fixture-recovery-operation-v1";

  async decide(context: CompiledAgentContext): Promise<OperationDecision> {
    const { objectives, telemetry } = context.payload;
    let selected: ContextOperationCandidate | null = null;
    if (!objectives.coolingOperational) {
      selected = find(context, (candidate) => candidate.kind === "repair_system" && candidate.target.id === "cooling");
    } else if (!objectives.coolingPowered && telemetry.reactorHeat > (objectives.lifeSupportPowered ? 70 : 20)) {
      selected = find(context, (candidate) => candidate.kind === "set_power" && candidate.target.id === "cooling" && candidate.successCondition.kind === "system_power" && candidate.successCondition.powered);
    } else if (!objectives.breachSealed) {
      selected = find(context, (candidate) => candidate.kind === "seal_hazard");
    } else if (!objectives.lifeSupportOperational) {
      selected = find(context, (candidate) => candidate.kind === "repair_system" && candidate.target.id === "life-support");
    } else if (!objectives.lifeSupportPowered) {
      selected = find(context, (candidate) => candidate.kind === "set_power" && candidate.target.id === "life-support" && candidate.successCondition.kind === "system_power" && candidate.successCondition.powered);
    } else if (objectives.coolingPowered && telemetry.reactorHeat <= 20) {
      selected = find(context, (candidate) => candidate.kind === "set_power" && candidate.target.id === "cooling" && candidate.successCondition.kind === "system_power" && !candidate.successCondition.powered);
    } else if (!objectives.crewStabilized) {
      selected = find(context, (candidate) => candidate.kind === "stabilize_crew");
    } else if (!objectives.communicationsOperational) {
      selected = find(context, (candidate) => candidate.kind === "repair_system" && candidate.target.id === "communications");
    } else if (!objectives.communicationsPowered) {
      selected = find(context, (candidate) => candidate.kind === "set_power" && candidate.target.id === "communications" && candidate.successCondition.kind === "system_power" && candidate.successCondition.powered);
    } else if (!objectives.distressSent) {
      selected = find(context, (candidate) => candidate.kind === "send_distress");
    }
    selected ??= find(context, (candidate) => candidate.kind === "wait");
    return {
      providerId: this.providerId,
      contextId: context.contextId,
      selectedOperationCandidateId: selected?.operationCandidateId ?? null,
      riskLevel: selected?.projectedTerminalFailure ? "critical" : "medium",
      confidence: selected ? 1 : 0,
      rationale: selected
        ? `Choose admitted strategic Operation: ${selected.label}`
        : "No admitted strategic Operation is available.",
    };
  }
}
