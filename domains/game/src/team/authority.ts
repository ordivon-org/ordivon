import { sha256 } from "../digest.ts";
import type { PrimitiveWorldCommand, WorldState } from "../model.ts";
import type {
  ActorProfile,
  AuthorityAttributes,
  AuthorityDecision,
  AuthorityOutcome,
  AuthorityPolicyMode,
  TeamActionCandidate,
} from "./model.ts";

function target(command: PrimitiveWorldCommand): AuthorityAttributes["target"] {
  switch (command.kind) {
    case "move": return { objectId: command.targetRoomId, domain: "room", criticality: "routine" };
    case "pickup_item": return { objectId: command.itemId, domain: "item", criticality: "routine" };
    case "repair_system": return { objectId: command.targetSystemId, domain: "system", criticality: command.targetSystemId === "cooling" ? "critical" : "important" };
    case "set_power": return { objectId: command.targetSystemId, domain: "system", criticality: command.targetSystemId === "life-support" ? "critical" : "important" };
    case "seal_hull": return { objectId: command.targetHazardId, domain: "hazard", criticality: "critical" };
    case "contain_hazard": return { objectId: command.targetHazardId, domain: "hazard", criticality: "critical" };
    case "stabilize_crew": return { objectId: command.targetCrewId, domain: "crew", criticality: "important" };
    case "send_distress": return { objectId: command.targetSystemId, domain: "mission", criticality: "important" };
    case "wait": return { objectId: "simulation-clock", domain: "time", criticality: "routine" };
  }
}

function riskTags(command: PrimitiveWorldCommand): string[] {
  switch (command.kind) {
    case "set_power": return command.enabled ? ["power-change"] : ["power-change", "shutdown"];
    case "seal_hull": return ["irreversible", "hazard-control"];
    case "contain_hazard": return ["hazard-control", "alternative-objective"];
    case "send_distress": return ["external-signal"];
    case "repair_system": return ["resource-consuming", "system-change"];
    case "stabilize_crew": return ["resource-consuming", "medical"];
    case "move":
    case "pickup_item":
    case "wait": return [];
  }
}

function communicationAvailable(state: WorldState): boolean {
  const communications = state.systems.communications;
  return Boolean(communications?.powered && (communications.integrity ?? 0) >= 0.8);
}

function outcomeFor(mode: AuthorityPolicyMode, command: PrimitiveWorldCommand): { outcome: AuthorityOutcome; reason: string } {
  const criticalShutdown = command.kind === "set_power" && !command.enabled && command.targetSystemId === "life-support";
  const highRisk = command.kind === "set_power" || command.kind === "seal_hull" || command.kind === "contain_hazard";
  if (criticalShutdown) {
    return mode === "locked"
      ? { outcome: "deny", reason: "locked policy denies life-support shutdown" }
      : { outcome: "require-human", reason: "life-support shutdown requires explicit human authority" };
  }
  if (mode === "supervised" && (highRisk || command.kind === "send_distress")) {
    return { outcome: "require-human", reason: "supervised policy requires human authority for this action" };
  }
  if (mode === "locked" && highRisk) {
    return { outcome: "require-human", reason: "locked policy requires human authority for high-risk action" };
  }
  return { outcome: "permit", reason: "policy permits the actor-scoped action" };
}

export function evaluateAuthority(
  runId: string,
  profile: ActorProfile,
  capabilities: string[],
  actionCandidateId: string,
  contextDigest: string,
  worldDigest: string,
  state: WorldState,
  command: PrimitiveWorldCommand,
  policyMode: AuthorityPolicyMode,
  policyRevision = 1,
): AuthorityDecision {
  const attributes: AuthorityAttributes = {
    subject: {
      actorId: profile.actorId,
      role: profile.role,
      capabilities: [...capabilities].sort(),
      mandate: profile.role === "coordinator" ? ["coordinate"] : [profile.role],
    },
    action: { operationKind: command.kind, riskTags: riskTags(command) },
    target: target(command),
    environment: {
      missionPhase: state.mission.status === "running" ? "running" : "terminal",
      oxygenBand: state.resources.oxygen < 25 ? "critical" : state.resources.oxygen < 50 ? "low" : "stable",
      reactorBand: state.resources.reactorHeat > 90 ? "critical" : state.resources.reactorHeat > 70 ? "high" : "stable",
      communicationAvailable: communicationAvailable(state),
    },
    policyId: `${profile.authorityPolicyId}:${policyMode}`,
  };
  const result = outcomeFor(policyMode, command);
  const identity = {
    runId, actorId: profile.actorId, actionCandidateId, contextDigest, worldDigest,
    policyMode, policyRevision, attributes, outcome: result.outcome,
  };
  return {
    decisionId: `authority-decision:${sha256(identity)}`,
    runId,
    actorId: profile.actorId,
    actionCandidateId,
    contextDigest,
    worldDigest,
    policyMode,
    policyRevision,
    attributes,
    outcome: result.outcome,
    reason: result.reason,
    createdAt: new Date(state.turn * 1_000).toISOString(),
  };
}

export function candidateAllowed(candidate: Pick<TeamActionCandidate, "authorityOutcome">, granted: boolean): boolean {
  return candidate.authorityOutcome === "permit" || (candidate.authorityOutcome === "require-human" && granted);
}
