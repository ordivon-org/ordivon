SCHEMA_SQL = r"""
CREATE TABLE IF NOT EXISTS host_v2_schema (
    singleton boolean PRIMARY KEY DEFAULT true CHECK (singleton),
    schema_version integer NOT NULL CHECK (schema_version = 1)
);
INSERT INTO host_v2_schema(singleton, schema_version)
VALUES (true, 1)
ON CONFLICT (singleton) DO UPDATE SET schema_version = EXCLUDED.schema_version;

CREATE TABLE IF NOT EXISTS tasks (
    task_id text PRIMARY KEY,
    revision bigint NOT NULL CHECK (revision >= 1),
    state text NOT NULL CHECK (state IN ('open','completed','abandoned')),
    current_checkpoint_digest text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    updated_at timestamptz NOT NULL DEFAULT clock_timestamp()
);

CREATE TABLE IF NOT EXISTS checkpoints (
    task_id text NOT NULL REFERENCES tasks(task_id) ON DELETE RESTRICT,
    revision bigint NOT NULL CHECK (revision >= 1),
    checkpoint_digest text NOT NULL,
    payload jsonb NOT NULL,
    writer_label text,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    PRIMARY KEY (task_id, revision)
);

CREATE TABLE IF NOT EXISTS task_events (
    task_id text NOT NULL REFERENCES tasks(task_id) ON DELETE RESTRICT,
    revision bigint NOT NULL CHECK (revision >= 1),
    event_type text NOT NULL CHECK (event_type IN ('adopt','checkpoint')),
    request_digest text NOT NULL,
    checkpoint_digest text NOT NULL,
    resulting_state text NOT NULL CHECK (resulting_state IN ('open','completed','abandoned')),
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    PRIMARY KEY (task_id, revision)
);

CREATE TABLE IF NOT EXISTS command_receipts (
    client_request_id text PRIMARY KEY,
    operation text NOT NULL,
    request_digest text NOT NULL,
    response jsonb,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp()
);

ALTER TABLE command_receipts ALTER COLUMN response DROP NOT NULL;

CREATE INDEX IF NOT EXISTS tasks_state_updated_idx ON tasks(state, updated_at DESC, task_id);
"""
