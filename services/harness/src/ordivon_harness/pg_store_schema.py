"""Original Harness PG schema, issuer predicate and configuration.

Original PostgreSQL connection and existing transaction authority are retained.
"""

from __future__ import annotations
import re
import os


_SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_info (key text PRIMARY KEY, value text NOT NULL);
INSERT INTO schema_info(key,value) VALUES ('schema_version','1') ON CONFLICT DO NOTHING;
CREATE TABLE IF NOT EXISTS objects (
 digest text PRIMARY KEY, kind text NOT NULL, byte_length bigint NOT NULL CHECK (byte_length >= 0),
 content bytea NOT NULL, first_seen_at_ms bigint NOT NULL CHECK (first_seen_at_ms >= 0)
);
CREATE TABLE IF NOT EXISTS runs (
 harness_run_id text PRIMARY KEY,
 contract_digest text NOT NULL UNIQUE,
 contract_object_digest text NOT NULL REFERENCES objects(digest),
 caller_id text NOT NULL, caller_run_ref text NOT NULL,
 status text NOT NULL, revision bigint NOT NULL CHECK (revision >= 1),
 created_at_ms bigint NOT NULL CHECK (created_at_ms >= 0),
 updated_at_ms bigint NOT NULL CHECK (updated_at_ms >= created_at_ms),
 terminal_event_id text,
 UNIQUE(caller_id, caller_run_ref)
);
CREATE TABLE IF NOT EXISTS run_events (
 sequence bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 event_id text NOT NULL UNIQUE,
 harness_run_id text NOT NULL REFERENCES runs(harness_run_id) ON DELETE CASCADE,
 run_revision bigint NOT NULL CHECK (run_revision >= 1),
 event_kind text NOT NULL, payload_digest text NOT NULL REFERENCES objects(digest),
 caused_by_event_id text REFERENCES run_events(event_id),
 recorded_at_ms bigint NOT NULL CHECK (recorded_at_ms >= 0),
 UNIQUE(harness_run_id,run_revision)
);
CREATE TABLE IF NOT EXISTS run_object_refs (
 harness_run_id text NOT NULL REFERENCES runs(harness_run_id) ON DELETE CASCADE,
 event_id text NOT NULL REFERENCES run_events(event_id) ON DELETE CASCADE,
 digest text NOT NULL REFERENCES objects(digest),
 role text NOT NULL CHECK (role IN ('payload','reference')),
 PRIMARY KEY(event_id,digest)
);
CREATE UNIQUE INDEX IF NOT EXISTS run_object_refs_one_payload
 ON run_object_refs(event_id) WHERE role='payload';
CREATE TABLE IF NOT EXISTS run_leases (
 harness_run_id text PRIMARY KEY REFERENCES runs(harness_run_id) ON DELETE CASCADE,
 owner_id text NOT NULL, lease_revision bigint NOT NULL CHECK (lease_revision >= 1),
 run_revision bigint NOT NULL CHECK (run_revision >= 1),
 expires_at_ms bigint NOT NULL CHECK (expires_at_ms >= 0)
);
"""

_SCHEMA_NAME = re.compile(r"[a-z][a-z0-9_]{0,62}\Z")

# Issuer-owned PostgreSQL SECURITY DEFINER predicate. It only exports the
# current Tool-prepared Event payload and associated Fence CAS bytes, while
# holding runs FOR SHARE until the caller's Job transaction COMMIT. The
# Runtime service SQL role needs EXECUTE, NOT issuer table SELECT or UPDATE.
_ISSUER_ADMISSION_FUNCTION = """
CREATE OR REPLACE FUNCTION {schema}.harness_current_dispatch_cut(
    p_run_id text, p_revision bigint, p_fence_digest text
)
RETURNS TABLE(
    event_kind text, payload_digest text, payload_kind text,
    payload_len bigint, payload_content bytea,
    fence_kind text, fence_len bigint, fence_content bytea,
    intent_digest text, intent_kind text, intent_len bigint, intent_content bytea
)
LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog
AS $source$
DECLARE
    locked_status text;
    locked_revision bigint;
BEGIN
    SELECT r.status,r.revision INTO locked_status,locked_revision
      FROM {schema}.runs r WHERE r.harness_run_id=p_run_id FOR SHARE;
    IF NOT FOUND OR locked_status != 'active'
       OR locked_revision != p_revision THEN
        RETURN;
    END IF;
    RETURN QUERY
    SELECT e.event_kind,e.payload_digest,p.kind,p.byte_length,p.content,
           f.kind,f.byte_length,f.content,
           i.digest,i.kind,i.byte_length,i.content
      FROM {schema}.run_events e
      JOIN {schema}.objects p ON p.digest=e.payload_digest
      JOIN {schema}.run_object_refs payload_ref
        ON payload_ref.event_id=e.event_id
       AND payload_ref.harness_run_id=e.harness_run_id
       AND payload_ref.role='payload'
       AND payload_ref.digest=e.payload_digest
      CROSS JOIN LATERAL (
        SELECT convert_from(p.content,'UTF8')::jsonb AS body
      ) AS original
      JOIN {schema}.run_object_refs refs
        ON refs.event_id=e.event_id AND refs.role='reference'
       AND refs.harness_run_id=e.harness_run_id
      JOIN {schema}.objects f ON f.digest=refs.digest
      JOIN {schema}.objects i ON i.digest=(
        original.body #>> '{{data,toolStepIntentObjectDigest}}'
      )
     WHERE e.harness_run_id=p_run_id AND e.run_revision=p_revision
       AND e.event_kind='harness.tool-step-prepared'
       AND p.kind='ordivon.harness-run-event-payload'
       AND f.digest=p_fence_digest
       AND f.digest=(original.body #>> '{{data,dispatchFenceObjectDigest}}')
       AND f.kind='harness-dispatch-fence'
       AND i.kind='harness-tool-step-intent'
       AND EXISTS (
         SELECT 1 FROM {schema}.run_object_refs link
          WHERE link.event_id=e.event_id AND link.role='reference'
            AND link.harness_run_id=e.harness_run_id
            AND link.digest=i.digest
       )
       AND EXISTS (
         SELECT 1 FROM {schema}.run_object_refs link
         JOIN {schema}.objects o ON o.digest=link.digest
          WHERE link.event_id=e.event_id AND link.role='reference'
            AND link.harness_run_id=e.harness_run_id
            AND link.digest=(original.body #>> '{{data,snapshotObjectDigest}}')
            AND o.kind='harness-run-snapshot'
       )
       AND EXISTS (
         SELECT 1 FROM {schema}.run_object_refs link
         JOIN {schema}.objects o ON o.digest=link.digest
          WHERE link.event_id=e.event_id AND link.role='reference'
            AND link.harness_run_id=e.harness_run_id
            AND link.digest=(original.body #>> '{{data,stateObjectDigest}}')
            AND o.kind='harness-run-state'
       );
END
$source$;
REVOKE ALL ON FUNCTION {schema}.harness_current_dispatch_cut(text,bigint,text)
FROM PUBLIC;
"""


def configured_postgres() -> tuple[str, str]:
    """The owner default is PG-only. No SQLite state-root or import fallback."""
    # Preserve the already-published Harness PG CLI authority while retiring
    # SQLite entirely: the explicit marker is advisory and cannot select SQLite.
    dsn = (os.environ.get("ORDIVON_HARNESS_PG_DSN") or os.environ.get("HARNESS_PG_DSN", "")).strip()
    if not dsn:
        raise RuntimeError(
            "HARNESS_PG_DSN required (or ORDIVON_HARNESS_PG_DSN); SQLite fallback prohibited"
        )
    schema = os.environ.get("ORDIVON_HARNESS_PG_SCHEMA") or os.environ.get(
        "HARNESS_PG_SCHEMA", "harness"
    )
    if not _SCHEMA_NAME.fullmatch(schema):
        raise ValueError("HARNESS_PG_SCHEMA must be one plain SQL identifier")
    return dsn, schema
