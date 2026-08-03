import { sha256 } from "../digest.ts";
import {
  buildStationZeroV3PlanPreview,
  createStationZeroV3PlayCatalog,
  fixtureStationZeroV3AgentProviderFactory,
} from "./agent-planning.ts";
import { createStationZeroV3PlayView } from "./play-projection.ts";
import { StationZeroV3PlanningStore } from "./planning-store.ts";
import type {
  StationZeroV3AgentProviderFactory,
  StationZeroV3CommanderOrder,
  StationZeroV3CommitReceipt,
  StationZeroV3OrderSaveReceipt,
  StationZeroV3PlanPreview,
  StationZeroV3PlayCatalog,
  StationZeroV3PlayRunSummary,
  StationZeroV3PlayView,
  StationZeroV3PreviewReceipt,
} from "./p3-model.ts";
import { StationZeroV3Store } from "./persistence.ts";
import { StationZeroV3TurnService } from "./turn-service.ts";
import { STATION_ZERO_FACTION_IDS } from "./model.ts";

export interface StationZeroV3PlayServiceOptions {
  providerFactory?: StationZeroV3AgentProviderFactory;
}

export type StationZeroV3CommanderOrderPatch = Partial<Pick<
  StationZeroV3CommanderOrder,
  | "primaryObjectiveId"
  | "posture"
  | "formation"
  | "retreatHealthThreshold"
  | "lethalForce"
  | "collateralPolicy"
  | "lootPolicy"
  | "protectedActorId"
  | "priorityTargetActorId"
  | "commanderDirectiveId"
>>;

export class StationZeroV3PlayService {
  readonly store: StationZeroV3Store;
  readonly turns: StationZeroV3TurnService;
  readonly planning: StationZeroV3PlanningStore;
  readonly providerFactory: StationZeroV3AgentProviderFactory;

  constructor(store: StationZeroV3Store, options: StationZeroV3PlayServiceOptions = {}) {
    this.store = store;
    this.turns = new StationZeroV3TurnService(store);
    this.planning = new StationZeroV3PlanningStore(store);
    this.providerFactory = options.providerFactory ?? fixtureStationZeroV3AgentProviderFactory;
  }

  catalog(): StationZeroV3PlayCatalog {
    return createStationZeroV3PlayCatalog();
  }

  listRuns(): StationZeroV3PlayRunSummary[] {
    return this.store.listRuns().map((run) => {
      const state = this.store.loadState(run.runId);
      return {
        runId: run.runId,
        status: run.status,
        turn: state.encounter.turn,
        turnLimit: state.encounter.turnLimit,
        createdAt: run.createdAt,
        outcome: state.factions.rescue.outcome,
      };
    }).sort((left, right) => right.createdAt.localeCompare(left.createdAt));
  }

  initialize(input: { runId: string; seed?: string }): StationZeroV3PlayView {
    this.store.createRun(input);
    this.resume(input.runId);
    return this.state(input.runId);
  }

  resume(runId: string): StationZeroV3PlayView {
    this.turns.recover(runId);
    const state = this.store.loadState(runId);
    if (state.encounter.status === "running") {
      const latest = this.store.latestPlanning(runId);
      if (!latest || latest.status === "resolved") {
        const planning = this.turns.openPlanning(runId);
        this.planning.ensureDefaultOrder(runId, planning.planningId);
      } else if (latest.status === "open") {
        this.planning.ensureDefaultOrder(runId, latest.planningId);
      }
    }
    this.planning.verifyRun(runId);
    return this.state(runId);
  }

  state(runId: string): StationZeroV3PlayView {
    this.store.getRun(runId);
    return createStationZeroV3PlayView(this.store, this.turns, this.planning, runId);
  }

  saveOrder(runId: string, patch: StationZeroV3CommanderOrderPatch): StationZeroV3OrderSaveReceipt & { view: StationZeroV3PlayView } {
    const planning = this.requireOpenPlanning(runId);
    const current = this.planning.currentOrder(runId, planning.planningId);
    const order: StationZeroV3CommanderOrder = {
      ...current.order,
      ...patch,
      runId,
      planningId: planning.planningId,
      expectedWorldRevision: planning.worldRevision,
      expectedTurn: planning.turn,
      issuedBy: "player:mission-control",
    };
    const receipt = this.planning.saveOrder(runId, planning.planningId, order);
    return {
      runId: receipt.runId,
      planningId: receipt.planningId,
      orderRevision: receipt.orderRevision,
      orderDigest: receipt.orderDigest,
      idempotent: receipt.idempotent,
      view: this.state(runId),
    };
  }

  async generatePreview(runId: string): Promise<StationZeroV3PreviewReceipt & { view: StationZeroV3PlayView }> {
    const planning = this.requireOpenPlanning(runId);
    const head = this.planning.ensureDefaultOrder(runId, planning.planningId);
    const current = this.planning.currentOrder(runId, planning.planningId);
    const retained = this.planning.currentPreview(runId, planning.planningId);
    if (retained && head.previewDigest === retained.previewDigest && retained.orderDigest === current.orderDigest) {
      return { preview: retained, idempotent: true, view: this.state(runId) };
    }
    const state = this.store.stateAtRevision(runId, planning.worldRevision);
    const preview = await buildStationZeroV3PlanPreview({
      state,
      planning,
      orderRevision: current.orderRevision,
      order: current.order,
      orderDigest: current.orderDigest,
      providerFactory: this.providerFactory,
    });
    const receipt = this.planning.savePreview(preview);
    return { ...receipt, view: this.state(runId) };
  }

  async commitPreview(runId: string, previewId?: string): Promise<StationZeroV3CommitReceipt & { view: StationZeroV3PlayView }> {
    const planning = this.requireCurrentPlanning(runId);
    const preview = previewId
      ? this.planning.getPreview(runId, planning.planningId, previewId)
      : this.planning.currentPreview(runId, planning.planningId);
    if (!preview) throw new TypeError("Generate a Plan Preview before committing the Turn");
    const head = this.planning.getHead(runId, planning.planningId);
    if (head.previewId !== preview.previewId || head.previewDigest !== preview.previewDigest) {
      throw new TypeError("Only the active Plan Preview may be committed");
    }

    if (planning.status === "open") {
      for (const factionId of STATION_ZERO_FACTION_IDS) {
        this.turns.submitPlan(runId, planning.planningId, preview.factionPlans[factionId]);
      }
      this.planning.markCommitted(runId, planning.planningId, preview.previewId);
    } else if (planning.status === "committed") {
      if (head.status !== "committed" || head.committedPreviewId !== preview.previewId) {
        throw new TypeError("Committed Planning is not bound to the selected Plan Preview");
      }
    } else {
      throw new TypeError("Resolved Station Zero v3 Planning cannot execute again");
    }
    const execution = this.turns.execute(runId, planning.planningId);
    const state = this.store.loadState(runId);
    let nextPlanningId: string | null = null;
    if (state.encounter.status === "running") {
      const next = this.turns.openPlanning(runId);
      this.planning.ensureDefaultOrder(runId, next.planningId);
      nextPlanningId = next.planningId;
    }
    this.planning.verifyRun(runId);
    return {
      runId,
      planningId: planning.planningId,
      previewId: preview.previewId,
      turnSequence: execution.observation.turnSequence,
      worldRevision: state.revision,
      hostState: execution.host.state,
      nextPlanningId,
      view: this.state(runId),
    };
  }

  recover(runId: string): StationZeroV3PlayView {
    this.turns.recover(runId);
    this.planning.verifyRun(runId);
    return this.resume(runId);
  }

  preview(runId: string): StationZeroV3PlanPreview | null {
    const planning = this.store.latestPlanning(runId);
    return planning ? this.planning.currentPreview(runId, planning.planningId) : null;
  }

  private requireCurrentPlanning(runId: string) {
    const planning = this.store.latestPlanning(runId);
    if (!planning) throw new TypeError("Station Zero v3 Run has no Planning Head");
    return planning;
  }

  private requireOpenPlanning(runId: string) {
    const planning = this.requireCurrentPlanning(runId);
    if (planning.status !== "open") throw new TypeError("Station Zero v3 Planning is not open");
    return planning;
  }
}

export function stationZeroV3PlanDigestMap(preview: StationZeroV3PlanPreview): Record<string, string> {
  return Object.fromEntries(STATION_ZERO_FACTION_IDS.map((factionId) => [factionId, sha256(preview.factionPlans[factionId])]));
}
