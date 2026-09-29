"""introduce Social Work Fabric Work Graph

Revision ID: 0006
Revises: 0005
"""

from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None

_SCHEMA_V6_DELTA = r"""
CREATE TABLE actor_refs (
    actor_ref text PRIMARY KEY,
    actor_kind text NOT NULL CHECK (actor_kind IN ('unknown','human','agent','service','organization')),
    created_at timestamptz NOT NULL DEFAULT clock_timestamp()
);

CREATE TABLE works (
    work_ref text PRIMARY KEY,
    kind text NOT NULL,
    state text NOT NULL CHECK (state IN ('open','completed','abandoned')),
    current_revision bigint NOT NULL CHECK (current_revision >= 1),
    current_snapshot_digest text NOT NULL,
    created_by_actor_ref text NOT NULL REFERENCES actor_refs(actor_ref) ON DELETE RESTRICT,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    updated_at timestamptz NOT NULL DEFAULT clock_timestamp()
);

CREATE TABLE work_snapshots (
    work_ref text NOT NULL REFERENCES works(work_ref) ON DELETE RESTRICT,
    revision bigint NOT NULL CHECK (revision >= 1),
    snapshot_digest text NOT NULL,
    payload jsonb NOT NULL,
    writer_actor_ref text NOT NULL REFERENCES actor_refs(actor_ref) ON DELETE RESTRICT,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    PRIMARY KEY (work_ref, revision)
);

CREATE TABLE work_relations (
    source_work_ref text NOT NULL REFERENCES works(work_ref) ON DELETE RESTRICT,
    relation text NOT NULL CHECK (relation IN ('parent_of','depends_on','blocks','relates_to')),
    target_work_ref text NOT NULL REFERENCES works(work_ref) ON DELETE RESTRICT,
    created_by_actor_ref text NOT NULL REFERENCES actor_refs(actor_ref) ON DELETE RESTRICT,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    PRIMARY KEY (source_work_ref, relation, target_work_ref),
    CHECK (source_work_ref <> target_work_ref)
);

CREATE INDEX works_state_updated_idx ON works(state, updated_at DESC, work_ref);
CREATE INDEX work_relation_target_idx ON work_relations(target_work_ref, relation, source_work_ref);
CREATE INDEX work_snapshot_digest_idx ON work_snapshots(snapshot_digest);

ALTER TABLE host_v2_schema DROP CONSTRAINT IF EXISTS host_v2_schema_schema_version_check;
ALTER TABLE host_v2_schema ADD CONSTRAINT host_v2_schema_schema_version_check CHECK (schema_version BETWEEN 1 AND 6);
UPDATE host_v2_schema SET schema_version=6 WHERE singleton;
"""


def upgrade() -> None:
    op.execute(_SCHEMA_V6_DELTA)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS work_relations")
    op.execute("DROP TABLE IF EXISTS work_snapshots")
    op.execute("DROP TABLE IF EXISTS works")
    op.execute("DROP TABLE IF EXISTS actor_refs")
    op.execute(
        "ALTER TABLE host_v2_schema DROP CONSTRAINT IF EXISTS host_v2_schema_schema_version_check"
    )
    op.execute("UPDATE host_v2_schema SET schema_version=5 WHERE singleton")
    op.execute(
        "ALTER TABLE host_v2_schema ADD CONSTRAINT host_v2_schema_schema_version_check "
        "CHECK (schema_version BETWEEN 1 AND 5)"
    )
