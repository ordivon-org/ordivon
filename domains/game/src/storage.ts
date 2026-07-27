import { mkdirSync } from "node:fs";
import { dirname } from "node:path";
import { DatabaseSync } from "node:sqlite";

import { canonicalJson, sha256 } from "./digest.ts";
import type { ApplyResult, WorldCommand, WorldEvent, WorldState } from "./model.ts";
import { assertWorldInvariants, initialWorld } from "./scenario.ts";
import { applyWorldCommand } from "./world.ts";

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

export interface PersistedApplyResult {
  result: ApplyResult;
  idempotent: boolean;
}

export interface ReplayResult {
  state: WorldState;
  digest: string;
  eventCount: number;
  verified: true;
}

export class GameStore {
  readonly db: DatabaseSync;
  readonly dbPath: string;

  constructor(dbPath: string, genesis: WorldState = initialWorld()) {
    this.dbPath = dbPath;
    if (dbPath !== ":memory:") mkdirSync(dirname(dbPath), { recursive: true });

    this.db = new DatabaseSync(dbPath);
    this.db.exec("PRAGMA foreign_keys = ON; PRAGMA journal_mode = WAL; PRAGMA synchronous = FULL;");
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS snapshots (
        revision INTEGER PRIMARY KEY,
        state_json TEXT NOT NULL,
        digest TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
      );

      CREATE TABLE IF NOT EXISTS events (
        sequence INTEGER PRIMARY KEY AUTOINCREMENT,
        command_id TEXT NOT NULL UNIQUE,
        command_json TEXT NOT NULL,
        event_json TEXT NOT NULL,
        before_digest TEXT NOT NULL,
        after_digest TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
      );
    `);

    const row = this.db.prepare("SELECT COUNT(*) AS count FROM snapshots").get() as { count: number };
    if (Number(row.count) === 0) this.persistSnapshot(genesis);
    else this.loadState();
  }

  private persistSnapshot(state: WorldState): void {
    assertWorldInvariants(state);
    this.db
      .prepare("INSERT INTO snapshots (revision, state_json, digest) VALUES (?, ?, ?)")
      .run(state.revision, canonicalJson(state), sha256(state));
  }

  loadState(): WorldState {
    const row = this.db
      .prepare("SELECT state_json, digest FROM snapshots ORDER BY revision DESC LIMIT 1")
      .get() as SnapshotRow | undefined;
    if (!row) throw new Error("world state is missing");
    const state = JSON.parse(row.state_json) as WorldState;
    if (state.schemaVersion !== 2) {
      throw new Error("incompatible world schema; remove the old local database and restart");
    }
    assertWorldInvariants(state);
    const actualDigest = sha256(state);
    if (actualDigest !== row.digest) {
      throw new Error(`snapshot digest mismatch: expected ${row.digest}, got ${actualDigest}`);
    }
    return state;
  }

  apply(command: WorldCommand): PersistedApplyResult {
    const existing = this.db
      .prepare("SELECT command_json, event_json, before_digest, after_digest FROM events WHERE command_id = ?")
      .get(command.commandId) as EventRow | undefined;

    if (existing) {
      if (existing.command_json !== canonicalJson(command)) {
        return {
          idempotent: false,
          result: {
            status: "rejected",
            state: this.loadState(),
            code: "invalid_command",
            reason: "commandId is already bound to a different command",
          },
        };
      }
      return {
        idempotent: true,
        result: {
          status: "accepted",
          state: this.loadState(),
          event: JSON.parse(existing.event_json) as WorldEvent,
        },
      };
    }

    this.db.exec("BEGIN IMMEDIATE");
    try {
      const state = this.loadState();
      const result = applyWorldCommand(state, command);
      if (result.status === "rejected") {
        this.db.exec("ROLLBACK");
        return { result, idempotent: false };
      }
      this.db
        .prepare(
          `INSERT INTO events
            (command_id, command_json, event_json, before_digest, after_digest)
           VALUES (?, ?, ?, ?, ?)`,
        )
        .run(
          command.commandId,
          canonicalJson(command),
          canonicalJson(result.event),
          result.event.beforeDigest,
          result.event.afterDigest,
        );
      this.persistSnapshot(result.state);
      this.db.exec("COMMIT");
      return { result, idempotent: false };
    } catch (error) {
      this.db.exec("ROLLBACK");
      throw error;
    }
  }

  events(): WorldEvent[] {
    const rows = this.db.prepare("SELECT event_json FROM events ORDER BY sequence ASC").all() as unknown as Array<{ event_json: string }>;
    return rows.map((row) => JSON.parse(row.event_json) as WorldEvent);
  }

  replay(): ReplayResult {
    const genesisRow = this.db
      .prepare("SELECT state_json, digest FROM snapshots ORDER BY revision ASC LIMIT 1")
      .get() as SnapshotRow | undefined;
    if (!genesisRow) throw new Error("genesis snapshot is missing");
    let state = JSON.parse(genesisRow.state_json) as WorldState;
    assertWorldInvariants(state);
    if (sha256(state) !== genesisRow.digest) throw new Error("genesis snapshot digest mismatch");

    const rows = this.db
      .prepare("SELECT command_json, event_json, before_digest, after_digest FROM events ORDER BY sequence ASC")
      .all() as unknown as EventRow[];
    for (const row of rows) {
      if (sha256(state) !== row.before_digest) throw new Error("replay before-digest mismatch");
      const command = JSON.parse(row.command_json) as WorldCommand;
      const replayed = applyWorldCommand(state, command);
      if (replayed.status !== "accepted") throw new Error(`replay command rejected: ${replayed.reason}`);
      if (replayed.event.afterDigest !== row.after_digest) throw new Error("replay after-digest mismatch");
      if (canonicalJson(replayed.event) !== row.event_json) throw new Error("replayed event differs from retained event");
      state = replayed.state;
    }

    const current = this.loadState();
    const replayDigest = sha256(state);
    if (replayDigest !== sha256(current)) throw new Error("replay terminal state differs from persisted state");
    return { state, digest: replayDigest, eventCount: rows.length, verified: true };
  }

  eventCount(): number {
    const row = this.db.prepare("SELECT COUNT(*) AS count FROM events").get() as { count: number };
    return Number(row.count);
  }

  close(): void {
    this.db.close();
  }
}
