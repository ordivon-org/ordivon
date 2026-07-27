import type { DatabaseSync } from "node:sqlite";

import { canonicalJson, sha256 } from "../digest.ts";
import type { WorldState } from "../model.ts";
import type { RunMetadata } from "../run.ts";
import {
  goalIdFor,
  taskIdFor,
  terminalGoalStatus,
  terminalTaskPhase,
  type AgentAttempt,
  type AgentGoal,
  type AgentProjection,
  type AgentTask,
  type HostArtifact,
  type HostJournalEvent,
} from "./model.ts";

interface JournalRow {
  run_id: string;
  sequence: number;
  event_id: string;
  event_type: string;
  payload_json: string;
  previous_digest: string;
  record_digest: string;
  created_at: string;
}
interface JsonRow { value_json: string }
interface ArtifactRow {
  digest: string;
  kind: string;
  content_json: string;
  byte_length: number;
  created_at: string;
}

export class HostStoreError extends Error {
  readonly code: "host_corrupt" | "host_constraint";
  constructor(code: HostStoreError["code"], message: string, options?: ErrorOptions) {
    super(message, options);
    this.name = "HostStoreError";
    this.code = code;
  }
}

function recordDigest(row: Omit<JournalRow, "record_digest" | "created_at">): string {
  return sha256({
    kind: "ordivon.game.host-journal-record",
    runId: row.run_id,
    sequence: Number(row.sequence),
    eventId: row.event_id,
    eventType: row.event_type,
    payloadJson: row.payload_json,
    previousDigest: row.previous_digest,
  });
}

function parse<T>(text: string, label: string): T {
  try { return JSON.parse(text) as T; }
  catch (error) { throw new HostStoreError("host_corrupt", `${label} is invalid JSON`, { cause: error }); }
}

export class HostStore {
  readonly db: DatabaseSync;

  constructor(db: DatabaseSync) {
    this.db = db;
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS host_artifacts (
        digest TEXT PRIMARY KEY,
        kind TEXT NOT NULL,
        content_json TEXT NOT NULL,
        byte_length INTEGER NOT NULL,
        created_at TEXT NOT NULL
      );
      CREATE TABLE IF NOT EXISTS host_journal (
        run_id TEXT NOT NULL,
        sequence INTEGER NOT NULL,
        event_id TEXT NOT NULL,
        event_type TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        previous_digest TEXT NOT NULL,
        record_digest TEXT NOT NULL,
        created_at TEXT NOT NULL,
        PRIMARY KEY (run_id, sequence),
        UNIQUE (run_id, event_id),
        FOREIGN KEY (run_id) REFERENCES runs(run_id)
      );
      CREATE TABLE IF NOT EXISTS host_goals (
        run_id TEXT PRIMARY KEY,
        goal_id TEXT NOT NULL UNIQUE,
        status TEXT NOT NULL,
        revision INTEGER NOT NULL,
        value_json TEXT NOT NULL,
        FOREIGN KEY (run_id) REFERENCES runs(run_id)
      );
      CREATE TABLE IF NOT EXISTS host_tasks (
        run_id TEXT PRIMARY KEY,
        task_id TEXT NOT NULL UNIQUE,
        phase TEXT NOT NULL,
        revision INTEGER NOT NULL,
        value_json TEXT NOT NULL,
        FOREIGN KEY (run_id) REFERENCES runs(run_id)
      );
      CREATE TABLE IF NOT EXISTS host_attempts (
        attempt_id TEXT PRIMARY KEY,
        run_id TEXT NOT NULL,
        task_id TEXT NOT NULL,
        attempt_number INTEGER NOT NULL,
        status TEXT NOT NULL,
        revision INTEGER NOT NULL,
        value_json TEXT NOT NULL,
        FOREIGN KEY (run_id) REFERENCES runs(run_id)
      );
      CREATE INDEX IF NOT EXISTS host_attempts_run_idx
        ON host_attempts(run_id, attempt_number);
    `);
  }

  initializeRun(run: RunMetadata, world: WorldState, providerOrder: string[] = ["fixture"]): AgentProjection {
    const existing = this.db.prepare("SELECT value_json FROM host_goals WHERE run_id = ?").get(run.runId) as JsonRow | undefined;
    if (existing) return this.getProjection(run.runId);
    const now = new Date().toISOString();
    const goal: AgentGoal = {
      goalId: goalIdFor(run.runId), runId: run.runId, actorId: "engineer-01",
      statement: "Stabilize Station Zero and transmit a verified rescue signal.",
      successCondition: { missionStatus: "victory", missionReason: "rescue_signal_verified" },
      status: terminalGoalStatus(world.mission.status), revision: 1, createdAt: now, updatedAt: now,
    };
    const task: AgentTask = {
      taskId: taskIdFor(run.runId), goalId: goal.goalId, runId: run.runId, actorId: "engineer-01",
      phase: terminalTaskPhase(world.mission.status), revision: 1, activeAttemptId: null,
      completedAttemptIds: [], blockers: [], providerOrder: [...providerOrder], createdAt: now, updatedAt: now,
    };
    this.db.exec("BEGIN IMMEDIATE");
    try {
      this.db.prepare("INSERT INTO host_goals (run_id, goal_id, status, revision, value_json) VALUES (?, ?, ?, ?, ?)")
        .run(run.runId, goal.goalId, goal.status, goal.revision, canonicalJson(goal));
      this.db.prepare("INSERT INTO host_tasks (run_id, task_id, phase, revision, value_json) VALUES (?, ?, ?, ?, ?)")
        .run(run.runId, task.taskId, task.phase, task.revision, canonicalJson(task));
      this.appendEventInTransaction(run.runId, "goal_created", `host-event:${goal.goalId}:created`, goal, now);
      this.appendEventInTransaction(run.runId, "task_created", `host-event:${task.taskId}:created`, task, now);
      this.db.exec("COMMIT");
    } catch (error) {
      try { this.db.exec("ROLLBACK"); } catch {}
      throw error;
    }
    return { goal, task, attempts: [] };
  }

  putArtifact<T>(kind: string, content: T): HostArtifact<T> {
    if (!kind || kind !== kind.trim()) throw new TypeError("artifact kind must be non-empty and trimmed");
    const contentJson = canonicalJson(content);
    const digest = sha256({ kind, content });
    const existing = this.db.prepare("SELECT * FROM host_artifacts WHERE digest = ?").get(digest) as ArtifactRow | undefined;
    if (existing) {
      if (existing.kind !== kind || existing.content_json !== contentJson) {
        throw new HostStoreError("host_corrupt", "artifact digest is bound to different content");
      }
      return { digest, kind, content, byteLength: Number(existing.byte_length), createdAt: existing.created_at };
    }
    const createdAt = new Date().toISOString();
    const byteLength = Buffer.byteLength(contentJson);
    this.db.prepare("INSERT INTO host_artifacts (digest, kind, content_json, byte_length, created_at) VALUES (?, ?, ?, ?, ?)")
      .run(digest, kind, contentJson, byteLength, createdAt);
    return { digest, kind, content, byteLength, createdAt };
  }

  getArtifact<T>(digest: string): HostArtifact<T> {
    const row = this.db.prepare("SELECT * FROM host_artifacts WHERE digest = ?").get(digest) as ArtifactRow | undefined;
    if (!row) throw new Error(`unknown Host Artifact: ${digest}`);
    const content = parse<T>(row.content_json, "Host Artifact");
    if (sha256({ kind: row.kind, content }) !== row.digest) {
      throw new HostStoreError("host_corrupt", "Host Artifact digest mismatch");
    }
    return { digest: row.digest, kind: row.kind, content, byteLength: Number(row.byte_length), createdAt: row.created_at };
  }

  getGoal(runId: string): AgentGoal {
    const row = this.db.prepare("SELECT value_json FROM host_goals WHERE run_id = ?").get(runId) as JsonRow | undefined;
    if (!row) throw new Error(`Host Goal is not initialized: ${runId}`);
    return parse<AgentGoal>(row.value_json, "Goal");
  }

  getTask(runId: string): AgentTask {
    const row = this.db.prepare("SELECT value_json FROM host_tasks WHERE run_id = ?").get(runId) as JsonRow | undefined;
    if (!row) throw new Error(`Host Task is not initialized: ${runId}`);
    return parse<AgentTask>(row.value_json, "Task");
  }

  getAttempt(attemptId: string): AgentAttempt {
    const row = this.db.prepare("SELECT value_json FROM host_attempts WHERE attempt_id = ?").get(attemptId) as JsonRow | undefined;
    if (!row) throw new Error(`unknown Host Attempt: ${attemptId}`);
    return parse<AgentAttempt>(row.value_json, "Attempt");
  }

  listAttempts(runId: string): AgentAttempt[] {
    const rows = this.db.prepare("SELECT value_json FROM host_attempts WHERE run_id = ? ORDER BY attempt_number, attempt_id")
      .all(runId) as unknown as JsonRow[];
    return rows.map((row) => parse<AgentAttempt>(row.value_json, "Attempt"));
  }

  getProjection(runId: string): AgentProjection {
    return { goal: this.getGoal(runId), task: this.getTask(runId), attempts: this.listAttempts(runId) };
  }

  saveGoal(goal: AgentGoal, eventType: string, eventId: string, payload: unknown = goal): HostJournalEvent {
    return this.withTransaction(goal.runId, () => {
      this.db.prepare("UPDATE host_goals SET status = ?, revision = ?, value_json = ? WHERE run_id = ?")
        .run(goal.status, goal.revision, canonicalJson(goal), goal.runId);
      return this.appendEventInTransaction(goal.runId, eventType, eventId, payload, goal.updatedAt);
    });
  }

  saveTask(task: AgentTask, eventType: string, eventId: string, payload: unknown = task): HostJournalEvent {
    return this.withTransaction(task.runId, () => {
      this.db.prepare("UPDATE host_tasks SET phase = ?, revision = ?, value_json = ? WHERE run_id = ?")
        .run(task.phase, task.revision, canonicalJson(task), task.runId);
      return this.appendEventInTransaction(task.runId, eventType, eventId, payload, task.updatedAt);
    });
  }

  createAttempt(attempt: AgentAttempt, eventType = "attempt_created"): HostJournalEvent {
    return this.withTransaction(attempt.runId, () => {
      this.db.prepare(`INSERT INTO host_attempts
        (attempt_id, run_id, task_id, attempt_number, status, revision, value_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)`)
        .run(attempt.attemptId, attempt.runId, attempt.taskId, attempt.attemptNumber,
          attempt.status, attempt.revision, canonicalJson(attempt));
      return this.appendEventInTransaction(attempt.runId, eventType,
        `host-event:${attempt.attemptId}:created`, attempt, attempt.createdAt);
    });
  }

  saveAttempt(attempt: AgentAttempt, eventType: string, eventId: string, payload: unknown = attempt): HostJournalEvent {
    return this.withTransaction(attempt.runId, () => {
      this.db.prepare("UPDATE host_attempts SET status = ?, revision = ?, value_json = ? WHERE attempt_id = ?")
        .run(attempt.status, attempt.revision, canonicalJson(attempt), attempt.attemptId);
      return this.appendEventInTransaction(attempt.runId, eventType, eventId, payload, attempt.updatedAt);
    });
  }


  activateAttempt(task: AgentTask, attempt: AgentAttempt): HostJournalEvent {
    return this.withTransaction(task.runId, () => {
      this.db.prepare(`INSERT INTO host_attempts
        (attempt_id, run_id, task_id, attempt_number, status, revision, value_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)`)
        .run(attempt.attemptId, attempt.runId, attempt.taskId, attempt.attemptNumber,
          attempt.status, attempt.revision, canonicalJson(attempt));
      this.db.prepare("UPDATE host_tasks SET phase = ?, revision = ?, value_json = ? WHERE run_id = ?")
        .run(task.phase, task.revision, canonicalJson(task), task.runId);
      return this.appendEventInTransaction(task.runId, "attempt_activated",
        `host-event:${attempt.attemptId}:activated`, { task, attempt }, attempt.createdAt);
    });
  }

  saveTaskAndAttempt(
    task: AgentTask,
    attempt: AgentAttempt,
    eventType: string,
    eventId: string,
    payload: unknown = { task, attempt },
  ): HostJournalEvent {
    return this.withTransaction(task.runId, () => {
      this.db.prepare("UPDATE host_tasks SET phase = ?, revision = ?, value_json = ? WHERE run_id = ?")
        .run(task.phase, task.revision, canonicalJson(task), task.runId);
      this.db.prepare("UPDATE host_attempts SET status = ?, revision = ?, value_json = ? WHERE attempt_id = ?")
        .run(attempt.status, attempt.revision, canonicalJson(attempt), attempt.attemptId);
      return this.appendEventInTransaction(task.runId, eventType, eventId, payload, attempt.updatedAt);
    });
  }


  saveGoalTaskAndAttempt(
    goal: AgentGoal,
    task: AgentTask,
    attempt: AgentAttempt,
    eventType: string,
    eventId: string,
    payload: unknown = { goal, task, attempt },
  ): HostJournalEvent {
    return this.withTransaction(goal.runId, () => {
      this.db.prepare("UPDATE host_goals SET status = ?, revision = ?, value_json = ? WHERE run_id = ?")
        .run(goal.status, goal.revision, canonicalJson(goal), goal.runId);
      this.db.prepare("UPDATE host_tasks SET phase = ?, revision = ?, value_json = ? WHERE run_id = ?")
        .run(task.phase, task.revision, canonicalJson(task), task.runId);
      this.db.prepare("UPDATE host_attempts SET status = ?, revision = ?, value_json = ? WHERE attempt_id = ?")
        .run(attempt.status, attempt.revision, canonicalJson(attempt), attempt.attemptId);
      return this.appendEventInTransaction(goal.runId, eventType, eventId, payload, attempt.updatedAt);
    });
  }

  saveGoalAndTask(
    goal: AgentGoal,
    task: AgentTask,
    eventType: string,
    eventId: string,
    payload: unknown = { goal, task },
  ): HostJournalEvent {
    return this.withTransaction(goal.runId, () => {
      this.db.prepare("UPDATE host_goals SET status = ?, revision = ?, value_json = ? WHERE run_id = ?")
        .run(goal.status, goal.revision, canonicalJson(goal), goal.runId);
      this.db.prepare("UPDATE host_tasks SET phase = ?, revision = ?, value_json = ? WHERE run_id = ?")
        .run(task.phase, task.revision, canonicalJson(task), task.runId);
      return this.appendEventInTransaction(goal.runId, eventType, eventId, payload, task.updatedAt);
    });
  }

  appendEvent(runId: string, eventType: string, eventId: string, payload: unknown): HostJournalEvent {
    return this.withTransaction(runId, () => this.appendEventInTransaction(runId, eventType, eventId, payload, new Date().toISOString()));
  }

  withTransaction<T>(runId: string, operation: () => T): T {
    const run = this.db.prepare("SELECT 1 AS present FROM runs WHERE run_id = ?").get(runId) as { present: number } | undefined;
    if (!run) throw new Error(`unknown run: ${runId}`);
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

  appendEventInTransaction(runId: string, eventType: string, eventId: string, payload: unknown, createdAt: string): HostJournalEvent {
    const payloadJson = canonicalJson(payload);
    const existing = this.db.prepare("SELECT * FROM host_journal WHERE run_id = ? AND event_id = ?")
      .get(runId, eventId) as JournalRow | undefined;
    if (existing) {
      if (existing.event_type !== eventType || existing.payload_json !== payloadJson) {
        throw new HostStoreError("host_constraint", "Host Event identity is bound to different content");
      }
      return this.fromJournalRow(existing);
    }
    const last = this.db.prepare("SELECT sequence, record_digest FROM host_journal WHERE run_id = ? ORDER BY sequence DESC LIMIT 1")
      .get(runId) as { sequence: number; record_digest: string } | undefined;
    const base = {
      run_id: runId,
      sequence: Number(last?.sequence ?? -1) + 1,
      event_id: eventId,
      event_type: eventType,
      payload_json: payloadJson,
      previous_digest: last?.record_digest ?? "",
    };
    const digest = recordDigest(base);
    this.db.prepare(`INSERT INTO host_journal
      (run_id, sequence, event_id, event_type, payload_json, previous_digest, record_digest, created_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?)`)
      .run(runId, base.sequence, eventId, eventType, payloadJson, base.previous_digest, digest, createdAt);
    return { runId, sequence: base.sequence, eventId, eventType, payload,
      previousDigest: base.previous_digest, recordDigest: digest, createdAt };
  }

  listJournal(runId: string): HostJournalEvent[] {
    const rows = this.db.prepare("SELECT * FROM host_journal WHERE run_id = ? ORDER BY sequence")
      .all(runId) as unknown as JournalRow[];
    return rows.map((row) => this.fromJournalRow(row));
  }

  private fromJournalRow(row: JournalRow): HostJournalEvent {
    return {
      runId: row.run_id, sequence: Number(row.sequence), eventId: row.event_id,
      eventType: row.event_type, payload: parse(row.payload_json, "Host Journal payload"),
      previousDigest: row.previous_digest, recordDigest: row.record_digest, createdAt: row.created_at,
    };
  }

  verifyJournal(runId: string): void {
    const rows = this.db.prepare("SELECT * FROM host_journal WHERE run_id = ? ORDER BY sequence")
      .all(runId) as unknown as JournalRow[];
    let previous = "";
    for (let index = 0; index < rows.length; index += 1) {
      const row = rows[index];
      if (!row || Number(row.sequence) !== index) {
        throw new HostStoreError("host_corrupt", "Host Journal sequence is discontinuous");
      }
      if (row.previous_digest !== previous) {
        throw new HostStoreError("host_corrupt", "Host Journal previous digest mismatch");
      }
      const actual = recordDigest(row);
      if (actual !== row.record_digest) {
        throw new HostStoreError("host_corrupt", "Host Journal record digest mismatch");
      }
      previous = actual;
    }
  }
}
