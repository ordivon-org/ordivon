"""host v2 core tables

Revision ID: 0001
Revises:
"""
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

_SCHEMA_V1 = r"""
CREATE TABLE host_v2_schema (
    singleton boolean PRIMARY KEY DEFAULT true CHECK (singleton),
    schema_version integer NOT NULL CHECK (schema_version = 1)
);
INSERT INTO host_v2_schema(singleton, schema_version) VALUES (true, 1);

CREATE TABLE tasks (
    task_id text PRIMARY KEY,
    revision bigint NOT NULL CHECK (revision >= 1),
    state text NOT NULL CHECK (state IN ('open','completed','abandoned')),
    current_checkpoint_digest text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    updated_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
CREATE TABLE checkpoints (
    task_id text NOT NULL REFERENCES tasks(task_id) ON DELETE RESTRICT,
    revision bigint NOT NULL CHECK (revision >= 1),
    checkpoint_digest text NOT NULL,
    payload jsonb NOT NULL,
    writer_label text,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    PRIMARY KEY (task_id, revision)
);
CREATE TABLE task_events (
    task_id text NOT NULL REFERENCES tasks(task_id) ON DELETE RESTRICT,
    revision bigint NOT NULL CHECK (revision >= 1),
    event_type text NOT NULL CHECK (event_type IN ('adopt','checkpoint')),
    request_digest text NOT NULL,
    checkpoint_digest text NOT NULL,
    resulting_state text NOT NULL CHECK (resulting_state IN ('open','completed','abandoned')),
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    PRIMARY KEY (task_id, revision)
);
CREATE TABLE command_receipts (
    client_request_id text PRIMARY KEY,
    operation text NOT NULL,
    request_digest text NOT NULL,
    response jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
CREATE INDEX tasks_state_updated_idx ON tasks(state, updated_at DESC, task_id);
"""

def upgrade() -> None:
    op.execute(_SCHEMA_V1)

def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS command_receipts")
    op.execute("DROP TABLE IF EXISTS task_events")
    op.execute("DROP TABLE IF EXISTS checkpoints")
    op.execute("DROP TABLE IF EXISTS tasks")
    op.execute("DROP TABLE IF EXISTS host_v2_schema")
