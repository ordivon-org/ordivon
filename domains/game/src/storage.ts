import { mkdirSync } from "node:fs";
import { dirname } from "node:path";
import { DatabaseSync } from "node:sqlite";

import { canonicalJson, sha256 } from "./digest.ts";
import type { ApplyResult, WorldCommand, WorldEvent, WorldState } from "./model.ts";
import { resolveRuleset, resolveScenario } from "./registry.ts";
import {
  CURRENT_BUILD,
  DEFAULT_RUN_ID,
  newRunId,
  type CreateRunInput,
  type RunMetadata,
} from "./run.ts";
import { assertWorldInvariants } from "./scenario.ts";

interface EventRow {
  command_json: string;
  event_json: string;
  before_digest: string;
  after_digest: string;
}

interface SnapshotRow {
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
  state: WorldState;
  digest: string;
  eventCount: number;
  verified: true;
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

export class GameStore {
  readonly db: DatabaseSync;
  readonly dbPath: string;
  activeRunId: string;

  constructor(dbPath: string, activeRunId = DEFAULT_RUN_ID) {
    this.dbPath = dbPath;
    this.activeRunId = activeRunId;
    if (dbPath !== ":memory:") mkdirSync(dirname(dbPath), { recursive: true });

    this.db = new DatabaseSync(dbPath);
    this.db.exec("PRAGMA foreign_keys = ON; PRAGMA journal_mode = WAL; PRAGMA synchronous = FULL;");
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
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (run_id, event_sequence),
        UNIQUE (run_id, command_id),
        FOREIGN KEY (run_id) REFERENCES runs(run_id)
      );

      CREATE TABLE IF NOT EXISTS snapshots (
        run_id TEXT NOT NULL,
        revision INTEGER NOT NULL,
        state_json TEXT NOT NULL,
        digest TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (run_id, revision),
        FOREIGN KEY (run_id) REFERENCES runs(run_id)
      );
    `);

    if (this.listRuns().length === 0) this.createRun({ runId: activeRunId });
    if (!this.findRun(activeRunId)) this.activeRunId = this.listRuns()[0]?.runId ?? activeRunId;
    this.loadState(this.activeRunId);
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
    const rows = this.db.prepare("SELECT * FROM runs ORDER BY created_at ASC, run_id ASC").all() as unknown as RunRow[];
    return rows.map(metadataFromRow);
  }

  setActiveRun(runId: string): void {
    this.getRun(runId);
    this.activeRunId = runId;
  }

  createRun(input: CreateRunInput = {}): RunMetadata {
    const scenarioId = input.scenarioId ?? "station-zero";
    const scenarioVersion = input.scenarioVersion ?? 1;
    const rulesetId = input.rulesetId ?? "station-zero-core";
    const rulesetVersion = input.rulesetVersion ?? 1;
    const scenario = resolveScenario(scenarioId, scenarioVersion);
    resolveRuleset(rulesetId, rulesetVersion);
    const genesis = input.genesis ?? scenario.create(input.seed);
    assertWorldInvariants(genesis);
    const runId = input.runId ?? newRunId();
    const createdAt = new Date().toISOString();
    const metadata: RunMetadata = {
      runId,
      scenarioId,
      scenarioVersion,
      rulesetId,
      rulesetVersion,
      stateSchemaVersion: genesis.schemaVersion,
      seed: genesis.seed,
      status: genesis.mission.status,
      createdAt,
      createdWithBuild: input.createdWithBuild ?? CURRENT_BUILD,
    };

    this.db.exec("BEGIN IMMEDIATE");
    try {
      this.db
        .prepare(`INSERT INTO runs
          (run_id, scenario_id, scenario_version, ruleset_id, ruleset_version,
           state_schema_version, seed, status, created_at, created_with_build)
          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`)
        .run(
          metadata.runId,
          metadata.scenarioId,
          metadata.scenarioVersion,
          metadata.rulesetId,
          metadata.rulesetVersion,
          metadata.stateSchemaVersion,
          metadata.seed,
          metadata.status,
          metadata.createdAt,
          metadata.createdWithBuild,
        );
      this.persistSnapshot(metadata.runId, genesis);
      this.db.exec("COMMIT");
    } catch (error) {
      this.db.exec("ROLLBACK");
      throw error;
    }
    return metadata;
  }

  private persistSnapshot(runId: string, state: WorldState): void {
    assertWorldInvariants(state);
    this.db
      .prepare("INSERT INTO snapshots (run_id, revision, state_json, digest) VALUES (?, ?, ?, ?)")
      .run(runId, state.revision, canonicalJson(state), sha256(state));
  }

  loadState(runId = this.activeRunId): WorldState {
    const metadata = this.getRun(runId);
    const row = this.db
      .prepare("SELECT state_json, digest FROM snapshots WHERE run_id = ? ORDER BY revision DESC LIMIT 1")
      .get(runId) as SnapshotRow | undefined;
    if (!row) throw new Error(`world state is missing for run: ${runId}`);
    const state = JSON.parse(row.state_json) as WorldState;
    if (state.schemaVersion !== metadata.stateSchemaVersion) {
      throw new Error(`state schema mismatch for run ${runId}`);
    }
    assertWorldInvariants(state);
    const actualDigest = sha256(state);
    if (actualDigest !== row.digest) {
      throw new Error(`snapshot digest mismatch: expected ${row.digest}, got ${actualDigest}`);
    }
    return state;
  }

  apply(command: WorldCommand, runId = this.activeRunId): PersistedApplyResult {
    const metadata = this.getRun(runId);
    const existing = this.db
      .prepare(`SELECT c.command_sequence, c.command_json, e.event_json, c.before_digest, c.after_digest
        FROM commands c JOIN events e
          ON e.run_id = c.run_id AND e.event_sequence = c.command_sequence
        WHERE c.run_id = ? AND c.command_id = ?`)
      .get(runId, command.commandId) as (EventRow & { command_sequence: number }) | undefined;

    if (existing) {
      if (existing.command_json !== canonicalJson(command)) {
        return {
          idempotent: false,
          runId,
          commandSequence: Number(existing.command_sequence),
          result: {
            status: "rejected",
            state: this.loadState(runId),
            code: "invalid_command",
            reason: "commandId is already bound to a different command in this run",
          },
        };
      }
      return {
        idempotent: true,
        runId,
        commandSequence: Number(existing.command_sequence),
        result: {
          status: "accepted",
          state: this.loadState(runId),
          event: JSON.parse(existing.event_json) as WorldEvent,
        },
      };
    }

    this.db.exec("BEGIN IMMEDIATE");
    try {
      const state = this.loadState(runId);
      const result = resolveRuleset(metadata.rulesetId, metadata.rulesetVersion).apply(state, command);
      if (result.status === "rejected") {
        this.db.exec("ROLLBACK");
        return { result, idempotent: false, runId, commandSequence: this.eventCount(runId) };
      }
      const row = this.db
        .prepare("SELECT COALESCE(MAX(command_sequence), -1) + 1 AS sequence FROM commands WHERE run_id = ?")
        .get(runId) as { sequence: number };
      const sequence = Number(row.sequence);
      this.db
        .prepare(`INSERT INTO commands
          (run_id, command_sequence, command_id, command_json, before_digest, after_digest)
          VALUES (?, ?, ?, ?, ?, ?)`)
        .run(
          runId,
          sequence,
          command.commandId,
          canonicalJson(command),
          result.event.beforeDigest,
          result.event.afterDigest,
        );
      this.db
        .prepare(`INSERT INTO events
          (run_id, event_sequence, command_id, event_json, before_digest, after_digest)
          VALUES (?, ?, ?, ?, ?, ?)`)
        .run(
          runId,
          sequence,
          command.commandId,
          canonicalJson(result.event),
          result.event.beforeDigest,
          result.event.afterDigest,
        );
      this.persistSnapshot(runId, result.state);
      this.db.prepare("UPDATE runs SET status = ? WHERE run_id = ?").run(result.state.mission.status, runId);
      this.db.exec("COMMIT");
      return { result, idempotent: false, runId, commandSequence: sequence };
    } catch (error) {
      this.db.exec("ROLLBACK");
      throw error;
    }
  }

  events(runId = this.activeRunId): WorldEvent[] {
    this.getRun(runId);
    const rows = this.db
      .prepare("SELECT event_json FROM events WHERE run_id = ? ORDER BY event_sequence ASC")
      .all(runId) as unknown as Array<{ event_json: string }>;
    return rows.map((row) => JSON.parse(row.event_json) as WorldEvent);
  }

  replay(runId = this.activeRunId): ReplayResult {
    const metadata = this.getRun(runId);
    const genesisRow = this.db
      .prepare("SELECT state_json, digest FROM snapshots WHERE run_id = ? ORDER BY revision ASC LIMIT 1")
      .get(runId) as SnapshotRow | undefined;
    if (!genesisRow) throw new Error("genesis snapshot is missing");
    let state = JSON.parse(genesisRow.state_json) as WorldState;
    assertWorldInvariants(state);
    if (sha256(state) !== genesisRow.digest) throw new Error("genesis snapshot digest mismatch");

    const rows = this.db
      .prepare(`SELECT c.command_json, e.event_json, c.before_digest, c.after_digest
        FROM commands c JOIN events e
          ON e.run_id = c.run_id AND e.event_sequence = c.command_sequence
        WHERE c.run_id = ? ORDER BY c.command_sequence ASC`)
      .all(runId) as unknown as EventRow[];
    const ruleset = resolveRuleset(metadata.rulesetId, metadata.rulesetVersion);
    for (const row of rows) {
      if (sha256(state) !== row.before_digest) throw new Error("replay before-digest mismatch");
      const command = JSON.parse(row.command_json) as WorldCommand;
      const replayed = ruleset.apply(state, command);
      if (replayed.status !== "accepted") throw new Error(`replay command rejected: ${replayed.reason}`);
      if (replayed.event.afterDigest !== row.after_digest) throw new Error("replay after-digest mismatch");
      if (canonicalJson(replayed.event) !== row.event_json) throw new Error("replayed event differs from retained event");
      state = replayed.state;
    }

    const current = this.loadState(runId);
    const replayDigest = sha256(state);
    if (replayDigest !== sha256(current)) throw new Error("replay terminal state differs from persisted state");
    return { runId, state, digest: replayDigest, eventCount: rows.length, verified: true };
  }

  eventCount(runId = this.activeRunId): number {
    const row = this.db
      .prepare("SELECT COUNT(*) AS count FROM events WHERE run_id = ?")
      .get(runId) as { count: number };
    return Number(row.count);
  }

  close(): void {
    this.db.close();
  }
}
