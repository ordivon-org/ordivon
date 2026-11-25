/** Approval lifecycle for the existing owner-local database. */
import type { DatabaseSync } from "node:sqlite";
import { WebProblem } from "./errors.ts";
import type { AgentEffectRequest } from "./model.ts";
import { requireSingleEffectWrite, type EffectApprovalRow } from "./store-effect-postconditions.ts";

export class EffectApprovalStore {
  private readonly db: DatabaseSync;

  constructor(db: DatabaseSync) {
    this.db = db;
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
          AND NOT EXISTS (
            SELECT 1 FROM agent_effects
            WHERE agent_effects.effect_id = pending_effect_approvals.effect_id
          )
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
    // Preserve terminal consumption evidence in the same native statement.
    // A late approval must not reopen a committed effect or replace its binding.
    const update = this.db
      .prepare(`
        INSERT INTO effect_approvals (
          effect_id, effect_digest, principal_id, credential_id,
          verified_at, expires_at, consumed_at
        ) SELECT ?, ?, ?, ?, ?, ?, NULL
        WHERE NOT EXISTS (SELECT 1 FROM agent_effects WHERE effect_id = ?)
        ON CONFLICT(effect_id) DO UPDATE SET
          credential_id = excluded.credential_id,
          verified_at = excluded.verified_at,
          expires_at = excluded.expires_at
        WHERE effect_approvals.consumed_at IS NULL
          AND effect_approvals.effect_digest = excluded.effect_digest
          AND effect_approvals.principal_id = excluded.principal_id
      `)
      .run(
        effectId,
        effectDigest,
        principalId,
        credentialId,
        now,
        now + ttlSeconds,
        effectId,
      );
    if (update.changes !== 1) {
      throw new WebProblem(
        409, "effect-approval-closed", "Effect approval unavailable",
        "The Effect is already committed or the approval binding is no longer writable.",
      );
    }
  }

  effectApproval(
    principalId: string,
    effect: AgentEffectRequest,
    now: number,
  ): { verified: boolean; principalId: string | null; effectId: string | null; effectDigest: string | null; method: "webauthn" | null } {
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
      ? { verified: false, principalId: null, effectId: null, effectDigest: null, method: null }
      : {
          verified: true,
          principalId,
          effectId: effect.effectId,
          effectDigest: effect.effectDigest,
          method: "webauthn",
        };
  }

  readLiveApproval(principalId: string, effect: AgentEffectRequest, now: number): EffectApprovalRow | undefined {
    return this.db.prepare(`
      SELECT * FROM effect_approvals
      WHERE effect_id = ? AND effect_digest = ? AND principal_id = ?
        AND consumed_at IS NULL AND expires_at > ?
    `).get(effect.effectId, effect.effectDigest, principalId, now) as EffectApprovalRow | undefined;
  }

  consumeApproval(effectId: string, now: number): void {
    requireSingleEffectWrite(this.db.prepare(
      "UPDATE effect_approvals SET consumed_at = ? WHERE effect_id = ? AND consumed_at IS NULL",
    ).run(now, effectId).changes, "approval consumption");
  }
}
