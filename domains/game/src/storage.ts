import { mkdirSync } from "node:fs";
import { dirname } from "node:path";
import { DatabaseSync } from "node:sqlite";

import { canonicalJson, sha256 } from "./digest.ts";
import type { ApplyResult, JournalEvent, PrimitiveWorldCommand, TickBatch, WorldCommand, WorldEvent, WorldState } from "./model.ts";
import { RULESET_VERSION, SCENARIO_VERSION, resolveRuleset, resolveScenario } from "./registry.ts";
import type { PointInTimeReplayResult } from "./replay/model.ts";
import { CURRENT_BUILD, CURRENT_INPUTS_DIGEST } from "./build.ts";
import {
  DEFAULT_RUN_ID,
  newRunId,
  type CreateRunInput,
  type RunMetadata,
} from "./run.ts";
import { assertWorldInvariants } from "./scenario.ts";

export const DEFAULT_SNAPSHOT_INTERVAL = 8;
function currentEvaluatedInputsDigest(): string {
  return CURRENT_INPUTS_DIGEST;
}
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
  previous_digest: string;
  record_digest: string;
}

interface EventRow {
  event_sequence: number;
  command_id: string;
  event_json: string;
  before_digest: string;
  after_digest: string;
  previous_digest: string;
  record_digest: string;
}

interface SnapshotRow {
  revision: number;
  command_sequence: number;
  state_json: string;
  digest: string;
}

interface RunRow {
  run_id: string;
  scenario_id: string;
  scenario_version: number;
  scenario_case_id: string;
  ruleset_id: string;
  ruleset_version: number;
  state_schema_version: number;
  seed: string;
  genesis_digest: string;
  evaluated_inputs_digest: string;
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

export type StorageFaultPoint =
  | "before_begin"
  | "after_begin"
  | "before_command_insert"
  | "after_command_insert"
  | "after_event_insert"
  | "before_snapshot"
  | "after_snapshot"
  | "before_commit"
  | "after_commit";

export interface StoreOptions {
  activeRunId?: string;
  snapshotInterval?: number;
  busyTimeoutMs?: number;
  faultInjector?: (point: StorageFaultPoint) => void;
}

function metadataFromRow(row: RunRow): RunMetadata {
  return {
    runId: row.run_id,
    scenarioId: row.scenario_id,
    scenarioVersion: Number(row.scenario_version),
    scenarioCaseId: row.scenario_case_id,
    rulesetId: row.ruleset_id,
    rulesetVersion: Number(row.ruleset_version),
    stateSchemaVersion: Number(row.state_schema_version),
    seed: row.seed,
    genesisDigest: row.genesis_digest,
    evaluatedInputsDigest: row.evaluated_inputs_digest,
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
  if (code.includes("CONSTRAINT") || message.includes("constraint failed")) {
    throw new StorageError("storage_constraint", "storage constraint rejected the write", { cause: error });
  }
  if (
    code.includes("CORRUPT") ||
    code.includes("NOTADB") ||
    message.includes("file is not a database") ||
    message.includes("database disk image is malformed")
  ) {
    throw new StorageError("storage_corrupt", "storage is corrupt", { cause: error });
  }
  throw error;
}

function parseStoredJson<T>(json: string, label: string): T {
  try {
    return JSON.parse(json) as T;
  } catch (error) {
    throw new StorageError("storage_corrupt", `${label} JSON is invalid`, { cause: error });
  }
}

function parseStoredWorldState(json: string, label: string): WorldState {
  try {
    const state = parseStoredJson<WorldState>(json, label);
    assertWorldInvariants(state);
    return state;
  } catch (error) {
    if (error instanceof StorageError) throw error;
    throw new StorageError("storage_corrupt", `${label} World state is invalid`, { cause: error });
  }
}

function parseJournalEvent(_runId: string, _sequence: number, json: string): JournalEvent {
  const parsed = parseStoredJson<JournalEvent>(json, "retained Event");
  if (!parsed || typeof parsed !== "object" || !("event" in parsed) || !parsed.event || typeof parsed.event !== "object") {
    throw new StorageError("storage_corrupt", "retained Event envelope is invalid");
  }
  return parsed;
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
    previousDigest: row.previous_digest,
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
    previousDigest: row.previous_digest,
  });
}

export class GameStore {
  readonly db: DatabaseSync;
  readonly dbPath: string;
  readonly snapshotInterval: number;
  readonly faultInjector: ((point: StorageFaultPoint) => void) | undefined;
  activeRunId: string;

  constructor(dbPath: string, options: StoreOptions | string = {}) {
    const normalized = typeof options === "string" ? { activeRunId: options } : options;
    this.dbPath = dbPath;
    this.activeRunId = normalized.activeRunId ?? DEFAULT_RUN_ID;
    this.snapshotInterval = normalized.snapshotInterval ?? DEFAULT_SNAPSHOT_INTERVAL;
    this.faultInjector = normalized.faultInjector;
    if (!Number.isSafeInteger(this.snapshotInterval) || this.snapshotInterval < 1) {
      throw new TypeError("snapshotInterval must be a positive integer");
    }
    if (dbPath !== ":memory:") mkdirSync(dirname(dbPath), { recursive: true });
    this.db = new DatabaseSync(dbPath);

    try {
      this.db.exec(`PRAGMA busy_timeout = ${normalized.busyTimeoutMs ?? 5000};`);
      this.db.exec(`
        PRAGMA foreign_keys = ON;
        PRAGMA journal_mode = WAL;
        PRAGMA synchronous = FULL;
      `);
      this.createSchema();
      this.pruneSnapshots();
      if (this.listRuns().length === 0) this.createRun({ runId: this.activeRunId });
      if (!this.findRun(this.activeRunId)) this.activeRunId = this.listRuns()[0]?.runId ?? this.activeRunId;
      this.recover(this.activeRunId);
    } catch (error) {
      mapStorageError(error);
    }
  }

  private inject(point: StorageFaultPoint): void {
    this.faultInjector?.(point);
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
      CREATE TABLE IF NOT EXISTS commands (
        run_id TEXT NOT NULL,
        command_sequence INTEGER NOT NULL,
        command_id TEXT NOT NULL,
        command_json TEXT NOT NULL,
        before_digest TEXT NOT NULL,
        after_digest TEXT NOT NULL,
        previous_digest TEXT NOT NULL,
        record_digest TEXT NOT NULL,
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
        previous_digest TEXT NOT NULL,
        record_digest TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (run_id, event_sequence),
        UNIQUE (run_id, command_id),
        FOREIGN KEY (run_id) REFERENCES runs(run_id)
      );
      CREATE TABLE IF NOT EXISTS snapshots (
        run_id TEXT NOT NULL,
        revision INTEGER NOT NULL,
        command_sequence INTEGER NOT NULL,
        state_json TEXT NOT NULL,
        digest TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (run_id, revision),
        FOREIGN KEY (run_id) REFERENCES runs(run_id)
      );
    `);
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
      const scenarioVersion = input.scenarioVersion ?? SCENARIO_VERSION;
      const rulesetId = input.rulesetId ?? "station-zero-core";
      const rulesetVersion = input.rulesetVersion ?? RULESET_VERSION;
      const scenario = resolveScenario(scenarioId, scenarioVersion);
      resolveRuleset(rulesetId, rulesetVersion);
      if (input.genesis && input.scenarioCaseId && input.scenarioCaseId !== "custom-genesis") {
        throw new TypeError("custom Genesis must use scenarioCaseId custom-genesis");
      }
      const scenarioCaseId = input.scenarioCaseId ?? (input.genesis ? "custom-genesis" : scenario.defaultCaseId);
      const genesis = input.genesis ?? scenario.create({ caseId: scenarioCaseId, ...(input.seed ? { seed: input.seed } : {}) });
      assertWorldInvariants(genesis);
      const genesisDigest = sha256(genesis);
      const evaluatedInputsDigest = input.evaluatedInputsDigest ?? currentEvaluatedInputsDigest();
      const metadata: RunMetadata = {
        runId: input.runId ?? newRunId(),
        scenarioId,
        scenarioVersion,
        scenarioCaseId,
        rulesetId,
        rulesetVersion,
        stateSchemaVersion: genesis.schemaVersion,
        seed: genesis.seed,
        genesisDigest,
        evaluatedInputsDigest,
        status: genesis.mission.status,
        createdAt: new Date().toISOString(),
        createdWithBuild: input.createdWithBuild ?? CURRENT_BUILD,
      };
      this.db.exec("BEGIN IMMEDIATE");
      try {
        this.db.prepare(`INSERT INTO runs
          (run_id, scenario_id, scenario_version, scenario_case_id, ruleset_id, ruleset_version,
           state_schema_version, seed, genesis_digest, evaluated_inputs_digest, status, created_at, created_with_build)
          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`)
          .run(metadata.runId, metadata.scenarioId, metadata.scenarioVersion, metadata.scenarioCaseId, metadata.rulesetId,
            metadata.rulesetVersion, metadata.stateSchemaVersion, metadata.seed, metadata.genesisDigest,
            metadata.evaluatedInputsDigest, metadata.status, metadata.createdAt, metadata.createdWithBuild);
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
    return row;
  }

  private readSnapshotAtOrBefore(runId: string, revision: number): SnapshotRow {
    const row = this.db.prepare(`SELECT revision, command_sequence, state_json, digest FROM snapshots
      WHERE run_id = ? AND revision <= ? ORDER BY revision DESC LIMIT 1`).get(runId, revision) as SnapshotRow | undefined;
    if (!row) throw new StorageError("storage_corrupt", `snapshot is missing at or before revision ${revision}`);
    return row;
  }

  private snapshotState(runId: string, snapshot: SnapshotRow, metadata: RunMetadata): WorldState {
    const state = parseStoredWorldState(snapshot.state_json, "Snapshot");
    if (sha256(state) !== snapshot.digest) {
      throw new StorageError("storage_corrupt", "Snapshot digest mismatch");
    }
    const revision = Number(snapshot.revision);
    const commandSequence = Number(snapshot.command_sequence ?? revision - 1);
    if (state.revision !== revision) {
      throw new StorageError("storage_corrupt", "Snapshot revision differs from retained World state");
    }
    if (commandSequence !== revision - 1) {
      throw new StorageError("storage_corrupt", "Snapshot command sequence does not match its revision");
    }
    if (revision === 0) {
      if (snapshot.digest !== metadata.genesisDigest) {
        throw new StorageError("storage_corrupt", "Genesis Snapshot digest differs from Run metadata");
      }
      return state;
    }
    const command = this.db.prepare("SELECT after_digest FROM commands WHERE run_id = ? AND command_sequence = ?")
      .get(runId, commandSequence) as { after_digest: string } | undefined;
    if (!command || command.after_digest !== snapshot.digest) {
      throw new StorageError("storage_corrupt", "Snapshot digest is not anchored to its retained Command");
    }
    return state;
  }

  verifyStream(runId = this.activeRunId): void {
    this.getRun(runId);
    const commands = this.db.prepare("SELECT * FROM commands WHERE run_id = ? ORDER BY command_sequence").all(runId) as unknown as CommandRow[];
    let previous = "";
    for (let index = 0; index < commands.length; index += 1) {
      const row = commands[index];
      if (!row || Number(row.command_sequence) !== index) {
        throw new StorageError("storage_corrupt", "command sequence is not contiguous");
      }
      if ((row.previous_digest ?? "") !== previous || row.record_digest !== commandDigest(runId, row)) {
        throw new StorageError("storage_corrupt", "command hash chain mismatch");
      }
      previous = row.record_digest;
    }
    const events = this.db.prepare("SELECT * FROM events WHERE run_id = ? ORDER BY event_sequence").all(runId) as unknown as EventRow[];
    previous = "";
    for (let index = 0; index < events.length; index += 1) {
      const row = events[index];
      if (!row || Number(row.event_sequence) !== index) {
        throw new StorageError("storage_corrupt", "event sequence is not contiguous");
      }
      if ((row.previous_digest ?? "") !== previous || row.record_digest !== eventDigest(runId, row)) {
        throw new StorageError("storage_corrupt", "event hash chain mismatch");
      }
      previous = row.record_digest;
    }
    if (commands.length !== events.length) throw new StorageError("storage_corrupt", "command and event counts diverged");
    for (let index = 0; index < commands.length; index += 1) {
      const command = commands[index];
      const event = events[index];
      if (
        !command ||
        !event ||
        command.command_sequence !== event.event_sequence ||
        command.command_id !== event.command_id ||
        command.before_digest !== event.before_digest ||
        command.after_digest !== event.after_digest
      ) {
        throw new StorageError("storage_corrupt", "command and event streams are misaligned");
      }
      const retainedCommand = parseStoredJson<WorldCommand>(command.command_json, "retained Command");
      const retainedEvent = parseJournalEvent(runId, index, event.event_json);
      const eventBindsCommand = retainedEvent.event.commandId === event.command_id || (
        retainedEvent.event.commandKind === "team_tick" &&
        retainedEvent.event.intentReceipts?.some((receipt) => receipt.commandId === event.command_id) === true
      );
      if (
        !retainedCommand ||
        typeof retainedCommand !== "object" ||
        retainedCommand.commandId !== command.command_id ||
        retainedEvent.commandSequence !== index ||
        retainedEvent.worldRevision !== retainedEvent.event.worldRevision ||
        !eventBindsCommand ||
        retainedEvent.event.beforeDigest !== event.before_digest ||
        retainedEvent.event.afterDigest !== event.after_digest
      ) {
        throw new StorageError("storage_corrupt", "retained Command or Event identity is inconsistent");
      }
    }
  }

  private replayStateFromSnapshot(
    runId: string,
    snapshot: SnapshotRow,
    targetRevision?: number,
    streamVerified = false,
  ): PointInTimeReplayResult {
    const metadata = this.getRun(runId);
    if (!streamVerified) this.verifyStream(runId);
    const terminalRevision = this.eventCount(runId);
    const revision = targetRevision ?? terminalRevision;
    if (!Number.isSafeInteger(revision) || revision < 0 || revision > terminalRevision) {
      throw new TypeError(`revision must be an integer from 0 to ${terminalRevision}`);
    }
    if (Number(snapshot.revision) > revision) {
      throw new StorageError("storage_corrupt", "selected Snapshot is newer than the target revision");
    }
    let state = this.snapshotState(runId, snapshot, metadata);
    const startSequence = Number(snapshot.command_sequence ?? snapshot.revision - 1);
    const rows = this.db.prepare(`SELECT c.command_sequence, c.command_id, c.command_json,
      c.before_digest, c.after_digest, c.previous_digest, c.record_digest, e.event_json
      FROM commands c JOIN events e ON e.run_id = c.run_id AND e.event_sequence = c.command_sequence
      WHERE c.run_id = ? AND c.command_sequence > ? AND c.command_sequence < ? ORDER BY c.command_sequence`)
      .all(runId, startSequence, revision) as unknown as Array<CommandRow & { event_json: string }>;
    const ruleset = resolveRuleset(metadata.rulesetId, metadata.rulesetVersion);
    for (const row of rows) {
      if (sha256(state) !== row.before_digest) throw new StorageError("storage_corrupt", "replay before-digest mismatch");
      const command = parseStoredJson<WorldCommand>(row.command_json, "retained Command");
      let replayed;
      try {
        replayed = ruleset.applyTick(state, {
          tickId: `tick:${runId}:${state.turn + 1}`,
          expectedWorldRevision: state.revision,
          intents: [{ commandSequence: Number(row.command_sequence), command }],
        });
      } catch (error) {
        throw new StorageError("storage_corrupt", "retained Command cannot be replayed", { cause: error });
      }
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
    if (state.revision !== revision) {
      throw new StorageError("storage_corrupt", "replay did not reach the requested revision");
    }
    const digest = sha256(state);
    const expectedDigest = revision === 0
      ? metadata.genesisDigest
      : (this.db.prepare("SELECT after_digest FROM commands WHERE run_id = ? AND command_sequence = ?")
          .get(runId, revision - 1) as { after_digest?: string } | undefined)?.after_digest;
    if (!expectedDigest || expectedDigest !== digest) {
      throw new StorageError("storage_corrupt", "point-in-time digest differs from retained evidence");
    }
    return {
      runId,
      revision,
      state,
      digest,
      replayedCommandCount: rows.length,
      snapshotRevision: Number(snapshot.revision),
      verified: true,
    };
  }

  recover(runId = this.activeRunId): ReplayResult {
    try {
      this.getRun(runId);
      const replay = this.replayStateFromSnapshot(runId, this.readSnapshot(runId, true));
      return {
        runId: replay.runId,
        mode: "recovery",
        state: replay.state,
        digest: replay.digest,
        eventCount: this.eventCount(runId),
        replayedCommandCount: replay.replayedCommandCount,
        snapshotRevision: replay.snapshotRevision,
        verified: true,
      };
    } catch (error) {
      mapStorageError(error);
    }
  }

  verifyReplay(runId = this.activeRunId): ReplayResult {
    try {
      this.getRun(runId);
      const replay = this.replayStateFromSnapshot(runId, this.readSnapshot(runId, false));
      return {
        runId: replay.runId,
        mode: "verify",
        state: replay.state,
        digest: replay.digest,
        eventCount: this.eventCount(runId),
        replayedCommandCount: replay.replayedCommandCount,
        snapshotRevision: replay.snapshotRevision,
        verified: true,
      };
    } catch (error) {
      mapStorageError(error);
    }
  }

  stateAtRevision(revision: number, runId = this.activeRunId): PointInTimeReplayResult {
    try {
      if (!Number.isSafeInteger(revision) || revision < 0) {
        throw new TypeError("revision must be a non-negative integer");
      }
      this.getRun(runId);
      return this.replayStateFromSnapshot(runId, this.readSnapshotAtOrBefore(runId, revision), revision);
    } catch (error) {
      mapStorageError(error);
    }
  }

  statesAtEveryRevision(runId = this.activeRunId): PointInTimeReplayResult[] {
    try {
      this.getRun(runId);
      this.verifyStream(runId);
      const terminalRevision = this.eventCount(runId);
      return Array.from(
        { length: terminalRevision + 1 },
        (_, revision) => this.replayStateFromSnapshot(
          runId,
          this.readSnapshotAtOrBefore(runId, revision),
          revision,
          true,
        ),
      );
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

  applyTeamTick(batch: TickBatch, runId = this.activeRunId): PersistedApplyResult {
    const metadata = this.getRun(runId);
    if (metadata.rulesetVersion < 3) {
      return {
        idempotent: false,
        runId,
        commandSequence: this.eventCount(runId),
        result: {
          status: "rejected",
          state: this.loadState(runId),
          code: "invalid_command",
          reason: "multi-Actor TickBatch requires station-zero-core@3",
        },
      };
    }
    const commands: PrimitiveWorldCommand[] = [];
    for (const intent of batch.intents) {
      if (intent.command.kind === "team_tick") {
        return {
          idempotent: false,
          runId,
          commandSequence: this.eventCount(runId),
          result: {
            status: "rejected",
            state: this.loadState(runId),
            code: "invalid_command",
            reason: "nested team_tick is invalid",
          },
        };
      }
      commands.push(intent.command);
    }
    const command: WorldCommand = {
      kind: "team_tick",
      commandId: `team-tick:${batch.tickId}`,
      actorId: "team-coordinator",
      expectedRevision: batch.expectedWorldRevision,
      tickId: batch.tickId,
      intents: commands,
    };
    return this.apply(command, runId);
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

      this.inject("before_begin");
      this.db.exec("BEGIN IMMEDIATE");
      this.inject("after_begin");
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
        this.inject("before_command_insert");
        this.db.prepare(`INSERT INTO commands
          (run_id, command_sequence, command_id, command_json, before_digest, after_digest, previous_digest, record_digest)
          VALUES (?, ?, ?, ?, ?, ?, ?, ?)`)
          .run(runId, sequence, command.commandId, commandBase.command_json, commandBase.before_digest,
            commandBase.after_digest, commandBase.previous_digest, commandRecordDigest);
        this.inject("after_command_insert");

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
        this.inject("after_event_insert");

        const shouldSnapshot = result.state.revision % this.snapshotInterval === 0 || result.state.mission.status !== "running";
        if (shouldSnapshot) {
          this.inject("before_snapshot");
          this.persistSnapshot(runId, result.state, sequence);
          this.inject("after_snapshot");
        }
        this.db.prepare("UPDATE runs SET status = ? WHERE run_id = ?").run(result.state.mission.status, runId);
        this.inject("before_commit");
        this.db.exec("COMMIT");
        this.inject("after_commit");
        return { result, idempotent: false, runId, commandSequence: sequence };
      } catch (error) {
        try { this.db.exec("ROLLBACK"); } catch {}
        throw error;
      }
    } catch (error) {
      mapStorageError(error);
    }
  }


  commandReceipt(commandId: string, runId = this.activeRunId): {
    commandSequence: number;
    command: WorldCommand;
    journalEvent: JournalEvent;
  } | null {
    this.getRun(runId);
    const row = this.db.prepare(`SELECT c.command_sequence, c.command_json, e.event_json
      FROM commands c JOIN events e
        ON e.run_id = c.run_id AND e.event_sequence = c.command_sequence
      WHERE c.run_id = ? AND c.command_id = ?`)
      .get(runId, commandId) as
      { command_sequence: number; command_json: string; event_json: string } | undefined;
    if (!row) return null;
    const sequence = Number(row.command_sequence);
    return {
      commandSequence: sequence,
      command: JSON.parse(row.command_json) as WorldCommand,
      journalEvent: parseJournalEvent(runId, sequence, row.event_json),
    };
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
