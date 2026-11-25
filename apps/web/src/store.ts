import { randomUUID } from "node:crypto";
import { DatabaseSync } from "node:sqlite";

import { hashToken } from "./identity-digests.ts";
import { WebProblem } from "./errors.ts";
import { AgentGrantStore } from "./store-agent-grants.ts";
import { SessionStore } from "./store-sessions.ts";
import { ChallengeStore } from "./store-challenges.ts";
import { initializeWebStoreSchema } from "./store-schema.ts";
import { EffectReceiptStore } from "./store-effect-receipts.ts";
import { insertAuditRow } from "./store-audit.ts";
import { EffectApprovalStore } from "./store-effect-approvals.ts";
import { AgentEffectStore } from "./store-agent-effects.ts";
import { newCanaryDraft, insertCanaryDraft, listPrincipalCanaryNotes } from "./store-canary-notes.ts";
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
} from "./store-row-projections.ts";
import type {
  PrincipalRow,
  CredentialRow,
} from "./store-row-projections.ts";

export class WebStore {
  readonly db: DatabaseSync;
  private readonly grants: AgentGrantStore;
  private readonly sessions: SessionStore;
  private readonly challenges: ChallengeStore;
  private readonly receipts: EffectReceiptStore;
  private readonly approvals: EffectApprovalStore;
  private readonly effects: AgentEffectStore;

  constructor(path: string) {
    this.db = new DatabaseSync(path);
    initializeWebStoreSchema(this.db);
    this.grants = new AgentGrantStore(this.db, (...args) => this.audit(...args));
    this.challenges = new ChallengeStore(this.db);
    this.receipts = new EffectReceiptStore(this.db);
    this.approvals = new EffectApprovalStore(this.db);
    this.effects = new AgentEffectStore(this.db, this.grants, this.receipts, this.approvals);
    this.sessions = new SessionStore(this.db, (...args) => this.audit(...args), (id) => this.getPrincipal(id));
  }

  close(): void {
    if (this.db.isOpen) this.db.close();
  }

  audit(
    eventType: string,
    now: number,
    principalId: string | null,
    objectType: string | null,
    objectId: string | null,
    detail: unknown,
  ): number | bigint {
    return insertAuditRow(this.db, {
      event_id: randomUUID(), principal_id: principalId, event_type: eventType,
      object_type: objectType, object_id: objectId, detail_json: JSON.stringify(detail),
      created_at: now,
    });
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
    return this.challenges.createChallenge(purpose, principalId, challenge, now, ttlSeconds, payload);
  }

  consumeChallenge(
    challengeId: string,
    purpose: ChallengePurpose,
    now: number,
  ): ChallengeRecord {
    return this.challenges.consumeChallenge(challengeId, purpose, now);
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
    const note = newCanaryDraft(principalId, content, now);
    insertCanaryDraft(this.db, note);
    this.audit("canary.note.created", now, principalId, "canary-note", note.noteId, {});
    return note;
  }

  listCanaryNotes(principalId: string): CanaryNote[] {
    return listPrincipalCanaryNotes(this.db, principalId);
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
    return this.receipts.getAgentEffect(effectId);
  }

  resolveAgentEffectReplay(agentId: string, effect: AgentEffectRequest): AgentEffectReceipt | null {
    return this.receipts.resolveAgentEffectReplay(agentId, effect);
  }

  registerPendingEffectApproval(principalId: string, effect: AgentEffectRequest, now: number, ttlSeconds = 300): void {
    this.approvals.registerPendingEffectApproval(principalId, effect, now, ttlSeconds);
  }

  requirePendingEffectApproval(principalId: string, effectId: string, now: number): { effectId: string; effectDigest: string } {
    return this.approvals.requirePendingEffectApproval(principalId, effectId, now);
  }

  putEffectApproval(principalId: string, credentialId: string, effectId: string, effectDigest: string, now: number, ttlSeconds = 120): void {
    this.approvals.putEffectApproval(principalId, credentialId, effectId, effectDigest, now, ttlSeconds);
  }

  effectApproval(principalId: string, effect: AgentEffectRequest, now: number): ReturnType<EffectApprovalStore["effectApproval"]> {
    return this.approvals.effectApproval(principalId, effect, now);
  }

  commitAgentCanaryCreate(grant: AgentGrantSnapshot, agentId: string, effect: AgentEffectRequest, content: string, now: number): { receipt: AgentEffectReceipt; replayed: boolean } {
    return this.effects.commitAgentCanaryCreate(grant, agentId, effect, content, now);
  }

  commitAgentCanaryPublish(grant: AgentGrantSnapshot, agentId: string, effect: AgentEffectRequest, noteId: string, now: number): { receipt: AgentEffectReceipt; replayed: boolean } {
    return this.effects.commitAgentCanaryPublish(grant, agentId, effect, noteId, now);
  }
}
