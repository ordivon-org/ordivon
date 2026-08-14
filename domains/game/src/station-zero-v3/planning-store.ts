import { canonicalJson, sha256 } from "../digest.ts";
import { assertStationZeroFactionTurnPlan } from "./contracts.ts";
import { prepareStationZeroV3Commitment } from "./reducer.ts";
import {
  assertStationZeroV3AgentDecision,
  assertStationZeroV3CommanderOrder,
  initialStationZeroV3CommanderOrder,
} from "./agent-planning.ts";
import type { StationZeroFactionId, StationZeroV3WorldState } from "./model.ts";
import { STATION_ZERO_FACTION_IDS } from "./model.ts";
import type { StationZeroV3PlanningHead } from "./p2-model.ts";
import type {
  StationZeroV3OrderHead,
  StationZeroV3OrderRevision,
  StationZeroV3OrderSaveReceipt,
  StationZeroV3PlanPreview,
  StationZeroV3PreviewReceipt,
} from "./p3-model.ts";
import type { StationZeroV3Store } from "./persistence.ts";

export type StationZeroV3PlanningStoreErrorCode =
  | "station_zero_v3_planning_conflict"
  | "station_zero_v3_planning_corrupt";

export class StationZeroV3PlanningStoreError extends Error {
  readonly code: StationZeroV3PlanningStoreErrorCode;

  constructor(code: StationZeroV3PlanningStoreErrorCode, message: string, options?: ErrorOptions) {
    super(message, options);
    this.name = "StationZeroV3PlanningStoreError";
    this.code = code;
  }
}

interface OrderHeadRow {
  run_id: string;
  planning_id: string;
  order_revision: number;
  status: string;
  head_json: string;
  head_digest: string;
}

interface OrderRow {
  run_id: string;
  planning_id: string;
  order_revision: number;
  order_json: string;
  order_digest: string;
  previous_digest: string;
  row_digest: string;
  created_at: string;
}

interface PreviewRow {
  run_id: string;
  planning_id: string;
  preview_id: string;
  order_revision: number;
  order_digest: string;
  preview_json: string;
  preview_digest: string;
  created_at: string;
}

function parseJson<T>(json: string, label: string): T {
  try {
    return JSON.parse(json) as T;
  } catch (error) {
    throw new StationZeroV3PlanningStoreError("station_zero_v3_planning_corrupt", `${label} JSON is invalid`, { cause: error });
  }
}

function orderRowDigest(row: Omit<OrderRow, "row_digest" | "created_at">): string {
  return sha256({
    kind: "ordivon.game.station-zero-v3-order-row",
    runId: row.run_id,
    planningId: row.planning_id,
    orderRevision: Number(row.order_revision),
    orderJson: row.order_json,
    orderDigest: row.order_digest,
    previousDigest: row.previous_digest,
  });
}

function orderHeadDigest(head: StationZeroV3OrderHead): string {
  return sha256(head);
}

function previewContentDigest(preview: StationZeroV3PlanPreview): string {
  const { previewDigest: _previewDigest, ...base } = preview;
  return sha256(base);
}

export class StationZeroV3PlanningStore {
  readonly world: StationZeroV3Store;

  constructor(world: StationZeroV3Store) {
    this.world = world;
    this.createSchema();
  }

  private createSchema(): void {
    this.world.db.exec(`
      CREATE TABLE IF NOT EXISTS station_zero_v3_order_revisions (
        run_id TEXT NOT NULL,
        planning_id TEXT NOT NULL,
        order_revision INTEGER NOT NULL,
        order_json TEXT NOT NULL,
        order_digest TEXT NOT NULL,
        previous_digest TEXT NOT NULL,
        row_digest TEXT NOT NULL,
        created_at TEXT NOT NULL,
        PRIMARY KEY (run_id, planning_id, order_revision),
        UNIQUE (run_id, planning_id, order_digest),
        FOREIGN KEY (run_id, planning_id) REFERENCES station_zero_v3_planning_heads(run_id, planning_id)
      );

      CREATE TABLE IF NOT EXISTS station_zero_v3_order_heads (
        run_id TEXT NOT NULL,
        planning_id TEXT NOT NULL,
        order_revision INTEGER NOT NULL,
        status TEXT NOT NULL,
        head_json TEXT NOT NULL,
        head_digest TEXT NOT NULL,
        PRIMARY KEY (run_id, planning_id),
        FOREIGN KEY (run_id, planning_id) REFERENCES station_zero_v3_planning_heads(run_id, planning_id)
      );

      CREATE TABLE IF NOT EXISTS station_zero_v3_plan_previews (
        run_id TEXT NOT NULL,
        planning_id TEXT NOT NULL,
        preview_id TEXT NOT NULL,
        order_revision INTEGER NOT NULL,
        order_digest TEXT NOT NULL,
        preview_json TEXT NOT NULL,
        preview_digest TEXT NOT NULL,
        created_at TEXT NOT NULL,
        PRIMARY KEY (run_id, planning_id, preview_id),
        UNIQUE (run_id, planning_id, preview_digest),
        FOREIGN KEY (run_id, planning_id) REFERENCES station_zero_v3_planning_heads(run_id, planning_id)
      );
    `);
  }

  private planningSource(planning: StationZeroV3PlanningHead): StationZeroV3WorldState {
    const source = this.world.stateAtRevision(planning.runId, planning.worldRevision);
    if (sha256(source) !== planning.worldDigest) {
      throw new StationZeroV3PlanningStoreError("station_zero_v3_planning_corrupt", `Planning source World differs from history: ${planning.planningId}`);
    }
    const commitment = prepareStationZeroV3Commitment(source);
    if (sha256(commitment) !== planning.commitmentDigest) {
      throw new StationZeroV3PlanningStoreError("station_zero_v3_planning_corrupt", `Planning commitment differs from history: ${planning.planningId}`);
    }
    return source;
  }

  ensureInitialOrder(runId: string, planningId: string): StationZeroV3OrderHead {
    const retained = this.headOrNull(runId, planningId);
    if (retained) return retained;
    const planning = this.world.getPlanning(runId, planningId);
    if (planning.status !== "open") throw new TypeError("Initial Order can be created only for open Planning");
    const state = this.planningSource(planning);
    let previousOrder: StationZeroV3OrderRevision["order"] | null = null;
    const previousTurn = this.world.latestTurnReceipt(runId);
    if (previousTurn && previousTurn.turnSequence === planning.turn - 1) {
      const previousHead = this.headOrNull(runId, previousTurn.planningId);
      if (!previousHead || previousHead.status !== "committed" || !previousHead.committedPreviewId) {
        throw new StationZeroV3PlanningStoreError("station_zero_v3_planning_corrupt", "Previous resolved Turn lacks a committed Commander Order");
      }
      previousOrder = this.currentOrder(runId, previousTurn.planningId).order;
    }
    const order = initialStationZeroV3CommanderOrder(runId, planning, state, previousOrder);
    return this.saveOrder(runId, planningId, order, state).head;
  }

  saveOrder(
    runId: string,
    planningId: string,
    order: StationZeroV3OrderRevision["order"],
    sourceState?: StationZeroV3WorldState,
  ): StationZeroV3OrderSaveReceipt & { head: StationZeroV3OrderHead } {
    const planning = this.world.getPlanning(runId, planningId);
    if (planning.status !== "open") throw new TypeError("Commander Order can be edited only while Planning is open");
    if (Object.keys(planning.submittedPlanDigests).length > 0) {
      throw new StationZeroV3PlanningStoreError("station_zero_v3_planning_conflict", "Commander Order cannot change after a Faction Plan entered the durable commitment path");
    }
    const state = sourceState ?? this.planningSource(planning);
    assertStationZeroV3CommanderOrder(state, planning, order);
    const digest = sha256(order);
    const current = this.headOrNull(runId, planningId);
    if (current && current.orderDigest === digest) {
      return { runId, planningId, orderRevision: current.orderRevision, orderDigest: digest, idempotent: true, head: current };
    }
    if (current?.status === "committed") {
      throw new StationZeroV3PlanningStoreError("station_zero_v3_planning_conflict", "Committed Commander Order is immutable");
    }
    const nextRevision = (current?.orderRevision ?? 0) + 1;
    const createdAt = new Date().toISOString();
    const previousRow = current ? this.orderRow(runId, planningId, current.orderRevision) : null;
    const rowBase: Omit<OrderRow, "row_digest" | "created_at"> = {
      run_id: runId,
      planning_id: planningId,
      order_revision: nextRevision,
      order_json: canonicalJson(order),
      order_digest: digest,
      previous_digest: previousRow?.row_digest ?? "",
    };
    const nextHead: StationZeroV3OrderHead = {
      schemaVersion: 1,
      kind: "ordivon.game.station-zero-v3-order-head",
      runId,
      planningId,
      orderRevision: nextRevision,
      orderDigest: digest,
      status: "draft",
      previewId: null,
      previewDigest: null,
      committedPreviewId: null,
      committedAt: null,
      updatedAt: createdAt,
    };
    this.world.db.exec("BEGIN IMMEDIATE");
    try {
      const freshPlanning = this.world.getPlanning(runId, planningId);
      const freshHead = this.headOrNull(runId, planningId);
      if (freshPlanning.status !== "open" || Object.keys(freshPlanning.submittedPlanDigests).length > 0 ||
          (freshHead ? orderHeadDigest(freshHead) : null) !== (current ? orderHeadDigest(current) : null)) {
        throw new StationZeroV3PlanningStoreError("station_zero_v3_planning_conflict", "Planning or Commander Order changed concurrently");
      }
      this.world.db.prepare(`INSERT INTO station_zero_v3_order_revisions
        (run_id, planning_id, order_revision, order_json, order_digest, previous_digest, row_digest, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)`)
        .run(runId, planningId, nextRevision, rowBase.order_json, digest, rowBase.previous_digest, orderRowDigest(rowBase), createdAt);
      this.world.db.prepare(`INSERT INTO station_zero_v3_order_heads
        (run_id, planning_id, order_revision, status, head_json, head_digest)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(run_id, planning_id) DO UPDATE SET
          order_revision = excluded.order_revision,
          status = excluded.status,
          head_json = excluded.head_json,
          head_digest = excluded.head_digest`)
        .run(runId, planningId, nextRevision, nextHead.status, canonicalJson(nextHead), orderHeadDigest(nextHead));
      this.world.db.exec("COMMIT");
    } catch (error) {
      try { this.world.db.exec("ROLLBACK"); } catch {}
      throw error;
    }
    return { runId, planningId, orderRevision: nextRevision, orderDigest: digest, idempotent: false, head: nextHead };
  }

  currentOrder(runId: string, planningId: string): StationZeroV3OrderRevision {
    const head = this.getHead(runId, planningId);
    const row = this.orderRow(runId, planningId, head.orderRevision);
    if (!row) throw new StationZeroV3PlanningStoreError("station_zero_v3_planning_corrupt", "Commander Order Head has no revision row");
    this.assertOrderRow(row, head);
    return {
      orderRevision: head.orderRevision,
      order: parseJson(row.order_json, "Commander Order"),
      orderDigest: row.order_digest,
      createdAt: row.created_at,
    };
  }

  savePreview(preview: StationZeroV3PlanPreview): StationZeroV3PreviewReceipt {
    const planning = this.world.getPlanning(preview.runId, preview.planningId);
    if (planning.status !== "open") throw new TypeError("Plan Preview can be retained only while Planning is open");
    if (Object.keys(planning.submittedPlanDigests).length > 0) {
      throw new StationZeroV3PlanningStoreError("station_zero_v3_planning_conflict", "Plan Preview cannot change after durable Faction Plan submission");
    }
    const state = this.planningSource(planning);
    const current = this.currentOrder(preview.runId, preview.planningId);
    if (preview.orderRevision !== current.orderRevision || preview.orderDigest !== current.orderDigest) {
      throw new StationZeroV3PlanningStoreError("station_zero_v3_planning_conflict", "Plan Preview was generated from a stale Commander Order");
    }
    this.assertPreview(state, planning, preview);
    const existing = this.previewOrNull(preview.runId, preview.planningId, preview.previewId);
    if (existing) {
      if (existing.previewDigest !== preview.previewDigest || canonicalJson(existing) !== canonicalJson(preview)) {
        throw new StationZeroV3PlanningStoreError("station_zero_v3_planning_conflict", "Plan Preview identity is bound to different content");
      }
      return { preview: existing, idempotent: true };
    }
    const head = this.getHead(preview.runId, preview.planningId);
    if (head.status === "committed") throw new StationZeroV3PlanningStoreError("station_zero_v3_planning_conflict", "Committed Plan Preview is immutable");
    const nextHead: StationZeroV3OrderHead = {
      ...head,
      status: "previewed",
      previewId: preview.previewId,
      previewDigest: preview.previewDigest,
      updatedAt: new Date().toISOString(),
    };
    this.world.db.exec("BEGIN IMMEDIATE");
    try {
      const fresh = this.getHead(preview.runId, preview.planningId);
      if (orderHeadDigest(fresh) !== orderHeadDigest(head)) {
        throw new StationZeroV3PlanningStoreError("station_zero_v3_planning_conflict", "Commander Order Head changed before Preview persistence");
      }
      this.world.db.prepare(`INSERT INTO station_zero_v3_plan_previews
        (run_id, planning_id, preview_id, order_revision, order_digest, preview_json, preview_digest, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)`)
        .run(preview.runId, preview.planningId, preview.previewId, preview.orderRevision, preview.orderDigest,
          canonicalJson(preview), preview.previewDigest, preview.generatedAt);
      this.updateHead(head, nextHead);
      this.world.db.exec("COMMIT");
    } catch (error) {
      try { this.world.db.exec("ROLLBACK"); } catch {}
      throw error;
    }
    return { preview, idempotent: false };
  }

  currentPreview(runId: string, planningId: string): StationZeroV3PlanPreview | null {
    const head = this.headOrNull(runId, planningId);
    if (!head?.previewId) return null;
    const preview = this.previewOrNull(runId, planningId, head.previewId);
    if (!preview || preview.previewDigest !== head.previewDigest) {
      throw new StationZeroV3PlanningStoreError("station_zero_v3_planning_corrupt", "Commander Order Head Preview reference is invalid");
    }
    return preview;
  }

  getPreview(runId: string, planningId: string, previewId: string): StationZeroV3PlanPreview {
    const preview = this.previewOrNull(runId, planningId, previewId);
    if (!preview) throw new Error(`unknown Station Zero v3 Plan Preview: ${previewId}`);
    return preview;
  }

  markCommitted(runId: string, planningId: string, previewId: string): StationZeroV3OrderHead {
    const preview = this.getPreview(runId, planningId, previewId);
    const head = this.getHead(runId, planningId);
    if (head.status === "committed") {
      if (head.committedPreviewId !== previewId) {
        throw new StationZeroV3PlanningStoreError("station_zero_v3_planning_conflict", "Planning is already committed to another Preview");
      }
      return head;
    }
    if (head.previewId !== previewId || head.previewDigest !== preview.previewDigest) {
      throw new StationZeroV3PlanningStoreError("station_zero_v3_planning_conflict", "Only the active Plan Preview may be committed");
    }
    const planning = this.world.getPlanning(runId, planningId);
    const expectedDigests = Object.fromEntries(STATION_ZERO_FACTION_IDS.map((factionId) => [factionId, sha256(preview.factionPlans[factionId])])) as Record<StationZeroFactionId, string>;
    if (STATION_ZERO_FACTION_IDS.some((factionId) => planning.submittedPlanDigests[factionId] !== expectedDigests[factionId])) {
      throw new StationZeroV3PlanningStoreError("station_zero_v3_planning_conflict", "Durable Faction Plans do not match the selected Preview");
    }
    const now = new Date().toISOString();
    const next: StationZeroV3OrderHead = {
      ...head,
      status: "committed",
      committedPreviewId: previewId,
      committedAt: now,
      updatedAt: now,
    };
    this.updateHead(head, next);
    return next;
  }

  getHead(runId: string, planningId: string): StationZeroV3OrderHead {
    const head = this.headOrNull(runId, planningId);
    if (!head) throw new Error(`unknown Station Zero v3 Commander Order Head: ${planningId}`);
    return head;
  }

  headOrNull(runId: string, planningId: string): StationZeroV3OrderHead | null {
    const row = this.world.db.prepare(`SELECT * FROM station_zero_v3_order_heads WHERE run_id = ? AND planning_id = ?`)
      .get(runId, planningId) as OrderHeadRow | undefined;
    if (!row) return null;
    const head = parseJson<StationZeroV3OrderHead>(row.head_json, "Commander Order Head");
    if (
      head.schemaVersion !== 1 || head.kind !== "ordivon.game.station-zero-v3-order-head" ||
      head.runId !== row.run_id || head.planningId !== row.planning_id || head.orderRevision !== Number(row.order_revision) ||
      head.status !== row.status || orderHeadDigest(head) !== row.head_digest
    ) throw new StationZeroV3PlanningStoreError("station_zero_v3_planning_corrupt", `Commander Order Head is inconsistent: ${planningId}`);
    return head;
  }

  private orderRow(runId: string, planningId: string, revision: number): OrderRow | null {
    return (this.world.db.prepare(`SELECT * FROM station_zero_v3_order_revisions
      WHERE run_id = ? AND planning_id = ? AND order_revision = ?`).get(runId, planningId, revision) as OrderRow | undefined) ?? null;
  }

  private previewOrNull(runId: string, planningId: string, previewId: string): StationZeroV3PlanPreview | null {
    const row = this.world.db.prepare(`SELECT * FROM station_zero_v3_plan_previews
      WHERE run_id = ? AND planning_id = ? AND preview_id = ?`).get(runId, planningId, previewId) as PreviewRow | undefined;
    if (!row) return null;
    const preview = parseJson<StationZeroV3PlanPreview>(row.preview_json, "Plan Preview");
    if (
      preview.previewId !== row.preview_id || preview.runId !== row.run_id || preview.planningId !== row.planning_id ||
      preview.orderRevision !== Number(row.order_revision) || preview.orderDigest !== row.order_digest ||
      preview.previewDigest !== row.preview_digest || preview.generatedAt !== row.created_at ||
      previewContentDigest(preview) !== preview.previewDigest
    ) throw new StationZeroV3PlanningStoreError("station_zero_v3_planning_corrupt", `Plan Preview is inconsistent: ${previewId}`);
    return preview;
  }

  private updateHead(previous: StationZeroV3OrderHead, next: StationZeroV3OrderHead): void {
    const result = this.world.db.prepare(`UPDATE station_zero_v3_order_heads
      SET order_revision = ?, status = ?, head_json = ?, head_digest = ?
      WHERE run_id = ? AND planning_id = ? AND head_digest = ?`)
      .run(next.orderRevision, next.status, canonicalJson(next), orderHeadDigest(next),
        previous.runId, previous.planningId, orderHeadDigest(previous));
    if (Number(result.changes) !== 1) throw new StationZeroV3PlanningStoreError("station_zero_v3_planning_conflict", "Commander Order Head changed concurrently");
  }

  private assertOrderRow(row: OrderRow, head?: StationZeroV3OrderHead): void {
    if (!Number.isSafeInteger(Number(row.order_revision)) || Number(row.order_revision) < 1 || orderRowDigest({
      run_id: row.run_id,
      planning_id: row.planning_id,
      order_revision: Number(row.order_revision),
      order_json: row.order_json,
      order_digest: row.order_digest,
      previous_digest: row.previous_digest,
    }) !== row.row_digest) throw new StationZeroV3PlanningStoreError("station_zero_v3_planning_corrupt", "Commander Order row digest mismatch");
    const order = parseJson<StationZeroV3OrderRevision["order"]>(row.order_json, "Commander Order");
    if (sha256(order) !== row.order_digest || (head && head.orderRevision === Number(row.order_revision) && head.orderDigest !== row.order_digest)) {
      throw new StationZeroV3PlanningStoreError("station_zero_v3_planning_corrupt", "Commander Order digest differs from content or Head");
    }
  }

  private assertPreview(
    state: StationZeroV3WorldState,
    planning: StationZeroV3PlanningHead,
    preview: StationZeroV3PlanPreview,
  ): void {
    if (
      preview.schemaVersion !== 1 || preview.kind !== "ordivon.game.station-zero-v3-plan-preview" ||
      preview.runId !== planning.runId || preview.planningId !== planning.planningId ||
      preview.worldRevision !== planning.worldRevision || preview.worldDigest !== planning.worldDigest ||
      previewContentDigest(preview) !== preview.previewDigest
    ) throw new StationZeroV3PlanningStoreError("station_zero_v3_planning_corrupt", "Plan Preview identity or digest is invalid");
    assertStationZeroV3CommanderOrder(state, planning, preview.playerOrder);
    for (const context of preview.contexts) {
      if (context.planningId !== planning.planningId || context.worldDigest !== planning.worldDigest) {
        throw new StationZeroV3PlanningStoreError("station_zero_v3_planning_corrupt", "Plan Preview contains a Context from another World");
      }
      const { contextDigest: _contextDigest, ...contextBase } = context;
      if (sha256(contextBase) !== context.contextDigest) throw new StationZeroV3PlanningStoreError("station_zero_v3_planning_corrupt", "Agent Context digest differs from content");
      const decision = preview.agentDecisions.find((entry) => entry.contextId === context.contextId);
      if (decision) assertStationZeroV3AgentDecision(context, decision);
    }
    for (const factionId of STATION_ZERO_FACTION_IDS) {
      const plan = preview.factionPlans[factionId];
      if (!plan || plan.factionId !== factionId) throw new StationZeroV3PlanningStoreError("station_zero_v3_planning_corrupt", `Plan Preview lacks ${factionId} Plan`);
      assertStationZeroFactionTurnPlan(state, plan);
    }
    const plannedActorIds = new Set(STATION_ZERO_FACTION_IDS.flatMap((factionId) => preview.factionPlans[factionId].actorIntents.map((intent) => intent.actorId)));
    const activeFactionActorIds = Object.values(state.actors).filter((actor) => actor.factionId !== null && actor.lifeState === "active").map((actor) => actor.actorId);
    if (activeFactionActorIds.some((actorId) => !plannedActorIds.has(actorId))) {
      throw new StationZeroV3PlanningStoreError("station_zero_v3_planning_corrupt", "Plan Preview omits an active faction Actor");
    }
  }

  verifyRun(runId: string): void {
    this.world.recover(runId);
    for (const planning of this.world.listPlanning(runId)) {
      const head = this.headOrNull(runId, planning.planningId);
      if (!head) continue;
      const state = this.planningSource(planning);
      const rows = this.world.db.prepare(`SELECT * FROM station_zero_v3_order_revisions
        WHERE run_id = ? AND planning_id = ? ORDER BY order_revision`).all(runId, planning.planningId) as unknown as OrderRow[];
      let previousDigest = "";
      for (const [index, row] of rows.entries()) {
        if (Number(row.order_revision) !== index + 1 || row.previous_digest !== previousDigest) {
          throw new StationZeroV3PlanningStoreError("station_zero_v3_planning_corrupt", "Commander Order revision chain is discontinuous");
        }
        this.assertOrderRow(row, head);
        const order = parseJson<StationZeroV3OrderRevision["order"]>(row.order_json, "Commander Order");
        assertStationZeroV3CommanderOrder(state, planning, order);
        previousDigest = row.row_digest;
      }
      if (rows.length !== head.orderRevision) throw new StationZeroV3PlanningStoreError("station_zero_v3_planning_corrupt", "Commander Order Head revision differs from retained history");
      const previews = this.world.db.prepare(`SELECT * FROM station_zero_v3_plan_previews
        WHERE run_id = ? AND planning_id = ? ORDER BY created_at, preview_id`).all(runId, planning.planningId) as unknown as PreviewRow[];
      for (const row of previews) {
        const preview = this.previewOrNull(runId, planning.planningId, row.preview_id)!;
        this.assertPreview(state, planning, preview);
      }
      if (head.previewId) this.currentPreview(runId, planning.planningId);
      if (head.status === "committed") {
        if (!head.committedPreviewId || head.previewId !== head.committedPreviewId) {
          throw new StationZeroV3PlanningStoreError("station_zero_v3_planning_corrupt", "Committed Commander Order Head lacks its selected Preview");
        }
        const preview = this.getPreview(runId, planning.planningId, head.committedPreviewId);
        if (STATION_ZERO_FACTION_IDS.some((factionId) => planning.submittedPlanDigests[factionId] !== sha256(preview.factionPlans[factionId]))) {
          throw new StationZeroV3PlanningStoreError("station_zero_v3_planning_corrupt", "Committed Preview differs from durable Faction Plans");
        }
      }
    }
  }
}
