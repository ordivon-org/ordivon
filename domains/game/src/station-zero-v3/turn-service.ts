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

export interface StationZeroV3TurnServiceOptions {
  executor?: StationZeroV3TurnExecutor;
  executorOptions?: StationZeroV3TurnExecutorOptions;
}

export interface StationZeroV3ExecutionResult {
  observation: StationZeroV3ExecutorObservation;
}

export class StationZeroV3TurnService {
  readonly store: StationZeroV3Store;
  readonly executor: StationZeroV3TurnExecutor;

  constructor(store: StationZeroV3Store, options: StationZeroV3TurnServiceOptions = {}) {
    this.store = store;
    this.executor = options.executor ?? new StationZeroV3TurnExecutor(store, options.executorOptions);
  }

  openPlanning(runId: string): StationZeroV3PlanningHead {
    const latest = this.store.latestPlanning(runId);
    if (latest?.status === "committed" || latest?.status === "resolved") {
      const prepared = this.prepare(runId, latest.planningId).prepared;
      const observation = this.executor.observe(prepared);
      if (!observation) {
        if (latest.status === "committed") {
          throw new Error("Previous Station Zero v3 Turn is prepared but has no authoritative World result");
        }
        throw new Error("Resolved Station Zero v3 Turn has no authoritative World result");
      }
    }
    return this.store.openPlanning(runId);
  }

  submitPlan(runId: string, planningId: string, plan: StationZeroFactionTurnPlan): StationZeroV3PlanReceipt {
    return this.store.submitFactionPlan(runId, planningId, plan);
  }

  prepare(runId: string, planningId: string): { prepared: StationZeroV3PreparedTurn } {
    const planning = this.store.getPlanning(runId, planningId);
    const prepared = planning.status === "open"
      ? this.store.commitPlanning(runId, planningId)
      : this.store.preparedTurn(runId, planningId);
    return { prepared };
  }

  execute(runId: string, planningId: string): StationZeroV3ExecutionResult {
    const { prepared } = this.prepare(runId, planningId);
    return { observation: this.executor.deliver(prepared) };
  }

  observe(runId: string, planningId: string): StationZeroV3ExecutorObservation | null {
    const prepared = this.store.preparedTurn(runId, planningId);
    return this.executor.observe(prepared);
  }

  recover(runId: string): { world: StationZeroV3RecoveryResult } {
    const world = this.store.recover(runId);
    for (const planning of this.store.listPlanning(runId)) {
      if (planning.status === "open") continue;
      const prepared = this.prepare(runId, planning.planningId).prepared;
      const observation = this.executor.observe(prepared);
      if (planning.status === "resolved" && !observation) {
        throw new Error(`Resolved Station Zero v3 Planning lacks authoritative Turn evidence: ${planning.planningId}`);
      }
    }
    return { world };
  }
}
