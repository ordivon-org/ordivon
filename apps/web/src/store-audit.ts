/** Shared native audit insertion, without transaction ownership. */
import type { DatabaseSync } from "node:sqlite";

export type EffectAuditRow = {
  event_id: string;
  principal_id: string | null;
  event_type: string;
  object_type: string | null;
  object_id: string | null;
  detail_json: string;
  created_at: number;
};

export function insertAuditRow(db: DatabaseSync, row: EffectAuditRow): number | bigint {
  return db.prepare(`
    INSERT INTO audit_events (
      event_id, principal_id, event_type, object_type, object_id, detail_json, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?)
  `).run(row.event_id, row.principal_id, row.event_type, row.object_type,
    row.object_id, row.detail_json, row.created_at).changes;
}
