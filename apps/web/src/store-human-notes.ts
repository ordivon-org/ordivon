/** Human Note persistence only; HTTP admission remains with the existing route. */
import { randomUUID } from "node:crypto";
import { isDeepStrictEqual } from "node:util";
import type { DatabaseSync } from "node:sqlite";
import { WebProblem } from "./errors.ts";
import type { CanaryNote } from "./model.ts";
import { insertAuditRow, type EffectAuditRow } from "./store-audit.ts";
import { insertCanaryDraft, matchesStoredCanaryNote, newCanaryDraft } from "./store-canary-notes.ts";
import { runOwnerTransaction } from "./store-owner-transaction.ts";

function requireSingleNoteWrite(changes: number | bigint): void {
  if (changes !== 1 && changes !== 1n) {
    throw new WebProblem(500, "note-write-not-applied", "Note write not applied",
      "The new local Note and its audit must each affect exactly one row.");
  }
}

export function createHumanCanaryDraft(db: DatabaseSync, principalId: string, content: string, now: number): CanaryNote {
  return runOwnerTransaction(db, "note", () => {
    const note = newCanaryDraft(principalId, content, now);
    requireSingleNoteWrite(insertCanaryDraft(db, note));
    const audit: EffectAuditRow = {
      event_id: randomUUID(), principal_id: principalId, event_type: "canary.note.created",
      object_type: "canary-note", object_id: note.noteId, detail_json: "{}", created_at: now,
    };
    requireSingleNoteWrite(insertAuditRow(db, audit));
    const rows = db.prepare(`
      SELECT * FROM audit_events
      WHERE event_type = 'canary.note.created' AND object_type = 'canary-note' AND object_id = ?
      LIMIT 2
    `).all(note.noteId);
    if (rows.length !== 1 || !isDeepStrictEqual({ ...rows[0] }, audit)) {
      throw new WebProblem(500, "note-audit-mismatch", "Note audit mismatch",
        "The new local Note must have exactly its intended audit record.");
    }
    if (!matchesStoredCanaryNote(db, note)) {
      throw new WebProblem(500, "note-business-mismatch", "Note business state mismatch",
        "The new local Note does not match its intended state.");
    }
    return note;
  });
}
