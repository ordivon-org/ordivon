import { canonicalJson, sha256 } from "../digest.ts";
import { AgentSessionStore, type AgentSession } from "../agent/session-store.ts";
import { EmbeddedHostAuthority } from "../host-contract/embedded-authority.ts";
import { GameWorldExecutor, type GameWorldObservation } from "../host-contract/game-world-executor.ts";
import { protocolDigest, type ProtocolJson } from "../host-contract/canonical.ts";
import type {
  DispatchEnvelope,
  ObservationEnvelope,
  TaskDescriptor,
  TaskOutcome,
  VerificationReceipt,
} from "../host-contract/model.ts";
import type { AgentContextPayload, CompiledAgentContext, ContextOperationCandidate } from "./context.ts";
import { compileAgentContext } from "./context.ts";
import {
  compileSkillPlan,
  materializeSkillStep,
  operationSucceeded,
  type SkillPlan,
} from "./operations.ts";
import {
  goalIdFor,
  newAttemptId,
  taskIdFor,
  terminalGoalStatus,
  terminalTaskPhase,
  type AgentAttempt,
  type AgentGoal,
  type AgentProjection,
  type AgentTask,
} from "./model.ts";
import type { OperationDecision, OperationProvider } from "../providers/types.ts";
import { DecisionAdmissionError, ProviderAdapterError, admitOperationDecision } from "../providers/types.ts";
import type { GameStore } from "../storage.ts";
import { parseWorldCommand } from "../world.ts";

export type HostFaultPoint =
  | "after_context_artifact"
  | "after_provider_call"
  | "after_decision_artifact"
  | "after_dispatch_prepare"
  | "after_world_apply"
  | "after_observation"
  | "before_attempt_advance";

export interface AgentHostOptions {
  faultInjector?: (point: HostFaultPoint) => void;
}

export interface AgentHostStepReceipt {
  runId: string;
  status:
    | "context_compiled"
    | "decision_recorded"
    | "decision_rejected"
    | "dispatch_prepared"
    | "world_step_verified"
    | "attempt_succeeded"
    | "task_succeeded"
    | "task_failed"
    | "blocked"
    | "stable";
  taskPhase: AgentTask["phase"];
  attemptId: string | null;
  providerId: string | null;
  operationCandidateId: string | null;
  skillStepIndex: number | null;
  worldRevision: number;
  worldDigest: string;
  detail: string;
}

export interface AgentHostRunReceipt {
  runId: string;
  steps: AgentHostStepReceipt[];
  projection: AgentProjection;
  worldDigest: string;
  worldRevision: number;
}

function now(): string {
  return new Date().toISOString();
}

function protocolSha(value: string): `sha256:${string}` {
  return value.startsWith("sha256:") ? value as `sha256:${string}` : `sha256:${value}`;
}

function stepTaskId(runId: string, attempt: AgentAttempt): string {
  return `task:${runId.slice("run:".length)}:attempt:${attempt.attemptNumber}:step:${attempt.skillStepIndex}`;
}

function observationPayload(value: GameWorldObservation): ProtocolJson {
  return {
    schemaVersion: 1,
    kind: "ordivon.game.world-event-observation.v1",
    runId: value.runId,
    commandId: value.commandId,
    commandSequence: value.commandSequence,
    worldEventId: value.worldEventId,
    worldAfterDigest: value.worldAfterDigest === null ? null : protocolSha(value.worldAfterDigest),
    verificationSuccess: value.verificationSuccess,
    rejectionCode: value.rejectionCode,
    reason: value.reason,
  };
}

export class AgentHost {
  readonly game: GameStore;
  readonly provider: OperationProvider;
  readonly authority: EmbeddedHostAuthority;
  readonly host: EmbeddedHostAuthority["host"];
  readonly sessions: AgentSessionStore;
  readonly contract: { contracts: EmbeddedHostAuthority["contracts"] };
  readonly faultInjector: ((point: HostFaultPoint) => void) | undefined;

  constructor(game: GameStore, provider: OperationProvider, options: AgentHostOptions = {}) {
    this.game = game;
    this.provider = provider;
    this.authority = new EmbeddedHostAuthority(game);
    this.host = this.authority.host;
    this.sessions = new AgentSessionStore(this.host);
    this.contract = { contracts: this.authority.contracts };
    this.faultInjector = options.faultInjector;
  }

  initialize(runId = this.game.activeRunId, providerOrder = [this.provider.providerId]): AgentProjection {
    const session = this.sessions.initialize(runId, providerOrder);
    return this.project(runId, session);
  }

  syncContract(runId = this.game.activeRunId): void {
    this.authority.verify(runId);
  }

  projection(runId = this.game.activeRunId): AgentProjection {
    return this.project(runId, this.sessions.get(runId));
  }

  private project(runId: string, session: AgentSession): AgentProjection {
    const state = this.game.loadState(runId);
    const goalStatus = terminalGoalStatus(state.mission.status);
    const taskPhase: AgentTask["phase"] = session.activeAttempt
      ? "active"
      : state.mission.status === "running"
        ? session.mode === "blocked" ? "blocked" : "ready"
        : terminalTaskPhase(state.mission.status);
    const goalId = goalIdFor(runId);
    const goal: AgentGoal = {
      goalId,
      runId,
      actorId: "engineer-01",
      statement: "Stabilize Station Zero and transmit a verified rescue signal.",
      successCondition: { missionStatus: "victory", missionReason: "rescue_signal_verified" },
      status: goalStatus,
      revision: session.revision,
      createdAt: session.createdAt,
      updatedAt: session.updatedAt,
    };
    const attempts = [
      ...session.completedAttempts,
      ...(session.activeAttempt ? [session.activeAttempt] : []),
    ];
    const task: AgentTask = {
      taskId: taskIdFor(runId),
      goalId,
      runId,
      actorId: "engineer-01",
      phase: taskPhase,
      revision: session.revision,
      activeAttemptId: session.activeAttempt?.attemptId ?? null,
      completedAttemptIds: session.completedAttempts.map((attempt) => attempt.attemptId),
      blockers: [...session.blockers],
      providerOrder: [...session.providerOrder],
      createdAt: session.createdAt,
      updatedAt: session.updatedAt,
    };
    return { goal, task, attempts };
  }

  private inject(point: HostFaultPoint): void {
    this.faultInjector?.(point);
  }

  private receipt(
    runId: string,
    status: AgentHostStepReceipt["status"],
    detail: string,
  ): AgentHostStepReceipt {
    const projection = this.projection(runId);
    const state = this.game.loadState(runId);
    const active = projection.task.activeAttemptId
      ? projection.attempts.find((attempt) => attempt.attemptId === projection.task.activeAttemptId) ?? null
      : null;
    return {
      runId,
      status,
      taskPhase: projection.task.phase,
      attemptId: active?.attemptId ?? null,
      providerId: active?.providerId ?? null,
      operationCandidateId: active?.operationCandidateId ?? null,
      skillStepIndex: active?.skillStepIndex ?? null,
      worldRevision: state.revision,
      worldDigest: sha256(state),
      detail,
    };
  }

  async step(runId = this.game.activeRunId): Promise<AgentHostStepReceipt> {
    this.initialize(runId);
    this.game.verifyStream(runId);
    this.host.verifyJournal(runId);
    const state = this.game.loadState(runId);
    const session = this.sessions.get(runId);
    const projection = this.project(runId, session);

    if (session.activeAttempt) {
      const attempt = session.activeAttempt;
      if (["decision_recorded", "executing", "reconciling"].includes(attempt.status)) {
        return this.executeAttemptStep(runId, session, attempt);
      }
      if (attempt.status === "verifying") return this.verifyAttempt(runId, session, attempt);
      if (attempt.status === "provider_pending" || attempt.status === "context_pending") {
        if (state.mission.status !== "running") {
          return this.rejectAttempt(
            runId, session, attempt, "world_terminal",
            "World became terminal before Provider admission", false,
          );
        }
        return await this.invokeProvider(runId, session, projection, attempt);
      }
      return this.reconcileTerminalAttempt(runId, session, attempt);
    }
    if (state.mission.status !== "running") return this.synchronizeTerminal(runId, state.mission.status);
    if (session.mode === "blocked") {
      return this.receipt(runId, "blocked", "Task has no automatic progress");
    }
    return this.compileContext(runId, session, projection);
  }

  async run(runId = this.game.activeRunId, maximumSteps = 256): Promise<AgentHostRunReceipt> {
    if (!Number.isSafeInteger(maximumSteps) || maximumSteps < 1) throw new TypeError("maximumSteps must be positive");
    const steps: AgentHostStepReceipt[] = [];
    for (let index = 0; index < maximumSteps; index += 1) {
      const receipt = await this.step(runId);
      steps.push(receipt);
      if (["blocked", "succeeded", "failed", "cancelled"].includes(this.projection(runId).task.phase)) break;
    }
    this.syncContract(runId);
    const state = this.game.loadState(runId);
    return {
      runId,
      steps,
      projection: this.projection(runId),
      worldDigest: sha256(state),
      worldRevision: state.revision,
    };
  }

  private compileContext(
    runId: string,
    session: AgentSession,
    projection: AgentProjection,
  ): AgentHostStepReceipt {
    const context = compileAgentContext(
      this.game.getRun(runId),
      this.game.loadState(runId),
      projection,
      this.game.recentJournalEvents(12, runId),
    );
    const artifact = this.host.putArtifact("agent-context-v2", context.payload);
    this.inject("after_context_artifact");
    const timestamp = now();
    const attempt: AgentAttempt = {
      attemptId: newAttemptId(runId),
      taskId: projection.task.taskId,
      runId,
      attemptNumber: session.completedAttempts.length + 1,
      revision: 1,
      status: "provider_pending",
      providerId: null,
      contextDigest: artifact.digest,
      decisionDigest: null,
      planDigest: null,
      providerEvidenceDigest: null,
      operationCandidateId: null,
      skillStepIndex: 0,
      skillStepCount: 0,
      blocker: null,
      createdAt: timestamp,
      updatedAt: timestamp,
    };
    this.sessions.save(
      {
        ...session,
        revision: session.revision + 1,
        mode: "provider_pending",
        activeAttempt: attempt,
        blockers: [],
        updatedAt: timestamp,
      },
      "attempt_activated",
      `agent-event:${attempt.attemptId}:activated`,
      { attemptId: attempt.attemptId, contextDigest: artifact.digest },
    );
    return this.receipt(runId, "context_compiled", `Persisted Context ${context.contextId}`);
  }

  private contextFromAttempt(attempt: AgentAttempt): CompiledAgentContext {
    if (!attempt.contextDigest) throw new Error("Attempt has no Context Artifact");
    const artifact = this.host.getArtifact<AgentContextPayload>(attempt.contextDigest);
    return {
      payload: artifact.content,
      contextId: artifact.content.contextId,
      digest: sha256(artifact.content),
      byteLength: artifact.byteLength,
    };
  }

  private async invokeProvider(
    runId: string,
    session: AgentSession,
    projection: AgentProjection,
    attempt: AgentAttempt,
  ): Promise<AgentHostStepReceipt> {
    const context = this.contextFromAttempt(attempt);
    const current = this.game.loadState(runId);
    if (current.revision !== context.payload.run.worldRevision || sha256(current) !== context.payload.run.worldDigest) {
      return this.rejectAttempt(runId, session, attempt, "context_stale", "World changed before Provider admission", false);
    }
    let decision: OperationDecision;
    try {
      decision = await this.provider.decide(context);
      this.inject("after_provider_call");
    } catch (error) {
      if (!(error instanceof ProviderAdapterError)) throw error;
      return this.rejectAttempt(runId, session, attempt, `provider_${error.code}`, error.message, true);
    }
    const evidence = this.provider.evidenceMetadata?.() ?? null;
    const evidenceArtifact = evidence ? this.host.putArtifact("provider-evidence-v1", evidence) : null;
    const decisionArtifact = this.host.putArtifact("operation-decision-v1", decision);
    this.inject("after_decision_artifact");
    let candidate: ContextOperationCandidate | null;
    try {
      candidate = admitOperationDecision(context, this.game.loadState(runId), decision);
    } catch (error) {
      if (!(error instanceof DecisionAdmissionError)) throw error;
      return this.rejectAttempt(
        runId,
        session,
        attempt,
        `decision_${error.code}`,
        error.message,
        error.code !== "stale_world",
      );
    }
    if (!candidate) return this.rejectAttempt(runId, session, attempt, "provider_declined", "Provider selected no Operation", true);
    const plan = compileSkillPlan(this.game.loadState(runId), candidate);
    const planArtifact = this.host.putArtifact("skill-plan-v1", plan);
    const timestamp = now();
    const updated: AgentAttempt = {
      ...attempt,
      revision: attempt.revision + 1,
      status: "decision_recorded",
      providerId: decision.providerId,
      decisionDigest: decisionArtifact.digest,
      planDigest: planArtifact.digest,
      providerEvidenceDigest: evidenceArtifact?.digest ?? null,
      operationCandidateId: candidate.operationCandidateId,
      skillStepIndex: 0,
      skillStepCount: plan.steps.length,
      blocker: null,
      updatedAt: timestamp,
    };
    this.sessions.save(
      {
        ...session,
        revision: session.revision + 1,
        mode: "executing",
        activeAttempt: updated,
        updatedAt: timestamp,
      },
      "decision_recorded",
      `agent-event:${attempt.attemptId}:decision-recorded`,
      {
        attemptId: attempt.attemptId,
        contextDigest: attempt.contextDigest,
        decisionDigest: decisionArtifact.digest,
        planDigest: planArtifact.digest,
        providerEvidenceDigest: evidenceArtifact?.digest ?? null,
        operationCandidateId: candidate.operationCandidateId,
      },
    );
    return this.receipt(runId, "decision_recorded", `Provider selected ${candidate.label}`);
  }

  private executeAttemptStep(
    runId: string,
    session: AgentSession,
    attempt: AgentAttempt,
  ): AgentHostStepReceipt {
    if (!attempt.planDigest || !attempt.operationCandidateId) throw new Error("Attempt has no admitted Skill Plan");
    const plan = this.host.getArtifact<SkillPlan>(attempt.planDigest).content;
    if (attempt.skillStepIndex >= plan.steps.length) {
      return this.markAttemptVerifying(runId, session, attempt);
    }
    const hostTaskId = stepTaskId(runId, attempt);
    const descriptorExists = this.authority.contracts.latest(runId, hostTaskId, "ordivon.host-task-descriptor") !== null;
    const context = this.contextFromAttempt(attempt);
    const expectedRevision = context.payload.run.worldRevision + attempt.skillStepIndex;
    const current = this.game.loadState(runId);
    if (!descriptorExists && current.revision !== expectedRevision) {
      return this.rejectAttempt(
        runId,
        session,
        attempt,
        "world_drift",
        `Expected world revision ${expectedRevision}, found ${current.revision}`,
        false,
      );
    }
    const step = plan.steps[attempt.skillStepIndex];
    if (!step) throw new Error("Skill Plan step is missing");
    const descriptor: TaskDescriptor = {
      schemaVersion: 1,
      kind: "ordivon.host-task-descriptor",
      taskId: hostTaskId,
      goalId: goalIdFor(runId),
      workloadId: "ordivon.game.actor-step.v1",
      assigneeRef: `actor:${context.payload.agent.actorId}`,
      providerPolicyRef: `provider-policy:${attempt.providerId ?? this.provider.providerId}`,
      domainRef: `game-run:${runId}`,
      configurationDigests: [protocolDigest({
        attemptId: attempt.attemptId,
        operationCandidateId: attempt.operationCandidateId,
        skillStepIndex: attempt.skillStepIndex,
      })],
    };
    let hostProjection = this.authority.ensureTask(runId, descriptor);
    if (hostProjection.state === "ready") {
      const effectId = `effect:${hostTaskId.slice("task:".length)}`;
      const dispatchId = `dispatch:${hostTaskId.slice("task:".length)}`;
      const commandId = `command:${hostTaskId.slice("task:".length)}`;
      const worldCommand = materializeSkillStep(current, step, commandId);
      const request = {
        schemaVersion: 1,
        kind: "ordivon.game.world-command-request",
        runId,
        commandId,
        requiredWorldRevision: current.revision,
        requiredWorldDigest: protocolSha(sha256(current)),
        command: worldCommand as unknown as ProtocolJson,
      } satisfies ProtocolJson;
      const effect = {
        schemaVersion: 1,
        kind: "ordivon.game.world-effect",
        effectId,
        runId,
        taskId: hostTaskId,
        attemptId: attempt.attemptId,
        operationCandidateId: attempt.operationCandidateId,
        skillStepIndex: attempt.skillStepIndex,
        commandId,
      } satisfies ProtocolJson;
      const dispatch: DispatchEnvelope = {
        schemaVersion: 1,
        kind: "ordivon.dispatch-envelope",
        dispatchId,
        effectId,
        executorId: "executor:game-world-v1",
        requestDigest: protocolDigest(request),
        idempotencyKey: commandId,
        requiredStateRefs: [{ ref: `game-world:${runId}`, digest: protocolSha(sha256(current)) }],
        expectedObservationKind: "ordivon.game.world-event-observation.v1",
      };
      hostProjection = this.authority.prepare(runId, hostTaskId, effect, request as Record<string, ProtocolJson>, dispatch);
      this.inject("after_dispatch_prepare");
      return this.receipt(runId, "dispatch_prepared", `Prepared ${dispatchId}`);
    }
    if (hostProjection.state === "reconciling") {
      return this.deliverOrObserve(runId, session, attempt, hostTaskId);
    }
    if (hostProjection.state === "verifying") {
      const observation = this.authority.observation(runId, hostTaskId);
      const accepted = observation.status === "succeeded";
      const verification: VerificationReceipt = {
        schemaVersion: 1,
        kind: "ordivon.verification-receipt",
        dispatchId: observation.dispatchId,
        method: "game-world-event.v1",
        accepted,
        observationDigest: protocolDigest(observation),
        resultItems: [{
          subjectRef: hostTaskId,
          decisionDigest: protocolSha(attempt.decisionDigest ?? sha256({ attemptId: attempt.attemptId })),
          status: accepted ? "succeeded" : observation.status === "rejected" ? "rejected" : "failed",
          reason: accepted ? null : "World Observation was not successful",
          evidenceDigest: observation.payloadDigest,
        }],
      };
      this.authority.recordVerification(runId, hostTaskId, verification);
      return this.receipt(runId, "stable", `Recorded Verification for ${hostTaskId}`);
    }
    if (hostProjection.state === "result") {
      const verification = this.authority.verification(runId, hostTaskId);
      const outcome: TaskOutcome = {
        schemaVersion: 1,
        kind: "ordivon.task-outcome",
        taskId: hostTaskId,
        goalId: descriptor.goalId,
        status: verification.accepted ? "completed" : "failed",
        verificationDigest: protocolDigest(verification),
        artifactRefs: [],
      };
      hostProjection = this.authority.complete(runId, hostTaskId, outcome);
      this.inject("before_attempt_advance");
      return verification.accepted
        ? this.advanceAttemptStep(runId, session, attempt)
        : this.rejectAttempt(runId, session, attempt, "verification_failed", "World Event did not verify", true);
    }
    if (hostProjection.state === "completed") return this.advanceAttemptStep(runId, session, attempt);
    return this.rejectAttempt(runId, session, attempt, "effect_task_failed", `Effect Task ended ${hostProjection.state}`, true);
  }

  private deliverOrObserve(
    runId: string,
    session: AgentSession,
    attempt: AgentAttempt,
    hostTaskId: string,
  ): AgentHostStepReceipt {
    const requestArtifact = this.authority.relatedObjects(runId, hostTaskId)
      .find((artifact) => artifact.kind === "ordivon.game.world-command-request");
    if (!requestArtifact || typeof requestArtifact.content !== "object" || requestArtifact.content === null || Array.isArray(requestArtifact.content)) {
      throw new Error("Prepared Effect omitted its World Command request");
    }
    const command = parseWorldCommand(requestArtifact.content.command);
    const executor = new GameWorldExecutor(this.game, {
      faultInjector: () => this.inject("after_world_apply"),
    });
    const worldObservation = executor.observeCommand(command, runId) ?? executor.deliverCommand(command, runId);
    const payload = observationPayload(worldObservation);
    const observation: ObservationEnvelope = {
      schemaVersion: 1,
      kind: "ordivon.observation-envelope",
      dispatchId: this.authority.dispatch(runId, hostTaskId).dispatchId,
      executorId: worldObservation.executorId,
      status: worldObservation.status,
      payloadDigest: protocolDigest(payload),
      evidenceRefs: worldObservation.worldEventId
        ? [{ ref: worldObservation.worldEventId, kind: "game-world-event", digest: protocolDigest(payload) }]
        : [],
    };
    this.host.putProtocolArtifact("ordivon.game.world-event-observation.v1", payload);
    this.authority.recordObservation(runId, hostTaskId, observation);
    this.inject("after_observation");
    if (worldObservation.status === "rejected" || !worldObservation.verificationSuccess) {
      const verification: VerificationReceipt = {
        schemaVersion: 1,
        kind: "ordivon.verification-receipt",
        dispatchId: observation.dispatchId,
        method: "game-world-event.v1",
        accepted: false,
        observationDigest: protocolDigest(observation),
        resultItems: [{
          subjectRef: hostTaskId,
          decisionDigest: protocolSha(attempt.decisionDigest ?? sha256({ attemptId: attempt.attemptId })),
          status: worldObservation.status === "rejected" ? "rejected" : "failed",
          reason: worldObservation.reason ?? worldObservation.rejectionCode ?? "World verification failed",
          evidenceDigest: observation.payloadDigest,
        }],
      };
      this.authority.recordVerification(runId, hostTaskId, verification);
      this.authority.complete(runId, hostTaskId, {
        schemaVersion: 1,
        kind: "ordivon.task-outcome",
        taskId: hostTaskId,
        goalId: goalIdFor(runId),
        status: "failed",
        verificationDigest: protocolDigest(verification),
        artifactRefs: [],
      });
      return this.rejectAttempt(
        runId,
        session,
        attempt,
        worldObservation.rejectionCode ? `world_${worldObservation.rejectionCode}` : "verification_failed",
        worldObservation.reason ?? "World execution failed",
        worldObservation.rejectionCode !== "stale_revision",
      );
    }
    return this.receipt(runId, "stable", `Recorded Observation for ${hostTaskId}`);
  }

  private advanceAttemptStep(
    runId: string,
    session: AgentSession,
    attempt: AgentAttempt,
  ): AgentHostStepReceipt {
    const nextIndex = attempt.skillStepIndex + 1;
    const nextStatus = nextIndex >= attempt.skillStepCount ? "verifying" as const : "executing" as const;
    const timestamp = now();
    const advanced: AgentAttempt = {
      ...attempt,
      revision: attempt.revision + 1,
      status: nextStatus,
      skillStepIndex: nextIndex,
      updatedAt: timestamp,
    };
    this.sessions.save(
      {
        ...session,
        revision: session.revision + 1,
        mode: nextStatus === "verifying" ? "verifying" : "executing",
        activeAttempt: advanced,
        updatedAt: timestamp,
      },
      "skill_step_verified",
      `agent-event:${attempt.attemptId}:step:${attempt.skillStepIndex}:verified`,
      {
        attemptId: attempt.attemptId,
        skillStepIndex: attempt.skillStepIndex,
        hostTaskId: stepTaskId(runId, attempt),
      },
    );
    return this.receipt(runId, "world_step_verified", `Verified Skill step ${attempt.skillStepIndex}`);
  }

  private markAttemptVerifying(
    runId: string,
    session: AgentSession,
    attempt: AgentAttempt,
  ): AgentHostStepReceipt {
    const timestamp = now();
    const verifying = { ...attempt, revision: attempt.revision + 1, status: "verifying" as const, updatedAt: timestamp };
    this.sessions.save(
      {
        ...session,
        revision: session.revision + 1,
        mode: "verifying",
        activeAttempt: verifying,
        updatedAt: timestamp,
      },
      "attempt_verifying",
      `agent-event:${attempt.attemptId}:verifying`,
      { attemptId: attempt.attemptId },
    );
    return this.verifyAttempt(runId, this.sessions.get(runId), verifying);
  }

  private verifyAttempt(
    runId: string,
    session: AgentSession,
    attempt: AgentAttempt,
  ): AgentHostStepReceipt {
    const context = this.contextFromAttempt(attempt);
    const candidate = context.payload.allowedOperations.find(
      (item) => item.operationCandidateId === attempt.operationCandidateId,
    );
    if (!candidate) throw new Error("Attempt Operation is absent from its retained Context");
    const state = this.game.loadState(runId);
    if (state.mission.status === "failure") {
      return this.finishAttempt(runId, session, attempt, "failed", state.mission.reason, "task_failed");
    }
    if (!operationSucceeded(state, candidate.successCondition)) {
      return this.rejectAttempt(runId, session, attempt, "operation_unverified", "Operation success condition is not satisfied", true);
    }
    const eventType = state.mission.status === "victory" ? "task_succeeded" : "attempt_succeeded";
    return this.finishAttempt(runId, session, attempt, "succeeded", null, eventType);
  }

  private finishAttempt(
    runId: string,
    session: AgentSession,
    attempt: AgentAttempt,
    status: "succeeded" | "failed",
    blocker: string | null,
    eventType: "attempt_succeeded" | "task_succeeded" | "task_failed",
  ): AgentHostStepReceipt {
    const timestamp = now();
    const completed: AgentAttempt = {
      ...attempt,
      revision: attempt.revision + 1,
      status,
      blocker,
      updatedAt: timestamp,
    };
    this.sessions.save(
      {
        ...session,
        revision: session.revision + 1,
        mode: "idle",
        activeAttempt: null,
        completedAttempts: [...session.completedAttempts, completed],
        blockers: blocker ? [blocker] : [],
        updatedAt: timestamp,
      },
      eventType,
      `agent-event:${attempt.attemptId}:${eventType}`,
      { attemptId: attempt.attemptId, operationCandidateId: attempt.operationCandidateId, blocker },
    );
    if (eventType === "task_succeeded") return this.receipt(runId, "task_succeeded", "Verified rescue signal completed the Goal");
    if (eventType === "task_failed") return this.receipt(runId, "task_failed", blocker ?? "Mission failed");
    return this.receipt(runId, "attempt_succeeded", `Verified Operation ${candidateLabel(this.contextFromAttempt(attempt), attempt.operationCandidateId)}`);
  }

  private rejectAttempt(
    runId: string,
    session: AgentSession,
    attempt: AgentAttempt,
    code: string,
    detail: string,
    blocked: boolean,
  ): AgentHostStepReceipt {
    const timestamp = now();
    const rejected: AgentAttempt = {
      ...attempt,
      revision: attempt.revision + 1,
      status: blocked ? "blocked" : "failed",
      blocker: code,
      updatedAt: timestamp,
    };
    this.sessions.save(
      {
        ...session,
        revision: session.revision + 1,
        mode: blocked ? "blocked" : "idle",
        activeAttempt: null,
        completedAttempts: [...session.completedAttempts, rejected],
        blockers: blocked ? [code] : [],
        updatedAt: timestamp,
      },
      blocked ? "task_blocked" : "decision_rejected",
      `agent-event:${attempt.attemptId}:${code}`,
      { code, detail },
    );
    return this.receipt(runId, blocked ? "blocked" : "decision_rejected", detail);
  }

  private reconcileTerminalAttempt(
    runId: string,
    session: AgentSession,
    attempt: AgentAttempt,
  ): AgentHostStepReceipt {
    const timestamp = now();
    this.sessions.save(
      {
        ...session,
        revision: session.revision + 1,
        mode: attempt.status === "blocked" ? "blocked" : "idle",
        activeAttempt: null,
        completedAttempts: [...session.completedAttempts, attempt],
        blockers: attempt.blocker ? [attempt.blocker] : [],
        updatedAt: timestamp,
      },
      "task_reconciled",
      `agent-event:${attempt.attemptId}:reconciled`,
      { attemptId: attempt.attemptId, status: attempt.status },
    );
    return this.receipt(runId, attempt.status === "blocked" ? "blocked" : "stable", "Detached terminal Attempt reconciled");
  }

  private synchronizeTerminal(
    runId: string,
    missionStatus: "victory" | "failure",
  ): AgentHostStepReceipt {
    const eventType = missionStatus === "victory" ? "task_succeeded" : "task_failed";
    this.host.appendEvent(
      runId,
      eventType,
      `agent-event:${runId}:terminal:${missionStatus}`,
      { runId, missionStatus, worldDigest: sha256(this.game.loadState(runId)) },
    );
    return this.receipt(runId, eventType, "Synchronized terminal World state");
  }
}

function candidateLabel(context: CompiledAgentContext, operationCandidateId: string | null): string {
  return context.payload.allowedOperations.find((candidate) => candidate.operationCandidateId === operationCandidateId)?.label
    ?? operationCandidateId
    ?? "unknown";
}
