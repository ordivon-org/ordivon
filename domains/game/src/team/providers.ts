import type { WorldState } from "../model.ts";
import { ProviderAdapterError } from "../providers/types.ts";
import type { CompiledTeamContext, TeamProviderDecision } from "./model.ts";

export interface TeamDecisionProvider {
  readonly providerId: string;
  decide(context: CompiledTeamContext): Promise<TeamProviderDecision>;
  evidenceMetadata?(): Record<string, unknown> | null;
}

export class TeamDecisionAdmissionError extends Error {
  readonly code: "wrong_context" | "stale_world" | "invented_action" | "invalid_decision";
  constructor(code: TeamDecisionAdmissionError["code"], message: string) {
    super(message);
    this.name = "TeamDecisionAdmissionError";
    this.code = code;
  }
}

export function validateTeamProviderDecision(decision: TeamProviderDecision): void {
  if (!decision.providerId.trim() || !decision.rationale.trim()) {
    throw new TeamDecisionAdmissionError("invalid_decision", "providerId and rationale are required");
  }
  if (!Number.isFinite(decision.confidence) || decision.confidence < 0 || decision.confidence > 1) {
    throw new TeamDecisionAdmissionError("invalid_decision", "confidence must be between 0 and 1");
  }
}

export function parseTeamProviderDecision(
  context: CompiledTeamContext,
  value: unknown,
  providerId: string,
): TeamProviderDecision {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new ProviderAdapterError("invalid_output", "Team Provider Decision must be one JSON object");
  }
  const record = value as Record<string, unknown>;
  const expected = ["confidence", "contextId", "rationale", "selectedActionCandidateId"];
  if (Object.keys(record).sort().join("|") !== expected.join("|")) {
    throw new ProviderAdapterError("invalid_output", "Team Provider Decision fields differ from the contract");
  }
  if (
    typeof record.contextId !== "string" ||
    (record.selectedActionCandidateId !== null && typeof record.selectedActionCandidateId !== "string") ||
    typeof record.confidence !== "number" ||
    typeof record.rationale !== "string"
  ) {
    throw new ProviderAdapterError("invalid_output", "Team Provider Decision field types are invalid");
  }
  const decision: TeamProviderDecision = {
    providerId,
    contextId: record.contextId,
    selectedActionCandidateId: record.selectedActionCandidateId,
    confidence: record.confidence,
    rationale: record.rationale,
  };
  try { validateTeamProviderDecision(decision); }
  catch (error) { throw new ProviderAdapterError("invalid_output", "Team Provider Decision values are invalid", { cause: error }); }
  if (decision.contextId !== context.contextId) {
    throw new ProviderAdapterError("invalid_output", "Team Provider copied another Context identity");
  }
  if (
    decision.selectedActionCandidateId !== null &&
    !context.allowedActions.some((candidate) => candidate.actionCandidateId === decision.selectedActionCandidateId)
  ) {
    throw new ProviderAdapterError("invalid_output", "Team Provider invented an Action identity");
  }
  return decision;
}

export function admitTeamProviderDecision(
  context: CompiledTeamContext,
  currentState: WorldState,
  currentWorldDigest: string,
  decision: TeamProviderDecision,
) {
  validateTeamProviderDecision(decision);
  if (decision.contextId !== context.contextId) {
    throw new TeamDecisionAdmissionError("wrong_context", "Team Decision targets another Context");
  }
  if (currentState.revision !== context.worldRevision || currentWorldDigest !== context.worldDigest) {
    throw new TeamDecisionAdmissionError("stale_world", "Team Decision targets a stale world");
  }
  if (decision.selectedActionCandidateId === null) return null;
  const candidate = context.allowedActions.find((entry) => entry.actionCandidateId === decision.selectedActionCandidateId);
  if (!candidate) throw new TeamDecisionAdmissionError("invented_action", "Team Decision selected an Action outside the admitted frontier");
  return candidate;
}

export interface FixtureTeamProviderOptions {
  breachStrategy?: "security-contain" | "engineer-seal";
  failActors?: string[];
}

const ENGINEER_SCHEDULE = new Map<number, string>([
  [0, "move:power-junction"],
  [1, "move:reactor"],
  [2, "repair:cooling"],
  [3, "move:power-junction"],
  [4, "power:cooling:true"],
  [5, "move:storage"],
  [6, "pickup:spare-parts:2"],
  [7, "move:power-junction"],
  [8, "move:life-support"],
  [9, "repair:life-support"],
  [10, "move:power-junction"],
  [11, "power:life-support:true"],
  [12, "move:communications"],
  [13, "repair:communications"],
  [14, "move:power-junction"],
  [15, "power:communications:true"],
  [16, "move:communications"],
  [17, "distress:communications"],
]);

const MEDIC_SCHEDULE = new Map<number, string>([
  [0, "move:power-junction"],
  [1, "move:medical-bay"],
  [2, "pickup:medkit:1"],
  [3, "stabilize:crew-01"],
]);

const SECURITY_SCHEDULE = new Map<number, string>([
  [0, "move:power-junction"],
  [1, "move:storage"],
  [2, "move:maintenance"],
  [3, "contain:maintenance-breach"],
]);

export class FixtureTeamProvider implements TeamDecisionProvider {
  readonly providerId = "fixture-team-policy-v1";
  readonly breachStrategy: "security-contain" | "engineer-seal";
  readonly failActors: Set<string>;

  constructor(options: FixtureTeamProviderOptions = {}) {
    this.breachStrategy = options.breachStrategy ?? "security-contain";
    this.failActors = new Set(options.failActors ?? []);
  }

  async decide(context: CompiledTeamContext): Promise<TeamProviderDecision> {
    if (this.failActors.has(context.actorId)) {
      throw new ProviderAdapterError("process_failed", `Fixture Provider failed for ${context.actorId}`);
    }
    const desired = this.desiredAction(context);
    const candidate = context.allowedActions.find((entry) => entry.actionId === desired)
      ?? context.allowedActions.find((entry) => entry.actionId === "wait")
      ?? context.allowedActions[0]
      ?? null;
    return {
      providerId: this.providerId,
      contextId: context.contextId,
      selectedActionCandidateId: candidate?.actionCandidateId ?? null,
      confidence: candidate ? 1 : 0,
      rationale: candidate ? `Fixture schedule selected ${candidate.actionId}` : "No admitted action is available",
    };
  }

  private desiredAction(context: CompiledTeamContext): string {
    if (context.actorId === "engineer-01") {
      if (this.breachStrategy === "engineer-seal" && context.worldRevision === 7) return "move:maintenance";
      if (this.breachStrategy === "engineer-seal" && context.worldRevision === 8) return "seal:maintenance-breach";
      return ENGINEER_SCHEDULE.get(context.worldRevision) ?? "wait";
    }
    if (context.actorId === "medic-01") return MEDIC_SCHEDULE.get(context.worldRevision) ?? "wait";
    if (context.actorId === "security-01") {
      if (this.breachStrategy === "engineer-seal") return "wait";
      return SECURITY_SCHEDULE.get(context.worldRevision) ?? "wait";
    }
    return "wait";
  }
}
