import { canonicalJson } from "../digest.ts";
import type { AgentAttempt } from "../host/model.ts";
import type { HostStore } from "../host/store.ts";

export type AgentSessionMode = "idle" | "provider_pending" | "executing" | "verifying" | "blocked";

export interface AgentSession {
  schemaVersion: 1;
  kind: "ordivon.game.agent-session";
  runId: string;
  revision: number;
  mode: AgentSessionMode;
  providerOrder: string[];
  activeAttempt: AgentAttempt | null;
  completedAttempts: AgentAttempt[];
  blockers: string[];
  createdAt: string;
  updatedAt: string;
}

interface SessionRow { value_json: string }

export class AgentSessionStore {
  readonly host: HostStore;

  constructor(host: HostStore) {
    this.host = host;
    this.host.db.exec(`
      CREATE TABLE IF NOT EXISTS game_agent_sessions (
        run_id TEXT PRIMARY KEY,
        revision INTEGER NOT NULL,
        mode TEXT NOT NULL,
        value_json TEXT NOT NULL,
        FOREIGN KEY (run_id) REFERENCES runs(run_id)
      );
    `);
  }

  initialize(runId: string, providerOrder: string[]): AgentSession {
    const existing = this.find(runId);
    if (existing) return existing;
    const timestamp = new Date().toISOString();
    const session: AgentSession = {
      schemaVersion: 1,
      kind: "ordivon.game.agent-session",
      runId,
      revision: 1,
      mode: "idle",
      providerOrder: [...providerOrder],
      activeAttempt: null,
      completedAttempts: [],
      blockers: [],
      createdAt: timestamp,
      updatedAt: timestamp,
    };
    return this.host.withTransaction(runId, () => {
      this.host.db.prepare(`INSERT INTO game_agent_sessions (run_id, revision, mode, value_json)
        VALUES (?, ?, ?, ?)`)
        .run(runId, session.revision, session.mode, canonicalJson(session));
      this.host.appendEventInTransaction(runId, "goal_created", `agent-event:${runId}:goal-created`, { runId }, timestamp);
      this.host.appendEventInTransaction(runId, "task_created", `agent-event:${runId}:session-created`, { session }, timestamp);
      return session;
    });
  }

  get(runId: string): AgentSession {
    const session = this.find(runId);
    if (!session) throw new Error(`Agent Session is not initialized: ${runId}`);
    return session;
  }

  save(
    session: AgentSession,
    eventType: string,
    eventId: string,
    payload: unknown = { session },
  ): AgentSession {
    const current = this.get(session.runId);
    if (session.revision !== current.revision + 1) throw new Error("Agent Session revision is not consecutive");
    return this.host.withTransaction(session.runId, () => {
      this.host.db.prepare(`UPDATE game_agent_sessions SET revision = ?, mode = ?, value_json = ?
        WHERE run_id = ? AND revision = ?`)
        .run(session.revision, session.mode, canonicalJson(session), session.runId, current.revision);
      this.host.appendEventInTransaction(session.runId, eventType, eventId, payload, session.updatedAt);
      return session;
    });
  }

  private find(runId: string): AgentSession | null {
    const row = this.host.db.prepare("SELECT value_json FROM game_agent_sessions WHERE run_id = ?")
      .get(runId) as SessionRow | undefined;
    return row ? JSON.parse(row.value_json) as AgentSession : null;
  }
}
