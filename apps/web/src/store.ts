import { randomUUID } from "node:crypto";
import { DatabaseSync } from "node:sqlite";

import { hashToken, stableDigest } from "./identity-digests.ts";
import { WebProblem } from "./errors.ts";
import { AgentGrantStore } from "./store-agent-grants.ts";
import { SessionStore } from "./store-sessions.ts";
import { initializeWebStoreSchema } from "./store-schema.ts";
import type {
  AgentEffectReceipt,
  AgentEffectRequest,
  AgentGrantCreate,
  AgentGrantSnapshot,
  AuthenticatedSession,
  CanaryNote,
  ChallengePurpose,
  ChallengeRecord,
  Principal,
  SessionView,
  StoredCredential,
} from "./model.ts";

import {
  principalFromRow,
  credentialFromRow,
  noteFromRow,
  effectReceiptFromRow,
} from "./store-row-projections.ts";
import type {
  PrincipalRow,
  CredentialRow,
  ChallengeRow,
  AgentEffectRow,
  NoteRow,
} from "./store-row-projections.ts";

export class WebStore {
  readonly db: DatabaseSync;
  private readonly grants: AgentGrantStore;
  private readonly sessions: SessionStore;

  constructor(path: string) {
    this.db = new DatabaseSync(path);
    initializeWebStoreSchema(this.db);
    this.grants = new AgentGrantStore(this.db, (...args) => this.audit(...args));
    this.sessions = new SessionStore(this.db, (...args) => this.audit(...args), (id) => this.getPrincipal(id));
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
    payload: unknown = {},
  ): ChallengeRecord {
    const challengeId = randomUUID();
    const payloadDigest = stableDigest(payload);
    const record: ChallengeRecord = {
      challengeId,
      purpose,
      principalId,
      challenge,
      payloadDigest,
      payload,
      expiresAt: now + ttlSeconds,
    };
    this.db
      .prepare(`
        INSERT INTO webauthn_challenges (
          challenge_id, purpose, principal_id, challenge,
          payload_digest, payload_json, expires_at, consumed_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, NULL)
      `)
      .run(
        record.challengeId,
        record.purpose,
        record.principalId,
        record.challenge,
        record.payloadDigest,
        JSON.stringify(record.payload),
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
        payloadDigest: row.payload_digest,
        payload: JSON.parse(row.payload_json) as unknown,
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
    return this.sessions.createSession(principalId, now, idleSeconds, absoluteSeconds, userAgent);
  }

  authenticateSession(
    token: string,
    now: number,
    idleSeconds: number,
  ): AuthenticatedSession {
    return this.sessions.authenticateSession(token, now, idleSeconds);
  }

  listSessions(principalId: string): SessionView[] {
    return this.sessions.listSessions(principalId);
  }

  revokeSession(
    principalId: string,
    sessionId: string,
    now: number,
  ): boolean {
    return this.sessions.revokeSession(principalId, sessionId, now);
  }

  revokeAllSessions(principalId: string, now: number): number {
    return this.sessions.revokeAllSessions(principalId, now);
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

  consumeDpopProof(
    proofId: string,
    nowEpochSeconds: number,
    ttlSeconds = 600,
  ): void {
    const bytes = Buffer.byteLength(proofId, "utf8");
    if (
      bytes < 1 ||
      bytes > 256 ||
      !Number.isSafeInteger(ttlSeconds) ||
      ttlSeconds < 1
    ) {
      throw new WebProblem(
        401,
        "dpop-proof-invalid",
        "Agent verification failed",
        "The DPoP proof identity is invalid.",
      );
    }
    const proofHash = hashToken(proofId);
    this.db.exec("BEGIN IMMEDIATE");
    try {
      this.db
        .prepare("DELETE FROM dpop_proofs WHERE expires_at <= ?")
        .run(nowEpochSeconds);
      const existing = this.db
        .prepare("SELECT proof_hash FROM dpop_proofs WHERE proof_hash = ?")
        .get(proofHash);
      if (existing !== undefined) {
        throw new WebProblem(
          401,
          "dpop-proof-replayed",
          "Agent verification failed",
          "The DPoP proof has already been consumed.",
        );
      }
      this.db
        .prepare("INSERT INTO dpop_proofs (proof_hash, expires_at) VALUES (?, ?)")
        .run(proofHash, nowEpochSeconds + ttlSeconds);
      this.db.exec("COMMIT");
    } catch (error) {
      this.db.exec("ROLLBACK");
      throw error;
    }
  }

  createAgentGrant(input: AgentGrantCreate, now: number): AgentGrantSnapshot {
    return this.grants.createAgentGrant(input, now);
  }

  getAgentGrant(grantId: string): AgentGrantSnapshot {
    return this.grants.getAgentGrant(grantId);
  }

  listAgentGrants(principalId: string): AgentGrantSnapshot[] {
    return this.grants.listAgentGrants(principalId);
  }

  revokeAgentGrant(
    principalId: string,
    grantId: string,
    expectedDigest: string,
    now: number,
  ): AgentGrantSnapshot {
    return this.grants.revokeAgentGrant(principalId, grantId, expectedDigest, now);
  }

  resolveAgentGrant(
    agentId: string,
    audience: string,
    action: string,
    resource: string,
    now: number,
  ): AgentGrantSnapshot {
    return this.grants.resolveAgentGrant(agentId, audience, action, resource, now);
  }

  getAgentEffect(effectId: string): AgentEffectReceipt | null {
    const row = this.db
      .prepare("SELECT * FROM agent_effects WHERE effect_id = ?")
      .get(effectId) as AgentEffectRow | undefined;
    return row === undefined ? null : effectReceiptFromRow(row);
  }

  resolveAgentEffectReplay(
    agentId: string,
    effect: AgentEffectRequest,
  ): AgentEffectReceipt | null {
    const existing = this.getAgentEffect(effect.effectId);
    if (existing === null) return null;
    if (existing.agentId !== agentId) {
      throw new WebProblem(
        403,
        "effect-actor-mismatch",
        "Effect actor mismatch",
        "The committed effect belongs to a different Agent.",
      );
    }
    if (existing.effectDigest !== effect.effectDigest) {
      throw new WebProblem(
        409,
        "effect-conflict",
        "Effect conflict",
        "The effect identifier is already bound to different content.",
      );
    }
    return existing;
  }

  registerPendingEffectApproval(
    principalId: string,
    effect: AgentEffectRequest,
    now: number,
    ttlSeconds = 300,
  ): void {
    const existing = this.db
      .prepare(
        "SELECT effect_digest, principal_id FROM pending_effect_approvals WHERE effect_id = ?",
      )
      .get(effect.effectId) as
      | { effect_digest: string; principal_id: string }
      | undefined;
    if (
      existing !== undefined &&
      (existing.effect_digest !== effect.effectDigest ||
        existing.principal_id !== principalId)
    ) {
      throw new WebProblem(
        409,
        "pending-effect-conflict",
        "Pending effect conflict",
        "The effect identifier is already bound to a different Principal or digest.",
      );
    }
    this.db
      .prepare(`
        INSERT INTO pending_effect_approvals (
          effect_id, effect_digest, principal_id, expires_at, created_at
        ) VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(effect_id) DO UPDATE SET
          expires_at = excluded.expires_at
      `)
      .run(
        effect.effectId,
        effect.effectDigest,
        principalId,
        now + ttlSeconds,
        now,
      );
  }

  requirePendingEffectApproval(
    principalId: string,
    effectId: string,
    now: number,
  ): { effectId: string; effectDigest: string } {
    const row = this.db
      .prepare(`
        SELECT effect_id, effect_digest
        FROM pending_effect_approvals
        WHERE effect_id = ? AND principal_id = ? AND expires_at > ?
      `)
      .get(effectId, principalId, now) as
      | { effect_id: string; effect_digest: string }
      | undefined;
    if (row === undefined) {
      throw new WebProblem(
        404,
        "pending-effect-not-found",
        "Pending effect not found",
        "No live step-up request exists for this Principal and effect.",
      );
    }
    return { effectId: row.effect_id, effectDigest: row.effect_digest };
  }

  putEffectApproval(
    principalId: string,
    credentialId: string,
    effectId: string,
    effectDigest: string,
    now: number,
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
        now,
        now + ttlSeconds,
      );
  }

  effectApproval(
    principalId: string,
    effect: AgentEffectRequest,
    now: number,
  ): { verified: boolean; principalId: string | null; effectId: string | null; method: "webauthn" | null } {
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
      .get(effect.effectId, effect.effectDigest, principalId, now) as
      | { effect_id: string }
      | undefined;
    return row === undefined
      ? { verified: false, principalId: null, effectId: null, method: null }
      : {
          verified: true,
          principalId,
          effectId: effect.effectId,
          method: "webauthn",
        };
  }

  commitAgentCanaryCreate(
    grant: AgentGrantSnapshot,
    agentId: string,
    effect: AgentEffectRequest,
    content: string,
    now: number,
  ): { receipt: AgentEffectReceipt; replayed: boolean } {
    // Reuse the same exact actor/digest replay contract as the admission surface.
    const existing = this.resolveAgentEffectReplay(agentId, effect);
    if (existing !== null) {
      return { receipt: existing, replayed: true };
    }

    this.db.exec("BEGIN IMMEDIATE");
    try {
      const current = this.getAgentGrant(grant.grantId);
      if (
        current.grantDigest !== grant.grantDigest ||
        current.revision !== grant.revision ||
        !current.active ||
        current.expiresAtEpochSeconds <= now ||
        current.remainingEffects <= 0
      ) {
        throw new WebProblem(
          409,
          "agent-grant-changed",
          "Agent Grant changed",
          "Mutable Agent authority changed before the Effect commit fence.",
        );
      }
      const noteId = randomUUID();
      const note: CanaryNote = {
        noteId,
        principalId: current.principalId,
        content,
        state: "DRAFT",
        createdAt: now,
        publishedAt: null,
      };
      this.db
        .prepare(`
          INSERT INTO canary_notes (
            note_id, principal_id, content, state, created_at, published_at
          ) VALUES (?, ?, ?, 'DRAFT', ?, NULL)
        `)
        .run(note.noteId, note.principalId, note.content, note.createdAt);
      this.db
        .prepare(
          "UPDATE agent_grants SET remaining_effects = remaining_effects - 1, revision = revision + 1 WHERE grant_id = ? AND revision = ?",
        )
        .run(current.grantId, current.revision);
      const result = { note };
      this.db
        .prepare(`
          INSERT INTO agent_effects (
            effect_id, effect_digest, principal_id, agent_id, grant_id,
            action, resource, result_json, committed_at
          ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        `)
        .run(
          effect.effectId,
          effect.effectDigest,
          current.principalId,
          agentId,
          current.grantId,
          effect.action,
          effect.resource,
          JSON.stringify(result),
          now,
        );
      this.audit("agent.effect.committed", now, current.principalId, "effect", effect.effectId, {
        agentId,
        grantId: current.grantId,
        action: effect.action,
      });
      this.db.exec("COMMIT");
      return { receipt: this.getAgentEffect(effect.effectId)!, replayed: false };
    } catch (error) {
      this.db.exec("ROLLBACK");
      throw error;
    }
  }

  commitAgentCanaryPublish(
    grant: AgentGrantSnapshot,
    agentId: string,
    effect: AgentEffectRequest,
    noteId: string,
    now: number,
  ): { receipt: AgentEffectReceipt; replayed: boolean } {
    // Reuse the same exact actor/digest replay contract as the admission surface.
    const existing = this.resolveAgentEffectReplay(agentId, effect);
    if (existing !== null) {
      return { receipt: existing, replayed: true };
    }

    this.db.exec("BEGIN IMMEDIATE");
    try {
      const current = this.getAgentGrant(grant.grantId);
      const approval = this.db
        .prepare(`
          SELECT effect_id FROM effect_approvals
          WHERE effect_id = ?
            AND effect_digest = ?
            AND principal_id = ?
            AND consumed_at IS NULL
            AND expires_at > ?
        `)
        .get(effect.effectId, effect.effectDigest, current.principalId, now) as
        | { effect_id: string }
        | undefined;
      if (
        current.grantDigest !== grant.grantDigest ||
        current.revision !== grant.revision ||
        !current.active ||
        current.expiresAtEpochSeconds <= now ||
        current.remainingEffects <= 0 ||
        approval === undefined
      ) {
        throw new WebProblem(
          409,
          "effect-fence-rejected",
          "Effect fence rejected",
          "Mutable authority or the effect-bound approval changed before commit.",
        );
      }
      const noteRow = this.db
        .prepare("SELECT * FROM canary_notes WHERE note_id = ? AND principal_id = ?")
        .get(noteId, current.principalId) as NoteRow | undefined;
      if (noteRow === undefined || noteRow.state !== "DRAFT") {
        throw new WebProblem(
          409,
          "canary-note-not-publishable",
          "Canary note not publishable",
          "The requested canary note is missing or no longer a draft.",
        );
      }
      this.db
        .prepare(
          "UPDATE canary_notes SET state = 'PUBLISHED', published_at = ? WHERE note_id = ?",
        )
        .run(now, noteId);
      this.db
        .prepare(
          "UPDATE effect_approvals SET consumed_at = ? WHERE effect_id = ? AND consumed_at IS NULL",
        )
        .run(now, effect.effectId);
      this.db
        .prepare(
          "UPDATE agent_grants SET remaining_effects = remaining_effects - 1, revision = revision + 1 WHERE grant_id = ? AND revision = ?",
        )
        .run(current.grantId, current.revision);
      const result = { note: noteFromRow({ ...noteRow, state: "PUBLISHED", published_at: now }) };
      this.db
        .prepare(`
          INSERT INTO agent_effects (
            effect_id, effect_digest, principal_id, agent_id, grant_id,
            action, resource, result_json, committed_at
          ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        `)
        .run(
          effect.effectId,
          effect.effectDigest,
          current.principalId,
          agentId,
          current.grantId,
          effect.action,
          effect.resource,
          JSON.stringify(result),
          now,
        );
      this.audit("agent.effect.committed", now, current.principalId, "effect", effect.effectId, {
        agentId,
        grantId: current.grantId,
        action: effect.action,
      });
      this.db.exec("COMMIT");
      return { receipt: this.getAgentEffect(effect.effectId)!, replayed: false };
    } catch (error) {
      this.db.exec("ROLLBACK");
      throw error;
    }
  }
}
