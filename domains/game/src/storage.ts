import { mkdirSync } from "node:fs";
import { dirname } from "node:path";
import { DatabaseSync } from "node:sqlite";

import { canonicalJson, sha256 } from "./digest.ts";
import type { ApplyResult, JournalEvent, WorldCommand, WorldEvent, WorldState } from "./model.ts";
import { resolveRuleset, resolveScenario } from "./registry.ts";
import {
  CURRENT_BUILD,
  DEFAULT_RUN_ID,
  newRunId,
  type CreateRunInput,
  type RunMetadata,
} from "./run.ts";
import { assertWorldInvariants } from "./scenario.ts";

export const DEFAULT_SNAPSHOT_INTERVAL = 8;
export type StorageErrorCode = "storage_busy" | "storage_corrupt" | "storage_constraint";

export class StorageError extends Error {
  readonly code: StorageErrorCode;

  constructor(code: StorageErrorCode, message: string, options?: ErrorOptions) {
    super(message, options);
    this.name = "StorageError";
    this.code = code;
  }
}

interface CommandRow {
  command_sequence: number;
  command_id: string;
  command_json: string;
  before_digest: string;
  after_digest: string;
  previous_digest: string | null;
  record_digest: string | null;
}

interface EventRow {
  event_sequence: number;
  command_id: string;
  event_json: string;
  before_digest: string;
  after_digest: string;
  previous_digest: string | null;
  record_digest: string | null;
}

interface SnapshotRow {
  revision: number;
  command_sequence: number | null;
  state_json: string;
  digest: string;
}

interface RunRow {
  run_id: string;
  scenario_id: string;
  scenario_version: number;
  ruleset_id: string;
  ruleset_version: number;
  state_schema_version: number;
  seed: string;
  status: RunMetadata["status"];
  created_at: string;
  created_with_build: string;
}

export interface PersistedApplyResult {
  result: ApplyResult;
  idempotent: boolean;
  runId: string;
  commandSequence: number;
}

export interface ReplayResult {
  runId: string;
  mode: "recovery" | "verify";
  state: WorldState;
  digest: string;
  eventCount: number;
  replayedCommandCount: number;
  snapshotRevision: number;
  verified: true;
}

export interface StoreOptions {
  activeRunId?: string;
  snapshotInterval?: number;
  busyTimeoutMs?: number;
}

function metadataFromRow(row: RunRow): RunMetadata {
  return {
    runId: row.run_id,
    scenarioId: row.scenario_id,
    scenarioVersion: Number(row.scenario_version),
    rulesetId: row.ruleset_id,
    rulesetVersion: Number(row.ruleset_version),
    stateSchemaVersion: Number(row.state_schema_version),
    seed: row.seed,
    status: row.status,
    createdAt: row.created_at,
    createdWithBuild: row.created_with_build,
  };
}

function sqliteCode(error: unknown): string {
  return error && typeof error === "object" && "code" in error ? String(error.code) : "";
}

function mapStorageError(error: unknown): never {
  if (error instanceof StorageError) throw error;
  const code = sqliteCode(error);
  const message = error instanceof Error ? error.message.toLowerCase() : String(error).toLowerCase();
  if (code.includes("BUSY") || code.includes("LOCKED") || message.includes("database is locked") || message.includes("database is busy")) {
    throw new StorageError("storage_busy", "storage is temporarily busy", { cause: error });
  }
  if (code.includes("CONSTRAINT")) {
    throw new StorageError("storage_constraint", "storage constraint rejected the write", { cause: error });
  }
  if (code.includes("CORRUPT") || code.includes("NOTADB")) {
    throw new StorageError("storage_corrupt", "storage is corrupt", { cause: error });
  }
  throw error;
}

function parseJournalEvent(runId: string, sequence: number, json: string): JournalEvent {
  const parsed = JSON.parse(json) as JournalEvent | WorldEvent;
  if ("event" in parsed) return parsed;
  return {
    tickId: `legacy:${runId}:${sequence}`,
    commandSequence: sequence,
    simulationTick: parsed.turn,
    worldRevision: parsed.worldRevision,
    event: parsed,
  };
}

function commandDigest(runId: string, row: Omit<CommandRow, "record_digest">): string {
  return sha256({
    kind: "command",
    runId,
    sequence: Number(row.command_sequence),
    commandId: row.command_id,
    commandJson: row.command_json,
    beforeDigest: row.before_digest,
    afterDigest: row.after_digest,
    previousDigest: row.previous_digest ?? "",
  });
}

function eventDigest(runId: string, row: Omit<EventRow, "record_digest">): string {
  return sha256({
    kind: "event",
    runId,
    sequence: Number(row.event_sequence),
    commandId: row.command_id,
    eventJson: row.event_json,
    beforeDigest: row.before_digest,
    afterDigest: row.after_digest,
    previousDigest: row.previous_digest ?? "",
  });
}

export class GameStore {
  readonly db: DatabaseSync;
  readonly dbPath: string;
  readonly snapshotInterval: number;
  activeRunId: string;

  constructor(dbPath: string, options: StoreOptions | string = {}) {
    const normalized = typeof options === "string" ? { activeRunId: options } : options;
    this.dbPath = dbPath;
    this.activeRunId = normalized.activeRunId ?? DEFAULT_RUN_ID;
    this.snapshotInterval = normalized.snapshotInterval ?? DEFAULT_SNAPSHOT_INTERVAL;
    if (!Number.isSafeInteger(this.snapshotInterval) || this.snapshotInterval < 1) {
      throw new TypeError("snapshotInterval must be a positive integer");
    }
    if (dbPath !== ":memory:") mkdirSync(dirname(dbPath), { recursive: true });
    this.db = new DatabaseSync(dbPath);

    try {
      this.db.exec(`
        PRAGMA foreign_keys = ON;
        PRAGMA journal_mode = WAL;
        PRAGMA synchronous = FULL;
        PRAGMA busy_timeout = ${normalized.busyTimeoutMs ?? 5000};
      `);
      this.createSchema();
      this.migrateSchema();
      this.backfillIntegrityMetadata();
      this.pruneSnapshots();
      if (this.listRuns().length === 0) this.createRun({ runId: this.activeRunId });
      if (!this.findRun(this.activeRunId)) this.activeRunId = this.listRuns()[0]?.runId ?? this.activeRunId;
      this.recover(this.activeRunId);
    } catch (error) {
      mapStorageError(error);
    }
  }

  private createSchema(): void {
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS runs (
        run_id TEXT PRIMARY KEY,
        scenario_id TEXT NOT NULL,
        scenario_version INTEGER NOT NULL,
        ruleset_id TEXT NOT NULL,
        ruleset_version INTEGER NOT NULL,
        state_schema_version INTEGER NOT NULL,
        seed TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL,
        created_with_build TEXT NOT NULL
      );
      CREATE TABLE IF NOT EXISTS commands (
        run_id TEXT NOT NULL,
        command_sequence INTEGER NOT NULL,
        command_id TEXT NOT NULL,
        command_json TEXT NOT NULL,
        before_digest TEXT NOT NULL,
        after_digest TEXT NOT NULL,
        previous_digest TEXT,
        record_digest TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (run_id, command_sequence),
        UNIQUE (run_id, command_id),
        FOREIGN KEY (run_id) REFERENCES runs(run_id)
      );
      CREATE TABLE IF NOT EXISTS events (
        run_id TEXT NOT NULL,
        event_sequence INTEGER NOT NULL,
        command_id TEXT NOT NULL,
        event_json TEXT NOT NULL,
        before_digest TEXT NOT NULL,
        after_digest TEXT NOT NULL,
        previous_digest TEXT,
        record_digest TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (run_id, event_sequence),
        UNIQUE (run_id, command_id),
        FOREIGN KEY (run_id) REFERENCES runs(run_id)
      );
      CREATE TABLE IF NOT EXISTS snapshots (
        run_id TEXT NOT NULL,
        revision INTEGER NOT NULL,
        command_sequence INTEGER,
        state_json TEXT NOT NULL,
        digest TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (run_id, revision),
        FOREIGN KEY (run_id) REFERENCES runs(run_id)
      );
    `);
  }

  private hasColumn(table: string, column: string): boolean {
    const rows = this.db.prepare(`PRAGMA table_info(${table})`).all() as unknown as Array<{ name: string }>;
    return rows.some((row) => row.name === column);
  }

  private migrateSchema(): void {
    if (!this.hasColumn("commands", "previous_digest")) this.db.exec("ALTER TABLE commands ADD COLUMN previous_digest TEXT");
    if (!this.hasColumn("commands", "record_digest")) this.db.exec("ALTER TABLE commands ADD COLUMN record_digest TEXT");
    if (!this.hasColumn("events", "previous_digest")) this.db.exec("ALTER TABLE events ADD COLUMN previous_digest TEXT");
    if (!this.hasColumn("events", "record_digest")) this.db.exec("ALTER TABLE events ADD COLUMN record_digest TEXT");
    if (!this.hasColumn("snapshots", "command_sequence")) this.db.exec("ALTER TABLE snapshots ADD COLUMN command_sequence INTEGER");
    this.db.exec("UPDATE snapshots SET command_sequence = revision - 1 WHERE command_sequence IS NULL");
  }

  private backfillIntegrityMetadata(): void {
    for (const run of this.listRuns()) {
      let previous = "";
      const commands = this.db.prepare("SELECT * FROM commands WHERE run_id = ? ORDER BY command_sequence").all(run.runId) as unknown as CommandRow[];
      for (const row of commands) {
        if (row.previous_digest === null || row.record_digest === null) {
          const base = { ...row, previous_digest: previous };
          const digest = commandDigest(run.runId, base);
          this.db.prepare("UPDATE commands SET previous_digest = ?, record_digest = ? WHERE run_id = ? AND command_sequence = ?")
            .run(previous, digest, run.runId, row.command_sequence);
          previous = digest;
        } else {
          previous = row.record_digest;
        }
      }
      previous = "";
      const events = this.db.prepare("SELECT * FROM events WHERE run_id = ? ORDER BY event_sequence").all(run.runId) as unknown as EventRow[];
      for (const row of events) {
        if (row.previous_digest === null || row.record_digest === null) {
          const base = { ...row, previous_digest: previous };
          const digest = eventDigest(run.runId, base);
          this.db.prepare("UPDATE events SET previous_digest = ?, record_digest = ? WHERE run_id = ? AND event_sequence = ?")
            .run(previous, digest, run.runId, row.event_sequence);
          previous = digest;
        } else {
          previous = row.record_digest;
        }
      }
    }
  }

  private pruneSnapshots(): void {
    for (const run of this.listRuns()) {
      const latest = this.db.prepare("SELECT MAX(revision) AS revision FROM snapshots WHERE run_id = ?")
        .get(run.runId) as { revision: number | null };
      const terminalRevision = run.status === "running" ? -1 : Number(latest.revision ?? -1);
      this.db.prepare(`DELETE FROM snapshots
        WHERE run_id = ? AND revision != 0 AND (revision % ?) != 0 AND revision != ?`)
        .run(run.runId, this.snapshotInterval, terminalRevision);
    }
  }

  private findRun(runId: string): RunMetadata | null {
    const row = this.db.prepare("SELECT * FROM runs WHERE run_id = ?").get(runId) as RunRow | undefined;
    return row ? metadataFromRow(row) : null;
  }

  getRun(runId = this.activeRunId): RunMetadata {
    const metadata = this.findRun(runId);
    if (!metadata) throw new Error(`unknown run: ${runId}`);
    resolveScenario(metadata.scenarioId, metadata.scenarioVersion);
    resolveRuleset(metadata.rulesetId, metadata.rulesetVersion);
    return metadata;
  }

  listRuns(): RunMetadata[] {
    const rows = this.db.prepare("SELECT * FROM runs ORDER BY created_at, run_id").all() as unknown as RunRow[];
    return rows.map(metadataFromRow);
  }

  setActiveRun(runId: string): void {
    this.getRun(runId);
    this.activeRunId = runId;
  }

  createRun(input: CreateRunInput = {}): RunMetadata {
    try {
      const scenarioId = input.scenarioId ?? "station-zero";
      const scenarioVersion = input.scenarioVersion ?? 1;
      const rulesetId = input.rulesetId ?? "station-zero-core";
      const rulesetVersion = input.rulesetVersion ?? 2;
      const scenario = resolveScenario(scenarioId, scenarioVersion);
      resolveRuleset(rulesetId, rulesetVersion);
      const genesis = input.genesis ?? scenario.create(input.seed);
      assertWorldInvariants(genesis);
      const metadata: RunMetadata = {
        runId: input.runId ?? newRunId(),
        scenarioId,
        scenarioVersion,
        rulesetId,
        rulesetVersion,
        stateSchemaVersion: genesis.schemaVersion,
        seed: genesis.seed,
        status: genesis.mission.status,
        createdAt: new Date().toISOString(),
        createdWithBuild: input.createdWithBuild ?? CURRENT_BUILD,
      };
      this.db.exec("BEGIN IMMEDIATE");
      try {
        this.db.prepare(`INSERT INTO runs
          (run_id, scenario_id, scenario_version, ruleset_id, ruleset_version,
           state_schema_version, seed, status, created_at, created_with_build)
          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`)
          .run(metadata.runId, metadata.scenarioId, metadata.scenarioVersion, metadata.rulesetId,
            metadata.rulesetVersion, metadata.stateSchemaVersion, metadata.seed, metadata.status,
            metadata.createdAt, metadata.createdWithBuild);
        this.persistSnapshot(metadata.runId, genesis, -1);
        this.db.exec("COMMIT");
      } catch (error) {
        this.db.exec("ROLLBACK");
        throw error;
      }
      return metadata;
    } catch (error) {
      mapStorageError(error);
    }
  }

  private persistSnapshot(runId: string, state: WorldState, commandSequence: number): void {
    assertWorldInvariants(state);
    this.db.prepare("INSERT INTO snapshots (run_id, revision, command_sequence, state_json, digest) VALUES (?, ?, ?, ?, ?)")
      .run(runId, state.revision, commandSequence, canonicalJson(state), sha256(state));
  }

  private readSnapshot(runId: string, latest: boolean): SnapshotRow {
    const direction = latest ? "DESC" : "ASC";
    const row = this.db.prepare(`SELECT revision, command_sequence, state_json, digest FROM snapshots
      WHERE run_id = ? ORDER BY revision ${direction} LIMIT 1`).get(runId) as SnapshotRow | undefined;
    if (!row) throw new StorageError("storage_corrupt", `snapshot is missing for run: ${runId}`);
    const state = JSON.parse(row.state_json) as WorldState;
    assertWorldInvariants(state);
    if (sha256(state) !== row.digest) throw new StorageError("storage_corrupt", "snapshot digest mismatch");
    return row;
  }

  verifyStream(runId = this.activeRunId): void {
    this.getRun(runId);
    const commands = this.db.prepare("SELECT * FROM commands WHERE run_id = ? ORDER BY command_sequence").all(runId) as unknown as CommandRow[];
    let previous = "";
    for (const row of commands) {
      if ((row.previous_digest ?? "") !== previous || row.record_digest !== commandDigest(runId, row)) {
        throw new StorageError("storage_corrupt", "command hash chain mismatch");
      }
      previous = row.record_digest;
    }
    const events = this.db.prepare("SELECT * FROM events WHERE run_id = ? ORDER BY event_sequence").all(runId) as unknown as EventRow[];
    previous = "";
    for (const row of events) {
      if ((row.previous_digest ?? "") !== previous || row.record_digest !== eventDigest(runId, row)) {
        throw new StorageError("storage_corrupt", "event hash chain mismatch");
      }
      previous = row.record_digest;
    }
    if (commands.length !== events.length) throw new StorageError("storage_corrupt", "command and event counts diverged");
    for (let index = 0; index < commands.length; index += 1) {
      const command = commands[index];
      const event = events[index];
      if (!command || !event || command.command_sequence !== event.event_sequence || command.command_id !== event.command_id) {
        throw new StorageError("storage_corrupt", "command and event streams are misaligned");
      }
    }
  }

  private replayFromSnapshot(runId: string, snapshot: SnapshotRow, mode: ReplayResult["mode"]): ReplayResult {
    const metadata = this.getRun(runId);
    this.verifyStream(runId);
    let state = JSON.parse(snapshot.state_json) as WorldState;
    const startSequence = Number(snapshot.command_sequence ?? snapshot.revision - 1);
    const rows = this.db.prepare(`SELECT c.command_sequence, c.command_id, c.command_json,
      c.before_digest, c.after_digest, c.previous_digest, c.record_digest, e.event_json
      FROM commands c JOIN events e ON e.run_id = c.run_id AND e.event_sequence = c.command_sequence
      WHERE c.run_id = ? AND c.command_sequence > ? ORDER BY c.command_sequence`)
      .all(runId, startSequence) as unknown as Array<CommandRow & { event_json: string }>;
    const ruleset = resolveRuleset(metadata.rulesetId, metadata.rulesetVersion);
    for (const row of rows) {
      if (sha256(state) !== row.before_digest) throw new StorageError("storage_corrupt", "replay before-digest mismatch");
      const command = JSON.parse(row.command_json) as WorldCommand;
      const replayed = ruleset.applyTick(state, {
        tickId: `tick:${runId}:${state.turn + 1}`,
        expectedWorldRevision: state.revision,
        intents: [{ commandSequence: Number(row.command_sequence), command }],
      });
      if (replayed.status !== "accepted") throw new StorageError("storage_corrupt", `replay command rejected: ${replayed.reason}`);
      const actual = replayed.journalEvents[0];
      if (!actual || actual.event.afterDigest !== row.after_digest) {
        throw new StorageError("storage_corrupt", "replay after-digest mismatch");
      }
      const retained = parseJournalEvent(runId, Number(row.command_sequence), row.event_json);
      if (canonicalJson(actual) !== canonicalJson(retained)) {
        throw new StorageError("storage_corrupt", "replayed event differs from retained event");
      }
      state = replayed.state;
    }
    const digest = sha256(state);
    const latest = this.db.prepare("SELECT after_digest FROM commands WHERE run_id = ? ORDER BY command_sequence DESC LIMIT 1")
      .get(runId) as { after_digest: string } | undefined;
    if (latest && latest.after_digest !== digest) throw new StorageError("storage_corrupt", "terminal command digest mismatch");
    return {
      runId,
      mode,
      state,
      digest,
      eventCount: this.eventCount(runId),
      replayedCommandCount: rows.length,
      snapshotRevision: Number(snapshot.revision),
      verified: true,
    };
  }

  recover(runId = this.activeRunId): ReplayResult {
    try {
      return this.replayFromSnapshot(runId, this.readSnapshot(runId, true), "recovery");
    } catch (error) {
      mapStorageError(error);
    }
  }

  verifyReplay(runId = this.activeRunId): ReplayResult {
    try {
      return this.replayFromSnapshot(runId, this.readSnapshot(runId, false), "verify");
    } catch (error) {
      mapStorageError(error);
    }
  }

  replay(runId = this.activeRunId): ReplayResult {
    return this.verifyReplay(runId);
  }

  loadState(runId = this.activeRunId): WorldState {
    return this.recover(runId).state;
  }

  apply(command: WorldCommand, runId = this.activeRunId): PersistedApplyResult {
    try {
      const metadata = this.getRun(runId);
      const existing = this.db.prepare(`SELECT c.command_sequence, c.command_json, e.event_json
        FROM commands c JOIN events e ON e.run_id = c.run_id AND e.event_sequence = c.command_sequence
        WHERE c.run_id = ? AND c.command_id = ?`).get(runId, command.commandId) as
        { command_sequence: number; command_json: string; event_json: string } | undefined;
      if (existing) {
        if (existing.command_json !== canonicalJson(command)) {
          return {
            idempotent: false,
            runId,
            commandSequence: Number(existing.command_sequence),
            result: { status: "rejected", state: this.loadState(runId), code: "invalid_command",
              reason: "commandId is already bound to a different command in this run" },
          };
        }
        return {
          idempotent: true,
          runId,
          commandSequence: Number(existing.command_sequence),
          result: { status: "accepted", state: this.loadState(runId),
            event: parseJournalEvent(runId, Number(existing.command_sequence), existing.event_json).event },
        };
      }

      this.db.exec("BEGIN IMMEDIATE");
      try {
        const state = this.loadState(runId);
        const sequenceRow = this.db.prepare("SELECT COALESCE(MAX(command_sequence), -1) + 1 AS sequence FROM commands WHERE run_id = ?")
          .get(runId) as { sequence: number };
        const sequence = Number(sequenceRow.sequence);
        const tick = resolveRuleset(metadata.rulesetId, metadata.rulesetVersion).applyTick(state, {
          tickId: `tick:${runId}:${state.turn + 1}`,
          expectedWorldRevision: state.revision,
          intents: [{ commandSequence: sequence, command }],
        });
        if (tick.status === "rejected") {
          this.db.exec("ROLLBACK");
          return { result: tick as ApplyResult, idempotent: false, runId, commandSequence: sequence };
        }
        const journalEvent = tick.journalEvents[0];
        if (!journalEvent) throw new Error("accepted tick produced no journal event");
        const result: Extract<ApplyResult, { status: "accepted" }> = {
          status: "accepted",
          state: tick.state,
          event: journalEvent.event,
        };

        const previousCommand = this.db.prepare("SELECT record_digest FROM commands WHERE run_id = ? ORDER BY command_sequence DESC LIMIT 1")
          .get(runId) as { record_digest: string } | undefined;
        const commandBase: Omit<CommandRow, "record_digest"> = {
          command_sequence: sequence,
          command_id: command.commandId,
          command_json: canonicalJson(command),
          before_digest: result.event.beforeDigest,
          after_digest: result.event.afterDigest,
          previous_digest: previousCommand?.record_digest ?? "",
        };
        const commandRecordDigest = commandDigest(runId, commandBase);
        this.db.prepare(`INSERT INTO commands
          (run_id, command_sequence, command_id, command_json, before_digest, after_digest, previous_digest, record_digest)
          VALUES (?, ?, ?, ?, ?, ?, ?, ?)`)
          .run(runId, sequence, command.commandId, commandBase.command_json, commandBase.before_digest,
            commandBase.after_digest, commandBase.previous_digest, commandRecordDigest);

        const previousEvent = this.db.prepare("SELECT record_digest FROM events WHERE run_id = ? ORDER BY event_sequence DESC LIMIT 1")
          .get(runId) as { record_digest: string } | undefined;
        const eventBase: Omit<EventRow, "record_digest"> = {
          event_sequence: sequence,
          command_id: command.commandId,
          event_json: canonicalJson(journalEvent),
          before_digest: result.event.beforeDigest,
          after_digest: result.event.afterDigest,
          previous_digest: previousEvent?.record_digest ?? "",
        };
        const eventRecordDigest = eventDigest(runId, eventBase);
        this.db.prepare(`INSERT INTO events
          (run_id, event_sequence, command_id, event_json, before_digest, after_digest, previous_digest, record_digest)
          VALUES (?, ?, ?, ?, ?, ?, ?, ?)`)
          .run(runId, sequence, command.commandId, eventBase.event_json, eventBase.before_digest,
            eventBase.after_digest, eventBase.previous_digest, eventRecordDigest);

        const shouldSnapshot = result.state.revision % this.snapshotInterval === 0 || result.state.mission.status !== "running";
        if (shouldSnapshot) this.persistSnapshot(runId, result.state, sequence);
        this.db.prepare("UPDATE runs SET status = ? WHERE run_id = ?").run(result.state.mission.status, runId);
        this.db.exec("COMMIT");
        return { result, idempotent: false, runId, commandSequence: sequence };
      } catch (error) {
        this.db.exec("ROLLBACK");
        throw error;
      }
    } catch (error) {
      mapStorageError(error);
    }
  }

  journalEvents(runId = this.activeRunId): JournalEvent[] {
    this.getRun(runId);
    const rows = this.db.prepare("SELECT event_sequence, event_json FROM events WHERE run_id = ? ORDER BY event_sequence")
      .all(runId) as unknown as Array<{ event_sequence: number; event_json: string }>;
    return rows.map((row) => parseJournalEvent(runId, Number(row.event_sequence), row.event_json));
  }

  recentJournalEvents(limit = 8, runId = this.activeRunId): JournalEvent[] {
    if (!Number.isSafeInteger(limit) || limit < 1) throw new TypeError("limit must be positive");
    this.getRun(runId);
    const rows = this.db.prepare("SELECT event_sequence, event_json FROM events WHERE run_id = ? ORDER BY event_sequence DESC LIMIT ?")
      .all(runId, limit) as unknown as Array<{ event_sequence: number; event_json: string }>;
    return rows.reverse().map((row) => parseJournalEvent(runId, Number(row.event_sequence), row.event_json));
  }

  events(runId = this.activeRunId): WorldEvent[] {
    return this.journalEvents(runId).map((record) => record.event);
  }

  eventCount(runId = this.activeRunId): number {
    const row = this.db.prepare("SELECT COUNT(*) AS count FROM events WHERE run_id = ?").get(runId) as { count: number };
    return Number(row.count);
  }

  snapshotCount(runId = this.activeRunId): number {
    const row = this.db.prepare("SELECT COUNT(*) AS count FROM snapshots WHERE run_id = ?").get(runId) as { count: number };
    return Number(row.count);
  }

  close(): void {
    this.db.close();
  }
}
