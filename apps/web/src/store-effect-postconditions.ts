// Transaction-local observations; caller retains all write and commit authority.
import type { DatabaseSync } from "node:sqlite";
import { isDeepStrictEqual } from "node:util";
import { WebProblem } from "./errors.ts";
import type { AgentGrantSnapshot, CanaryNote } from "./model.ts";
import { noteFromRow, type NoteRow } from "./store-row-projections.ts";

export type EffectAuditRow = {
  event_id: string;
  principal_id: string | null;
  event_type: string;
  object_type: string | null;
  object_id: string | null;
  detail_json: string;
  created_at: number;
};

export type EffectApprovalRow = {
  effect_id: string;
  effect_digest: string;
  principal_id: string;
  credential_id: string;
  verified_at: number;
  expires_at: number;
  consumed_at: number | null;
};

export function assertWrittenEffectAudit(db: DatabaseSync, expected: EffectAuditRow): void {
  const rows = db.prepare(`
    SELECT * FROM audit_events
    WHERE event_type = 'agent.effect.committed' AND object_type = 'effect' AND object_id = ?
  `).all(expected.object_id);
  if (rows.length !== 1 || !isDeepStrictEqual({ ...rows[0] }, expected)) {
    throw new WebProblem(500, "effect-audit-mismatch", "Effect audit mismatch",
      "The new local Effect must have exactly its intended committed audit record.");
  }
}

export function assertWrittenEffectApproval(db: DatabaseSync, expected: EffectApprovalRow): void {
  const row = db.prepare("SELECT * FROM effect_approvals WHERE effect_id = ?").get(expected.effect_id);
  if (row === undefined || !isDeepStrictEqual({ ...row }, expected)) {
    throw new WebProblem(500, "effect-approval-mismatch", "Effect approval mismatch",
      "The consumed approval does not match its intended terminal state.");
  }
}

export function assertWrittenBusinessState(
  db: DatabaseSync, note: CanaryNote, prior: AgentGrantSnapshot, observedGrant: AgentGrantSnapshot,
): void {
  const row = db.prepare("SELECT * FROM canary_notes WHERE note_id = ?")
    .get(note.noteId) as NoteRow | undefined;
  const expectedGrant = {
    ...prior, remainingEffects: prior.remainingEffects - 1, revision: prior.revision + 1,
  };
  if (row === undefined || !isDeepStrictEqual(noteFromRow(row), note) ||
      !isDeepStrictEqual(observedGrant, expectedGrant)) {
    throw new WebProblem(500, "effect-business-mismatch", "Effect business state mismatch",
      "The newly written note or Grant does not match the intended local Effect.");
  }
}
