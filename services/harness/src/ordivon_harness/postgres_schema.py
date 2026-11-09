"""Versioned PostgreSQL DDL for the Harness-owned Run Journal/CAS.

Pure schema declaration only; initialization and transaction ownership remain
inside postgres_store.PostgresHarnessStore. No Host/Runtime schema is managed here.
"""

from __future__ import annotations

HARNESS_POSTGRES_SCHEMA_SQL = """
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
