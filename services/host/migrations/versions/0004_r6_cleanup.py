"""remove unused generic surfaces and advance Host schema

Revision ID: 0004
Revises: 0003
"""

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DROP TABLE IF EXISTS activity_log")
    op.execute("DROP TABLE IF EXISTS extension_history")
    op.execute("DROP TABLE IF EXISTS extension_states")
    op.execute("ALTER TABLE host_v2_schema DROP CONSTRAINT IF EXISTS host_v2_schema_schema_version_check")
    op.execute(
        "ALTER TABLE host_v2_schema ADD CONSTRAINT host_v2_schema_schema_version_check "
        "CHECK (schema_version BETWEEN 1 AND 4)"
    )
    op.execute("UPDATE host_v2_schema SET schema_version=4 WHERE singleton")


def downgrade() -> None:
    op.execute(
        "CREATE TABLE extension_states ("
        "task_id text NOT NULL REFERENCES tasks(task_id) ON DELETE RESTRICT, namespace text NOT NULL,"
        "task_revision bigint NOT NULL CHECK (task_revision >= 1), payload_digest text NOT NULL,"
        "payload jsonb NOT NULL, updated_at timestamptz NOT NULL DEFAULT clock_timestamp(),"
        "PRIMARY KEY (task_id, namespace))"
    )
    op.execute(
        "CREATE TABLE extension_history ("
        "task_id text NOT NULL REFERENCES tasks(task_id) ON DELETE RESTRICT, namespace text NOT NULL,"
        "task_revision bigint NOT NULL CHECK (task_revision >= 1), payload_digest text NOT NULL,"
        "payload jsonb NOT NULL, created_at timestamptz NOT NULL DEFAULT clock_timestamp(),"
        "PRIMARY KEY (task_id, namespace, task_revision))"
    )
    op.execute(
        "CREATE TABLE activity_log ("
        "sequence bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, activity_kind text NOT NULL,"
        "subject_id text NOT NULL, task_revision bigint, payload jsonb NOT NULL DEFAULT '{}'::jsonb,"
        "created_at timestamptz NOT NULL DEFAULT clock_timestamp())"
    )
    op.execute("CREATE INDEX activity_sequence_idx ON activity_log(sequence)")
    op.execute("ALTER TABLE host_v2_schema DROP CONSTRAINT IF EXISTS host_v2_schema_schema_version_check")
    op.execute(
        "ALTER TABLE host_v2_schema ADD CONSTRAINT host_v2_schema_schema_version_check "
        "CHECK (schema_version BETWEEN 1 AND 3)"
    )
    op.execute("UPDATE host_v2_schema SET schema_version=3 WHERE singleton")
