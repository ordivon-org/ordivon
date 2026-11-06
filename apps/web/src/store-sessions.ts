/** Browser Session persistence facet; the WebStore retains SQLite authority and public API. */
import { randomBytes, randomUUID } from "node:crypto";
import type { DatabaseSync } from "node:sqlite";

import { hashToken } from "./identity-digests.ts";
import { WebProblem } from "./errors.ts";
import { sessionFromRow } from "./store-row-projections.ts";
import type { SessionRow } from "./store-row-projections.ts";
import type {
  AuthenticatedSession,
  Principal,
  SessionView,
} from "./model.ts";

type AuditSink = (
  eventType: string,
  now: number,
  principalId: string | null,
  objectType: string | null,
  objectId: string | null,
  detail: unknown,
) => void;

function randomToken(): string {
  return randomBytes(32).toString("base64url");
}

export class SessionStore {
  private readonly db: DatabaseSync;
  private readonly audit: AuditSink;
  private readonly getPrincipal: (principalId: string) => Principal;

  constructor(
    db: DatabaseSync,
    audit: AuditSink,
    getPrincipal: (principalId: string) => Principal,
  ) {
    this.db = db;
    this.audit = audit;
    this.getPrincipal = getPrincipal;
  }

  createSession(
    principalId: string,
    now: number,
    idleSeconds: number,
    absoluteSeconds: number,
    userAgent: string | null,
  ): { token: string; session: SessionView } {
    const token = randomToken();
    const tokenHash = hashToken(token);
    const sessionId = randomUUID();
    const row: SessionRow = {
      session_id: sessionId,
      token_hash: tokenHash,
      principal_id: principalId,
      created_at: now,
      authenticated_at: now,
      last_seen_at: now,
      idle_expires_at: now + idleSeconds,
      absolute_expires_at: now + absoluteSeconds,
      revoked_at: null,
      authn_method: "webauthn",
      user_agent: userAgent,
    };
    this.db
      .prepare(`
        INSERT INTO sessions (
          session_id, token_hash, principal_id, created_at, authenticated_at,
          last_seen_at, idle_expires_at, absolute_expires_at, revoked_at,
          authn_method, user_agent
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?)
      `)
      .run(
        row.session_id,
        row.token_hash,
        row.principal_id,
        row.created_at,
        row.authenticated_at,
        row.last_seen_at,
        row.idle_expires_at,
        row.absolute_expires_at,
        row.authn_method,
        row.user_agent,
      );
    this.audit("session.created", now, principalId, "session", sessionId, {
      authnMethod: row.authn_method,
    });
    return { token, session: sessionFromRow(row) };
  }

  authenticateSession(
    token: string,
    now: number,
    idleSeconds: number,
  ): AuthenticatedSession {
    const tokenHash = hashToken(token);
    const row = this.db
      .prepare("SELECT * FROM sessions WHERE token_hash = ?")
      .get(tokenHash) as SessionRow | undefined;
    if (
      row === undefined ||
      row.revoked_at !== null ||
      row.idle_expires_at <= now ||
      row.absolute_expires_at <= now
    ) {
      throw new WebProblem(
        401,
        "session-invalid",
        "Authentication required",
        "The browser session is missing, expired, or revoked.",
      );
    }
    const newIdleExpiry = Math.min(now + idleSeconds, row.absolute_expires_at);
    this.db
      .prepare(
        "UPDATE sessions SET last_seen_at = ?, idle_expires_at = ? WHERE session_id = ?",
      )
      .run(now, newIdleExpiry, row.session_id);
    const principal = this.getPrincipal(row.principal_id);
    return {
      tokenHash,
      principal,
      session: sessionFromRow({
        ...row,
        last_seen_at: now,
        idle_expires_at: newIdleExpiry,
      }),
    };
  }

  listSessions(principalId: string): SessionView[] {
    const rows = this.db
      .prepare(
        "SELECT * FROM sessions WHERE principal_id = ? ORDER BY created_at DESC",
      )
      .all(principalId) as unknown as SessionRow[];
    return rows.map(sessionFromRow);
  }

  revokeSession(
    principalId: string,
    sessionId: string,
    now: number,
  ): boolean {
    const result = this.db
      .prepare(
        "UPDATE sessions SET revoked_at = ? WHERE session_id = ? AND principal_id = ? AND revoked_at IS NULL",
      )
      .run(now, sessionId, principalId);
    if (result.changes === 1) {
      this.audit("session.revoked", now, principalId, "session", sessionId, {});
      return true;
    }
    return false;
  }

  revokeAllSessions(principalId: string, now: number): number {
    const result = this.db
      .prepare(
        "UPDATE sessions SET revoked_at = ? WHERE principal_id = ? AND revoked_at IS NULL",
      )
      .run(now, principalId);
    this.audit(
      "session.revoked-all",
      now,
      principalId,
      "principal",
      principalId,
      { count: result.changes },
    );
    return Number(result.changes);
  }
}
