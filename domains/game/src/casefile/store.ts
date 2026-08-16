import { mkdirSync } from "node:fs";
import { dirname } from "node:path";
import { DatabaseSync } from "node:sqlite";

import { canonicalJson, sha256 } from "../digest.ts";
import { CASEFILE_PERSON_IDS, type CasefileRunState } from "./model.ts";
import { casefileScenario } from "./content.ts";

export type CasefileStoreErrorCode = "casefile_not_found" | "casefile_conflict" | "casefile_corrupt";

export class CasefileStoreError extends Error {
  readonly code: CasefileStoreErrorCode;
  constructor(code: CasefileStoreErrorCode, message: string, options?: ErrorOptions) {
    super(message, options);
    this.name = "CasefileStoreError";
    this.code = code;
  }
}

interface RunRow {
  run_id: string;
  scenario_id: string;
  revision: number;
  status: string;
  state_json: string;
  state_digest: string;
  updated_at: string;
}

function validateState(value: unknown): CasefileRunState {
  if (!value || typeof value !== "object" || Array.isArray(value)) throw new TypeError("Casefile state must be one object");
  const state = value as CasefileRunState;
  if (state.schemaVersion !== 1 || state.kind !== "ordivon.game.casefile-run-state") throw new TypeError("unsupported Casefile state schema");
  if (typeof state.runId !== "string" || !state.runId.trim()) throw new TypeError("Casefile runId is invalid");
  casefileScenario(state.scenarioId);
  if (!Number.isSafeInteger(state.revision) || state.revision < 0) throw new TypeError("Casefile revision is invalid");
  if (!Number.isSafeInteger(state.movesRemaining) || state.movesRemaining < 0 || state.movesRemaining > 8) throw new TypeError("Casefile movesRemaining is invalid");
  if (!["investigating", "solved", "failed"].includes(state.status)) throw new TypeError("Casefile status is invalid");
  if (!Array.isArray(state.inspectedTraceIds) || !Array.isArray(state.confrontedKeys) || !Array.isArray(state.statements)) throw new TypeError("Casefile collections are invalid");
  for (const personId of CASEFILE_PERSON_IDS) {
    if (!Number.isSafeInteger(state.askedCount?.[personId]) || state.askedCount[personId] < 0 || state.askedCount[personId] > 2) {
      throw new TypeError(`Casefile askedCount is invalid for ${personId}`);
    }
  }
  if (state.status === "investigating" && state.outcome !== null) throw new TypeError("investigating Casefile cannot have outcome");
  if (state.status !== "investigating" && state.outcome === null) throw new TypeError("terminal Casefile must have outcome");
  return structuredClone(state);
}

function parseRow(row: RunRow): CasefileRunState {
  let value: unknown;
  try { value = JSON.parse(row.state_json); }
  catch (error) { throw new CasefileStoreError("casefile_corrupt", `Casefile state JSON is invalid for ${row.run_id}`, { cause: error }); }
  let state: CasefileRunState;
  try { state = validateState(value); }
  catch (error) { throw new CasefileStoreError("casefile_corrupt", `Casefile state is invalid for ${row.run_id}`, { cause: error }); }
  if (state.runId !== row.run_id || state.scenarioId !== row.scenario_id || state.revision !== Number(row.revision) || state.status !== row.status) {
    throw new CasefileStoreError("casefile_corrupt", `Casefile row metadata diverges for ${row.run_id}`);
  }
  if (sha256(state) !== row.state_digest) throw new CasefileStoreError("casefile_corrupt", `Casefile state digest mismatch for ${row.run_id}`);
  return state;
}

export class CasefileStore {
  readonly db: DatabaseSync;
  readonly dbPath: string;

  constructor(dbPath: string) {
    this.dbPath = dbPath;
    if (dbPath !== ":memory:") mkdirSync(dirname(dbPath), { recursive: true });
    this.db = new DatabaseSync(dbPath);
    this.db.exec(`
      PRAGMA journal_mode = WAL;
      PRAGMA synchronous = FULL;
      PRAGMA busy_timeout = 5000;
      CREATE TABLE IF NOT EXISTS casefile_runs (
        run_id TEXT PRIMARY KEY,
        scenario_id TEXT NOT NULL,
        revision INTEGER NOT NULL,
        status TEXT NOT NULL,
        state_json TEXT NOT NULL,
        state_digest TEXT NOT NULL,
        updated_at TEXT NOT NULL
      );
    `);
  }

  close(): void { this.db.close(); }

  list(): Array<{ runId: string; scenarioId: string; revision: number; status: string; updatedAt: string }> {
    const rows = this.db.prepare("SELECT run_id, scenario_id, revision, status, updated_at FROM casefile_runs ORDER BY updated_at DESC, run_id")
      .all() as unknown as Array<{ run_id: string; scenario_id: string; revision: number; status: string; updated_at: string }>;
    return rows.map((row) => ({ runId: row.run_id, scenarioId: row.scenario_id, revision: Number(row.revision), status: row.status, updatedAt: row.updated_at }));
  }

  create(state: CasefileRunState): void {
    const validated = validateState(state);
    if (validated.revision !== 0) throw new TypeError("new Casefile run must begin at revision zero");
    const now = new Date().toISOString();
    try {
      this.db.prepare(`INSERT INTO casefile_runs (run_id, scenario_id, revision, status, state_json, state_digest, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)`)
        .run(validated.runId, validated.scenarioId, validated.revision, validated.status, canonicalJson(validated), sha256(validated), now);
    } catch (error) {
      throw new CasefileStoreError("casefile_conflict", `Casefile run already exists or could not be created: ${validated.runId}`, { cause: error });
    }
  }

  read(runId: string): CasefileRunState {
    const row = this.db.prepare("SELECT * FROM casefile_runs WHERE run_id = ?").get(runId) as RunRow | undefined;
    if (!row) throw new CasefileStoreError("casefile_not_found", `unknown Casefile run: ${runId}`);
    return parseRow(row);
  }

  save(expectedRevision: number, state: CasefileRunState): void {
    const validated = validateState(state);
    if (validated.revision !== expectedRevision + 1) throw new TypeError("Casefile save must advance exactly one revision");
    const now = new Date().toISOString();
    const result = this.db.prepare(`UPDATE casefile_runs
      SET scenario_id = ?, revision = ?, status = ?, state_json = ?, state_digest = ?, updated_at = ?
      WHERE run_id = ? AND revision = ?`)
      .run(validated.scenarioId, validated.revision, validated.status, canonicalJson(validated), sha256(validated), now, validated.runId, expectedRevision);
    if (Number(result.changes) !== 1) throw new CasefileStoreError("casefile_conflict", `stale Casefile revision for ${validated.runId}`);
  }
}
