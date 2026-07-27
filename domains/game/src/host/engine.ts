import { canonicalJson, sha256 } from "../digest.ts";
import type { AgentContextPayload, CompiledAgentContext } from "./context.ts";
import { compileAgentContext } from "./context.ts";
import {
  compileSkillPlan,
  materializeSkillStep,
  operationSucceeded,
  type OperationCandidate,
  type SkillPlan,
} from "./operations.ts";
import {
  newAttemptId,
  terminalGoalStatus,
  terminalTaskPhase,
  type AgentAttempt,
  type AgentGoal,
  type AgentProjection,
  type AgentTask,
} from "./model.ts";
import {
  HostExecutionStore,
  type HostDispatch,
  type HostEffect,
  type HostObservation,
} from "./execution-store.ts";
import { HostStore } from "./store.ts";
import type { OperationDecision, OperationProvider } from "../providers/types.ts";
import { DecisionAdmissionError, ProviderAdapterError, admitOperationDecision } from "../providers/types.ts";
import type { GameStore } from "../storage.ts";

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

export class AgentHost {
  readonly game: GameStore;
  readonly provider: OperationProvider;
  readonly host: HostStore;
  readonly execution: HostExecutionStore;
  readonly faultInjector: ((point: HostFaultPoint) => void) | undefined;

  constructor(game: GameStore, provider: OperationProvider, options: AgentHostOptions = {}) {
    this.game = game;
    this.provider = provider;
    this.host = new HostStore(game.db);
    this.execution = new HostExecutionStore(game.db, this.host);
    this.faultInjector = options.faultInjector;
  }

  initialize(runId = this.game.activeRunId, providerOrder = [this.provider.providerId]): AgentProjection {
    return this.host.initializeRun(this.game.getRun(runId), this.game.loadState(runId), providerOrder);
  }

  projection(runId = this.game.activeRunId): AgentProjection {
    return this.host.getProjection(runId);
  }

  private inject(point: HostFaultPoint): void {
    this.faultInjector?.(point);
  }

  private receipt(
    runId: string,
    status: AgentHostStepReceipt["status"],
    detail: string,
    projection = this.host.getProjection(runId),
  ): AgentHostStepReceipt {
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
    let projection = this.host.getProjection(runId);

    if (state.mission.status !== "running") {
      if (projection.task.activeAttemptId) {
        return this.verifyAttempt(runId, projection, this.host.getAttempt(projection.task.activeAttemptId));
      }
      return this.synchronizeTerminal(runId, state.mission.status, projection);
    }
    if (["blocked", "succeeded", "failed", "cancelled"].includes(projection.task.phase)) {
      return this.receipt(runId, projection.task.phase === "blocked" ? "blocked" : "stable", "Task has no automatic progress", projection);
    }
    if (!projection.task.activeAttemptId) {
      return this.compileContext(runId, projection);
    }
    const attempt = this.host.getAttempt(projection.task.activeAttemptId);
    if (attempt.status === "provider_pending" || attempt.status === "context_pending") {
      return await this.invokeProvider(runId, projection, attempt);
    }
    if (["decision_recorded", "executing", "reconciling"].includes(attempt.status)) {
      return this.executeAttemptStep(runId, projection, attempt);
    }
    if (attempt.status === "verifying") {
      return this.verifyAttempt(runId, projection, attempt);
    }
    if (["blocked", "failed", "cancelled", "succeeded"].includes(attempt.status)) {
      const task = { ...projection.task, activeAttemptId: null, phase: attempt.status === "succeeded" ? "ready" as const : "blocked" as const, revision: projection.task.revision + 1, updatedAt: now() };
      this.host.saveTask(task, "task_reconciled", `host-event:${task.taskId}:reconciled:${task.revision}`);
      return this.receipt(runId, task.phase === "blocked" ? "blocked" : "stable", "Detached terminal Attempt reconciled");
    }
    return this.receipt(runId, "stable", "No Host transition matched", projection);
  }

  async run(runId = this.game.activeRunId, maximumSteps = 256): Promise<AgentHostRunReceipt> {
    if (!Number.isSafeInteger(maximumSteps) || maximumSteps < 1) throw new TypeError("maximumSteps must be positive");
    const steps: AgentHostStepReceipt[] = [];
    for (let index = 0; index < maximumSteps; index += 1) {
      const receipt = await this.step(runId);
      steps.push(receipt);
      const projection = this.host.getProjection(runId);
      if (["blocked", "succeeded", "failed", "cancelled"].includes(projection.task.phase)) break;
    }
    const state = this.game.loadState(runId);
    return {
      runId,
      steps,
      projection: this.host.getProjection(runId),
      worldDigest: sha256(state),
      worldRevision: state.revision,
    };
  }

  private compileContext(runId: string, projection: AgentProjection): AgentHostStepReceipt {
    const state = this.game.loadState(runId);
    const context = compileAgentContext(
      this.game.getRun(runId),
      state,
      projection,
      this.game.recentJournalEvents(12, runId),
    );
    const artifact = this.host.putArtifact("agent-context-v2", context.payload);
    this.inject("after_context_artifact");
    const createdAt = now();
    const attempt: AgentAttempt = {
      attemptId: newAttemptId(runId),
      taskId: projection.task.taskId,
      runId,
      attemptNumber: projection.attempts.length + 1,
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
      createdAt,
      updatedAt: createdAt,
    };
    const task: AgentTask = {
      ...projection.task,
      phase: "active",
      revision: projection.task.revision + 1,
      activeAttemptId: attempt.attemptId,
      blockers: [],
      updatedAt: createdAt,
    };
    this.host.activateAttempt(task, attempt);
    return this.receipt(runId, "context_compiled", `Persisted Context ${context.contextId}`);
  }

  private contextFromAttempt(attempt: AgentAttempt): CompiledAgentContext {
    if (!attempt.contextDigest) throw new Error("Attempt has no Context Artifact");
    const artifact = this.host.getArtifact<AgentContextPayload>(attempt.contextDigest);
    const payload = artifact.content;
    return {
      payload,
      contextId: payload.contextId,
      digest: sha256(payload),
      byteLength: artifact.byteLength,
    };
  }

  private async invokeProvider(
    runId: string,
    projection: AgentProjection,
    attempt: AgentAttempt,
  ): Promise<AgentHostStepReceipt> {
    const context = this.contextFromAttempt(attempt);
    const current = this.game.loadState(runId);
    if (
      current.revision !== context.payload.run.worldRevision ||
      sha256(current) !== context.payload.run.worldDigest
    ) {
      return this.rejectAttempt(runId, projection, attempt, "context_stale", "World changed before Provider admission", false);
    }
    let decision: OperationDecision;
    try {
      decision = await this.provider.decide(context);
      this.inject("after_provider_call");
    } catch (error) {
      if (!(error instanceof ProviderAdapterError)) throw error;
      return this.rejectAttempt(runId, projection, attempt, `provider_${error.code}`, error.message, true);
    }
    const evidence = this.provider.evidenceMetadata?.() ?? null;
    const evidenceArtifact = evidence ? this.host.putArtifact("provider-evidence-v1", evidence) : null;
    const decisionArtifact = this.host.putArtifact("operation-decision-v1", decision);
    this.inject("after_decision_artifact");

    let candidate: OperationCandidate | null;
    try {
      candidate = admitOperationDecision(context, this.game.loadState(runId), decision);
    } catch (error) {
      if (!(error instanceof DecisionAdmissionError)) throw error;
      const retryable = error.code === "stale_world";
      return this.rejectAttempt(runId, projection, attempt, `decision_${error.code}`, error.message, !retryable);
    }
    if (!candidate) {
      return this.rejectAttempt(runId, projection, attempt, "provider_declined", "Provider selected no Operation", true);
    }
    const plan = compileSkillPlan(this.game.loadState(runId), candidate);
    const planArtifact = this.host.putArtifact("skill-plan-v1", plan);
    const updatedAt = now();
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
      updatedAt,
    };
    const task = { ...projection.task, revision: projection.task.revision + 1, updatedAt };
    this.host.saveTaskAndAttempt(task, updated, "decision_recorded",
      `host-event:${attempt.attemptId}:decision-recorded`, {
        attemptId: attempt.attemptId,
        contextDigest: attempt.contextDigest,
        decisionDigest: decisionArtifact.digest,
        planDigest: planArtifact.digest,
        providerEvidenceDigest: evidenceArtifact?.digest ?? null,
        operationCandidateId: candidate.operationCandidateId,
      });
    return this.receipt(runId, "decision_recorded", `Provider selected ${candidate.label}`);
  }

  private executeAttemptStep(
    runId: string,
    projection: AgentProjection,
    attempt: AgentAttempt,
  ): AgentHostStepReceipt {
    if (!attempt.planDigest || !attempt.operationCandidateId) throw new Error("Attempt has no admitted Skill Plan");
    const plan = this.host.getArtifact<SkillPlan>(attempt.planDigest).content;
    if (attempt.skillStepIndex >= plan.steps.length) {
      const updatedAt = now();
      const verifying = { ...attempt, revision: attempt.revision + 1, status: "verifying" as const, updatedAt };
      const task = { ...projection.task, revision: projection.task.revision + 1, updatedAt };
      this.host.saveTaskAndAttempt(task, verifying, "attempt_verifying",
        `host-event:${attempt.attemptId}:verifying`, { attemptId: attempt.attemptId });
      return this.verifyAttempt(runId, this.host.getProjection(runId), verifying);
    }
    let dispatch = this.execution.findDispatchForStep(attempt.attemptId, attempt.skillStepIndex);
    if (dispatch) return this.reconcileDispatch(runId, projection, attempt, dispatch);
    const context = this.contextFromAttempt(attempt);
    const expectedRevision = context.payload.run.worldRevision + attempt.skillStepIndex;
    const current = this.game.loadState(runId);
    if (current.revision !== expectedRevision) {
      return this.rejectAttempt(runId, projection, attempt, "world_drift", `Expected world revision ${expectedRevision}, found ${current.revision}`, false);
    }
    if (!dispatch) {
      const step = plan.steps[attempt.skillStepIndex];
      if (!step) throw new Error("Skill Plan step is missing");
      const effectId = `effect:${attempt.attemptId}:${attempt.skillStepIndex}`;
      const dispatchId = `dispatch:${effectId}`;
      const commandId = `command:${dispatchId}`;
      const createdAt = now();
      const effect: HostEffect = {
        effectId,
        runId,
        taskId: attempt.taskId,
        attemptId: attempt.attemptId,
        operationCandidateId: attempt.operationCandidateId,
        skillStepIndex: attempt.skillStepIndex,
        requiredWorldRevision: current.revision,
        requiredWorldDigest: sha256(current),
        commandId,
        worldCommand: materializeSkillStep(current, step, commandId),
        status: "proposed",
        createdAt,
        updatedAt: createdAt,
      };
      this.execution.putEffect(effect);
      dispatch = this.execution.putDispatch({
        dispatchId,
        effectId,
        runId,
        attemptId: attempt.attemptId,
        skillStepIndex: attempt.skillStepIndex,
        commandId,
        status: "pending",
        worldEventId: null,
        commandSequence: null,
        error: null,
        createdAt,
        updatedAt: createdAt,
      });
      this.inject("after_dispatch_prepare");
      return this.receipt(runId, "dispatch_prepared", `Prepared ${dispatch.dispatchId}`);
    }
    throw new Error("unreachable Dispatch state");
  }

  private reconcileDispatch(
    runId: string,
    projection: AgentProjection,
    attempt: AgentAttempt,
    dispatch: HostDispatch,
  ): AgentHostStepReceipt {
    const effect = this.execution.getEffect(dispatch.effectId);
    let observation = this.execution.findObservation(dispatch.dispatchId);
    if (!observation) {
      let retained = this.game.commandReceipt(dispatch.commandId, runId);
      if (!retained) {
        const applied = this.game.apply(effect.worldCommand, runId);
        if (applied.result.status !== "accepted") {
          const updatedAt = now();
          this.execution.saveDispatch({ ...dispatch, status: "rejected", error: `${applied.result.code}: ${applied.result.reason}`, updatedAt }, "dispatch_rejected");
          this.execution.saveEffect({ ...effect, status: "rejected", updatedAt }, "effect_rejected");
          return this.rejectAttempt(
            runId,
            projection,
            attempt,
            `world_${applied.result.code}`,
            applied.result.reason,
            applied.result.code !== "stale_revision",
          );
        }
        this.inject("after_world_apply");
        retained = this.game.commandReceipt(dispatch.commandId, runId);
      }
      if (!retained) throw new Error("accepted world Command has no retained receipt");
      if (canonicalJson(retained.command) !== canonicalJson(effect.worldCommand)) {
        throw new Error("retained Command differs from the prepared Effect");
      }
      const event = retained.journalEvent.event;
      observation = {
        observationId: `observation:${dispatch.dispatchId}`,
        dispatchId: dispatch.dispatchId,
        effectId: effect.effectId,
        runId,
        commandId: dispatch.commandId,
        commandSequence: retained.commandSequence,
        worldEventId: event.eventId,
        worldAfterDigest: event.afterDigest,
        facts: event.facts ?? [],
        verification: event.verification ?? null,
        createdAt: now(),
      };
      this.execution.putObservation(observation);
      this.inject("after_observation");
    }
    if (observation.verification?.success !== true) {
      return this.rejectAttempt(runId, projection, attempt, "verification_failed", "World Event did not contain successful Verification", true);
    }
    const updatedAt = now();
    if (dispatch.status !== "succeeded") {
      dispatch = this.execution.saveDispatch({
        ...dispatch,
        status: "succeeded",
        worldEventId: observation.worldEventId,
        commandSequence: observation.commandSequence,
        error: null,
        updatedAt,
      }, "dispatch_succeeded");
    }
    if (effect.status !== "succeeded") {
      this.execution.saveEffect({ ...effect, status: "succeeded", updatedAt }, "effect_succeeded");
    }
    this.inject("before_attempt_advance");
    const nextIndex = attempt.skillStepIndex + 1;
    const nextStatus = nextIndex >= attempt.skillStepCount ? "verifying" as const : "executing" as const;
    const advanced: AgentAttempt = {
      ...attempt,
      revision: attempt.revision + 1,
      status: nextStatus,
      skillStepIndex: nextIndex,
      updatedAt,
    };
    const task = { ...projection.task, revision: projection.task.revision + 1, updatedAt };
    this.host.saveTaskAndAttempt(task, advanced, "skill_step_verified",
      `host-event:${attempt.attemptId}:step:${attempt.skillStepIndex}:verified`, {
        attemptId: attempt.attemptId,
        skillStepIndex: attempt.skillStepIndex,
        dispatchId: dispatch.dispatchId,
        observationId: observation.observationId,
      });
    return this.receipt(runId, "world_step_verified", `Verified Skill step ${attempt.skillStepIndex}`);
  }

  private verifyAttempt(
    runId: string,
    projection: AgentProjection,
    attempt: AgentAttempt,
  ): AgentHostStepReceipt {
    const context = this.contextFromAttempt(attempt);
    const candidate = context.payload.allowedOperations.find(
      (item) => item.operationCandidateId === attempt.operationCandidateId,
    );
    if (!candidate) throw new Error("Attempt Operation is absent from its retained Context");
    const state = this.game.loadState(runId);
    const updatedAt = now();
    if (state.mission.status === "failure") {
      const failedAttempt = { ...attempt, revision: attempt.revision + 1, status: "failed" as const, blocker: state.mission.reason, updatedAt };
      const goal: AgentGoal = { ...projection.goal, status: "failed", revision: projection.goal.revision + 1, updatedAt };
      const task: AgentTask = { ...projection.task, phase: "failed", revision: projection.task.revision + 1, activeAttemptId: null, blockers: [state.mission.reason ?? "mission_failure"], updatedAt };
      this.host.saveGoalTaskAndAttempt(goal, task, failedAttempt, "task_failed",
        `host-event:${task.taskId}:failed`, { missionReason: state.mission.reason });
      return this.receipt(runId, "task_failed", state.mission.reason ?? "Mission failed");
    }
    if (!operationSucceeded(state, candidate.successCondition)) {
      return this.rejectAttempt(runId, projection, attempt, "operation_unverified", "Operation success condition is not satisfied", true);
    }
    const succeededAttempt: AgentAttempt = {
      ...attempt,
      revision: attempt.revision + 1,
      status: "succeeded",
      blocker: null,
      updatedAt,
    };
    const completedAttemptIds = projection.task.completedAttemptIds.includes(attempt.attemptId)
      ? projection.task.completedAttemptIds
      : [...projection.task.completedAttemptIds, attempt.attemptId];
    if (state.mission.status === "victory") {
      const goal: AgentGoal = { ...projection.goal, status: "succeeded", revision: projection.goal.revision + 1, updatedAt };
      const task: AgentTask = { ...projection.task, phase: "succeeded", revision: projection.task.revision + 1, activeAttemptId: null, completedAttemptIds, blockers: [], updatedAt };
      this.host.saveGoalTaskAndAttempt(goal, task, succeededAttempt, "task_succeeded",
        `host-event:${task.taskId}:succeeded`, { worldDigest: sha256(state), missionReason: state.mission.reason });
      return this.receipt(runId, "task_succeeded", "Verified rescue signal completed the Goal");
    }
    const task: AgentTask = {
      ...projection.task,
      phase: "ready",
      revision: projection.task.revision + 1,
      activeAttemptId: null,
      completedAttemptIds,
      blockers: [],
      updatedAt,
    };
    this.host.saveTaskAndAttempt(task, succeededAttempt, "attempt_succeeded",
      `host-event:${attempt.attemptId}:succeeded`, { operationCandidateId: attempt.operationCandidateId });
    return this.receipt(runId, "attempt_succeeded", `Verified Operation ${candidate.label}`);
  }

  private rejectAttempt(
    runId: string,
    projection: AgentProjection,
    attempt: AgentAttempt,
    code: string,
    detail: string,
    blocked: boolean,
  ): AgentHostStepReceipt {
    const updatedAt = now();
    const rejected: AgentAttempt = {
      ...attempt,
      revision: attempt.revision + 1,
      status: blocked ? "blocked" : "failed",
      blocker: code,
      updatedAt,
    };
    const task: AgentTask = {
      ...projection.task,
      phase: blocked ? "blocked" : "ready",
      revision: projection.task.revision + 1,
      activeAttemptId: null,
      blockers: blocked ? [code] : [],
      updatedAt,
    };
    this.host.saveTaskAndAttempt(task, rejected, blocked ? "task_blocked" : "decision_rejected",
      `host-event:${attempt.attemptId}:${code}`, { code, detail });
    return this.receipt(runId, blocked ? "blocked" : "decision_rejected", detail);
  }

  private synchronizeTerminal(
    runId: string,
    missionStatus: "victory" | "failure",
    projection: AgentProjection,
  ): AgentHostStepReceipt {
    const desiredGoal = terminalGoalStatus(missionStatus);
    const desiredTask = terminalTaskPhase(missionStatus);
    if (projection.goal.status === desiredGoal && projection.task.phase === desiredTask) {
      return this.receipt(runId, missionStatus === "victory" ? "task_succeeded" : "task_failed", "Terminal world already synchronized", projection);
    }
    const updatedAt = now();
    const goal = { ...projection.goal, status: desiredGoal, revision: projection.goal.revision + 1, updatedAt };
    const task = { ...projection.task, phase: desiredTask, revision: projection.task.revision + 1, activeAttemptId: null, updatedAt };
    this.host.saveGoalAndTask(goal, task, missionStatus === "victory" ? "task_succeeded" : "task_failed",
      `host-event:${task.taskId}:terminal-sync:${task.revision}`, { missionStatus });
    return this.receipt(runId, missionStatus === "victory" ? "task_succeeded" : "task_failed", "Synchronized terminal World state");
  }
}
