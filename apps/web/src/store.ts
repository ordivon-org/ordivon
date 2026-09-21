import { createHash, randomBytes, randomUUID } from "node:crypto";
import { DatabaseSync } from "node:sqlite";

import { WebProblem } from "./errors.ts";
import type {
  AuthenticatedSession,
  CanaryNote,
  ChallengePurpose,
  ChallengeRecord,
  Principal,
  SessionView,
  StoredCredential,
} from "./model.ts";

interface PrincipalRow {
  principal_id: string;
  user_name: string;
  display_name: string;
}

interface CredentialRow {
  credential_id: string;
  principal_id: string;
  public_key: Uint8Array;
  counter: number;
  transports_json: string;
  device_type: string;
  backed_up: number;
  created_at: number;
  last_used_at: number;
  revoked_at: number | null;
}

interface ChallengeRow {
  challenge_id: string;
  purpose: ChallengePurpose;
  principal_id: string;
  challenge: string;
  expires_at: number;
  consumed_at: number | null;
}

interface SessionRow {
  session_id: string;
  token_hash: string;
  principal_id: string;
  created_at: number;
  authenticated_at: number;
  last_seen_at: number;
  idle_expires_at: number;
  absolute_expires_at: number;
  revoked_at: number | null;
  authn_method: "webauthn";
  user_agent: string | null;
}

interface NoteRow {
  note_id: string;
  principal_id: string;
  content: string;
  state: "DRAFT" | "PUBLISHED";
  created_at: number;
  published_at: number | null;
}

function hashToken(token: string): string {
  return createHash("sha256").update(token).digest("hex");
}

function randomToken(): string {
  return randomBytes(32).toString("base64url");
}

function parseStringArray(value: string): string[] {
  const parsed: unknown = JSON.parse(value);
  if (!Array.isArray(parsed) || parsed.some((item) => typeof item !== "string")) {
    throw new WebProblem(
      500,
      "credential-corrupt",
      "Credential state invalid",
      "Stored credential transports are invalid.",
    );
  }
  return parsed;
}

function principalFromRow(row: PrincipalRow): Principal {
  return {
    principalId: row.principal_id,
    userName: row.user_name,
    displayName: row.display_name,
  };
}

function sessionFromRow(row: SessionRow): SessionView {
  return {
    sessionId: row.session_id,
    principalId: row.principal_id,
    createdAt: row.created_at,
    authenticatedAt: row.authenticated_at,
    lastSeenAt: row.last_seen_at,
    idleExpiresAt: row.idle_expires_at,
    absoluteExpiresAt: row.absolute_expires_at,
    revokedAt: row.revoked_at,
    authnMethod: row.authn_method,
    userAgent: row.user_agent,
  };
}

function credentialFromRow(row: CredentialRow): StoredCredential {
  return {
    credentialId: row.credential_id,
    principalId: row.principal_id,
    publicKey: Uint8Array.from(row.public_key),
    counter: row.counter,
    transports: parseStringArray(row.transports_json),
    deviceType: row.device_type,
    backedUp: row.backed_up === 1,
    createdAt: row.created_at,
    lastUsedAt: row.last_used_at,
    revokedAt: row.revoked_at,
  };
}

function noteFromRow(row: NoteRow): CanaryNote {
  return {
    noteId: row.note_id,
    principalId: row.principal_id,
    content: row.content,
    state: row.state,
    createdAt: row.created_at,
    publishedAt: row.published_at,
  };
}

export class WebStore {
  readonly db: DatabaseSync;

  constructor(path: string) {
    this.db = new DatabaseSync(path);
    this.db.exec("PRAGMA foreign_keys = ON");
    this.db.exec("PRAGMA journal_mode = WAL");
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS principals (
        principal_id TEXT PRIMARY KEY,
        user_name TEXT NOT NULL UNIQUE,
        display_name TEXT NOT NULL,
        created_at INTEGER NOT NULL
      );

      CREATE TABLE IF NOT EXISTS webauthn_credentials (
        credential_id TEXT PRIMARY KEY,
        principal_id TEXT NOT NULL,
        public_key BLOB NOT NULL,
        counter INTEGER NOT NULL,
        transports_json TEXT NOT NULL,
        device_type TEXT NOT NULL,
        backed_up INTEGER NOT NULL CHECK (backed_up IN (0, 1)),
        created_at INTEGER NOT NULL,
        last_used_at INTEGER NOT NULL,
        revoked_at INTEGER,
        FOREIGN KEY(principal_id) REFERENCES principals(principal_id)
      );

      CREATE INDEX IF NOT EXISTS webauthn_credentials_principal
        ON webauthn_credentials(principal_id, revoked_at);

      CREATE TABLE IF NOT EXISTS webauthn_challenges (
        challenge_id TEXT PRIMARY KEY,
        purpose TEXT NOT NULL,
        principal_id TEXT NOT NULL,
        challenge TEXT NOT NULL,
        expires_at INTEGER NOT NULL,
        consumed_at INTEGER,
        FOREIGN KEY(principal_id) REFERENCES principals(principal_id)
      );

      CREATE TABLE IF NOT EXISTS sessions (
        session_id TEXT PRIMARY KEY,
        token_hash TEXT NOT NULL UNIQUE,
        principal_id TEXT NOT NULL,
        created_at INTEGER NOT NULL,
        authenticated_at INTEGER NOT NULL,
        last_seen_at INTEGER NOT NULL,
        idle_expires_at INTEGER NOT NULL,
        absolute_expires_at INTEGER NOT NULL,
        revoked_at INTEGER,
        authn_method TEXT NOT NULL,
        user_agent TEXT,
        FOREIGN KEY(principal_id) REFERENCES principals(principal_id)
      );

      CREATE INDEX IF NOT EXISTS sessions_principal
        ON sessions(principal_id, revoked_at, absolute_expires_at);

      CREATE TABLE IF NOT EXISTS canary_notes (
        note_id TEXT PRIMARY KEY,
        principal_id TEXT NOT NULL,
        content TEXT NOT NULL,
        state TEXT NOT NULL CHECK (state IN ('DRAFT', 'PUBLISHED')),
        created_at INTEGER NOT NULL,
        published_at INTEGER,
        FOREIGN KEY(principal_id) REFERENCES principals(principal_id)
      );

      CREATE TABLE IF NOT EXISTS audit_events (
        event_id TEXT PRIMARY KEY,
        principal_id TEXT,
        event_type TEXT NOT NULL,
        object_type TEXT,
        object_id TEXT,
        detail_json TEXT NOT NULL,
        created_at INTEGER NOT NULL
      );

      CREATE INDEX IF NOT EXISTS audit_events_principal_created
        ON audit_events(principal_id, created_at);
    `);
  }

  close(): void {
    this.db.close();
  }

  audit(
    eventType: string,
    now: number,
    principalId: string | null,
    objectType: string | null,
    objectId: string | null,
    detail: unknown,
  ): void {
    this.db
      .prepare(`
        INSERT INTO audit_events (
          event_id, principal_id, event_type, object_type, object_id, detail_json, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
      `)
      .run(
        randomUUID(),
        principalId,
        eventType,
        objectType,
        objectId,
        JSON.stringify(detail),
        now,
      );
  }

  ensurePrincipal(
    principalId: string,
    userName: string,
    displayName: string,
    now: number,
  ): Principal {
    const row = this.db
      .prepare("SELECT * FROM principals WHERE principal_id = ?")
      .get(principalId) as PrincipalRow | undefined;
    if (row !== undefined) {
      if (row.user_name !== userName || row.display_name !== displayName) {
        throw new WebProblem(
          409,
          "principal-identity-conflict",
          "Principal identity conflict",
          "The Principal already exists with different account attributes.",
        );
      }
      return principalFromRow(row);
    }
    this.db
      .prepare(
        "INSERT INTO principals (principal_id, user_name, display_name, created_at) VALUES (?, ?, ?, ?)",
      )
      .run(principalId, userName, displayName, now);
    this.audit("principal.created", now, principalId, "principal", principalId, {});
    return { principalId, userName, displayName };
  }

  getPrincipal(principalId: string): Principal {
    const row = this.db
      .prepare("SELECT * FROM principals WHERE principal_id = ?")
      .get(principalId) as PrincipalRow | undefined;
    if (row === undefined) {
      throw new WebProblem(
        404,
        "principal-not-found",
        "Principal not found",
        "The requested Principal does not exist.",
      );
    }
    return principalFromRow(row);
  }

  findPrincipalByUserName(userName: string): Principal {
    const row = this.db
      .prepare("SELECT * FROM principals WHERE user_name = ?")
      .get(userName) as PrincipalRow | undefined;
    if (row === undefined) {
      throw new WebProblem(
        404,
        "principal-not-found",
        "Principal not found",
        "The requested Principal does not exist.",
      );
    }
    return principalFromRow(row);
  }

  listCredentials(principalId: string): StoredCredential[] {
    const rows = this.db
      .prepare(
        "SELECT * FROM webauthn_credentials WHERE principal_id = ? ORDER BY created_at",
      )
      .all(principalId) as unknown as CredentialRow[];
    return rows.map(credentialFromRow);
  }

  getActiveCredential(credentialId: string): StoredCredential {
    const row = this.db
      .prepare(
        "SELECT * FROM webauthn_credentials WHERE credential_id = ? AND revoked_at IS NULL",
      )
      .get(credentialId) as CredentialRow | undefined;
    if (row === undefined) {
      throw new WebProblem(
        403,
        "credential-not-found",
        "Credential unavailable",
        "The WebAuthn credential is unknown or revoked.",
      );
    }
    return credentialFromRow(row);
  }

  putCredential(
    principalId: string,
    credential: {
      id: string;
      publicKey: Uint8Array;
      counter: number;
      transports: readonly string[];
      deviceType: string;
      backedUp: boolean;
    },
    now: number,
  ): void {
    this.db
      .prepare(`
        INSERT INTO webauthn_credentials (
          credential_id, principal_id, public_key, counter, transports_json,
          device_type, backed_up, created_at, last_used_at, revoked_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)
      `)
      .run(
        credential.id,
        principalId,
        Buffer.from(credential.publicKey),
        credential.counter,
        JSON.stringify([...credential.transports]),
        credential.deviceType,
        credential.backedUp ? 1 : 0,
        now,
        now,
      );
    this.audit(
      "credential.registered",
      now,
      principalId,
      "webauthn-credential",
      credential.id,
      { deviceType: credential.deviceType, backedUp: credential.backedUp },
    );
  }

  updateCredentialCounter(
    credentialId: string,
    expectedCounter: number,
    newCounter: number,
    now: number,
  ): void {
    const result = this.db
      .prepare(`
        UPDATE webauthn_credentials
        SET counter = ?, last_used_at = ?
        WHERE credential_id = ? AND counter = ? AND revoked_at IS NULL
      `)
      .run(newCounter, now, credentialId, expectedCounter);
    if (result.changes !== 1) {
      throw new WebProblem(
        409,
        "credential-counter-conflict",
        "Credential state changed",
        "The WebAuthn credential counter changed concurrently.",
      );
    }
  }

  createChallenge(
    purpose: ChallengePurpose,
    principalId: string,
    challenge: string,
    now: number,
    ttlSeconds = 120,
  ): ChallengeRecord {
    const challengeId = randomUUID();
    const record: ChallengeRecord = {
      challengeId,
      purpose,
      principalId,
      challenge,
      expiresAt: now + ttlSeconds,
    };
    this.db
      .prepare(`
        INSERT INTO webauthn_challenges (
          challenge_id, purpose, principal_id, challenge, expires_at, consumed_at
        ) VALUES (?, ?, ?, ?, ?, NULL)
      `)
      .run(
        record.challengeId,
        record.purpose,
        record.principalId,
        record.challenge,
        record.expiresAt,
      );
    return record;
  }

  consumeChallenge(
    challengeId: string,
    purpose: ChallengePurpose,
    now: number,
  ): ChallengeRecord {
    this.db.exec("BEGIN IMMEDIATE");
    try {
      const row = this.db
        .prepare("SELECT * FROM webauthn_challenges WHERE challenge_id = ?")
        .get(challengeId) as ChallengeRow | undefined;
      if (
        row === undefined ||
        row.purpose !== purpose ||
        row.consumed_at !== null ||
        row.expires_at <= now
      ) {
        throw new WebProblem(
          409,
          "challenge-invalid",
          "Challenge unavailable",
          "The WebAuthn challenge is missing, expired, consumed, or has the wrong purpose.",
        );
      }
      const update = this.db
        .prepare(
          "UPDATE webauthn_challenges SET consumed_at = ? WHERE challenge_id = ? AND consumed_at IS NULL",
        )
        .run(now, challengeId);
      if (update.changes !== 1) {
        throw new WebProblem(
          409,
          "challenge-race",
          "Challenge already consumed",
          "The WebAuthn challenge was consumed concurrently.",
        );
      }
      this.db.exec("COMMIT");
      return {
        challengeId: row.challenge_id,
        purpose: row.purpose,
        principalId: row.principal_id,
        challenge: row.challenge,
        expiresAt: row.expires_at,
      };
    } catch (error) {
      this.db.exec("ROLLBACK");
      throw error;
    }
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

  createCanaryNote(
    principalId: string,
    content: string,
    now: number,
  ): CanaryNote {
    const noteId = randomUUID();
    this.db
      .prepare(`
        INSERT INTO canary_notes (
          note_id, principal_id, content, state, created_at, published_at
        ) VALUES (?, ?, ?, 'DRAFT', ?, NULL)
      `)
      .run(noteId, principalId, content, now);
    this.audit(
      "canary.note.created",
      now,
      principalId,
      "canary-note",
      noteId,
      {},
    );
    return {
      noteId,
      principalId,
      content,
      state: "DRAFT",
      createdAt: now,
      publishedAt: null,
    };
  }

  listCanaryNotes(principalId: string): CanaryNote[] {
    const rows = this.db
      .prepare(
        "SELECT * FROM canary_notes WHERE principal_id = ? ORDER BY created_at DESC",
      )
      .all(principalId) as unknown as NoteRow[];
    return rows.map(noteFromRow);
  }
}
