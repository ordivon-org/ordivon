import { createHash, randomUUID } from "node:crypto";
import { DatabaseSync } from "node:sqlite";

import { AdmissionLabError } from "./errors.ts";
import type { EffectRequest, GrantCreate, VerifiedApproval } from "./model.ts";

export type WebAuthnPurpose = "register" | "grant-issue" | "grant-revoke" | "effect-approve";

export interface StoredCredential {
  readonly id: string;
  readonly principalId: string;
  readonly publicKey: Uint8Array;
  readonly counter: number;
  readonly transports: readonly string[];
  readonly deviceType: string;
  readonly backedUp: boolean;
}

export interface ChallengeRecord {
  readonly challengeId: string;
  readonly purpose: WebAuthnPurpose;
  readonly principalId: string;
  readonly challenge: string;
  readonly payloadDigest: string;
  readonly payload: unknown;
  readonly expiresAtEpochSeconds: number;
}

interface CredentialRow {
  credential_id: string;
  principal_id: string;
  public_key: Uint8Array;
  counter: number;
  transports_json: string;
  device_type: string;
  backed_up: number;
}

interface ChallengeRow {
  challenge_id: string;
  purpose: WebAuthnPurpose;
  principal_id: string;
  challenge: string;
  payload_digest: string;
  payload_json: string;
  expires_at: number;
  consumed_at: number | null;
}

function stableDigest(value: unknown): string {
  return `sha256:${createHash("sha256").update(JSON.stringify(value)).digest("hex")}`;
}

function parseStringArray(value: string): string[] {
  const parsed: unknown = JSON.parse(value);
  if (!Array.isArray(parsed) || parsed.some((item) => typeof item !== "string")) {
    throw new AdmissionLabError("credential_corrupt", "Credential transports are invalid.", 500);
  }
  return parsed;
}

export class PrincipalStore {
  readonly db: DatabaseSync;

  constructor(path: string) {
    this.db = new DatabaseSync(path);
    this.db.exec("PRAGMA foreign_keys = ON");
    this.db.exec("PRAGMA journal_mode = WAL");
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS principals (
        principal_id TEXT PRIMARY KEY,
        user_name TEXT NOT NULL,
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
        last_used_at INTEGER,
        FOREIGN KEY(principal_id) REFERENCES principals(principal_id)
      );

      CREATE INDEX IF NOT EXISTS webauthn_credentials_principal
        ON webauthn_credentials(principal_id);

      CREATE TABLE IF NOT EXISTS webauthn_challenges (
        challenge_id TEXT PRIMARY KEY,
        purpose TEXT NOT NULL,
        principal_id TEXT NOT NULL,
        challenge TEXT NOT NULL,
        payload_digest TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        expires_at INTEGER NOT NULL,
        consumed_at INTEGER,
        FOREIGN KEY(principal_id) REFERENCES principals(principal_id)
      );

      CREATE TABLE IF NOT EXISTS pending_effect_approvals (
        effect_id TEXT PRIMARY KEY,
        effect_digest TEXT NOT NULL,
        principal_id TEXT NOT NULL,
        expires_at INTEGER NOT NULL,
        created_at INTEGER NOT NULL,
        FOREIGN KEY(principal_id) REFERENCES principals(principal_id)
      );

      CREATE TABLE IF NOT EXISTS effect_approvals (
        effect_id TEXT PRIMARY KEY,
        effect_digest TEXT NOT NULL,
        principal_id TEXT NOT NULL,
        credential_id TEXT NOT NULL,
        verified_at INTEGER NOT NULL,
        expires_at INTEGER NOT NULL,
        consumed_at INTEGER,
        FOREIGN KEY(principal_id) REFERENCES principals(principal_id),
        FOREIGN KEY(credential_id) REFERENCES webauthn_credentials(credential_id)
      );
    `);
  }

  close(): void {
    this.db.close();
  }

  ensurePrincipal(
    principalId: string,
    userName: string,
    displayName: string,
    nowEpochSeconds: number,
  ): void {
    const existing = this.db
      .prepare("SELECT principal_id, user_name, display_name FROM principals WHERE principal_id = ?")
      .get(principalId) as { principal_id: string; user_name: string; display_name: string } | undefined;
    if (existing !== undefined) {
      if (existing.user_name !== userName || existing.display_name !== displayName) {
        throw new AdmissionLabError(
          "principal_identity_conflict",
          "Principal enrollment identity does not match the existing record.",
          409,
        );
      }
      return;
    }
    this.db
      .prepare(
        "INSERT INTO principals (principal_id, user_name, display_name, created_at) VALUES (?, ?, ?, ?)",
      )
      .run(principalId, userName, displayName, nowEpochSeconds);
  }

  requirePrincipal(principalId: string): { userName: string; displayName: string } {
    const row = this.db
      .prepare("SELECT user_name, display_name FROM principals WHERE principal_id = ?")
      .get(principalId) as { user_name: string; display_name: string } | undefined;
    if (row === undefined) {
      throw new AdmissionLabError("principal_not_found", "Principal was not found.", 404);
    }
    return { userName: row.user_name, displayName: row.display_name };
  }

  listCredentials(principalId: string): StoredCredential[] {
    const rows = this.db
      .prepare("SELECT * FROM webauthn_credentials WHERE principal_id = ? ORDER BY credential_id")
      .all(principalId) as unknown as CredentialRow[];
    return rows.map((row) => ({
      id: row.credential_id,
      principalId: row.principal_id,
      publicKey: new Uint8Array(row.public_key),
      counter: row.counter,
      transports: parseStringArray(row.transports_json),
      deviceType: row.device_type,
      backedUp: row.backed_up === 1,
    }));
  }

  getCredential(credentialId: string): StoredCredential {
    const row = this.db
      .prepare("SELECT * FROM webauthn_credentials WHERE credential_id = ?")
      .get(credentialId) as CredentialRow | undefined;
    if (row === undefined) {
      throw new AdmissionLabError("credential_not_found", "WebAuthn credential was not found.", 403);
    }
    return {
      id: row.credential_id,
      principalId: row.principal_id,
      publicKey: new Uint8Array(row.public_key),
      counter: row.counter,
      transports: parseStringArray(row.transports_json),
      deviceType: row.device_type,
      backedUp: row.backed_up === 1,
    };
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
    nowEpochSeconds: number,
  ): void {
    this.db
      .prepare(`
        INSERT INTO webauthn_credentials (
          credential_id, principal_id, public_key, counter, transports_json,
          device_type, backed_up, created_at, last_used_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
      `)
      .run(
        credential.id,
        principalId,
        Buffer.from(credential.publicKey),
        credential.counter,
        JSON.stringify([...credential.transports]),
        credential.deviceType,
        credential.backedUp ? 1 : 0,
        nowEpochSeconds,
        nowEpochSeconds,
      );
  }

  updateCredentialCounter(
    credentialId: string,
    expectedCounter: number,
    newCounter: number,
    nowEpochSeconds: number,
  ): void {
    const result = this.db
      .prepare(`
        UPDATE webauthn_credentials
        SET counter = ?, last_used_at = ?
        WHERE credential_id = ? AND counter = ?
      `)
      .run(newCounter, nowEpochSeconds, credentialId, expectedCounter);
    if (result.changes !== 1) {
      throw new AdmissionLabError(
        "credential_counter_conflict",
        "WebAuthn credential counter changed concurrently.",
        409,
      );
    }
  }

  createChallenge(
    purpose: WebAuthnPurpose,
    principalId: string,
    challenge: string,
    payload: unknown,
    expiresAtEpochSeconds: number,
  ): ChallengeRecord {
    const challengeId = randomUUID();
    const payloadDigest = stableDigest(payload);
    this.db
      .prepare(`
        INSERT INTO webauthn_challenges (
          challenge_id, purpose, principal_id, challenge, payload_digest,
          payload_json, expires_at, consumed_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, NULL)
      `)
      .run(
        challengeId,
        purpose,
        principalId,
        challenge,
        payloadDigest,
        JSON.stringify(payload),
        expiresAtEpochSeconds,
      );
    return {
      challengeId,
      purpose,
      principalId,
      challenge,
      payloadDigest,
      payload,
      expiresAtEpochSeconds,
    };
  }

  consumeChallenge(
    challengeId: string,
    purpose: WebAuthnPurpose,
    nowEpochSeconds: number,
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
        row.expires_at <= nowEpochSeconds
      ) {
        throw new AdmissionLabError(
          "webauthn_challenge_invalid",
          "WebAuthn challenge is missing, expired, consumed, or has the wrong purpose.",
          409,
        );
      }
      const update = this.db
        .prepare(
          "UPDATE webauthn_challenges SET consumed_at = ? WHERE challenge_id = ? AND consumed_at IS NULL",
        )
        .run(nowEpochSeconds, challengeId);
      if (update.changes !== 1) {
        throw new AdmissionLabError(
          "webauthn_challenge_race",
          "WebAuthn challenge was consumed concurrently.",
          409,
        );
      }
      this.db.exec("COMMIT");
      return {
        challengeId: row.challenge_id,
        purpose: row.purpose,
        principalId: row.principal_id,
        challenge: row.challenge,
        payloadDigest: row.payload_digest,
        payload: JSON.parse(row.payload_json) as unknown,
        expiresAtEpochSeconds: row.expires_at,
      };
    } catch (error) {
      this.db.exec("ROLLBACK");
      throw error;
    }
  }

  registerPendingEffect(
    principalId: string,
    effect: EffectRequest,
    nowEpochSeconds: number,
    ttlSeconds = 300,
  ): void {
    this.db
      .prepare(`
        INSERT INTO pending_effect_approvals (
          effect_id, effect_digest, principal_id, expires_at, created_at
        ) VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(effect_id) DO UPDATE SET
          effect_digest = excluded.effect_digest,
          principal_id = excluded.principal_id,
          expires_at = excluded.expires_at
        WHERE pending_effect_approvals.effect_digest = excluded.effect_digest
          AND pending_effect_approvals.principal_id = excluded.principal_id
      `)
      .run(
        effect.effectId,
        effect.effectDigest,
        principalId,
        nowEpochSeconds + ttlSeconds,
        nowEpochSeconds,
      );
  }

  requirePendingEffect(
    principalId: string,
    effectId: string,
    nowEpochSeconds: number,
  ): { effectId: string; effectDigest: string } {
    const row = this.db
      .prepare(`
        SELECT effect_id, effect_digest
        FROM pending_effect_approvals
        WHERE effect_id = ? AND principal_id = ? AND expires_at > ?
      `)
      .get(effectId, principalId, nowEpochSeconds) as
      | { effect_id: string; effect_digest: string }
      | undefined;
    if (row === undefined) {
      throw new AdmissionLabError(
        "pending_effect_not_found",
        "No live step-up request exists for this Principal and effect.",
        404,
      );
    }
    return { effectId: row.effect_id, effectDigest: row.effect_digest };
  }

  putEffectApproval(
    principalId: string,
    credentialId: string,
    effectId: string,
    effectDigest: string,
    nowEpochSeconds: number,
    ttlSeconds = 120,
  ): void {
    this.db
      .prepare(`
        INSERT INTO effect_approvals (
          effect_id, effect_digest, principal_id, credential_id,
          verified_at, expires_at, consumed_at
        ) VALUES (?, ?, ?, ?, ?, ?, NULL)
        ON CONFLICT(effect_id) DO UPDATE SET
          effect_digest = excluded.effect_digest,
          principal_id = excluded.principal_id,
          credential_id = excluded.credential_id,
          verified_at = excluded.verified_at,
          expires_at = excluded.expires_at,
          consumed_at = NULL
      `)
      .run(
        effectId,
        effectDigest,
        principalId,
        credentialId,
        nowEpochSeconds,
        nowEpochSeconds + ttlSeconds,
      );
  }

  lookupEffectApproval(
    principalId: string,
    effect: EffectRequest,
    nowEpochSeconds: number,
  ): VerifiedApproval {
    const row = this.db
      .prepare(`
        SELECT effect_id
        FROM effect_approvals
        WHERE effect_id = ?
          AND effect_digest = ?
          AND principal_id = ?
          AND consumed_at IS NULL
          AND expires_at > ?
      `)
      .get(effect.effectId, effect.effectDigest, principalId, nowEpochSeconds) as
      | { effect_id: string }
      | undefined;
    if (row === undefined) {
      return { verified: false, principalId: null, effectId: null, method: null };
    }
    return {
      verified: true,
      principalId,
      effectId: effect.effectId,
      method: "webauthn",
    };
  }

  consumeEffectApproval(
    principalId: string,
    effect: EffectRequest,
    nowEpochSeconds: number,
  ): void {
    this.db
      .prepare(`
        UPDATE effect_approvals
        SET consumed_at = ?
        WHERE effect_id = ?
          AND effect_digest = ?
          AND principal_id = ?
          AND consumed_at IS NULL
          AND expires_at > ?
      `)
      .run(
        nowEpochSeconds,
        effect.effectId,
        effect.effectDigest,
        principalId,
        nowEpochSeconds,
      );
  }
}
