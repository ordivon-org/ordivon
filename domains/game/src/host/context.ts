import { canonicalJson, sha256 } from "../digest.ts";
import type { JournalEvent, WorldFact, WorldState } from "../model.ts";
import type { RunMetadata } from "../run.ts";
import { ENGINEER_ID, isOperational } from "../scenario.ts";
import type { AgentProjection } from "./model.ts";
import {
  compileOperationFrontier,
  type OperationCandidate,
  type OperationCandidateCore,
  type OperationProjection,
} from "./operations.ts";
import {
  analyzeGoalStrategy,
  type GoalStrategyAnalysis,
  type OperationStrategyAnalysis,
} from "./strategy.ts";

export const MAX_AGENT_CONTEXT_BYTES = 16 * 1024;

export type ContextOperationStrategy = Pick<OperationStrategyAnalysis,
  | "classification"
  | "strategicRank"
  | "selectionClass"
  | "projectedVictory"
  | "lowerBoundTimeFeasible"
  | "optimisticStepSlack"
  | "newlySatisfied"
  | "regressed"
  | "urgentMitigationsAdvanced"
  | "controlAdvantages"
  | "oneStepLookahead"
  | "summary"
>;

export interface ContextOperationCandidate extends OperationCandidateCore {
  planPreview: string[];
  projected: OperationProjection;
  projectedTerminalFailure: boolean;
  strategy: ContextOperationStrategy;
}

function projectOperationCandidate(candidate: OperationCandidate): ContextOperationCandidate {
  return {
    operationCandidateId: candidate.operationCandidateId,
    kind: candidate.kind,
    target: candidate.target,
    label: candidate.label,
    successCondition: candidate.successCondition,
    requiredWorldRevision: candidate.requiredWorldRevision,
    requiredWorldDigest: candidate.requiredWorldDigest,
    planId: candidate.planId,
    estimatedPrimitiveSteps: candidate.estimatedPrimitiveSteps,
    planPreview: candidate.planPreview,
    projected: candidate.projected,
    projectedTerminalFailure: candidate.projectedTerminalFailure,
    strategy: {
      classification: candidate.strategy.classification,
      strategicRank: candidate.strategy.strategicRank,
      selectionClass: candidate.strategy.selectionClass,
      projectedVictory: candidate.strategy.projectedVictory,
      lowerBoundTimeFeasible: candidate.strategy.lowerBoundTimeFeasible,
      optimisticStepSlack: candidate.strategy.optimisticStepSlack,
      newlySatisfied: candidate.strategy.newlySatisfied,
      regressed: candidate.strategy.regressed,
      urgentMitigationsAdvanced: candidate.strategy.urgentMitigationsAdvanced,
      controlAdvantages: candidate.strategy.controlAdvantages,
      oneStepLookahead: candidate.strategy.oneStepLookahead,
      summary: candidate.strategy.summary,
    },
  };
}

export interface AgentContextPayload {
  schemaVersion: 2;
  kind: "ordivon.game.agent-context";
  contextId: string;
  run: {
    runId: string;
    scenarioId: string;
    scenarioVersion: number;
    rulesetId: string;
    rulesetVersion: number;
    stateSchemaVersion: number;
    worldRevision: number;
    simulationTick: number;
    worldDigest: string;
  };
  agent: {
    actorId: string;
    location: string;
    health: number;
    inventory: WorldState["agents"][string]["inventory"];
    capabilities: string[];
  };
  goal: {
    goalId: string;
    revision: number;
    statement: string;
    successCondition: AgentProjection["goal"]["successCondition"];
    status: AgentProjection["goal"]["status"];
  };
  task: {
    taskId: string;
    revision: number;
    phase: AgentProjection["task"]["phase"];
    activeAttemptId: string | null;
    completedAttemptIds: string[];
    blockers: string[];
  };
  mission: {
    status: WorldState["mission"]["status"];
    reason: string | null;
    turnsRemaining: number;
  };
  telemetry: {
    batteryCharge: number;
    batteryInitial: number;
    oxygen: number;
    reactorHeat: number;
  };
  objectives: {
    coolingOperational: boolean;
    coolingPowered: boolean;
    breachSealed: boolean;
    lifeSupportOperational: boolean;
    lifeSupportPowered: boolean;
    crewStabilized: boolean;
    communicationsOperational: boolean;
    communicationsPowered: boolean;
    distressSent: boolean;
  };
  strategy: {
    goal: GoalStrategyAnalysis;
    decisionPolicy: string[];
  };
  recentFacts: WorldFact[];
  allowedOperations: ContextOperationCandidate[];
  instruction: string;
}

export interface CompiledAgentContext {
  payload: AgentContextPayload;
  contextId: string;
  digest: string;
  byteLength: number;
}

export class AgentContextError extends Error {
  readonly code: "context_too_large" | "missing_engineer";
  constructor(code: AgentContextError["code"], message: string) {
    super(message);
    this.name = "AgentContextError";
    this.code = code;
  }
}

function recentFacts(events: JournalEvent[], limit: number): WorldFact[] {
  const output = events.flatMap((record) => record.event.facts ?? []);
  return output.slice(Math.max(0, output.length - limit));
}

function basePayload(
  run: RunMetadata,
  state: WorldState,
  projection: AgentProjection,
  events: JournalEvent[],
  factLimit: number,
): Omit<AgentContextPayload, "contextId"> {
  const engineer = state.agents[ENGINEER_ID];
  if (!engineer) throw new AgentContextError("missing_engineer", "Engineer is missing from the world");
  const cooling = state.systems.cooling;
  const lifeSupport = state.systems["life-support"];
  const communications = state.systems.communications;
  return {
    schemaVersion: 2,
    kind: "ordivon.game.agent-context",
    run: {
      runId: run.runId,
      scenarioId: run.scenarioId,
      scenarioVersion: run.scenarioVersion,
      rulesetId: run.rulesetId,
      rulesetVersion: run.rulesetVersion,
      stateSchemaVersion: run.stateSchemaVersion,
      worldRevision: state.revision,
      simulationTick: state.turn,
      worldDigest: sha256(state),
    },
    agent: {
      actorId: engineer.id,
      location: engineer.location,
      health: engineer.health,
      inventory: structuredClone(engineer.inventory),
      capabilities: [...engineer.capabilities].sort(),
    },
    goal: {
      goalId: projection.goal.goalId,
      revision: projection.goal.revision,
      statement: projection.goal.statement,
      successCondition: projection.goal.successCondition,
      status: projection.goal.status,
    },
    task: {
      taskId: projection.task.taskId,
      revision: projection.task.revision,
      phase: projection.task.phase,
      activeAttemptId: projection.task.activeAttemptId,
      completedAttemptIds: [...projection.task.completedAttemptIds],
      blockers: [...projection.task.blockers],
    },
    mission: {
      status: state.mission.status,
      reason: state.mission.reason,
      turnsRemaining: Math.max(0, state.mission.turnLimit - state.turn),
    },
    telemetry: {
      batteryCharge: state.resources.batteryCharge,
      batteryInitial: state.resources.batteryInitial,
      oxygen: state.resources.oxygen,
      reactorHeat: state.resources.reactorHeat,
    },
    objectives: {
      coolingOperational: isOperational(cooling?.integrity ?? 0),
      coolingPowered: cooling?.powered ?? false,
      breachSealed: state.hazards["maintenance-breach"]?.sealed ?? false,
      lifeSupportOperational: isOperational(lifeSupport?.integrity ?? 0),
      lifeSupportPowered: lifeSupport?.powered ?? false,
      crewStabilized: state.crew["crew-01"]?.stabilized ?? false,
      communicationsOperational: isOperational(communications?.integrity ?? 0),
      communicationsPowered: communications?.powered ?? false,
      distressSent: state.mission.distressSent,
    },
    strategy: {
      goal: analyzeGoalStrategy(state),
      decisionPolicy: [
        "Choose the sole Operation with strategy.selectionClass=preferred unless the Context contains concrete contradictory evidence.",
        "Never choose selectionClass=blocked while preferred or viable exists.",
        "Defer selectionClass=defer while preferred exists; do not reinterpret a longer mission deadline as more urgent than a shorter survival threat.",
        "Treat urgentMitigationsAdvanced as transitive dependency evidence: repairing or powering a dependency advances the threatened safety requirement.",
        "Preserve satisfied victory requirements and distress prerequisites; a power shutdown marked goal_regression is not ordinary battery optimization.",
      ],
    },
    recentFacts: recentFacts(events, factLimit),
    allowedOperations: compileOperationFrontier(state).map(projectOperationCandidate),
    instruction: "Choose exactly one allowed Operation by copying its operationCandidateId. Apply strategy.decisionPolicy in order, beginning with selectionClass=preferred. Never invent objects, Commands, paths, Effects, or completion claims.",
  };
}

export function compileAgentContext(
  run: RunMetadata,
  state: WorldState,
  projection: AgentProjection,
  events: JournalEvent[] = [],
  maximumBytes = MAX_AGENT_CONTEXT_BYTES,
): CompiledAgentContext {
  if (!Number.isSafeInteger(maximumBytes) || maximumBytes < 1) {
    throw new TypeError("maximum context bytes must be a positive integer");
  }
  let factLimit = events.flatMap((record) => record.event.facts ?? []).length;
  while (factLimit >= 0) {
    const base = basePayload(run, state, projection, events, factLimit);
    const contextId = sha256(base);
    const payload: AgentContextPayload = { contextId, ...base };
    const serialized = canonicalJson(payload);
    const byteLength = Buffer.byteLength(serialized);
    if (byteLength <= maximumBytes) {
      return { payload, contextId, digest: sha256(payload), byteLength };
    }
    factLimit -= 1;
  }
  throw new AgentContextError(
    "context_too_large",
    `required Agent Context exceeds ${maximumBytes} bytes even without recent Facts`,
  );
}
