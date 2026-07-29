import { protocolBytes, protocolDigest, type ProtocolJson } from "./canonical.ts";
import { sha256 } from "../digest.ts";
import type {
  AdmittedDecision,
  CompiledContextEnvelope,
  CompiledContextPayload,
  ContextBlock,
  DecisionCandidate,
  DispatchEnvelope,
  ModelDecision,
  ModelInvocationIntent,
  ObservationEnvelope,
  StateRef,
  TaskDescriptor,
  TaskOutcome,
  VerificationReceipt,
  VerificationResultItem,
} from "./model.ts";
import { HostContractStore } from "./store.ts";
import { admitModelDecision } from "./validate.ts";
import type { AgentContextPayload } from "../host/context.ts";
import type {
  HostDispatch,
  HostEffect,
  HostObservation,
  HostExecutionStore,
} from "../host/execution-store.ts";
import type { AgentAttempt, AgentProjection } from "../host/model.ts";
import type { HostStore } from "../host/store.ts";
import type { PrimitiveWorldCommand } from "../model.ts";
import type { OperationDecision } from "../providers/types.ts";
import type { GameStore } from "../storage.ts";
import type { TeamExecutionStore } from "../team/execution-store.ts";
import type {
  ActionProposal,
  CompiledTeamContext,
  TeamContextReference,
  TeamDispatch,
  TeamEffect,
  TeamObservation,
  TeamProjection,
  TeamRound,
  TeamTaskProjection,
  TeamTickPlan,
} from "../team/model.ts";
import type { TeamStore } from "../team/store.ts";

function gameDigest(value: string): `sha256:${string}` {
  if (/^sha256:[0-9a-f]{64}$/.test(value)) return value as `sha256:${string}`;
  if (/^[0-9a-f]{64}$/.test(value)) return `sha256:${value}`;
  throw new TypeError(`Game digest is invalid: ${value}`);
}

function providerId(value: string): string {
  return value.startsWith("provider:") ? value : `provider:${value}`;
}

function semanticId(prefix: "effect" | "dispatch", value: string): string {
  return value.startsWith(`${prefix}:`) ? value : `${prefix}:${value}`;
}

function confidencePermille(value: number): number {
  if (!Number.isFinite(value)) return 0;
  return Math.max(0, Math.min(1000, Math.round(value * 1000)));
}

function protocolSafe(value: unknown): ProtocolJson {
  if (value === null || typeof value === "boolean" || typeof value === "string") return value;
  if (typeof value === "number") {
    if (!Number.isFinite(value)) throw new TypeError("non-finite domain number cannot enter Protocol");
    return Number.isSafeInteger(value) ? value : value.toString();
  }
  if (Array.isArray(value)) return value.map(protocolSafe);
  if (typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value as Record<string, unknown>)
        .filter(([, item]) => item !== undefined)
        .map(([key, item]) => [key, protocolSafe(item)]),
    );
  }
  throw new TypeError(`unsupported domain value: ${typeof value}`);
}

function stateRef(runId: string, digest: string): StateRef {
  return { ref: `game-world:${runId}`, digest: gameDigest(digest) };
}

function compiledContext(
  taskId: string,
  workloadId: string,
  world: StateRef,
  blocks: ContextBlock[],
  candidates: DecisionCandidate[],
  tokenBudget = 4_000,
): CompiledContextEnvelope {
  const payload: CompiledContextPayload = {
    schemaVersion: 1,
    kind: "ordivon.compiled-context",
    taskId,
    workloadId,
    stateRefs: [world],
    blocks,
    candidates,
    completedEffectIds: [],
    unresolvedDispatchIds: [],
    instruction: "Choose exactly one candidate identity. Domain policy and current state are rechecked after model invocation.",
  };
  const byteLength = protocolBytes(payload).byteLength;
  const estimatedTokens = Math.max(1, Math.ceil(byteLength / 4));
  return {
    schemaVersion: 1,
    kind: "ordivon.compiled-context-envelope",
    digest: protocolDigest(payload),
    byteLength,
    manifest: {
      tokenBudget: Math.max(tokenBudget, estimatedTokens),
      estimatedTokens,
      selectedBlockIds: blocks.map((block) => block.blockId),
      omittedBlockIds: [],
    },
    payload,
  };
}

function taskDescriptor(
  taskId: string,
  goalId: string,
  workloadId: string,
  assigneeRef: string | null,
  providerPolicyRef: string | null,
  domainRef: string,
  configuration: ProtocolJson,
): TaskDescriptor {
  return {
    schemaVersion: 1,
    kind: "ordivon.host-task-descriptor",
    taskId,
    goalId,
    workloadId,
    assigneeRef,
    providerPolicyRef,
    domainRef,
    configurationDigests: [protocolDigest(configuration)],
  };
}

function singleCandidate(candidate: AgentContextPayload["allowedOperations"][number], world: StateRef): DecisionCandidate {
  const proposal = {
    operationCandidateId: candidate.operationCandidateId,
    operationKind: candidate.kind,
    label: candidate.label,
    targetType: candidate.target.type,
    targetId: candidate.target.id,
    requiredWorldRevision: candidate.requiredWorldRevision,
    requiredWorldDigest: gameDigest(candidate.requiredWorldDigest),
    planId: candidate.planId,
    estimatedPrimitiveSteps: candidate.estimatedPrimitiveSteps,
  } satisfies ProtocolJson;
  return {
    candidateId: `candidate:${candidate.operationCandidateId}`,
    kind: "domain-action",
    summary: candidate.label,
    proposalDigest: protocolDigest(proposal),
    effectId: null,
    dispatchId: null,
    requiredStateRefs: [world],
  };
}

function singleContext(payload: AgentContextPayload): CompiledContextEnvelope {
  const world = stateRef(payload.run.runId, payload.run.worldDigest);
  const blockPayload = {
    runId: payload.run.runId,
    worldRevision: payload.run.worldRevision,
    simulationTick: payload.run.simulationTick,
    missionStatus: payload.mission.status,
    actorId: payload.agent.actorId,
    taskRevision: payload.task.revision,
    taskPhase: payload.task.phase,
  } satisfies ProtocolJson;
  const block: ContextBlock = {
    blockId: `context-block:${payload.task.taskId}:world:r${payload.run.worldRevision}`,
    kind: "world",
    priority: 100,
    required: true,
    freshness: "current",
    sourceRef: `game-world:${payload.run.runId}:r${payload.run.worldRevision}`,
    sourceOwner: "domain",
    sourceDigest: world.digest,
    trust: "authoritative",
    validityRefs: [world],
    payload: blockPayload,
  };
  return compiledContext(
    payload.task.taskId,
    "ordivon.game.actor-turn.v1",
    world,
    [block],
    payload.allowedOperations.map((candidate) => singleCandidate(candidate, world)),
  );
}

function singleDecision(
  attempt: AgentAttempt,
  context: CompiledContextEnvelope,
  decision: OperationDecision,
): ModelDecision {
  return {
    schemaVersion: 1,
    kind: "ordivon.model-decision",
    invocationId: `invocation:${attempt.attemptId}`,
    contextDigest: context.digest,
    candidateId: decision.selectedOperationCandidateId === null
      ? null
      : `candidate:${decision.selectedOperationCandidateId}`,
    providerId: providerId(decision.providerId),
    confidencePermille: confidencePermille(decision.confidence),
    rationale: decision.rationale,
  };
}

function singleDispatch(effect: HostEffect, dispatch: HostDispatch): { request: ProtocolJson; envelope: DispatchEnvelope } {
  const request = {
    schemaVersion: 1,
    kind: "ordivon.game.world-command-request",
    runId: effect.runId,
    commandId: effect.commandId,
    requiredWorldRevision: effect.requiredWorldRevision,
    requiredWorldDigest: gameDigest(effect.requiredWorldDigest),
    command: protocolSafe(effect.worldCommand),
  } satisfies ProtocolJson;
  return {
    request,
    envelope: {
      schemaVersion: 1,
      kind: "ordivon.dispatch-envelope",
      dispatchId: dispatch.dispatchId,
      effectId: dispatch.effectId,
      executorId: "executor:game-world-v1",
      requestDigest: protocolDigest(request),
      idempotencyKey: dispatch.commandId,
      requiredStateRefs: [stateRef(effect.runId, effect.requiredWorldDigest)],
      expectedObservationKind: "ordivon.game.world-event-observation.v1",
    },
  };
}

function singleObservation(value: HostObservation): { payload: ProtocolJson; envelope: ObservationEnvelope } {
  const payload = {
    schemaVersion: 1,
    kind: "ordivon.game.world-event-observation.v1",
    runId: value.runId,
    commandId: value.commandId,
    commandSequence: value.commandSequence,
    worldEventId: value.worldEventId,
    worldAfterDigest: gameDigest(value.worldAfterDigest),
    factCount: value.facts.length,
    verificationSuccess: value.verification?.success === true,
  } satisfies ProtocolJson;
  const payloadDigest = protocolDigest(payload);
  return {
    payload,
    envelope: {
      schemaVersion: 1,
      kind: "ordivon.observation-envelope",
      dispatchId: value.dispatchId,
      executorId: "executor:game-world-v1",
      status: value.verification?.success === true ? "succeeded" : "failed",
      payloadDigest,
      evidenceRefs: [{ ref: value.worldEventId, kind: "game-world-event", digest: payloadDigest }],
    },
  };
}

export class SingleActorHostContractAdapter {
  readonly game: GameStore;
  readonly host: HostStore;
  readonly execution: HostExecutionStore;
  readonly contracts: HostContractStore;
  private readonly descriptorRuns = new Set<string>();

  constructor(game: GameStore, host: HostStore, execution: HostExecutionStore) {
    this.game = game;
    this.host = host;
    this.execution = execution;
    this.contracts = new HostContractStore(host);
  }

  syncDescriptor(runId = this.game.activeRunId): void {
    if (this.descriptorRuns.has(runId)) return;
    const projection = this.host.getProjection(runId);
    const descriptor = taskDescriptor(
      projection.task.taskId,
      projection.goal.goalId,
      "ordivon.game.actor-turn.v1",
      `actor:${projection.task.actorId}`,
      `provider-policy:${projection.task.providerOrder.join("+") || "none"}`,
      `game-run:${runId}`,
      { actorId: projection.task.actorId, providerOrder: projection.task.providerOrder },
    );
    this.contracts.putWireObject(
      runId,
      "host-contract.task-descriptor",
      `host-contract:${descriptor.taskId}:descriptor`,
      descriptor.taskId,
      descriptor,
      { createdAt: projection.task.createdAt },
    );
    this.descriptorRuns.add(runId);
  }

  sync(runId = this.game.activeRunId): void {
    this.contracts.batch(runId, () => this.syncBatch(runId));
  }

  private syncBatch(runId: string): void {
    const projection = this.host.getProjection(runId);
    const descriptor = taskDescriptor(
      projection.task.taskId,
      projection.goal.goalId,
      "ordivon.game.actor-turn.v1",
      `actor:${projection.task.actorId}`,
      `provider-policy:${projection.task.providerOrder.join("+") || "none"}`,
      `game-run:${runId}`,
      { actorId: projection.task.actorId, providerOrder: projection.task.providerOrder },
    );
    const descriptorArtifact = this.contracts.putWireObject(
      runId,
      "host-contract.task-descriptor",
      `host-contract:${descriptor.taskId}:descriptor`,
      descriptor.taskId,
      descriptor,
      { createdAt: projection.task.createdAt },
    );

    const contextByAttempt = new Map<string, CompiledContextEnvelope>();
    const admittedByAttempt = new Map<string, AdmittedDecision>();
    for (const attempt of projection.attempts) {
      if (!attempt.contextDigest) continue;
      const legacy = this.host.getArtifact<AgentContextPayload>(attempt.contextDigest).content;
      const context = singleContext(legacy);
      contextByAttempt.set(attempt.attemptId, context);
      const contextArtifact = this.contracts.putWireObject(
        runId,
        "host-contract.context",
        `host-contract:${attempt.attemptId}:context`,
        attempt.taskId,
        context,
        { relatedDigests: [descriptorArtifact.digest as `sha256:${string}`], createdAt: attempt.createdAt },
      );
      const intent: ModelInvocationIntent = {
        schemaVersion: 1,
        kind: "ordivon.model-invocation-intent",
        invocationId: `invocation:${attempt.attemptId}`,
        taskId: attempt.taskId,
        contextDigest: context.digest,
        contextObjectDigest: contextArtifact.digest as `sha256:${string}`,
        providerPolicyRef: descriptor.providerPolicyRef ?? "provider-policy:none",
      };
      this.contracts.putWireObject(
        runId,
        "host-contract.invocation",
        `host-contract:${attempt.attemptId}:invocation`,
        attempt.taskId,
        intent,
        { relatedDigests: [contextArtifact.digest as `sha256:${string}`], createdAt: attempt.createdAt },
      );
      if (!attempt.decisionDigest) continue;
      const legacyDecision = this.host.getArtifact<OperationDecision>(attempt.decisionDigest).content;
      const decision = singleDecision(attempt, context, legacyDecision);
      const decisionArtifact = this.contracts.putWireObject(
        runId,
        "host-contract.decision",
        `host-contract:${attempt.attemptId}:decision`,
        attempt.taskId,
        decision,
        { relatedDigests: [contextArtifact.digest as `sha256:${string}`], createdAt: attempt.updatedAt },
      );
      const admitted = admitModelDecision(context, decision, { currentStateRefs: context.payload.stateRefs });
      admittedByAttempt.set(attempt.attemptId, admitted);
      this.contracts.putWireObject(
        runId,
        "host-contract.admitted-decision",
        `host-contract:${attempt.attemptId}:admitted`,
        attempt.taskId,
        admitted,
        { relatedDigests: [decisionArtifact.digest as `sha256:${string}`], createdAt: attempt.updatedAt },
      );
    }

    const effectById = new Map(this.execution.listEffects(runId).map((effect) => [effect.effectId, effect]));
    for (const effect of effectById.values()) {
      const effectValue = {
        schemaVersion: 1,
        kind: "ordivon.game.world-effect",
        effectId: effect.effectId,
        taskId: effect.taskId,
        attemptId: effect.attemptId,
        operationCandidateId: effect.operationCandidateId,
        skillStepIndex: effect.skillStepIndex,
        requiredWorldRevision: effect.requiredWorldRevision,
        requiredWorldDigest: gameDigest(effect.requiredWorldDigest),
        commandId: effect.commandId,
        commandKind: effect.worldCommand.kind,
      } satisfies ProtocolJson;
      this.contracts.putProtocolObject(
        runId,
        "host-contract.effect",
        `host-contract:${effect.effectId}:effect`,
        effect.taskId,
        effectValue,
        { createdAt: effect.createdAt },
      );
    }

    const dispatchById = new Map<string, DispatchEnvelope>();
    for (const dispatch of this.execution.listDispatches(runId)) {
      const effect = effectById.get(dispatch.effectId);
      if (!effect) throw new Error(`Dispatch has no Effect: ${dispatch.dispatchId}`);
      const mapped = singleDispatch(effect, dispatch);
      const requestArtifact = this.contracts.putProtocolObject(
        runId,
        "host-contract.executor-request",
        `host-contract:${dispatch.dispatchId}:request`,
        effect.taskId,
        mapped.request,
        { createdAt: dispatch.createdAt },
      );
      const dispatchArtifact = this.contracts.putWireObject(
        runId,
        "host-contract.dispatch",
        `host-contract:${dispatch.dispatchId}:dispatch`,
        effect.taskId,
        mapped.envelope,
        { relatedDigests: [requestArtifact.digest as `sha256:${string}`], createdAt: dispatch.createdAt },
      );
      dispatchById.set(dispatch.dispatchId, mapped.envelope);
      void dispatchArtifact;
    }

    const latestVerification = new Map<string, `sha256:${string}`>();
    for (const observation of this.execution.listObservations(runId)) {
      const dispatch = dispatchById.get(observation.dispatchId);
      const effect = effectById.get(observation.effectId);
      if (!dispatch || !effect) throw new Error(`Observation has no retained Dispatch: ${observation.dispatchId}`);
      const mapped = singleObservation(observation);
      const payloadArtifact = this.contracts.putProtocolObject(
        runId,
        "host-contract.observation-payload",
        `host-contract:${observation.observationId}:payload`,
        effect.taskId,
        mapped.payload,
        { createdAt: observation.createdAt },
      );
      const observationArtifact = this.contracts.putWireObject(
        runId,
        "host-contract.observation",
        `host-contract:${observation.observationId}:observation`,
        effect.taskId,
        mapped.envelope,
        { relatedDigests: [payloadArtifact.digest as `sha256:${string}`], createdAt: observation.createdAt },
      );
      if (mapped.envelope.status !== "succeeded") continue;
      const admitted = admittedByAttempt.get(effect.attemptId);
      const verification: VerificationReceipt = {
        schemaVersion: 1,
        kind: "ordivon.verification-receipt",
        dispatchId: dispatch.dispatchId,
        method: "game-world-event.v1",
        accepted: true,
        observationDigest: observationArtifact.digest as `sha256:${string}`,
        resultItems: [{
          subjectRef: effect.taskId,
          decisionDigest: admitted ? protocolDigest(admitted) : protocolDigest({ attemptId: effect.attemptId }),
          status: "succeeded",
          reason: null,
          evidenceDigest: mapped.envelope.payloadDigest,
        }],
      };
      const verificationArtifact = this.contracts.putWireObject(
        runId,
        "host-contract.verification",
        `host-contract:${observation.dispatchId}:verification`,
        effect.taskId,
        verification,
        { relatedDigests: [observationArtifact.digest as `sha256:${string}`], createdAt: observation.createdAt },
      );
      latestVerification.set(effect.taskId, verificationArtifact.digest as `sha256:${string}`);
    }

    if (["succeeded", "failed", "cancelled"].includes(projection.task.phase)) {
      const result = {
        runId,
        worldRevision: this.game.loadState(runId).revision,
        worldDigest: gameDigest(legacyWorldDigest(this.game, runId)),
        taskPhase: projection.task.phase,
      } satisfies ProtocolJson;
      const resultArtifact = this.host.putProtocolArtifact("game-result", result, projection.task.updatedAt);
      const status: TaskOutcome["status"] = projection.task.phase === "succeeded"
        ? "completed"
        : projection.task.phase === "cancelled"
          ? "cancelled"
          : "failed";
      const outcome: TaskOutcome = {
        schemaVersion: 1,
        kind: "ordivon.task-outcome",
        taskId: projection.task.taskId,
        goalId: projection.goal.goalId,
        status,
        verificationDigest: latestVerification.get(projection.task.taskId) ?? null,
        artifactRefs: [{ ref: `game-result:${runId}`, kind: "game-result", digest: resultArtifact.digest as `sha256:${string}` }],
      };
      this.contracts.putWireObject(
        runId,
        "host-contract.task-outcome",
        `host-contract:${projection.task.taskId}:outcome:${status}`,
        projection.task.taskId,
        outcome,
        { createdAt: projection.task.updatedAt },
      );
    }
  }
}

function legacyWorldDigest(game: GameStore, runId: string): string {
  return sha256(game.loadState(runId));
}

function teamCandidate(candidate: CompiledTeamContext["allowedActions"][number], world: StateRef): DecisionCandidate {
  const proposal = {
    actionCandidateId: candidate.actionCandidateId,
    actionId: candidate.actionId,
    actorId: candidate.actorId,
    worldRevision: candidate.worldRevision,
    worldDigest: gameDigest(candidate.worldDigest),
    commandId: candidate.command.commandId,
    commandKind: candidate.command.kind,
    objectiveIds: candidate.objectiveIds,
    authorityOutcome: candidate.authorityOutcome,
  } satisfies ProtocolJson;
  return {
    candidateId: `candidate:${candidate.actionCandidateId}`,
    kind: "domain-action",
    summary: candidate.label,
    proposalDigest: protocolDigest(proposal),
    effectId: null,
    dispatchId: null,
    requiredStateRefs: [world],
  };
}

function teamContext(value: CompiledTeamContext): CompiledContextEnvelope {
  const world = stateRef(value.runId, value.worldDigest);
  const blocks: ContextBlock[] = value.blocks.map((legacy) => ({
    blockId: `context-block:${legacy.blockId}`,
    kind: legacy.kind,
    priority: legacy.priority,
    required: legacy.required,
    freshness: legacy.freshness,
    sourceRef: `game-context-source:${legacy.blockId}`,
    sourceOwner: "domain",
    sourceDigest: gameDigest(legacy.sourceDigest),
    trust: legacy.kind === "message" ? "reported" : "authoritative",
    validityRefs: legacy.freshness === "current" ? [world] : [],
    payload: {
      legacyBlockId: legacy.blockId,
      kind: legacy.kind,
      estimatedTokens: legacy.estimatedTokens,
    },
  }));
  return compiledContext(
    value.taskId,
    "ordivon.game.actor-turn.v1",
    world,
    blocks,
    value.allowedActions.map((candidate) => teamCandidate(candidate, world)),
    value.manifest.tokenBudget,
  );
}

function teamTaskDescriptor(task: TeamTaskProjection, projection: TeamProjection): TaskDescriptor {
  const profile = task.actorId
    ? projection.profiles.find((candidate) => candidate.actorId === task.actorId) ?? null
    : null;
  return taskDescriptor(
    task.taskId,
    task.goalId,
    task.role === "coordinator" ? "ordivon.game.team-coordinator.v1" : "ordivon.game.actor-turn.v1",
    task.actorId ? `actor:${task.actorId}` : null,
    task.providerOrder.length > 0 ? `provider-policy:${task.providerOrder.join("+")}` : null,
    `game-run:${task.runId}`,
    {
      role: task.role,
      actorId: task.actorId,
      providerOrder: task.providerOrder,
      observationPolicyId: profile?.observationPolicyId ?? null,
      authorityPolicyId: profile?.authorityPolicyId ?? null,
    },
  );
}

function teamRoundSnapshot(round: TeamRound, proposals: ActionProposal[], coordinator: TeamTaskProjection): ProtocolJson {
  return {
    schemaVersion: 1,
    kind: "ordivon.goal-task-snapshot",
    goalId: coordinator.goalId,
    worldRevision: round.worldRevision,
    worldDigest: gameDigest(round.worldDigest),
    tasks: [
      ...proposals.map((proposal) => ({
        taskId: proposal.actorTaskId,
        revision: proposal.actorTaskRevision,
        contextId: proposal.contextId,
        contextDigest: gameDigest(proposal.contextDigest),
      })),
      {
        taskId: coordinator.taskId,
        revision: Math.max(1, round.worldRevision + 1),
        contextId: null,
        contextDigest: null,
      },
    ].sort((left, right) => left.taskId.localeCompare(right.taskId)),
  };
}

function teamDispatchEnvelope(effect: TeamEffect, dispatch: TeamDispatch, plan: TeamTickPlan): { request: ProtocolJson; envelope: DispatchEnvelope } {
  const request = {
    schemaVersion: 1,
    kind: "ordivon.game.team-tick-request",
    runId: effect.runId,
    tickPlanId: plan.tickPlanId,
    worldRevision: plan.worldRevision,
    worldDigest: gameDigest(plan.worldDigest),
    commands: plan.commands.map((command) => ({
      commandId: command.commandId,
      actorId: command.actorId,
      commandKind: command.kind,
    })),
    selectedProposalIds: plan.selectedProposalIds,
  } satisfies ProtocolJson;
  return {
    request,
    envelope: {
      schemaVersion: 1,
      kind: "ordivon.dispatch-envelope",
      dispatchId: semanticId("dispatch", dispatch.dispatchId),
      effectId: semanticId("effect", effect.effectId),
      executorId: "executor:game-world-v1",
      requestDigest: protocolDigest(request),
      idempotencyKey: dispatch.commandId,
      requiredStateRefs: [stateRef(effect.runId, effect.requiredWorldDigest)],
      expectedObservationKind: "ordivon.game.team-tick-observation.v1",
    },
  };
}

function teamObservationEnvelope(value: TeamObservation): { payload: ProtocolJson; envelope: ObservationEnvelope } {
  const payload = {
    schemaVersion: 1,
    kind: "ordivon.game.team-tick-observation.v1",
    runId: value.runId,
    roundId: value.roundId,
    commandId: value.commandId,
    commandSequence: value.commandSequence,
    worldEventId: value.worldEventId,
    worldAfterDigest: gameDigest(value.worldAfterDigest),
    intentCommandIds: value.intentCommandIds,
    verifiedIntentCommandIds: value.verifiedIntentCommandIds,
    verificationSuccess: value.verificationSuccess,
    factCount: value.facts.length,
  } satisfies ProtocolJson;
  const payloadDigest = protocolDigest(payload);
  return {
    payload,
    envelope: {
      schemaVersion: 1,
      kind: "ordivon.observation-envelope",
      dispatchId: semanticId("dispatch", value.dispatchId),
      executorId: "executor:game-world-v1",
      status: value.verificationSuccess ? "succeeded" : "failed",
      payloadDigest,
      evidenceRefs: [{ ref: value.worldEventId, kind: "game-tick-event", digest: payloadDigest }],
    },
  };
}

export class TeamHostContractAdapter {
  readonly game: GameStore;
  readonly team: TeamStore;
  readonly execution: TeamExecutionStore;
  readonly contracts: HostContractStore;
  private readonly descriptorTasks = new Set<string>();

  constructor(game: GameStore, team: TeamStore, execution: TeamExecutionStore) {
    this.game = game;
    this.team = team;
    this.execution = execution;
    this.contracts = new HostContractStore(team.host);
  }

  syncDescriptors(runId = this.game.activeRunId): void {
    const projection = this.team.projection(runId, false);
    for (const task of projection.tasks) {
      if (this.descriptorTasks.has(task.taskId)) continue;
      const descriptor = teamTaskDescriptor(task, projection);
      this.contracts.putWireObject(
        runId,
        "host-contract.task-descriptor",
        `host-contract:${task.taskId}:descriptor`,
        task.taskId,
        descriptor,
        { createdAt: task.createdAt },
      );
      this.descriptorTasks.add(task.taskId);
    }
  }

  sync(runId = this.game.activeRunId): void {
    this.contracts.batch(runId, () => this.syncBatch(runId));
  }

  private syncBatch(runId: string): void {
    const projection = this.team.projection(runId, false);
    const descriptorByTask = new Map<string, TaskDescriptor>();
    for (const task of projection.tasks) {
      const descriptor = teamTaskDescriptor(task, projection);
      descriptorByTask.set(task.taskId, descriptor);
      this.contracts.putWireObject(
        runId,
        "host-contract.task-descriptor",
        `host-contract:${task.taskId}:descriptor`,
        task.taskId,
        descriptor,
        { createdAt: task.createdAt },
      );
    }

    const contextById = new Map<string, CompiledContextEnvelope>();
    const contextArtifactById = new Map<string, `sha256:${string}`>();
    const admittedByProposal = new Map<string, AdmittedDecision>();
    const rounds = this.execution.listRounds(runId);
    for (const round of rounds) {
      for (const reference of this.execution.listContexts(round.roundId)) {
        const legacy = this.team.host.getArtifact<CompiledTeamContext>(reference.artifactDigest).content;
        const context = teamContext(legacy);
        contextById.set(reference.contextId, context);
        const contextArtifact = this.contracts.putWireObject(
          runId,
          "host-contract.context",
          `host-contract:${reference.contextId}:context`,
          reference.taskId,
          context,
          { createdAt: reference.createdAt },
        );
        contextArtifactById.set(reference.contextId, contextArtifact.digest as `sha256:${string}`);
        const descriptor = descriptorByTask.get(reference.taskId);
        const intent: ModelInvocationIntent = {
          schemaVersion: 1,
          kind: "ordivon.model-invocation-intent",
          invocationId: `invocation:${reference.contextId}`,
          taskId: reference.taskId,
          contextDigest: context.digest,
          contextObjectDigest: contextArtifact.digest as `sha256:${string}`,
          providerPolicyRef: descriptor?.providerPolicyRef ?? "provider-policy:none",
        };
        this.contracts.putWireObject(
          runId,
          "host-contract.invocation",
          `host-contract:${reference.contextId}:invocation`,
          reference.taskId,
          intent,
          { relatedDigests: [contextArtifact.digest as `sha256:${string}`], createdAt: reference.createdAt },
        );
      }

      const proposals = this.execution.listProposals(round.roundId);
      for (const proposal of proposals) {
        const context = contextById.get(proposal.contextId);
        const contextArtifactDigest = contextArtifactById.get(proposal.contextId);
        if (!context || !contextArtifactDigest) throw new Error(`Proposal has no retained Context: ${proposal.proposalId}`);
        const decision: ModelDecision = {
          schemaVersion: 1,
          kind: "ordivon.model-decision",
          invocationId: `invocation:${proposal.contextId}`,
          contextDigest: context.digest,
          candidateId: `candidate:${proposal.actionCandidateId}`,
          providerId: providerId(proposal.providerId),
          confidencePermille: confidencePermille(proposal.confidence),
          rationale: proposal.rationale,
        };
        const decisionArtifact = this.contracts.putWireObject(
          runId,
          "host-contract.decision",
          `host-contract:${proposal.proposalId}:decision`,
          proposal.actorTaskId,
          decision,
          { relatedDigests: [contextArtifactDigest], createdAt: proposal.createdAt },
        );
        const admitted = admitModelDecision(context, decision, { currentStateRefs: context.payload.stateRefs });
        admittedByProposal.set(proposal.proposalId, admitted);
        this.contracts.putWireObject(
          runId,
          "host-contract.admitted-decision",
          `host-contract:${proposal.proposalId}:admitted`,
          proposal.actorTaskId,
          admitted,
          { relatedDigests: [decisionArtifact.digest as `sha256:${string}`], createdAt: proposal.createdAt },
        );
      }

      const coordinator = projection.tasks.find((task) => task.role === "coordinator");
      if (!coordinator) throw new Error("Team Coordinator Task is missing");
      const contextCount = this.execution.listContexts(round.roundId).length;
      if (round.tickPlanId || (contextCount > 0 && round.resolvedActorIds.length >= contextCount)) {
        const snapshot = teamRoundSnapshot(round, proposals, coordinator);
        this.contracts.putProtocolObject(
          runId,
          "host-contract.goal-snapshot",
          `host-contract:${round.roundId}:goal-snapshot`,
          coordinator.taskId,
          snapshot,
          { createdAt: round.createdAt },
        );
      }

      if (!round.effectId || !round.dispatchId || !round.tickPlanId) continue;
      const effect = this.execution.getEffect(round.effectId);
      const dispatch = this.execution.getDispatch(round.dispatchId);
      const plan = this.execution.getTickPlan(round.tickPlanId);
      const effectValue = {
        schemaVersion: 1,
        kind: "ordivon.game.team-tick-effect",
        effectId: semanticId("effect", effect.effectId),
        domainEffectId: effect.effectId,
        domainDispatchId: dispatch.dispatchId,
        roundId: effect.roundId,
        runId: effect.runId,
        tickPlanId: effect.tickPlanId,
        requiredWorldRevision: effect.requiredWorldRevision,
        requiredWorldDigest: gameDigest(effect.requiredWorldDigest),
        selectedProposalIds: plan.selectedProposalIds,
      } satisfies ProtocolJson;
      this.contracts.putProtocolObject(
        runId,
        "host-contract.effect",
        `host-contract:${effect.effectId}:effect`,
        coordinator.taskId,
        effectValue,
        { createdAt: effect.createdAt },
      );
      const mappedDispatch = teamDispatchEnvelope(effect, dispatch, plan);
      const requestArtifact = this.contracts.putProtocolObject(
        runId,
        "host-contract.executor-request",
        `host-contract:${dispatch.dispatchId}:request`,
        coordinator.taskId,
        mappedDispatch.request,
        { createdAt: dispatch.createdAt },
      );
      const dispatchArtifact = this.contracts.putWireObject(
        runId,
        "host-contract.dispatch",
        `host-contract:${dispatch.dispatchId}:dispatch`,
        coordinator.taskId,
        mappedDispatch.envelope,
        { relatedDigests: [requestArtifact.digest as `sha256:${string}`], createdAt: dispatch.createdAt },
      );
      if (!round.observationId) continue;
      const observation = this.execution.findObservationForRound(round.roundId);
      if (!observation) throw new Error(`Round has no retained Observation: ${round.roundId}`);
      const mappedObservation = teamObservationEnvelope(observation);
      const payloadArtifact = this.contracts.putProtocolObject(
        runId,
        "host-contract.observation-payload",
        `host-contract:${observation.observationId}:payload`,
        coordinator.taskId,
        mappedObservation.payload,
        { createdAt: observation.createdAt },
      );
      const observationArtifact = this.contracts.putWireObject(
        runId,
        "host-contract.observation",
        `host-contract:${observation.observationId}:observation`,
        coordinator.taskId,
        mappedObservation.envelope,
        { relatedDigests: [payloadArtifact.digest as `sha256:${string}`], createdAt: observation.createdAt },
      );
      const verifiedCommands = new Set(observation.verifiedIntentCommandIds);
      const resultItems: VerificationResultItem[] = proposals.map((proposal) => {
        const admitted = admittedByProposal.get(proposal.proposalId);
        const succeeded = verifiedCommands.has(proposal.command.commandId);
        return {
          subjectRef: proposal.actorTaskId,
          decisionDigest: admitted ? protocolDigest(admitted) : protocolDigest({ proposalId: proposal.proposalId }),
          status: succeeded ? "succeeded" : "not-selected",
          reason: succeeded ? null : proposal.rejectionReason ?? "not-executed",
          evidenceDigest: mappedObservation.envelope.payloadDigest,
        };
      });
      const verification: VerificationReceipt = {
        schemaVersion: 1,
        kind: "ordivon.verification-receipt",
        dispatchId: mappedDispatch.envelope.dispatchId,
        method: "game-tick-intent-receipts.v1",
        accepted: observation.verificationSuccess,
        observationDigest: observationArtifact.digest as `sha256:${string}`,
        resultItems,
      };
      const verificationArtifact = this.contracts.putWireObject(
        runId,
        "host-contract.verification",
        `host-contract:${round.roundId}:verification`,
        coordinator.taskId,
        verification,
        {
          relatedDigests: [dispatchArtifact.digest as `sha256:${string}`, observationArtifact.digest as `sha256:${string}`],
          createdAt: observation.createdAt,
        },
      );

      const state = this.game.loadState(runId);
      if (state.mission.status !== "running" && round === rounds.at(-1)) {
        for (const task of projection.tasks) {
          const taskResult = {
            runId,
            taskId: task.taskId,
            worldRevision: state.revision,
            worldDigest: gameDigest(legacyWorldDigest(this.game, runId)),
            missionStatus: state.mission.status,
          } satisfies ProtocolJson;
          const taskResultArtifact = this.team.host.putProtocolArtifact("game-result", taskResult, task.updatedAt);
          const outcome: TaskOutcome = {
            schemaVersion: 1,
            kind: "ordivon.task-outcome",
            taskId: task.taskId,
            goalId: task.goalId,
            status: state.mission.status === "victory" ? "completed" : "failed",
            verificationDigest: verificationArtifact.digest as `sha256:${string}`,
            artifactRefs: [{
              ref: `game-result:${runId}:${task.taskId}`,
              kind: "game-result",
              digest: taskResultArtifact.digest as `sha256:${string}`,
            }],
          };
          this.contracts.putWireObject(
            runId,
            "host-contract.task-outcome",
            `host-contract:${task.taskId}:outcome:${outcome.status}`,
            task.taskId,
            outcome,
            { createdAt: task.updatedAt },
          );
        }
      }
    }
  }
}

export function commandProtocolDigest(command: PrimitiveWorldCommand): `sha256:${string}` {
  return protocolDigest(protocolSafe(command));
}
