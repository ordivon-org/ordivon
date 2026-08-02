import { canonicalJson } from "../digest.ts";
import type {
  StationZeroV3ExecutorObservation,
  StationZeroV3PreparedTurn,
  StationZeroV3TurnReceipt,
} from "./p2-model.ts";
import type { StationZeroV3Store } from "./persistence.ts";

export interface StationZeroV3TurnExecutorOptions {
  faultInjector?: (point: "after_world_commit") => void;
}

export class StationZeroV3TurnExecutor {
  readonly executorId = "executor:station-zero-v3-world-v1" as const;
  readonly store: StationZeroV3Store;
  readonly faultInjector: ((point: "after_world_commit") => void) | undefined;

  constructor(store: StationZeroV3Store, options: StationZeroV3TurnExecutorOptions = {}) {
    this.store = store;
    this.faultInjector = options.faultInjector;
  }

  deliver(prepared: StationZeroV3PreparedTurn): StationZeroV3ExecutorObservation {
    const retained = this.store.turnReceiptByBatch(prepared.planning.runId, prepared.batch.turnBatchId);
    if (retained) return this.fromReceipt(prepared, retained, true);
    const committed = this.store.applyPreparedTurn(prepared.planning.runId, prepared.planning.planningId);
    this.faultInjector?.("after_world_commit");
    const observed = this.store.turnReceiptByBatch(prepared.planning.runId, prepared.batch.turnBatchId);
    if (!observed) throw new Error("accepted Station Zero v3 Turn has no retained receipt");
    return this.fromReceipt(prepared, observed, committed.idempotent);
  }

  observe(prepared: StationZeroV3PreparedTurn): StationZeroV3ExecutorObservation | null {
    const retained = this.store.turnReceiptByBatch(prepared.planning.runId, prepared.batch.turnBatchId);
    return retained ? this.fromReceipt(prepared, retained, true) : null;
  }

  private fromReceipt(
    prepared: StationZeroV3PreparedTurn,
    receipt: StationZeroV3TurnReceipt,
    idempotent: boolean,
  ): StationZeroV3ExecutorObservation {
    if (
      receipt.planningId !== prepared.planning.planningId ||
      receipt.turnBatchId !== prepared.batch.turnBatchId ||
      receipt.taskId !== prepared.taskId ||
      receipt.dispatchId !== prepared.dispatchId ||
      canonicalJson(receipt.batch) !== canonicalJson(prepared.batch)
    ) {
      throw new Error("retained Station Zero v3 Turn differs from executor request");
    }
    if (!receipt.record.resolution.intentResolutions.every((resolution) => resolution.verificationPassed)) {
      throw new Error("retained Station Zero v3 Turn contains an unverified Intent Resolution");
    }
    return {
      schemaVersion: 1,
      kind: "ordivon.game.station-zero-v3-turn-observation",
      executorId: this.executorId,
      runId: receipt.runId,
      planningId: receipt.planningId,
      turnBatchId: receipt.turnBatchId,
      taskId: receipt.taskId,
      dispatchId: receipt.dispatchId,
      status: "succeeded",
      idempotent,
      turnSequence: receipt.turnSequence,
      worldEventId: receipt.event.eventId,
      worldEventDigest: receipt.eventDigest,
      turnRecordDigest: receipt.recordDigest,
      worldAfterDigest: receipt.stateDigest,
      verificationPassed: true,
    };
  }
}
