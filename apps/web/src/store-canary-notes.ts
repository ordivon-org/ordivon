/** Owner-local Note operations. Callers own business admission and transactions. */
import { randomUUID } from "node:crypto";
import { isDeepStrictEqual } from "node:util";
import type { DatabaseSync } from "node:sqlite";
import type { CanaryNote } from "./model.ts";
import { noteFromRow, type NoteRow } from "./store-row-projections.ts";

export function newCanaryDraft(principalId: string, content: string, now: number): CanaryNote {
  return {
    noteId: randomUUID(), principalId, content, state: "DRAFT",
    createdAt: now, publishedAt: null,
  };
}

export function insertCanaryDraft(db: DatabaseSync, note: CanaryNote): number | bigint {
  return db.prepare(`
    INSERT INTO canary_notes (
      note_id, principal_id, content, state, created_at, published_at
    ) VALUES (?, ?, ?, 'DRAFT', ?, NULL)
  `).run(note.noteId, note.principalId, note.content, note.createdAt).changes;
}

export function readPrincipalNoteRow(db: DatabaseSync, noteId: string, principalId: string): NoteRow | undefined {
  return db.prepare("SELECT * FROM canary_notes WHERE note_id = ? AND principal_id = ?")
    .get(noteId, principalId) as NoteRow | undefined;
}

export function publishCanaryDraft(db: DatabaseSync, noteId: string, now: number): number | bigint {
  return db.prepare("UPDATE canary_notes SET state = 'PUBLISHED', published_at = ? WHERE note_id = ?")
    .run(now, noteId).changes;
}

export function listPrincipalCanaryNotes(db: DatabaseSync, principalId: string): CanaryNote[] {
  const rows = db.prepare("SELECT * FROM canary_notes WHERE principal_id = ? ORDER BY created_at DESC, note_id ASC")
    .all(principalId) as unknown as NoteRow[];
  return rows.map(noteFromRow);
}

/** Compare the exact intended local Note after all writes in the transaction. */
export function matchesStoredCanaryNote(db: DatabaseSync, note: CanaryNote): boolean {
  const row = readPrincipalNoteRow(db, note.noteId, note.principalId);
  return row !== undefined && isDeepStrictEqual(noteFromRow(row), note);
}
