import { mkdirSync } from "node:fs";
import { dirname } from "node:path";
import { DatabaseSync } from "node:sqlite";

import { CURRENT_BUILD } from "../build.ts";
import { canonicalJson, sha256 } from "../digest.ts";
import { HostStore } from "../host-contract/journal.ts";
import { assertStationZeroTurnBatch, assertStationZeroFactionTurnPlan } from "./contracts.ts";
import { createStationZeroV3Genesis, assertStationZeroV3World } from "./genesis.ts";
import type {
  StationZeroFactionId,
  StationZeroFactionTurnPlan,
  StationZeroIntentResolutionStatus,
  StationZeroTurnBatch,
  StationZeroTurnRecord,
  StationZeroV3WorldState,
} from "./model.ts";
import { STATION_ZERO_FACTION_IDS } from "./model.ts";
import type {
  StationZeroV3PlanReceipt,
  StationZeroV3PlanningHead,
  StationZeroV3PreparedTurn,
  StationZeroV3RecoveryResult,
  StationZeroV3RunMetadata,
  StationZeroV3SubmittedPlanRecord,
  StationZeroV3TurnReceipt,
  StationZeroV3WorldEvent,
  StationZeroV3WorldHead,
} from "./p2-model.ts";
import {
  applyStationZeroV3Turn,
  canonicalizeStationZeroV3TurnBatch,
  prepareStationZeroV3Commitment,
  replayStationZeroV3Turn,
} from "./reducer.ts";

export type StationZeroV3StorageErrorCode =
  | "station_zero_v3_busy"
  | "station_zero_v3_corrupt"
  | "station_zero_v3_constraint";

export class StationZeroV3StorageError extends Error {
  readonly code: StationZeroV3StorageErrorCode;

  constructor(code: StationZeroV3StorageErrorCode, message: string, options?: ErrorOptions) {
    super(message, options);
    this.name = "StationZeroV3StorageError";
    this.code = code;
  }
}

export type StationZeroV3StorageFaultPoint =
  | "before_begin"
  | "after_begin"
  | "after_event_insert"
  | "after_record_insert"
  | "before_head_update"
  | "after_head_update"
  | "before_commit"
  | "after_commit";

export interface StationZeroV3StoreOptions {
  busyTimeoutMs?: number;
  createdWithBuild?: string;
  faultInjector?: (point: StationZeroV3StorageFaultPoint) => void;
}

interface RunRow {
  run_id: string;
  scenario_id: string;
  scenario_version: number;
  ruleset_id: string;
  ruleset_version: number;
  state_schema_version: number;
  seed: string;
  genesis_digest: string;
  status: string;
  created_at: string;
  created_with_build: string;
}

interface WorldHeadRow {
  run_id: string;
  revision: number;
  turn: number;
  phase: string;
  status: string;
  state_json: string;
  state_digest: string;
  last_turn_sequence: number;
  updated_at: string;
}

interface PlanningRow {
  run_id: string;
  planning_id: string;
  world_revision: number;
  planning_revision: number;
  status: string;
  head_json: string;
  head_digest: string;
}

interface PlanRow {
  faction_id: string;
  plan_json: string;
  plan_digest: string;
  submitted_at: string;
}

interface BatchRow {
  run_id: string;
  planning_id: string;
  turn_batch_id: string;
  batch_json: string;
  batch_digest: string;
  task_id: string;
  goal_id: string;
  effect_id: string;
  dispatch_id: string;
  created_at: string;
}

interface EventRow {
  run_id: string;
  turn_sequence: number;
  planning_id: string;
  turn_batch_id: string;
  event_id: string;
  event_json: string;
  event_digest: string;
  previous_digest: string;
  row_digest: string;
  created_at: string;
}

interface RecordRow {
  run_id: string;
  turn_sequence: number;
  planning_id: string;
  turn_batch_id: string;
  record_json: string;
  record_digest: string;
  event_digest: string;
  before_digest: string;
  after_digest: string;
  previous_digest: string;
  row_digest: string;
  created_at: string;
}

function sqliteCode(error: unknown): string {
  return error && typeof error === "object" && "code" in error ? String(error.code) : "";
}

function mapStorageError(error: unknown): never {
  if (error instanceof StationZeroV3StorageError) throw error;
  const code = sqliteCode(error);
  const message = error instanceof Error ? error.message.toLowerCase() : String(error).toLowerCase();
  if (code.includes("BUSY") || code.includes("LOCKED") || message.includes("database is locked") || message.includes("database is busy")) {
    throw new StationZeroV3StorageError("station_zero_v3_busy", "Station Zero v3 storage is temporarily busy", { cause: error });
  }
  if (code.includes("CONSTRAINT") || message.includes("constraint failed")) {
    throw new StationZeroV3StorageError("station_zero_v3_constraint", "Station Zero v3 storage constraint rejected the write", { cause: error });
  }
  if (
    code.includes("CORRUPT") ||
    code.includes("NOTADB") ||
    message.includes("file is not a database") ||
    message.includes("database disk image is malformed")
  ) {
    throw new StationZeroV3StorageError("station_zero_v3_corrupt", "Station Zero v3 storage is corrupt", { cause: error });
  }
  throw error;
}

function parseJson<T>(json: string, label: string): T {
  try {
    return JSON.parse(json) as T;
  } catch (error) {
    throw new StationZeroV3StorageError("station_zero_v3_corrupt", `${label} JSON is invalid`, { cause: error });
  }
}

function requireSafeInteger(value: number, label: string, minimum = 0): number {
  if (!Number.isSafeInteger(value) || value < minimum) {
    throw new StationZeroV3StorageError("station_zero_v3_corrupt", `${label} is invalid`);
  }
  return value;
}

function eventRowDigest(runId: string, row: Omit<EventRow, "row_digest" | "created_at">): string {
  return sha256({
    kind: "ordivon.game.station-zero-v3-world-event-row",
    runId,
    turnSequence: Number(row.turn_sequence),
    planningId: row.planning_id,
    turnBatchId: row.turn_batch_id,
    eventId: row.event_id,
    eventJson: row.event_json,
    eventDigest: row.event_digest,
    previousDigest: row.previous_digest,
  });
}

function recordRowDigest(runId: string, row: Omit<RecordRow, "row_digest" | "created_at">): string {
  return sha256({
    kind: "ordivon.game.station-zero-v3-turn-record-row",
    runId,
    turnSequence: Number(row.turn_sequence),
    planningId: row.planning_id,
    turnBatchId: row.turn_batch_id,
    recordJson: row.record_json,
    recordDigest: row.record_digest,
    eventDigest: row.event_digest,
    beforeDigest: row.before_digest,
    afterDigest: row.after_digest,
    previousDigest: row.previous_digest,
  });
}

function planningDigest(head: StationZeroV3PlanningHead): string {
  return sha256(head);
}

function planDigest(plan: StationZeroFactionTurnPlan): string {
  return sha256(plan);
}

function metadataFromRow(row: RunRow): StationZeroV3RunMetadata {
  if (
    row.scenario_id !== "station-zero" || Number(row.scenario_version) !== 3 ||
    row.ruleset_id !== "station-zero-core" || Number(row.ruleset_version) !== 4 ||
    Number(row.state_schema_version) !== 3
  ) {
    throw new StationZeroV3StorageError("station_zero_v3_corrupt", `Run is not a Station Zero v3 Run: ${row.run_id}`);
  }
  if (row.status !== "running" && row.status !== "terminal") {
    throw new StationZeroV3StorageError("station_zero_v3_corrupt", `Station Zero v3 Run status is invalid: ${row.run_id}`);
  }
  return {
    runId: row.run_id,
    scenarioId: "station-zero",
    scenarioVersion: 3,
    rulesetId: "station-zero-core",
    rulesetVersion: 4,
    stateSchemaVersion: 3,
    seed: row.seed,
    genesisDigest: row.genesis_digest,
    status: row.status,
    createdAt: row.created_at,
    createdWithBuild: row.created_with_build,
  };
}

function identityFor(runId: string, revision: number) {
  const suffix = `${runId}:r${revision}`;
  return {
    planningId: `planning:station-zero-v3:${suffix}`,
    turnBatchId: `turn-batch:station-zero-v3:${suffix}`,
    taskId: `task:station-zero-v3:${suffix}`,
    goalId: `goal:station-zero-v3:${runId}`,
    effectId: `effect:station-zero-v3:${suffix}`,
    dispatchId: `dispatch:station-zero-v3:${suffix}`,
  };
}

function resolutionCounts(record: StationZeroTurnRecord): Record<StationZeroIntentResolutionStatus, number> {
  const counts: Record<StationZeroIntentResolutionStatus, number> = {
    executed: 0,
    interrupted: 0,
    invalidated: 0,
    contested: 0,
    no_effect: 0,
  };
  for (const resolution of record.resolution.intentResolutions) counts[resolution.status] += 1;
  return counts;
}

export class StationZeroV3Store {
  readonly db: DatabaseSync;
  readonly dbPath: string;
  readonly host: HostStore;
  readonly createdWithBuild: string;
  readonly faultInjector: ((point: StationZeroV3StorageFaultPoint) => void) | undefined;

  constructor(dbPath: string, options: StationZeroV3StoreOptions = {}) {
    this.dbPath = dbPath;
    this.createdWithBuild = options.createdWithBuild ?? CURRENT_BUILD;
    this.faultInjector = options.faultInjector;
    if (dbPath !== ":memory:") mkdirSync(dirname(dbPath), { recursive: true });
    this.db = new DatabaseSync(dbPath);
    try {
      this.db.exec(`PRAGMA busy_timeout = ${options.busyTimeoutMs ?? 5000};`);
      this.db.exec(`
        PRAGMA foreign_keys = ON;
        PRAGMA journal_mode = WAL;
        PRAGMA synchronous = FULL;
      `);
      this.createSchema();
      this.host = new HostStore(this.db);
    } catch (error) {
      try { this.db.close(); } catch {}
      mapStorageError(error);
    }
  }

  private createSchema(): void {
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS runs (
        run_id TEXT PRIMARY KEY,
        scenario_id TEXT NOT NULL,
        scenario_version INTEGER NOT NULL,
        scenario_case_id TEXT NOT NULL,
        ruleset_id TEXT NOT NULL,
        ruleset_version INTEGER NOT NULL,
        state_schema_version INTEGER NOT NULL,
        seed TEXT NOT NULL,
        genesis_digest TEXT NOT NULL,
        evaluated_inputs_digest TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL,
        created_with_build TEXT NOT NULL
      );

      CREATE TABLE IF NOT EXISTS station_zero_v3_genesis (
        run_id TEXT PRIMARY KEY,
        state_json TEXT NOT NULL,
        state_digest TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (run_id) REFERENCES runs(run_id)
      );

      CREATE TABLE IF NOT EXISTS station_zero_v3_world_heads (
        run_id TEXT PRIMARY KEY,
        revision INTEGER NOT NULL,
        turn INTEGER NOT NULL,
        phase TEXT NOT NULL,
        status TEXT NOT NULL,
        state_json TEXT NOT NULL,
        state_digest TEXT NOT NULL,
        last_turn_sequence INTEGER NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (run_id) REFERENCES runs(run_id)
      );

      CREATE TABLE IF NOT EXISTS station_zero_v3_planning_heads (
        run_id TEXT NOT NULL,
        planning_id TEXT NOT NULL,
        world_revision INTEGER NOT NULL,
        planning_revision INTEGER NOT NULL,
        status TEXT NOT NULL,
        head_json TEXT NOT NULL,
        head_digest TEXT NOT NULL,
        PRIMARY KEY (run_id, planning_id),
        UNIQUE (run_id, world_revision),
        FOREIGN KEY (run_id) REFERENCES runs(run_id)
      );
      CREATE INDEX IF NOT EXISTS station_zero_v3_planning_latest_idx
        ON station_zero_v3_planning_heads(run_id, world_revision DESC);

      CREATE TABLE IF NOT EXISTS station_zero_v3_faction_plans (
        run_id TEXT NOT NULL,
        planning_id TEXT NOT NULL,
        faction_id TEXT NOT NULL,
        plan_json TEXT NOT NULL,
        plan_digest TEXT NOT NULL,
        submitted_at TEXT NOT NULL,
        PRIMARY KEY (run_id, planning_id, faction_id),
        FOREIGN KEY (run_id, planning_id) REFERENCES station_zero_v3_planning_heads(run_id, planning_id)
      );

      CREATE TABLE IF NOT EXISTS station_zero_v3_turn_batches (
        run_id TEXT NOT NULL,
        planning_id TEXT NOT NULL,
        turn_batch_id TEXT NOT NULL,
        batch_json TEXT NOT NULL,
        batch_digest TEXT NOT NULL,
        task_id TEXT NOT NULL,
        goal_id TEXT NOT NULL,
        effect_id TEXT NOT NULL,
        dispatch_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        PRIMARY KEY (run_id, planning_id),
        UNIQUE (run_id, turn_batch_id),
        UNIQUE (run_id, task_id),
        UNIQUE (run_id, dispatch_id),
        FOREIGN KEY (run_id, planning_id) REFERENCES station_zero_v3_planning_heads(run_id, planning_id)
      );

      CREATE TABLE IF NOT EXISTS station_zero_v3_world_events (
        run_id TEXT NOT NULL,
        turn_sequence INTEGER NOT NULL,
        planning_id TEXT NOT NULL,
        turn_batch_id TEXT NOT NULL,
        event_id TEXT NOT NULL,
        event_json TEXT NOT NULL,
        event_digest TEXT NOT NULL,
        previous_digest TEXT NOT NULL,
        row_digest TEXT NOT NULL,
        created_at TEXT NOT NULL,
        PRIMARY KEY (run_id, turn_sequence),
        UNIQUE (run_id, turn_batch_id),
        UNIQUE (run_id, event_id),
        FOREIGN KEY (run_id, planning_id) REFERENCES station_zero_v3_planning_heads(run_id, planning_id)
      );

      CREATE TABLE IF NOT EXISTS station_zero_v3_turn_records (
        run_id TEXT NOT NULL,
        turn_sequence INTEGER NOT NULL,
        planning_id TEXT NOT NULL,
        turn_batch_id TEXT NOT NULL,
        record_json TEXT NOT NULL,
        record_digest TEXT NOT NULL,
        event_digest TEXT NOT NULL,
        before_digest TEXT NOT NULL,
        after_digest TEXT NOT NULL,
        previous_digest TEXT NOT NULL,
        row_digest TEXT NOT NULL,
        created_at TEXT NOT NULL,
        PRIMARY KEY (run_id, turn_sequence),
        UNIQUE (run_id, turn_batch_id),
        FOREIGN KEY (run_id, planning_id) REFERENCES station_zero_v3_planning_heads(run_id, planning_id)
      );
    `);
  }

  private inject(point: StationZeroV3StorageFaultPoint): void {
    this.faultInjector?.(point);
  }

  private transaction<T>(operation: () => T): T {
    this.db.exec("BEGIN IMMEDIATE");
    try {
      const result = operation();
      this.db.exec("COMMIT");
      return result;
    } catch (error) {
      try { this.db.exec("ROLLBACK"); } catch {}
      throw error;
    }
  }

  createRun(input: { runId: string; seed?: string; createdWithBuild?: string }): StationZeroV3RunMetadata {
    if (!input.runId || input.runId !== input.runId.trim()) throw new TypeError("Station Zero v3 runId is required and must be trimmed");
    try {
      const existing = this.db.prepare("SELECT * FROM runs WHERE run_id = ?").get(input.runId) as RunRow | undefined;
      if (existing) {
        const metadata = metadataFromRow(existing);
        const expectedGenesis = createStationZeroV3Genesis(input.seed ?? metadata.seed);
        if (metadata.genesisDigest !== sha256(expectedGenesis)) {
          throw new StationZeroV3StorageError("station_zero_v3_constraint", "Station Zero v3 Run identity is bound to another Genesis");
        }
        this.recover(input.runId);
        return metadata;
      }

      const genesis = createStationZeroV3Genesis(input.seed);
      assertStationZeroV3World(genesis);
      const genesisDigest = sha256(genesis);
      const createdAt = new Date().toISOString();
      const createdWithBuild = input.createdWithBuild ?? this.createdWithBuild;
      const evaluatedInputsDigest = sha256({
        kind: "ordivon.game.station-zero-v3-evaluated-inputs",
        scenarioVersion: 3,
        rulesetVersion: 4,
        worldSchemaVersion: 3,
      });
      this.transaction(() => {
        this.db.prepare(`INSERT INTO runs
          (run_id, scenario_id, scenario_version, scenario_case_id, ruleset_id, ruleset_version,
           state_schema_version, seed, genesis_digest, evaluated_inputs_digest, status, created_at, created_with_build)
          VALUES (?, 'station-zero', 3, 'fixed-genesis', 'station-zero-core', 4, 3, ?, ?, ?, 'running', ?, ?)`)
          .run(input.runId, genesis.seed, genesisDigest, evaluatedInputsDigest, createdAt, createdWithBuild);
        this.db.prepare(`INSERT INTO station_zero_v3_genesis
          (run_id, state_json, state_digest, created_at) VALUES (?, ?, ?, ?)`)
          .run(input.runId, canonicalJson(genesis), genesisDigest, createdAt);
        this.writeWorldHead(input.runId, genesis, -1, createdAt, true);
      });
      return this.getRun(input.runId);
    } catch (error) {
      mapStorageError(error);
    }
  }

  getRun(runId: string): StationZeroV3RunMetadata {
    try {
      const row = this.db.prepare("SELECT * FROM runs WHERE run_id = ?").get(runId) as RunRow | undefined;
      if (!row) throw new Error(`unknown Station Zero v3 Run: ${runId}`);
      return metadataFromRow(row);
    } catch (error) {
      mapStorageError(error);
    }
  }

  listRuns(): StationZeroV3RunMetadata[] {
    try {
      const rows = this.db.prepare(`SELECT * FROM runs
        WHERE scenario_id = 'station-zero' AND scenario_version = 3
          AND ruleset_id = 'station-zero-core' AND ruleset_version = 4
        ORDER BY created_at, run_id`).all() as unknown as RunRow[];
      return rows.map(metadataFromRow);
    } catch (error) {
      mapStorageError(error);
    }
  }

  private genesis(runId: string): StationZeroV3WorldState {
    const metadata = this.getRun(runId);
    const row = this.db.prepare("SELECT state_json, state_digest FROM station_zero_v3_genesis WHERE run_id = ?")
      .get(runId) as { state_json: string; state_digest: string } | undefined;
    if (!row) throw new StationZeroV3StorageError("station_zero_v3_corrupt", `Station Zero v3 Genesis is missing: ${runId}`);
    const state = parseJson<StationZeroV3WorldState>(row.state_json, "Station Zero v3 Genesis");
    try { assertStationZeroV3World(state); }
    catch (error) { throw new StationZeroV3StorageError("station_zero_v3_corrupt", "Station Zero v3 Genesis is invalid", { cause: error }); }
    const digest = sha256(state);
    if (digest !== row.state_digest || digest !== metadata.genesisDigest || state.revision !== 0 || state.encounter.turn !== 0) {
      throw new StationZeroV3StorageError("station_zero_v3_corrupt", "Station Zero v3 Genesis digest or head is inconsistent");
    }
    return state;
  }

  private worldHeadFromRow(row: WorldHeadRow): StationZeroV3WorldHead {
    const state = parseJson<StationZeroV3WorldState>(row.state_json, "Station Zero v3 World Head");
    try { assertStationZeroV3World(state); }
    catch (error) { throw new StationZeroV3StorageError("station_zero_v3_corrupt", "Station Zero v3 World Head is invalid", { cause: error }); }
    const digest = sha256(state);
    if (
      digest !== row.state_digest || state.revision !== Number(row.revision) || state.encounter.turn !== Number(row.turn) ||
      state.encounter.phase !== row.phase || state.encounter.status !== row.status
    ) {
      throw new StationZeroV3StorageError("station_zero_v3_corrupt", "Station Zero v3 World Head metadata or digest differs from state");
    }
    return {
      runId: row.run_id,
      revision: Number(row.revision),
      turn: Number(row.turn),
      phase: state.encounter.phase,
      status: state.encounter.status,
      state,
      stateDigest: digest,
      lastTurnSequence: Number(row.last_turn_sequence),
      updatedAt: row.updated_at,
    };
  }

  loadWorldHead(runId: string): StationZeroV3WorldHead {
    try {
      this.getRun(runId);
      const row = this.db.prepare("SELECT * FROM station_zero_v3_world_heads WHERE run_id = ?")
        .get(runId) as WorldHeadRow | undefined;
      if (!row) {
        this.recover(runId);
        const rebuilt = this.db.prepare("SELECT * FROM station_zero_v3_world_heads WHERE run_id = ?")
          .get(runId) as WorldHeadRow | undefined;
        if (!rebuilt) throw new StationZeroV3StorageError("station_zero_v3_corrupt", "Station Zero v3 World Head could not be rebuilt");
        return this.worldHeadFromRow(rebuilt);
      }
      return this.worldHeadFromRow(row);
    } catch (error) {
      mapStorageError(error);
    }
  }

  loadState(runId: string): StationZeroV3WorldState {
    return structuredClone(this.loadWorldHead(runId).state);
  }

  stateAtRevision(runId: string, revision: number): StationZeroV3WorldState {
    this.getRun(runId);
    requireSafeInteger(revision, "Station Zero v3 World revision");
    const head = this.loadWorldHead(runId);
    if (revision > head.revision) throw new RangeError(`Station Zero v3 revision ${revision} is beyond World Head ${head.revision}`);
    return structuredClone(revision === 0 ? this.genesis(runId) : this.replayToSequence(runId, revision - 1));
  }

  private writeWorldHead(
    runId: string,
    state: StationZeroV3WorldState,
    lastTurnSequence: number,
    updatedAt: string,
    insertOnly = false,
  ): void {
    assertStationZeroV3World(state);
    const values = [
      runId,
      state.revision,
      state.encounter.turn,
      state.encounter.phase,
      state.encounter.status,
      canonicalJson(state),
      sha256(state),
      lastTurnSequence,
      updatedAt,
    ] as const;
    if (insertOnly) {
      this.db.prepare(`INSERT INTO station_zero_v3_world_heads
        (run_id, revision, turn, phase, status, state_json, state_digest, last_turn_sequence, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`).run(...values);
      return;
    }
    this.db.prepare(`INSERT INTO station_zero_v3_world_heads
      (run_id, revision, turn, phase, status, state_json, state_digest, last_turn_sequence, updated_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
      ON CONFLICT(run_id) DO UPDATE SET
        revision = excluded.revision,
        turn = excluded.turn,
        phase = excluded.phase,
        status = excluded.status,
        state_json = excluded.state_json,
        state_digest = excluded.state_digest,
        last_turn_sequence = excluded.last_turn_sequence,
        updated_at = excluded.updated_at`).run(...values);
  }

  private planningFromRow(row: PlanningRow): StationZeroV3PlanningHead {
    const head = parseJson<StationZeroV3PlanningHead>(row.head_json, "Station Zero v3 Planning Head");
    if (
      head.schemaVersion !== 1 || head.kind !== "ordivon.game.station-zero-v3-planning-head" ||
      head.runId !== row.run_id || head.planningId !== row.planning_id ||
      head.worldRevision !== Number(row.world_revision) || head.planningRevision !== Number(row.planning_revision) ||
      head.status !== row.status || planningDigest(head) !== row.head_digest
    ) {
      throw new StationZeroV3StorageError("station_zero_v3_corrupt", `Station Zero v3 Planning Head is inconsistent: ${row.planning_id}`);
    }
    if (!Number.isSafeInteger(head.planningRevision) || head.planningRevision < 1) {
      throw new StationZeroV3StorageError("station_zero_v3_corrupt", `Station Zero v3 Planning revision is invalid: ${row.planning_id}`);
    }
    return head;
  }

  getPlanning(runId: string, planningId: string): StationZeroV3PlanningHead {
    try {
      this.getRun(runId);
      const row = this.db.prepare("SELECT * FROM station_zero_v3_planning_heads WHERE run_id = ? AND planning_id = ?")
        .get(runId, planningId) as PlanningRow | undefined;
      if (!row) throw new Error(`unknown Station Zero v3 Planning Head: ${planningId}`);
      return this.planningFromRow(row);
    } catch (error) {
      mapStorageError(error);
    }
  }

  latestPlanning(runId: string): StationZeroV3PlanningHead | null {
    try {
      this.getRun(runId);
      const row = this.db.prepare(`SELECT * FROM station_zero_v3_planning_heads
        WHERE run_id = ? ORDER BY world_revision DESC LIMIT 1`).get(runId) as PlanningRow | undefined;
      return row ? this.planningFromRow(row) : null;
    } catch (error) {
      mapStorageError(error);
    }
  }

  listPlanning(runId: string): StationZeroV3PlanningHead[] {
    try {
      this.getRun(runId);
      const rows = this.db.prepare(`SELECT * FROM station_zero_v3_planning_heads
        WHERE run_id = ? ORDER BY world_revision`).all(runId) as unknown as PlanningRow[];
      return rows.map((row) => this.planningFromRow(row));
    } catch (error) {
      mapStorageError(error);
    }
  }

  openPlanning(runId: string): StationZeroV3PlanningHead {
    try {
      const world = this.loadWorldHead(runId);
      if (world.status !== "running") throw new TypeError("Cannot open Planning for a terminal Station Zero v3 Encounter");
      const identity = identityFor(runId, world.revision);
      const retained = this.db.prepare("SELECT * FROM station_zero_v3_planning_heads WHERE run_id = ? AND world_revision = ?")
        .get(runId, world.revision) as PlanningRow | undefined;
      if (retained) return this.planningFromRow(retained);

      const commitment = prepareStationZeroV3Commitment(world.state);
      const now = new Date().toISOString();
      const head: StationZeroV3PlanningHead = {
        schemaVersion: 1,
        kind: "ordivon.game.station-zero-v3-planning-head",
        planningId: identity.planningId,
        runId,
        worldRevision: world.revision,
        turn: world.turn,
        worldDigest: world.stateDigest,
        commitmentDigest: sha256(commitment),
        standingOrderRevision: world.state.encounter.activePlanRevision,
        planningRevision: 1,
        status: "open",
        submittedPlanDigests: {},
        turnBatchId: null,
        batchDigest: null,
        taskId: null,
        goalId: null,
        effectId: null,
        dispatchId: null,
        createdAt: now,
        updatedAt: now,
      };
      this.transaction(() => {
        const current = this.loadWorldHead(runId);
        if (current.stateDigest !== world.stateDigest) throw new StationZeroV3StorageError("station_zero_v3_constraint", "World Head changed while opening Planning");
        this.insertPlanning(head);
      });
      return this.getPlanning(runId, identity.planningId);
    } catch (error) {
      if (sqliteCode(error).includes("CONSTRAINT")) {
        const world = this.loadWorldHead(runId);
        const retained = this.db.prepare("SELECT * FROM station_zero_v3_planning_heads WHERE run_id = ? AND world_revision = ?")
          .get(runId, world.revision) as PlanningRow | undefined;
        if (retained) return this.planningFromRow(retained);
      }
      mapStorageError(error);
    }
  }

  private insertPlanning(head: StationZeroV3PlanningHead): void {
    this.db.prepare(`INSERT INTO station_zero_v3_planning_heads
      (run_id, planning_id, world_revision, planning_revision, status, head_json, head_digest)
      VALUES (?, ?, ?, ?, ?, ?, ?)`)
      .run(head.runId, head.planningId, head.worldRevision, head.planningRevision, head.status,
        canonicalJson(head), planningDigest(head));
  }

  private updatePlanning(previous: StationZeroV3PlanningHead, next: StationZeroV3PlanningHead): void {
    const result = this.db.prepare(`UPDATE station_zero_v3_planning_heads
      SET planning_revision = ?, status = ?, head_json = ?, head_digest = ?
      WHERE run_id = ? AND planning_id = ? AND head_digest = ?`)
      .run(next.planningRevision, next.status, canonicalJson(next), planningDigest(next),
        previous.runId, previous.planningId, planningDigest(previous));
    if (Number(result.changes) !== 1) {
      throw new StationZeroV3StorageError("station_zero_v3_constraint", "Station Zero v3 Planning Head changed concurrently");
    }
  }

  submittedPlans(runId: string, planningId: string): Partial<Record<StationZeroFactionId, StationZeroV3SubmittedPlanRecord>> {
    try {
      const planning = this.getPlanning(runId, planningId);
      const sourceState = this.stateAtRevision(runId, planning.worldRevision);
      return this.submittedPlansAgainstState(runId, planning, sourceState);
    } catch (error) {
      mapStorageError(error);
    }
  }

  private submittedPlansAgainstState(
    runId: string,
    planning: StationZeroV3PlanningHead,
    sourceState: StationZeroV3WorldState,
  ): Partial<Record<StationZeroFactionId, StationZeroV3SubmittedPlanRecord>> {
    const commitment = prepareStationZeroV3Commitment(sourceState);
    if (sha256(sourceState) !== planning.worldDigest || sha256(commitment) !== planning.commitmentDigest) {
      throw new StationZeroV3StorageError(
        "station_zero_v3_corrupt",
        `Planning Head source state differs from retained World history: ${planning.planningId}`,
      );
    }
    const rows = this.db.prepare(`SELECT faction_id, plan_json, plan_digest, submitted_at
      FROM station_zero_v3_faction_plans WHERE run_id = ? AND planning_id = ? ORDER BY faction_id`)
      .all(runId, planning.planningId) as unknown as PlanRow[];
    const records: Partial<Record<StationZeroFactionId, StationZeroV3SubmittedPlanRecord>> = {};
    for (const row of rows) {
      if (!STATION_ZERO_FACTION_IDS.includes(row.faction_id as StationZeroFactionId)) {
        throw new StationZeroV3StorageError("station_zero_v3_corrupt", `Retained Faction Plan has unknown Faction: ${row.faction_id}`);
      }
      const factionId = row.faction_id as StationZeroFactionId;
      const plan = parseJson<StationZeroFactionTurnPlan>(row.plan_json, "Station Zero v3 Faction Plan");
      if (planDigest(plan) !== row.plan_digest || planning.submittedPlanDigests[factionId] !== row.plan_digest) {
        throw new StationZeroV3StorageError("station_zero_v3_corrupt", `Retained Faction Plan digest differs from Planning Head: ${factionId}`);
      }
      try { assertStationZeroFactionTurnPlan(commitment, plan); }
      catch (error) {
        throw new StationZeroV3StorageError("station_zero_v3_corrupt", `Retained Faction Plan is invalid: ${factionId}`, { cause: error });
      }
      records[factionId] = { plan, planDigest: row.plan_digest, submittedAt: row.submitted_at };
    }
    if (Object.keys(records).length !== Object.keys(planning.submittedPlanDigests).length) {
      throw new StationZeroV3StorageError(
        "station_zero_v3_corrupt",
        `Planning Head submitted Plan count differs from retained rows: ${planning.planningId}`,
      );
    }
    return records;
  }

  submitFactionPlan(
    runId: string,
    planningId: string,
    plan: StationZeroFactionTurnPlan,
  ): StationZeroV3PlanReceipt {
    try {
      const planning = this.getPlanning(runId, planningId);
      if (planning.status !== "open") throw new TypeError("Faction Plans can be submitted only to an open Planning Head");
      const world = this.loadWorldHead(runId);
      if (world.revision !== planning.worldRevision || world.stateDigest !== planning.worldDigest) {
        throw new StationZeroV3StorageError("station_zero_v3_constraint", "Planning Head is stale against the current World Head");
      }
      const commitment = prepareStationZeroV3Commitment(world.state);
      if (sha256(commitment) !== planning.commitmentDigest) {
        throw new StationZeroV3StorageError("station_zero_v3_corrupt", "Planning commitment digest differs from the current World");
      }
      assertStationZeroFactionTurnPlan(commitment, plan);
      const digest = planDigest(plan);
      const existing = this.db.prepare(`SELECT faction_id, plan_json, plan_digest, submitted_at
        FROM station_zero_v3_faction_plans WHERE run_id = ? AND planning_id = ? AND faction_id = ?`)
        .get(runId, planningId, plan.factionId) as PlanRow | undefined;
      if (existing) {
        if (existing.plan_digest !== digest || existing.plan_json !== canonicalJson(plan)) {
          throw new StationZeroV3StorageError("station_zero_v3_constraint", `Faction ${plan.factionId} is already bound to another Plan`);
        }
        return {
          runId,
          planningId,
          factionId: plan.factionId,
          planDigest: digest,
          planningRevision: planning.planningRevision,
          idempotent: true,
        };
      }

      const now = new Date().toISOString();
      let next!: StationZeroV3PlanningHead;
      this.transaction(() => {
        const current = this.getPlanning(runId, planningId);
        if (current.status !== "open" || planningDigest(current) !== planningDigest(planning)) {
          throw new StationZeroV3StorageError("station_zero_v3_constraint", "Planning Head changed before Faction Plan submission");
        }
        this.db.prepare(`INSERT INTO station_zero_v3_faction_plans
          (run_id, planning_id, faction_id, plan_json, plan_digest, submitted_at)
          VALUES (?, ?, ?, ?, ?, ?)`)
          .run(runId, planningId, plan.factionId, canonicalJson(plan), digest, now);
        next = {
          ...current,
          planningRevision: current.planningRevision + 1,
          submittedPlanDigests: { ...current.submittedPlanDigests, [plan.factionId]: digest },
          updatedAt: now,
        };
        this.updatePlanning(current, next);
      });
      return {
        runId,
        planningId,
        factionId: plan.factionId,
        planDigest: digest,
        planningRevision: next.planningRevision,
        idempotent: false,
      };
    } catch (error) {
      mapStorageError(error);
    }
  }

  commitPlanning(runId: string, planningId: string): StationZeroV3PreparedTurn {
    try {
      const planning = this.getPlanning(runId, planningId);
      if (planning.status === "resolved") throw new TypeError("Resolved Planning cannot be committed again");
      const retainedBatch = this.batchRow(runId, planningId);
      if (planning.status === "committed") {
        if (!retainedBatch) throw new StationZeroV3StorageError("station_zero_v3_corrupt", "Committed Planning is missing its Turn Batch");
        return this.preparedFromRows(planning, retainedBatch);
      }
      if (retainedBatch) throw new StationZeroV3StorageError("station_zero_v3_corrupt", "Open Planning already retains a Turn Batch");

      const world = this.loadWorldHead(runId);
      if (world.revision !== planning.worldRevision || world.stateDigest !== planning.worldDigest) {
        throw new StationZeroV3StorageError("station_zero_v3_constraint", "Planning Head is stale against the current World Head");
      }
      const commitment = prepareStationZeroV3Commitment(world.state);
      if (sha256(commitment) !== planning.commitmentDigest) {
        throw new StationZeroV3StorageError("station_zero_v3_corrupt", "Planning commitment digest differs from current World");
      }
      const plans = this.submittedPlans(runId, planningId);
      const missing = STATION_ZERO_FACTION_IDS.filter((factionId) => !plans[factionId]);
      if (missing.length > 0) throw new TypeError(`Planning requires one Plan from every Faction; missing: ${missing.join(", ")}`);
      const identity = identityFor(runId, planning.worldRevision);
      const batch = canonicalizeStationZeroV3TurnBatch({
        turnBatchId: identity.turnBatchId,
        expectedWorldRevision: planning.worldRevision,
        expectedTurn: planning.turn,
        factionPlans: STATION_ZERO_FACTION_IDS.map((factionId) => plans[factionId]!.plan),
      });
      assertStationZeroTurnBatch(commitment, batch);
      const batchDigest = sha256(batch);
      const now = new Date().toISOString();
      let next!: StationZeroV3PlanningHead;
      this.transaction(() => {
        const current = this.getPlanning(runId, planningId);
        if (current.status !== "open" || planningDigest(current) !== planningDigest(planning)) {
          throw new StationZeroV3StorageError("station_zero_v3_constraint", "Planning Head changed before commitment");
        }
        this.db.prepare(`INSERT INTO station_zero_v3_turn_batches
          (run_id, planning_id, turn_batch_id, batch_json, batch_digest, task_id, goal_id, effect_id, dispatch_id, created_at)
          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`)
          .run(runId, planningId, identity.turnBatchId, canonicalJson(batch), batchDigest,
            identity.taskId, identity.goalId, identity.effectId, identity.dispatchId, now);
        next = {
          ...current,
          planningRevision: current.planningRevision + 1,
          status: "committed",
          turnBatchId: identity.turnBatchId,
          batchDigest,
          taskId: identity.taskId,
          goalId: identity.goalId,
          effectId: identity.effectId,
          dispatchId: identity.dispatchId,
          updatedAt: now,
        };
        this.updatePlanning(current, next);
      });
      return {
        planning: next,
        batch,
        batchDigest,
        taskId: identity.taskId,
        goalId: identity.goalId,
        effectId: identity.effectId,
        dispatchId: identity.dispatchId,
      };
    } catch (error) {
      if (sqliteCode(error).includes("CONSTRAINT")) {
        const planning = this.getPlanning(runId, planningId);
        const batch = this.batchRow(runId, planningId);
        if (planning.status === "committed" && batch) return this.preparedFromRows(planning, batch);
      }
      mapStorageError(error);
    }
  }

  preparedTurn(runId: string, planningId: string): StationZeroV3PreparedTurn {
    const planning = this.getPlanning(runId, planningId);
    const row = this.batchRow(runId, planningId);
    if (!row || (planning.status !== "committed" && planning.status !== "resolved")) {
      throw new Error(`Planning has no committed Turn Batch: ${planningId}`);
    }
    return this.preparedFromRows(planning, row);
  }

  private batchRow(runId: string, planningId: string): BatchRow | null {
    const row = this.db.prepare("SELECT * FROM station_zero_v3_turn_batches WHERE run_id = ? AND planning_id = ?")
      .get(runId, planningId) as BatchRow | undefined;
    return row ?? null;
  }

  private preparedFromRows(planning: StationZeroV3PlanningHead, row: BatchRow): StationZeroV3PreparedTurn {
    const batch = parseJson<StationZeroTurnBatch>(row.batch_json, "Station Zero v3 Turn Batch");
    let canonical: StationZeroTurnBatch;
    try {
      canonical = canonicalizeStationZeroV3TurnBatch(batch);
    } catch (error) {
      throw new StationZeroV3StorageError(
        "station_zero_v3_corrupt",
        `Committed Turn Batch differs from Planning Head: ${planning.planningId}`,
        { cause: error },
      );
    }
    if (
      row.run_id !== planning.runId || row.planning_id !== planning.planningId ||
      sha256(canonical) !== row.batch_digest || canonicalJson(canonical) !== row.batch_json ||
      planning.turnBatchId !== row.turn_batch_id || planning.batchDigest !== row.batch_digest ||
      planning.taskId !== row.task_id || planning.goalId !== row.goal_id ||
      planning.effectId !== row.effect_id || planning.dispatchId !== row.dispatch_id
    ) {
      throw new StationZeroV3StorageError("station_zero_v3_corrupt", `Committed Turn Batch differs from Planning Head: ${planning.planningId}`);
    }
    return {
      planning,
      batch: canonical,
      batchDigest: row.batch_digest,
      taskId: row.task_id,
      goalId: row.goal_id,
      effectId: row.effect_id,
      dispatchId: row.dispatch_id,
    };
  }

  applyPreparedTurn(runId: string, planningId: string): StationZeroV3TurnReceipt {
    try {
      const prepared = this.preparedTurn(runId, planningId);
      const existing = this.turnReceiptByBatch(runId, prepared.batch.turnBatchId);
      if (existing) {
        if (canonicalJson(existing.batch) !== canonicalJson(prepared.batch)) {
          throw new StationZeroV3StorageError("station_zero_v3_corrupt", "Retained Turn differs from the prepared Turn Batch");
        }
        return { ...existing, idempotent: true };
      }

      this.inject("before_begin");
      this.db.exec("BEGIN IMMEDIATE");
      let committed = false;
      try {
        this.inject("after_begin");
        const currentPrepared = this.preparedTurn(runId, planningId);
        const retainedInside = this.turnReceiptByBatch(runId, currentPrepared.batch.turnBatchId);
        if (retainedInside) {
          this.db.exec("COMMIT");
          committed = true;
          return { ...retainedInside, idempotent: true };
        }
        if (currentPrepared.planning.status !== "committed") {
          throw new StationZeroV3StorageError("station_zero_v3_constraint", "Only committed Planning can execute a Turn");
        }
        const world = this.loadWorldHead(runId);
        if (
          world.revision !== currentPrepared.planning.worldRevision ||
          world.stateDigest !== currentPrepared.planning.worldDigest
        ) {
          throw new StationZeroV3StorageError("station_zero_v3_constraint", "Prepared Turn is stale against the current World Head");
        }
        const commitment = prepareStationZeroV3Commitment(world.state);
        if (sha256(commitment) !== currentPrepared.planning.commitmentDigest) {
          throw new StationZeroV3StorageError("station_zero_v3_corrupt", "Prepared Turn commitment digest differs from current World");
        }
        const applied = applyStationZeroV3Turn(commitment, currentPrepared.batch);
        if (applied.status !== "accepted") {
          throw new StationZeroV3StorageError("station_zero_v3_corrupt", `Committed Turn Batch no longer admits: ${applied.reason}`);
        }
        const sequenceRow = this.db.prepare(`SELECT COALESCE(MAX(turn_sequence), -1) + 1 sequence
          FROM station_zero_v3_world_events WHERE run_id = ?`).get(runId) as { sequence: number };
        const turnSequence = Number(sequenceRow.sequence);
        const event: StationZeroV3WorldEvent = {
          schemaVersion: 1,
          kind: "ordivon.game.station-zero-v3-world-event",
          eventId: `world-event:${currentPrepared.batch.turnBatchId}`,
          runId,
          turnSequence,
          planningId,
          turnBatchId: currentPrepared.batch.turnBatchId,
          taskId: currentPrepared.taskId,
          dispatchId: currentPrepared.dispatchId,
          worldRevisionBefore: world.revision,
          worldRevisionAfter: applied.state.revision,
          turnBefore: world.turn,
          turnAfter: applied.state.encounter.turn,
          worldDigestBefore: world.stateDigest,
          commitmentDigestBefore: sha256(commitment),
          worldDigestAfter: sha256(applied.state),
          resolutionDigest: applied.resolution.deterministicDigest,
          turnRecordDigest: applied.record.recordDigest,
          intentResolutionCounts: resolutionCounts(applied.record),
          encounterStatus: applied.state.encounter.status,
          encounterReason: applied.state.encounter.reason,
          factionOutcomes: {
            rescue: applied.state.factions.rescue.outcome,
            pirate: applied.state.factions.pirate.outcome,
            swarm: applied.state.factions.swarm.outcome,
          },
        };
        const eventJson = canonicalJson(event);
        const eventDigest = sha256(event);
        const previousEvent = this.db.prepare(`SELECT row_digest FROM station_zero_v3_world_events
          WHERE run_id = ? ORDER BY turn_sequence DESC LIMIT 1`).get(runId) as { row_digest: string } | undefined;
        const eventBase: Omit<EventRow, "row_digest" | "created_at"> = {
          run_id: runId,
          turn_sequence: turnSequence,
          planning_id: planningId,
          turn_batch_id: currentPrepared.batch.turnBatchId,
          event_id: event.eventId,
          event_json: eventJson,
          event_digest: eventDigest,
          previous_digest: previousEvent?.row_digest ?? "",
        };
        const now = new Date().toISOString();
        const eventChainDigest = eventRowDigest(runId, eventBase);
        this.db.prepare(`INSERT INTO station_zero_v3_world_events
          (run_id, turn_sequence, planning_id, turn_batch_id, event_id, event_json, event_digest, previous_digest, row_digest, created_at)
          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`)
          .run(runId, turnSequence, planningId, currentPrepared.batch.turnBatchId, event.eventId,
            eventJson, eventDigest, eventBase.previous_digest, eventChainDigest, now);
        this.inject("after_event_insert");

        const previousRecord = this.db.prepare(`SELECT row_digest FROM station_zero_v3_turn_records
          WHERE run_id = ? ORDER BY turn_sequence DESC LIMIT 1`).get(runId) as { row_digest: string } | undefined;
        const recordJson = canonicalJson(applied.record);
        const recordBase: Omit<RecordRow, "row_digest" | "created_at"> = {
          run_id: runId,
          turn_sequence: turnSequence,
          planning_id: planningId,
          turn_batch_id: currentPrepared.batch.turnBatchId,
          record_json: recordJson,
          record_digest: applied.record.recordDigest,
          event_digest: eventDigest,
          before_digest: applied.record.stateDigestBefore,
          after_digest: applied.record.stateDigestAfter,
          previous_digest: previousRecord?.row_digest ?? "",
        };
        const recordChainDigest = recordRowDigest(runId, recordBase);
        this.db.prepare(`INSERT INTO station_zero_v3_turn_records
          (run_id, turn_sequence, planning_id, turn_batch_id, record_json, record_digest, event_digest,
           before_digest, after_digest, previous_digest, row_digest, created_at)
          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`)
          .run(runId, turnSequence, planningId, currentPrepared.batch.turnBatchId, recordJson,
            applied.record.recordDigest, eventDigest, applied.record.stateDigestBefore, applied.record.stateDigestAfter,
            recordBase.previous_digest, recordChainDigest, now);
        this.inject("after_record_insert");

        this.inject("before_head_update");
        this.writeWorldHead(runId, applied.state, turnSequence, now);
        const resolvedPlanning: StationZeroV3PlanningHead = {
          ...currentPrepared.planning,
          planningRevision: currentPrepared.planning.planningRevision + 1,
          status: "resolved",
          updatedAt: now,
        };
        this.updatePlanning(currentPrepared.planning, resolvedPlanning);
        this.db.prepare("UPDATE runs SET status = ? WHERE run_id = ?")
          .run(applied.state.encounter.status === "terminal" ? "terminal" : "running", runId);
        this.inject("after_head_update");
        this.inject("before_commit");
        this.db.exec("COMMIT");
        committed = true;
        this.inject("after_commit");
        return {
          runId,
          turnSequence,
          planningId,
          turnBatchId: currentPrepared.batch.turnBatchId,
          taskId: currentPrepared.taskId,
          dispatchId: currentPrepared.dispatchId,
          batch: currentPrepared.batch,
          event,
          eventDigest,
          record: applied.record,
          recordDigest: applied.record.recordDigest,
          state: applied.state,
          stateDigest: sha256(applied.state),
          idempotent: false,
        };
      } catch (error) {
        if (!committed) {
          try { this.db.exec("ROLLBACK"); } catch {}
        }
        throw error;
      }
    } catch (error) {
      mapStorageError(error);
    }
  }

  turnReceiptByBatch(runId: string, turnBatchId: string): StationZeroV3TurnReceipt | null {
    try {
      this.getRun(runId);
      const eventRow = this.db.prepare(`SELECT * FROM station_zero_v3_world_events
        WHERE run_id = ? AND turn_batch_id = ?`).get(runId, turnBatchId) as EventRow | undefined;
      if (!eventRow) return null;
      const recordRow = this.db.prepare(`SELECT * FROM station_zero_v3_turn_records
        WHERE run_id = ? AND turn_sequence = ?`).get(runId, eventRow.turn_sequence) as RecordRow | undefined;
      if (!recordRow) throw new StationZeroV3StorageError("station_zero_v3_corrupt", "World Event is missing its Turn Record");
      const batchRow = this.db.prepare(`SELECT * FROM station_zero_v3_turn_batches
        WHERE run_id = ? AND turn_batch_id = ?`).get(runId, turnBatchId) as BatchRow | undefined;
      if (!batchRow) throw new StationZeroV3StorageError("station_zero_v3_corrupt", "World Event is missing its prepared Turn Batch");
      return this.receiptFromRows(eventRow, recordRow, batchRow, true);
    } catch (error) {
      mapStorageError(error);
    }
  }

  latestTurnReceipt(runId: string): StationZeroV3TurnReceipt | null {
    try {
      this.getRun(runId);
      const eventRow = this.db.prepare(`SELECT * FROM station_zero_v3_world_events
        WHERE run_id = ? ORDER BY turn_sequence DESC LIMIT 1`).get(runId) as EventRow | undefined;
      if (!eventRow) return null;
      const recordRow = this.db.prepare(`SELECT * FROM station_zero_v3_turn_records
        WHERE run_id = ? AND turn_sequence = ?`).get(runId, eventRow.turn_sequence) as RecordRow | undefined;
      const batchRow = this.db.prepare(`SELECT * FROM station_zero_v3_turn_batches
        WHERE run_id = ? AND turn_batch_id = ?`).get(runId, eventRow.turn_batch_id) as BatchRow | undefined;
      if (!recordRow || !batchRow) throw new StationZeroV3StorageError("station_zero_v3_corrupt", "Latest World Event lacks aligned evidence");
      return this.receiptFromRows(eventRow, recordRow, batchRow, true);
    } catch (error) {
      mapStorageError(error);
    }
  }

  private receiptFromRows(
    eventRow: EventRow,
    recordRow: RecordRow,
    batchRow: BatchRow,
    idempotent: boolean,
  ): StationZeroV3TurnReceipt {
    this.assertEventRow(eventRow);
    this.assertRecordRow(recordRow);
    if (
      Number(eventRow.turn_sequence) !== Number(recordRow.turn_sequence) ||
      eventRow.planning_id !== recordRow.planning_id || eventRow.planning_id !== batchRow.planning_id ||
      eventRow.turn_batch_id !== recordRow.turn_batch_id || eventRow.turn_batch_id !== batchRow.turn_batch_id ||
      eventRow.event_digest !== recordRow.event_digest
    ) {
      throw new StationZeroV3StorageError("station_zero_v3_corrupt", "Station Zero v3 Event, Record, and Batch streams are misaligned");
    }
    const event = parseJson<StationZeroV3WorldEvent>(eventRow.event_json, "Station Zero v3 World Event");
    const record = parseJson<StationZeroTurnRecord>(recordRow.record_json, "Station Zero v3 Turn Record");
    const batch = parseJson<StationZeroTurnBatch>(batchRow.batch_json, "Station Zero v3 Turn Batch");
    const canonicalBatch = canonicalizeStationZeroV3TurnBatch(batch);
    if (
      sha256(event) !== eventRow.event_digest || event.turnRecordDigest !== record.recordDigest ||
      record.recordDigest !== recordRow.record_digest || record.stateDigestBefore !== recordRow.before_digest ||
      record.stateDigestAfter !== recordRow.after_digest || canonicalJson(canonicalBatch) !== batchRow.batch_json ||
      sha256(canonicalBatch) !== batchRow.batch_digest || canonicalJson(record.batch) !== canonicalJson(canonicalBatch)
    ) {
      throw new StationZeroV3StorageError("station_zero_v3_corrupt", "Station Zero v3 retained Turn evidence digest differs from content");
    }
    const state = this.replayToSequence(eventRow.run_id, Number(eventRow.turn_sequence));
    if (sha256(state) !== event.worldDigestAfter || sha256(state) !== record.stateDigestAfter) {
      throw new StationZeroV3StorageError("station_zero_v3_corrupt", "Station Zero v3 retained Turn after-state differs from Replay");
    }
    return {
      runId: eventRow.run_id,
      turnSequence: Number(eventRow.turn_sequence),
      planningId: eventRow.planning_id,
      turnBatchId: eventRow.turn_batch_id,
      taskId: batchRow.task_id,
      dispatchId: batchRow.dispatch_id,
      batch: canonicalBatch,
      event,
      eventDigest: eventRow.event_digest,
      record,
      recordDigest: recordRow.record_digest,
      state,
      stateDigest: sha256(state),
      idempotent,
    };
  }

  private assertEventRow(row: EventRow): void {
    requireSafeInteger(Number(row.turn_sequence), "Station Zero v3 Event sequence");
    const base: Omit<EventRow, "row_digest" | "created_at"> = {
      run_id: row.run_id,
      turn_sequence: Number(row.turn_sequence),
      planning_id: row.planning_id,
      turn_batch_id: row.turn_batch_id,
      event_id: row.event_id,
      event_json: row.event_json,
      event_digest: row.event_digest,
      previous_digest: row.previous_digest,
    };
    if (eventRowDigest(row.run_id, base) !== row.row_digest) {
      throw new StationZeroV3StorageError("station_zero_v3_corrupt", "Station Zero v3 World Event row digest mismatch");
    }
  }

  private assertRecordRow(row: RecordRow): void {
    requireSafeInteger(Number(row.turn_sequence), "Station Zero v3 Record sequence");
    const base: Omit<RecordRow, "row_digest" | "created_at"> = {
      run_id: row.run_id,
      turn_sequence: Number(row.turn_sequence),
      planning_id: row.planning_id,
      turn_batch_id: row.turn_batch_id,
      record_json: row.record_json,
      record_digest: row.record_digest,
      event_digest: row.event_digest,
      before_digest: row.before_digest,
      after_digest: row.after_digest,
      previous_digest: row.previous_digest,
    };
    if (recordRowDigest(row.run_id, base) !== row.row_digest) {
      throw new StationZeroV3StorageError("station_zero_v3_corrupt", "Station Zero v3 Turn Record row digest mismatch");
    }
  }

  private replayToSequence(runId: string, targetSequence: number): StationZeroV3WorldState {
    const genesis = this.genesis(runId);
    if (targetSequence < 0) return genesis;
    const rows = this.db.prepare(`SELECT record_json FROM station_zero_v3_turn_records
      WHERE run_id = ? AND turn_sequence <= ? ORDER BY turn_sequence`).all(runId, targetSequence) as unknown as Array<{ record_json: string }>;
    if (rows.length !== targetSequence + 1) {
      throw new StationZeroV3StorageError("station_zero_v3_corrupt", "Station Zero v3 Turn Record sequence is incomplete");
    }
    let state = genesis;
    for (const [index, row] of rows.entries()) {
      const record = parseJson<StationZeroTurnRecord>(row.record_json, "Station Zero v3 Turn Record");
      const commitment = prepareStationZeroV3Commitment(state);
      const replay = replayStationZeroV3Turn(commitment, record);
      state = replay.state;
      if (state.revision !== index + 1) {
        throw new StationZeroV3StorageError("station_zero_v3_corrupt", "Station Zero v3 Replay revision is discontinuous");
      }
    }
    return state;
  }

  recover(runId: string): StationZeroV3RecoveryResult {
    try {
      this.getRun(runId);
      const genesis = this.genesis(runId);
      const eventRows = this.db.prepare(`SELECT * FROM station_zero_v3_world_events
        WHERE run_id = ? ORDER BY turn_sequence`).all(runId) as unknown as EventRow[];
      const recordRows = this.db.prepare(`SELECT * FROM station_zero_v3_turn_records
        WHERE run_id = ? ORDER BY turn_sequence`).all(runId) as unknown as RecordRow[];
      if (eventRows.length !== recordRows.length) {
        throw new StationZeroV3StorageError("station_zero_v3_corrupt", "Station Zero v3 World Event and Turn Record counts diverged");
      }
      let previousEventDigest = "";
      let previousRecordDigest = "";
      let state = genesis;
      for (let index = 0; index < eventRows.length; index += 1) {
        const eventRow = eventRows[index];
        const recordRow = recordRows[index];
        if (!eventRow || !recordRow || Number(eventRow.turn_sequence) !== index || Number(recordRow.turn_sequence) !== index) {
          throw new StationZeroV3StorageError("station_zero_v3_corrupt", "Station Zero v3 retained Turn sequence is discontinuous");
        }
        this.assertEventRow(eventRow);
        this.assertRecordRow(recordRow);
        if (eventRow.previous_digest !== previousEventDigest || recordRow.previous_digest !== previousRecordDigest) {
          throw new StationZeroV3StorageError("station_zero_v3_corrupt", "Station Zero v3 retained Turn hash chain is discontinuous");
        }
        if (
          eventRow.planning_id !== recordRow.planning_id || eventRow.turn_batch_id !== recordRow.turn_batch_id ||
          eventRow.event_digest !== recordRow.event_digest
        ) {
          throw new StationZeroV3StorageError("station_zero_v3_corrupt", "Station Zero v3 World Event and Turn Record identities diverged");
        }
        const event = parseJson<StationZeroV3WorldEvent>(eventRow.event_json, "Station Zero v3 World Event");
        const record = parseJson<StationZeroTurnRecord>(recordRow.record_json, "Station Zero v3 Turn Record");
        const planning = this.getPlanning(runId, eventRow.planning_id);
        const batchRow = this.batchRow(runId, eventRow.planning_id);
        if (!batchRow || planning.status !== "resolved") {
          throw new StationZeroV3StorageError("station_zero_v3_corrupt", "Retained Turn is missing resolved Planning or its canonical Batch");
        }
        const prepared = this.preparedFromRows(planning, batchRow);
        const submittedPlans = this.submittedPlansAgainstState(runId, planning, state);
        if (
          STATION_ZERO_FACTION_IDS.some((factionId) => !submittedPlans[factionId]) ||
          STATION_ZERO_FACTION_IDS.some((factionId) =>
            canonicalJson(submittedPlans[factionId]!.plan) !==
            canonicalJson(prepared.batch.factionPlans.find((plan) => plan.factionId === factionId)))
        ) {
          throw new StationZeroV3StorageError(
            "station_zero_v3_corrupt",
            "Station Zero v3 retained Faction Plans differ from the canonical Turn Batch",
          );
        }
        if (
          sha256(event) !== eventRow.event_digest || event.eventId !== eventRow.event_id ||
          event.runId !== runId || event.turnSequence !== index || event.planningId !== eventRow.planning_id ||
          event.turnBatchId !== eventRow.turn_batch_id || event.turnBatchId !== prepared.batch.turnBatchId ||
          event.taskId !== prepared.taskId || event.dispatchId !== prepared.dispatchId ||
          event.turnRecordDigest !== record.recordDigest || record.recordDigest !== recordRow.record_digest ||
          record.stateDigestBefore !== recordRow.before_digest || record.stateDigestAfter !== recordRow.after_digest ||
          canonicalJson(record.batch) !== canonicalJson(prepared.batch) || event.worldDigestBefore !== sha256(state) ||
          planning.worldRevision !== state.revision || planning.turn !== state.encounter.turn ||
          planning.worldDigest !== sha256(state)
        ) {
          throw new StationZeroV3StorageError("station_zero_v3_corrupt", "Station Zero v3 retained Planning, Batch, Event, or Record identity is inconsistent");
        }
        const commitment = prepareStationZeroV3Commitment(state);
        if (
          event.commitmentDigestBefore !== sha256(commitment) ||
          planning.commitmentDigest !== sha256(commitment) ||
          planning.standingOrderRevision !== state.encounter.activePlanRevision
        ) {
          throw new StationZeroV3StorageError("station_zero_v3_corrupt", "Station Zero v3 Planning or World Event commitment differs from Replay");
        }
        const replay = replayStationZeroV3Turn(commitment, record);
        state = replay.state;
        if (
          event.worldRevisionAfter !== state.revision || event.turnAfter !== state.encounter.turn ||
          event.worldDigestAfter !== sha256(state) || event.resolutionDigest !== replay.resolution.deterministicDigest
        ) {
          throw new StationZeroV3StorageError("station_zero_v3_corrupt", "Station Zero v3 World Event differs from deterministic Replay");
        }
        previousEventDigest = eventRow.row_digest;
        previousRecordDigest = recordRow.row_digest;
      }

      const plannings = this.listPlanning(runId);
      const unresolvedPlannings = plannings.filter((planning) => planning.status !== "resolved");
      if (unresolvedPlannings.length > 1 || plannings.length !== eventRows.length + unresolvedPlannings.length) {
        throw new StationZeroV3StorageError(
          "station_zero_v3_corrupt",
          "Station Zero v3 Planning history does not align with retained Turns",
        );
      }
      const unresolvedPlanning = unresolvedPlannings[0];
      if (unresolvedPlanning) {
        if (
          unresolvedPlanning.worldRevision !== state.revision ||
          unresolvedPlanning.turn !== state.encounter.turn ||
          unresolvedPlanning.worldDigest !== sha256(state) ||
          unresolvedPlanning.standingOrderRevision !== state.encounter.activePlanRevision
        ) {
          throw new StationZeroV3StorageError(
            "station_zero_v3_corrupt",
            "Unresolved Station Zero v3 Planning does not target the current World Head",
          );
        }
        const submittedPlans = this.submittedPlansAgainstState(runId, unresolvedPlanning, state);
        const batchRow = this.batchRow(runId, unresolvedPlanning.planningId);
        if (unresolvedPlanning.status === "open" && batchRow) {
          throw new StationZeroV3StorageError("station_zero_v3_corrupt", "Open Planning unexpectedly retains a canonical Turn Batch");
        }
        if (unresolvedPlanning.status === "committed") {
          if (!batchRow) throw new StationZeroV3StorageError("station_zero_v3_corrupt", "Committed Planning is missing its canonical Turn Batch");
          const prepared = this.preparedFromRows(unresolvedPlanning, batchRow);
          if (
            STATION_ZERO_FACTION_IDS.some((factionId) => !submittedPlans[factionId]) ||
            STATION_ZERO_FACTION_IDS.some((factionId) =>
              canonicalJson(submittedPlans[factionId]!.plan) !==
              canonicalJson(prepared.batch.factionPlans.find((plan) => plan.factionId === factionId)))
          ) {
            throw new StationZeroV3StorageError(
              "station_zero_v3_corrupt",
              "Committed Planning Faction Plans differ from its canonical Turn Batch",
            );
          }
        }
      }

      const expectedLastSequence = eventRows.length - 1;
      const expectedDigest = sha256(state);
      const headRow = this.db.prepare("SELECT * FROM station_zero_v3_world_heads WHERE run_id = ?")
        .get(runId) as WorldHeadRow | undefined;
      let headRebuilt = false;
      if (!headRow) {
        this.transaction(() => this.writeWorldHead(runId, state, expectedLastSequence, new Date().toISOString(), true));
        headRebuilt = true;
      } else {
        const head = this.worldHeadFromRow(headRow);
        if (
          head.stateDigest !== expectedDigest || head.revision !== state.revision || head.turn !== state.encounter.turn ||
          head.lastTurnSequence !== expectedLastSequence
        ) {
          throw new StationZeroV3StorageError("station_zero_v3_corrupt", "Station Zero v3 World Head differs from retained Turn Replay");
        }
      }
      const expectedRunStatus = state.encounter.status === "terminal" ? "terminal" : "running";
      const metadata = this.getRun(runId);
      if (metadata.status !== expectedRunStatus) {
        throw new StationZeroV3StorageError("station_zero_v3_corrupt", "Station Zero v3 Run status differs from retained World Head");
      }
      return {
        runId,
        state,
        stateDigest: expectedDigest,
        turnCount: eventRows.length,
        lastTurnSequence: expectedLastSequence,
        verified: true,
        headRebuilt,
      };
    } catch (error) {
      mapStorageError(error);
    }
  }

  verify(runId: string): StationZeroV3RecoveryResult {
    const recovery = this.recover(runId);
    this.host.verifyJournal(runId);
    return recovery;
  }

  hostSequence(runId: string): number {
    this.getRun(runId);
    const row = this.db.prepare("SELECT COALESCE(MAX(sequence), -1) sequence FROM host_journal WHERE run_id = ?")
      .get(runId) as { sequence: number };
    return Number(row.sequence);
  }

  turnCount(runId: string): number {
    this.getRun(runId);
    const row = this.db.prepare("SELECT COUNT(*) count FROM station_zero_v3_turn_records WHERE run_id = ?")
      .get(runId) as { count: number };
    return Number(row.count);
  }

  close(): void {
    this.db.close();
  }
}
