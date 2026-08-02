import { EmbeddedHostAuthority, type EmbeddedHostProjection } from "../host-contract/embedded-authority.ts";
import { protocolDigest, type ProtocolJson } from "../host-contract/canonical.ts";
import type {
  DispatchEnvelope,
  ObservationEnvelope,
  TaskDescriptor,
  TaskOutcome,
  VerificationReceipt,
  VerificationResultItem,
} from "../host-contract/model.ts";
import type { StationZeroFactionTurnPlan } from "./model.ts";
import { StationZeroV3TurnExecutor, type StationZeroV3TurnExecutorOptions } from "./executor.ts";
import type {
  StationZeroV3ExecutorObservation,
  StationZeroV3PlanReceipt,
  StationZeroV3PlanningHead,
  StationZeroV3PreparedTurn,
  StationZeroV3RecoveryResult,
} from "./p2-model.ts";
import { StationZeroV3Store } from "./persistence.ts";

function prefixedDigest(value: string): `sha256:${string}` {
  return value.startsWith("sha256:") ? value as `sha256:${string}` : `sha256:${value}`;
}

function asProtocolRecord(value: object): Record<string, ProtocolJson> {
  return value as unknown as Record<string, ProtocolJson>;
}

export interface StationZeroV3TurnServiceOptions {
  executor?: StationZeroV3TurnExecutor;
  executorOptions?: StationZeroV3TurnExecutorOptions;
}

export interface StationZeroV3ExecutionResult {
  observation: StationZeroV3ExecutorObservation;
  host: EmbeddedHostProjection;
}

export class StationZeroV3TurnService {
  readonly store: StationZeroV3Store;
  readonly authority: EmbeddedHostAuthority;
  readonly executor: StationZeroV3TurnExecutor;

  constructor(store: StationZeroV3Store, options: StationZeroV3TurnServiceOptions = {}) {
    this.store = store;
    this.authority = new EmbeddedHostAuthority(store);
    this.executor = options.executor ?? new StationZeroV3TurnExecutor(store, options.executorOptions);
  }

  openPlanning(runId: string): StationZeroV3PlanningHead {
    const latest = this.store.latestPlanning(runId);
    if (latest?.status === "committed") {
      const prepared = this.prepare(runId, latest.planningId).prepared;
      if (!this.store.turnReceiptByBatch(runId, prepared.batch.turnBatchId)) {
        throw new Error("Previous Station Zero v3 Turn is prepared but has no authoritative World result");
      }
      const reconciled = this.reconcile(runId, latest.planningId);
      if (reconciled.state !== "completed") throw new Error("Previous Station Zero v3 Turn is not Host-complete");
    } else if (latest?.status === "resolved") {
      const reconciled = this.reconcile(runId, latest.planningId);
      if (reconciled.state !== "completed") throw new Error("Previous Station Zero v3 Turn is not Host-complete");
    }
    return this.store.openPlanning(runId);
  }

  submitPlan(runId: string, planningId: string, plan: StationZeroFactionTurnPlan): StationZeroV3PlanReceipt {
    return this.store.submitFactionPlan(runId, planningId, plan);
  }

  prepare(runId: string, planningId: string): {
    prepared: StationZeroV3PreparedTurn;
    host: EmbeddedHostProjection;
  } {
    const planning = this.store.getPlanning(runId, planningId);
    const prepared = planning.status === "open"
      ? this.store.commitPlanning(runId, planningId)
      : this.store.preparedTurn(runId, planningId);
    const descriptor = this.taskDescriptor(prepared);
    const effect = this.effect(prepared);
    const request = this.request(prepared);
    const dispatch = this.dispatch(prepared, request);
    this.authority.ensureTask(runId, descriptor);
    const host = this.authority.prepare(runId, prepared.taskId, effect, request, dispatch);
    return { prepared, host };
  }

  execute(runId: string, planningId: string): StationZeroV3ExecutionResult {
    const { prepared } = this.prepare(runId, planningId);
    const observation = this.executor.deliver(prepared);
    const host = this.reconcile(runId, planningId);
    return { observation, host };
  }

  observe(runId: string, planningId: string): StationZeroV3ExecutorObservation | null {
    const prepared = this.store.preparedTurn(runId, planningId);
    return this.executor.observe(prepared);
  }

  reconcile(runId: string, planningId: string): EmbeddedHostProjection {
    const { prepared } = this.prepare(runId, planningId);
    const executorObservation = this.executor.observe(prepared);
    if (!executorObservation) return this.authority.projection(runId, prepared.taskId);
    const receipt = this.store.turnReceiptByBatch(runId, prepared.batch.turnBatchId);
    if (!receipt) throw new Error("Station Zero v3 executor observation has no retained Turn receipt");

    const payload = asProtocolRecord(executorObservation);
    const payloadDigest = protocolDigest(payload);
    const observation: ObservationEnvelope = {
      schemaVersion: 1,
      kind: "ordivon.observation-envelope",
      dispatchId: prepared.dispatchId,
      executorId: this.executor.executorId,
      status: "succeeded",
      payloadDigest,
      evidenceRefs: [
        {
          ref: receipt.event.eventId,
          kind: receipt.event.kind,
          digest: prefixedDigest(receipt.eventDigest),
        },
        {
          ref: `turn-record:${receipt.turnBatchId}`,
          kind: receipt.record.kind,
          digest: prefixedDigest(receipt.recordDigest),
        },
      ],
    };
    const resultByIntent = new Map(receipt.record.resolution.intentResolutions.map((result) => [result.intentId, result]));
    const resultItems: VerificationResultItem[] = receipt.batch.factionPlans
      .flatMap((plan) => plan.actorIntents)
      .map((intent) => {
        const result = resultByIntent.get(intent.intentId);
        if (!result) throw new Error(`Station Zero v3 Turn Record is missing Intent Resolution: ${intent.intentId}`);
        return {
          subjectRef: intent.intentId,
          decisionDigest: protocolDigest(intent as unknown as ProtocolJson),
          status: result.status === "executed" || result.status === "no_effect" ? "succeeded" : "failed",
          reason: result.status === "executed" || result.status === "no_effect" ? null : result.reason,
          evidenceDigest: payloadDigest,
        } satisfies VerificationResultItem;
      });
    const verification: VerificationReceipt = {
      schemaVersion: 1,
      kind: "ordivon.verification-receipt",
      dispatchId: prepared.dispatchId,
      method: "station-zero-v3-turn-record.v1",
      accepted: receipt.record.resolution.intentResolutions.every((result) => result.verificationPassed),
      observationDigest: protocolDigest(observation),
      resultItems,
    };

    return this.authority.contracts.batch(runId, () => {
      this.authority.host.putProtocolArtifact(executorObservation.kind, payload);
      this.authority.recordObservation(runId, prepared.taskId, observation);
      const verified = this.authority.recordVerification(runId, prepared.taskId, verification);
      const outcome: TaskOutcome = {
        schemaVersion: 1,
        kind: "ordivon.task-outcome",
        taskId: prepared.taskId,
        goalId: prepared.goalId,
        status: verification.accepted ? "completed" : "failed",
        verificationDigest: verified.verificationDigest,
        artifactRefs: [
          {
            ref: receipt.event.eventId,
            kind: receipt.event.kind,
            digest: prefixedDigest(receipt.eventDigest),
          },
          {
            ref: `turn-record:${receipt.turnBatchId}`,
            kind: receipt.record.kind,
            digest: prefixedDigest(receipt.recordDigest),
          },
        ],
      };
      return this.authority.complete(runId, prepared.taskId, outcome);
    });
  }

  recover(runId: string): {
    world: StationZeroV3RecoveryResult;
    host: EmbeddedHostProjection | null;
  } {
    const world = this.store.recover(runId);
    const plannings = this.store.listPlanning(runId);
    let host: EmbeddedHostProjection | null = null;
    for (const planning of plannings) {
      if (planning.status === "open") continue;
      const prepared = this.prepare(runId, planning.planningId).prepared;
      const projection = this.store.turnReceiptByBatch(runId, prepared.batch.turnBatchId)
        ? this.reconcile(runId, planning.planningId)
        : this.authority.projection(runId, prepared.taskId);
      host = projection;
    }
    this.authority.verify(runId);
    return { world, host };
  }

  hostProjection(runId: string, planningId: string): EmbeddedHostProjection | null {
    const planning = this.store.getPlanning(runId, planningId);
    if (!planning.taskId) return null;
    const descriptor = this.authority.contracts.latest(runId, planning.taskId, "ordivon.host-task-descriptor");
    return descriptor ? this.authority.projection(runId, planning.taskId) : null;
  }

  private taskDescriptor(prepared: StationZeroV3PreparedTurn): TaskDescriptor {
    return {
      schemaVersion: 1,
      kind: "ordivon.host-task-descriptor",
      taskId: prepared.taskId,
      goalId: prepared.goalId,
      workloadId: "ordivon.game.station-zero-v3.turn.v1",
      assigneeRef: "coordinator:station-zero-v3",
      providerPolicyRef: null,
      domainRef: `game-run:${prepared.planning.runId}`,
      configurationDigests: [
        prefixedDigest(prepared.planning.worldDigest),
        prefixedDigest(prepared.planning.commitmentDigest),
        prefixedDigest(prepared.batchDigest),
      ].sort(),
    };
  }

  private effect(prepared: StationZeroV3PreparedTurn): Record<string, ProtocolJson> {
    return {
      schemaVersion: 1,
      kind: "ordivon.game.station-zero-v3-turn-effect",
      effectId: prepared.effectId,
      runId: prepared.planning.runId,
      planningId: prepared.planning.planningId,
      turnBatchId: prepared.batch.turnBatchId,
      batchDigest: prefixedDigest(prepared.batchDigest),
    };
  }

  private request(prepared: StationZeroV3PreparedTurn): Record<string, ProtocolJson> {
    return {
      schemaVersion: 1,
      kind: "ordivon.game.station-zero-v3-turn-request",
      runId: prepared.planning.runId,
      planningId: prepared.planning.planningId,
      turnBatchId: prepared.batch.turnBatchId,
      batchDigest: prefixedDigest(prepared.batchDigest),
      batch: prepared.batch as unknown as ProtocolJson,
    };
  }

  private dispatch(
    prepared: StationZeroV3PreparedTurn,
    request: Record<string, ProtocolJson>,
  ): DispatchEnvelope {
    return {
      schemaVersion: 1,
      kind: "ordivon.dispatch-envelope",
      dispatchId: prepared.dispatchId,
      effectId: prepared.effectId,
      executorId: this.executor.executorId,
      requestDigest: protocolDigest(request),
      idempotencyKey: prepared.batch.turnBatchId,
      requiredStateRefs: [
        {
          ref: `game-world:${prepared.planning.runId}`,
          digest: prefixedDigest(prepared.planning.worldDigest),
        },
        {
          ref: `station-zero-v3-planning:${prepared.planning.planningId}`,
          digest: prefixedDigest(prepared.planning.commitmentDigest),
        },
      ],
      expectedObservationKind: "ordivon.game.station-zero-v3-turn-observation",
    };
  }
}
