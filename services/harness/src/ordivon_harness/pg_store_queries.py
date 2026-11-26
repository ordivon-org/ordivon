"""Original Run projection and Journal read queries.

Original PostgreSQL connection and existing transaction authority are retained.
"""

from __future__ import annotations
from .store import (
    HarnessRunEventRecord,
    HarnessRunProjection,
)

from .pg_store_codec import decode_event_rows, run_projection

class PostgresQueries:
    """Original Run projection and Journal read queries."""

    def load_run(self, harness_run_id: str) -> HarnessRunProjection:
        row = self.connection.execute(
            "SELECT * FROM runs WHERE harness_run_id=%s", (harness_run_id,)
        ).fetchone()
        if row is None:
            raise KeyError(f"Harness Run does not exist: {harness_run_id}")
        return run_projection(harness_run_id, row)

    def list_runs(self) -> tuple[HarnessRunProjection, ...]:
        rows = self.connection.execute(
            "SELECT * FROM runs ORDER BY created_at_ms,harness_run_id"
        ).fetchall()
        return tuple(run_projection(row["harness_run_id"], row) for row in rows)

    def list_run_events(
        self, harness_run_id: str, *, after_sequence: int = 0
    ) -> tuple[HarnessRunEventRecord, ...]:
        if after_sequence < 0:
            raise ValueError("negative event cursor")
        self.load_run(harness_run_id)
        # Fetch CAS payloads alongside events. A left join preserves the
        # missing-object error; all content digest and kind checks still run.
        rows = self.connection.execute(
            "SELECT e.*, o.kind AS object_kind, o.byte_length AS object_byte_length, "
            "o.content AS object_content FROM run_events e "
            "LEFT JOIN objects o ON o.digest=e.payload_digest "
            "WHERE e.harness_run_id=%s AND e.sequence>%s ORDER BY e.sequence",
            (harness_run_id, after_sequence),
        ).fetchall()
        return decode_event_rows(rows)

    def list_committed_working_set_events(
        self, harness_run_id: str, *, before_sequence: int, limit: int
    ) -> tuple[HarnessRunEventRecord, ...]:
        """Latest committed Working Sets in descending order; at most limit+1 rows.

        This is a read-only PG specialization of the existing journal port.
        Content is still decoded and CAS checked by the same event decoder.
        """
        if before_sequence < 0 or limit < 1:
            raise ValueError("invalid Working Set page bounds")
        self.load_run(harness_run_id)
        rows = self.connection.execute(
            "SELECT e.*, o.kind AS object_kind, o.byte_length AS object_byte_length, "
            "o.content AS object_content FROM run_events e "
            "LEFT JOIN objects o ON o.digest=e.payload_digest "
            "WHERE e.harness_run_id=%s AND e.event_kind='harness.working-set-recorded' "
            "AND e.sequence<%s AND "
            # PostgreSQL can reorder OR operands. A CASE forces the CAS
            # integrity guards before UTF8/JSON parsing, allowing a corrupt
            # candidate to reach the original HarnessObjectCorrupt decoder.
            "CASE WHEN o.digest IS NULL THEN true "
            "WHEN o.kind != 'ordivon.harness-run-event-payload' THEN true "
            "WHEN o.byte_length != octet_length(o.content) THEN true "
            "WHEN o.digest != ('sha256:' || encode(sha256(o.content),'hex')) THEN true "
            "ELSE convert_from(o.content,'UTF8')::jsonb "
            "#> '{data,committed}' = 'true'::jsonb END "
            "ORDER BY e.sequence DESC LIMIT %s",
            (harness_run_id, before_sequence, limit + 1),
        ).fetchall()
        return decode_event_rows(rows)

    def find_working_set_event_sequence(
        self, harness_run_id: str, *, working_set_digest: str
    ) -> int:
        """Resolve the unique Journal identity without a full Run scan."""
        self.load_run(harness_run_id)
        rows = self.connection.execute(
            "SELECT e.*, o.kind AS object_kind, o.byte_length AS object_byte_length, "
            "o.content AS object_content FROM run_events e "
            "LEFT JOIN objects o ON o.digest=e.payload_digest "
            "WHERE e.harness_run_id=%s AND e.event_kind='harness.working-set-recorded' "
            # The current head identity lookup must share the same CASE
            # guard; otherwise one older corrupt Working Set throws raw PG
            # JSON/encoding errors before the source CAS decoder runs.
            "AND CASE WHEN o.digest IS NULL THEN true "
            "WHEN o.kind != 'ordivon.harness-run-event-payload' THEN true "
            "WHEN o.byte_length != octet_length(o.content) THEN true "
            "WHEN o.digest != ('sha256:' || encode(sha256(o.content),'hex')) THEN true "
            "ELSE convert_from(o.content,'UTF8')::jsonb "
            "#>> '{data,workingSetDigest}'=%s END "
            "ORDER BY e.sequence DESC LIMIT 2",
            (harness_run_id, working_set_digest),
        ).fetchall()
        matches = decode_event_rows(rows)
        if len(matches) != 1:
            raise ValueError("Harness Working Set must have exactly one durable Journal event")
        return matches[0].sequence
