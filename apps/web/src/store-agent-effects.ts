/** Transaction coordinator for local canary effects; no HTTP or WebStore dependency. */
import { randomUUID } from "node:crypto";
import type { DatabaseSync } from "node:sqlite";
import { WebProblem } from "./errors.ts";
import type { AgentEffectReceipt, AgentEffectRequest, AgentGrantSnapshot, CanaryNote } from "./model.ts";
import { scopeContains, type AgentGrantStore } from "./store-agent-grants.ts";
import { noteFromRow, type NoteRow } from "./store-row-projections.ts";
import type { EffectReceiptStore } from "./store-effect-receipts.ts";
import type { EffectApprovalStore } from "./store-effect-approvals.ts";
import { assertWrittenBusinessState, assertWrittenEffectApproval, requireSingleEffectWrite, type EffectApprovalRow } from "./store-effect-postconditions.ts";

export class AgentEffectStore {
  private readonly db: DatabaseSync;
  private readonly grants: AgentGrantStore;
  private readonly receipts: EffectReceiptStore;
  private readonly approvals: EffectApprovalStore;

  constructor(db: DatabaseSync, grants: AgentGrantStore, receipts: EffectReceiptStore, approvals: EffectApprovalStore) {
    this.db = db;
    this.grants = grants;
    this.receipts = receipts;
    this.approvals = approvals;
  }

  // OPA ALLOW is not the effect. Recheck concrete authority inside the
  // existing transaction before its write becomes visible.
  private assertCommitEffectBinding(
    current: AgentGrantSnapshot,
    selected: AgentGrantSnapshot,
    agentId: string,
    effect: AgentEffectRequest,
    expectedAction: string,
    expectedResource: string,
    expectedType: string,
  ): void {
    if (
      current.principalId !== selected.principalId ||
      current.agentId !== selected.agentId ||
      current.agentId !== agentId ||
      current.audience !== effect.audience ||
      !current.allowedActions.includes(effect.action) ||
      !current.resourcePrefixes.some((prefix) => scopeContains(prefix, effect.resource)) ||
      effect.action !== expectedAction ||
      effect.resource !== expectedResource ||
      effect.effectType !== expectedType
    ) {
      throw new WebProblem(
        403, "agent-effect-not-authorized", "Effect not authorized",
        "The current Agent Grant does not bind the concrete Effect and target.",
      );
    }
  }

  // One post-write protocol for both operations; the caller owns BEGIN/COMMIT.
  private finalizeNewEffect(
    current: AgentGrantSnapshot, agentId: string, effect: AgentEffectRequest,
    note: CanaryNote, now: number, approval: EffectApprovalRow | null,
  ): AgentEffectReceipt {
    requireSingleEffectWrite(this.db
      .prepare(
        "UPDATE agent_grants SET remaining_effects = remaining_effects - 1, revision = revision + 1 WHERE grant_id = ? AND revision = ?",
      )
      .run(current.grantId, current.revision).changes, "grant quota");
    // Missing, malformed or mismatched receipt rolls back the owner transaction.
    const receipt = this.receipts.recordNewEffectReceipt({
      effect_id: effect.effectId, effect_digest: effect.effectDigest,
      principal_id: current.principalId, agent_id: agentId, grant_id: current.grantId,
      action: effect.action, resource: effect.resource,
      result_json: JSON.stringify({ note }), committed_at: now,
    });
    if (approval !== null) assertWrittenEffectApproval(this.db, { ...approval, consumed_at: now });
    assertWrittenBusinessState(this.db, note, current, this.grants.getAgentGrant(current.grantId));
    return receipt;
  }

  // Historical replay is read-only on the common path. A miss is provisional
  // until the native writer lock is acquired; another connection may commit
  // the identity in between. Recheck before any mutable authority or writes.
  private commitOrReplay(
    agentId: string, effect: AgentEffectRequest, write: () => AgentEffectReceipt,
  ): { receipt: AgentEffectReceipt; replayed: boolean } {
    const existing = this.receipts.resolveAgentEffectReplay(agentId, effect);
    if (existing !== null) return { receipt: existing, replayed: true };

    this.db.exec("BEGIN IMMEDIATE");
    try {
      const committed = this.receipts.resolveAgentEffectReplay(agentId, effect);
      if (committed !== null) {
        this.db.exec("COMMIT");
        return { receipt: committed, replayed: true };
      }
      const receipt = write();
      this.db.exec("COMMIT");
      return { receipt, replayed: false };
    } catch (error) {
      // A failed acknowledgement is not evidence that COMMIT did not occur.
      // Only roll back a transaction that is still active; never auto-reissue.
      if (this.db.isTransaction) {
        try {
          this.db.exec("ROLLBACK");
        } catch (rollbackError) {
          throw new AggregateError([error, rollbackError], "Effect transaction and rollback failed");
        }
      }
      throw error;
    }
  }

  commitAgentCanaryCreate(
    grant: AgentGrantSnapshot,
    agentId: string,
    effect: AgentEffectRequest,
    content: string,
    now: number,
  ): { receipt: AgentEffectReceipt; replayed: boolean } {
    return this.commitOrReplay(agentId, effect, () => {
      const current = this.grants.getAgentGrant(grant.grantId);
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
      this.assertCommitEffectBinding(
        current, grant, agentId, effect,
        "canary.note.create", "/canary/notes", "website.canary.note.create",
      );
      const noteId = randomUUID();
      const note: CanaryNote = {
        noteId,
        principalId: current.principalId,
        content,
        state: "DRAFT",
        createdAt: now,
        publishedAt: null,
      };
      requireSingleEffectWrite(this.db
        .prepare(`
          INSERT INTO canary_notes (
            note_id, principal_id, content, state, created_at, published_at
          ) VALUES (?, ?, ?, 'DRAFT', ?, NULL)
        `)
        .run(note.noteId, note.principalId, note.content, note.createdAt).changes, "note creation");
      const receipt = this.finalizeNewEffect(current, agentId, effect, note, now, null);
      return receipt;
    });
  }

  commitAgentCanaryPublish(
    grant: AgentGrantSnapshot,
    agentId: string,
    effect: AgentEffectRequest,
    noteId: string,
    now: number,
  ): { receipt: AgentEffectReceipt; replayed: boolean } {
    return this.commitOrReplay(agentId, effect, () => {
      const current = this.grants.getAgentGrant(grant.grantId);
      const approval = this.approvals.readLiveApproval(current.principalId, effect, now);
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
      this.assertCommitEffectBinding(
        current, grant, agentId, effect,
        "canary.note.publish", "/canary/notes/" + noteId, "website.canary.note.publish",
      );
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
      requireSingleEffectWrite(this.db
        .prepare(
          "UPDATE canary_notes SET state = 'PUBLISHED', published_at = ? WHERE note_id = ?",
        )
        .run(now, noteId).changes, "note publication");
      this.approvals.consumeApproval(effect.effectId, now);
      const note = noteFromRow({ ...noteRow, state: "PUBLISHED", published_at: now });
      const receipt = this.finalizeNewEffect(current, agentId, effect, note, now, approval);
      return receipt;
    });
  }
}
