import { randomUUID } from "node:crypto";
import { DatabaseSync } from "node:sqlite";

import { consumeDpopProof } from "./store-dpop-proofs.ts";
import { WebProblem } from "./errors.ts";
import { requireUsableOwnerConnection } from "./store-connection-health.ts";
import { AgentGrantStore } from "./store-agent-grants.ts";
import { SessionStore } from "./store-sessions.ts";
import { ChallengeStore } from "./store-challenges.ts";
import { initializeWebStoreSchema } from "./store-schema.ts";
import { EffectReceiptStore } from "./store-effect-receipts.ts";
import { insertAuditRow } from "./store-audit.ts";
import { EffectApprovalStore } from "./store-effect-approvals.ts";
import { AgentEffectStore } from "./store-agent-effects.ts";
import { listPrincipalCanaryNotes } from "./store-canary-notes.ts";
import { createHumanCanaryDraft } from "./store-human-notes.ts";
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
  // Native handle retained for owner lifecycle and native test instrumentation.
  // Product operations below must go through the health-checked owner accessor.
  readonly db: DatabaseSync;
  private readonly components: {
    db: DatabaseSync;
    grants: AgentGrantStore;
    sessions: SessionStore;
    challenges: ChallengeStore;
    receipts: EffectReceiptStore;
    approvals: EffectApprovalStore;
    effects: AgentEffectStore;
  };

  constructor(path: string) {
    this.db = new DatabaseSync(path);
    initializeWebStoreSchema(this.db);
    const grants = new AgentGrantStore(this.db, (...args) => this.audit(...args));
    const receipts = new EffectReceiptStore(this.db);
    const approvals = new EffectApprovalStore(this.db);
    this.components = {
      db: this.db, grants, receipts, approvals,
      challenges: new ChallengeStore(this.db),
      effects: new AgentEffectStore(this.db, grants, receipts, approvals),
      sessions: new SessionStore(this.db, (...args) => this.audit(...args), (id) => this.getPrincipal(id)),
    };
  }

  private get owner(): WebStore["components"] {
    requireUsableOwnerConnection(this.db);
    return this.components;
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
    return insertAuditRow(this.owner.db, {
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
    const row = this.owner.db
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
    this.owner.db
      .prepare(
        "INSERT INTO principals (principal_id, user_name, display_name, created_at) VALUES (?, ?, ?, ?)",
      )
      .run(principalId, userName, displayName, now);
    this.audit("principal.created", now, principalId, "principal", principalId, {});
    return { principalId, userName, displayName };
  }

  getPrincipal(principalId: string): Principal {
    const row = this.owner.db
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
    const row = this.owner.db
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
    const rows = this.owner.db
      .prepare(
        "SELECT * FROM webauthn_credentials WHERE principal_id = ? ORDER BY created_at",
      )
      .all(principalId) as unknown as CredentialRow[];
    return rows.map(credentialFromRow);
  }

  getActiveCredential(credentialId: string): StoredCredential {
    const row = this.owner.db
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
    this.owner.db
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
    const result = this.owner.db
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
    return this.owner.challenges.createChallenge(purpose, principalId, challenge, now, ttlSeconds, payload);
  }

  consumeChallenge(
    challengeId: string,
    purpose: ChallengePurpose,
    now: number,
  ): ChallengeRecord {
    return this.owner.challenges.consumeChallenge(challengeId, purpose, now);
  }

  createSession(
    principalId: string,
    now: number,
    idleSeconds: number,
    absoluteSeconds: number,
    userAgent: string | null,
  ): { token: string; session: SessionView } {
    return this.owner.sessions.createSession(principalId, now, idleSeconds, absoluteSeconds, userAgent);
  }

  authenticateSession(
    token: string,
    now: number,
    idleSeconds: number,
  ): AuthenticatedSession {
    return this.owner.sessions.authenticateSession(token, now, idleSeconds);
  }

  listSessions(principalId: string): SessionView[] {
    return this.owner.sessions.listSessions(principalId);
  }

  revokeSession(
    principalId: string,
    sessionId: string,
    now: number,
  ): boolean {
    return this.owner.sessions.revokeSession(principalId, sessionId, now);
  }

  revokeAllSessions(principalId: string, now: number): number {
    return this.owner.sessions.revokeAllSessions(principalId, now);
  }

  createCanaryNote(
    principalId: string,
    content: string,
    now: number,
  ): CanaryNote {
    return createHumanCanaryDraft(this.owner.db, principalId, content, now);
  }

  listCanaryNotes(principalId: string): CanaryNote[] {
    return listPrincipalCanaryNotes(this.owner.db, principalId);
  }

  consumeDpopProof(proofId: string, nowEpochSeconds: number, ttlSeconds = 600): void {
    consumeDpopProof(this.owner.db, proofId, nowEpochSeconds, ttlSeconds);
  }

  createAgentGrant(input: AgentGrantCreate, now: number): AgentGrantSnapshot {
    return this.owner.grants.createAgentGrant(input, now);
  }

  getAgentGrant(grantId: string): AgentGrantSnapshot {
    return this.owner.grants.getAgentGrant(grantId);
  }

  listAgentGrants(principalId: string): AgentGrantSnapshot[] {
    return this.owner.grants.listAgentGrants(principalId);
  }

  revokeAgentGrant(
    principalId: string,
    grantId: string,
    expectedDigest: string,
    now: number,
  ): AgentGrantSnapshot {
    return this.owner.grants.revokeAgentGrant(principalId, grantId, expectedDigest, now);
  }

  resolveAgentGrant(
    agentId: string,
    audience: string,
    action: string,
    resource: string,
    now: number,
  ): AgentGrantSnapshot {
    return this.owner.grants.resolveAgentGrant(agentId, audience, action, resource, now);
  }

  getAgentEffect(effectId: string): AgentEffectReceipt | null {
    return this.owner.receipts.getAgentEffect(effectId);
  }

  resolveAgentEffectReplay(agentId: string, effect: AgentEffectRequest): AgentEffectReceipt | null {
    return this.owner.receipts.resolveAgentEffectReplay(agentId, effect);
  }

  registerPendingEffectApproval(principalId: string, effect: AgentEffectRequest, now: number, ttlSeconds = 300): void {
    this.owner.approvals.registerPendingEffectApproval(principalId, effect, now, ttlSeconds);
  }

  requirePendingEffectApproval(principalId: string, effectId: string, now: number): { effectId: string; effectDigest: string } {
    return this.owner.approvals.requirePendingEffectApproval(principalId, effectId, now);
  }

  putEffectApproval(principalId: string, credentialId: string, effectId: string, effectDigest: string, now: number, ttlSeconds = 120): void {
    this.owner.approvals.putEffectApproval(principalId, credentialId, effectId, effectDigest, now, ttlSeconds);
  }

  effectApproval(principalId: string, effect: AgentEffectRequest, now: number): ReturnType<EffectApprovalStore["effectApproval"]> {
    return this.owner.approvals.effectApproval(principalId, effect, now);
  }

  commitAgentCanaryCreate(grant: AgentGrantSnapshot, agentId: string, effect: AgentEffectRequest, content: string, now: number): { receipt: AgentEffectReceipt; replayed: boolean } {
    return this.owner.effects.commitAgentCanaryCreate(grant, agentId, effect, content, now);
  }

  commitAgentCanaryPublish(grant: AgentGrantSnapshot, agentId: string, effect: AgentEffectRequest, noteId: string, now: number): { receipt: AgentEffectReceipt; replayed: boolean } {
    return this.owner.effects.commitAgentCanaryPublish(grant, agentId, effect, noteId, now);
  }
}
