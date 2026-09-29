"""introduce Social Work Fabric Attention Fabric

Revision ID: 0008
Revises: 0007
"""

from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None

_SCHEMA_V8_DELTA = r"""
CREATE TABLE swf_change_clock (
    singleton boolean PRIMARY KEY DEFAULT true CHECK (singleton),
    value bigint NOT NULL CHECK (value >= 0)
);
INSERT INTO swf_change_clock(singleton,value) VALUES (true,0);

CREATE FUNCTION swf_next_change_sequence() RETURNS bigint
LANGUAGE plpgsql VOLATILE AS $$
DECLARE
    next_value bigint;
BEGIN
    UPDATE swf_change_clock
    SET value=value+1
    WHERE singleton
    RETURNING value INTO next_value;
    IF next_value IS NULL THEN
        RAISE EXCEPTION 'Social Work Fabric change clock is missing';
    END IF;
    RETURN next_value;
END
$$;

ALTER TABLE actor_refs ADD COLUMN change_sequence bigint NOT NULL DEFAULT swf_next_change_sequence();
ALTER TABLE works ADD COLUMN change_sequence bigint NOT NULL DEFAULT swf_next_change_sequence();
ALTER TABLE work_snapshots ADD COLUMN change_sequence bigint NOT NULL DEFAULT swf_next_change_sequence();
ALTER TABLE work_relations ADD COLUMN change_sequence bigint NOT NULL DEFAULT swf_next_change_sequence();
ALTER TABLE spaces ADD COLUMN change_sequence bigint NOT NULL DEFAULT swf_next_change_sequence();
ALTER TABLE space_subjects ADD COLUMN change_sequence bigint NOT NULL DEFAULT swf_next_change_sequence();
ALTER TABLE participations ADD COLUMN change_sequence bigint NOT NULL DEFAULT swf_next_change_sequence();
ALTER TABLE topics ADD COLUMN change_sequence bigint NOT NULL DEFAULT swf_next_change_sequence();
ALTER TABLE messages ADD COLUMN change_sequence bigint NOT NULL DEFAULT swf_next_change_sequence();
ALTER TABLE message_relations ADD COLUMN change_sequence bigint NOT NULL DEFAULT swf_next_change_sequence();
ALTER TABLE coordination_intents ADD COLUMN change_sequence bigint NOT NULL DEFAULT swf_next_change_sequence();

CREATE TABLE subscriptions (
    actor_ref text NOT NULL REFERENCES actor_refs(actor_ref) ON DELETE RESTRICT,
    target_kind text NOT NULL CHECK (target_kind IN ('work','space','topic')),
    target_ref text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    change_sequence bigint NOT NULL DEFAULT swf_next_change_sequence(),
    PRIMARY KEY (actor_ref, target_kind, target_ref)
);

CREATE TABLE attention_cursors (
    actor_ref text PRIMARY KEY REFERENCES actor_refs(actor_ref) ON DELETE RESTRICT,
    cursor bigint NOT NULL CHECK (cursor >= 0),
    updated_at timestamptz NOT NULL DEFAULT clock_timestamp()
);

CREATE INDEX work_snapshot_change_idx ON work_snapshots(change_sequence);
CREATE INDEX work_relation_change_idx ON work_relations(change_sequence);
CREATE INDEX work_change_idx ON works(change_sequence);
CREATE INDEX participation_change_idx ON participations(change_sequence);
CREATE INDEX topic_change_idx ON topics(change_sequence);
CREATE INDEX message_change_idx ON messages(change_sequence);
CREATE INDEX message_relation_change_idx ON message_relations(change_sequence);
CREATE INDEX intent_change_idx ON coordination_intents(change_sequence);
CREATE INDEX subscription_target_idx ON subscriptions(target_kind,target_ref,actor_ref);
CREATE INDEX subscription_change_idx ON subscriptions(change_sequence);

ALTER TABLE host_v2_schema DROP CONSTRAINT IF EXISTS host_v2_schema_schema_version_check;
ALTER TABLE host_v2_schema ADD CONSTRAINT host_v2_schema_schema_version_check CHECK (schema_version BETWEEN 1 AND 8);
UPDATE host_v2_schema SET schema_version=8 WHERE singleton;
"""


def upgrade() -> None:
    op.execute(_SCHEMA_V8_DELTA)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS attention_cursors")
    op.execute("DROP TABLE IF EXISTS subscriptions")
    for table in (
        "coordination_intents",
        "message_relations",
        "messages",
        "topics",
        "participations",
        "space_subjects",
        "spaces",
        "work_relations",
        "work_snapshots",
        "works",
        "actor_refs",
    ):
        op.execute(f"ALTER TABLE {table} DROP COLUMN IF EXISTS change_sequence")
    op.execute("DROP FUNCTION IF EXISTS swf_next_change_sequence()")
    op.execute("DROP TABLE IF EXISTS swf_change_clock")
    op.execute(
        "ALTER TABLE host_v2_schema DROP CONSTRAINT IF EXISTS host_v2_schema_schema_version_check"
    )
    op.execute("UPDATE host_v2_schema SET schema_version=7 WHERE singleton")
    op.execute(
        "ALTER TABLE host_v2_schema ADD CONSTRAINT host_v2_schema_schema_version_check "
        "CHECK (schema_version BETWEEN 1 AND 7)"
    )
