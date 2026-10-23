"""harden Social Work Fabric recovery and query paths

Revision ID: 0010
Revises: 0009
"""

from alembic import op

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None

_SCHEMA_V10_DELTA = r"""
CREATE TABLE topic_consumption_cursors (
    actor_ref text NOT NULL REFERENCES actor_refs(actor_ref) ON DELETE RESTRICT,
    topic_ref text NOT NULL REFERENCES topics(topic_ref) ON DELETE RESTRICT,
    cursor bigint NOT NULL CHECK (cursor >= 0),
    updated_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    PRIMARY KEY (actor_ref, topic_ref)
);

CREATE INDEX work_snapshot_target_change_idx ON work_snapshots(work_ref, change_sequence);
CREATE INDEX work_relation_source_change_idx ON work_relations(source_work_ref, change_sequence);
CREATE INDEX work_relation_target_change_idx ON work_relations(target_work_ref, change_sequence);
CREATE INDEX participation_actor_change_idx ON participations(actor_ref, change_sequence);
CREATE INDEX topic_space_change_idx ON topics(space_ref, change_sequence);
CREATE INDEX message_topic_change_idx ON messages(topic_ref, change_sequence);
CREATE INDEX message_space_change_idx ON messages(space_ref, change_sequence);
CREATE INDEX message_author_ref_idx ON messages(author_actor_ref, message_ref);
CREATE INDEX message_relation_target_change_idx ON message_relations(target_ref, relation, change_sequence);

ALTER TABLE host_v2_schema DROP CONSTRAINT IF EXISTS host_v2_schema_schema_version_check;
ALTER TABLE host_v2_schema ADD CONSTRAINT host_v2_schema_schema_version_check CHECK (schema_version BETWEEN 1 AND 10);
UPDATE host_v2_schema SET schema_version=10 WHERE singleton;
"""


def upgrade() -> None:
    op.execute(_SCHEMA_V10_DELTA)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS message_relation_target_change_idx")
    op.execute("DROP INDEX IF EXISTS message_author_ref_idx")
    op.execute("DROP INDEX IF EXISTS message_space_change_idx")
    op.execute("DROP INDEX IF EXISTS message_topic_change_idx")
    op.execute("DROP INDEX IF EXISTS topic_space_change_idx")
    op.execute("DROP INDEX IF EXISTS participation_actor_change_idx")
    op.execute("DROP INDEX IF EXISTS work_relation_target_change_idx")
    op.execute("DROP INDEX IF EXISTS work_relation_source_change_idx")
    op.execute("DROP INDEX IF EXISTS work_snapshot_target_change_idx")
    op.execute("DROP TABLE IF EXISTS topic_consumption_cursors")
    op.execute(
        "ALTER TABLE host_v2_schema DROP CONSTRAINT IF EXISTS host_v2_schema_schema_version_check"
    )
    op.execute("UPDATE host_v2_schema SET schema_version=9 WHERE singleton")
    op.execute(
        "ALTER TABLE host_v2_schema ADD CONSTRAINT host_v2_schema_schema_version_check "
        "CHECK (schema_version BETWEEN 1 AND 9)"
    )
