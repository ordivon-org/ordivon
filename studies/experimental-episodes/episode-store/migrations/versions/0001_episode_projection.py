"""experimental episode analytical projection

Revision ID: 0001
Revises:
"""

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

SCHEMA = r"""
CREATE TABLE experimental_schema (
    singleton boolean PRIMARY KEY DEFAULT true CHECK (singleton),
    schema_version integer NOT NULL CHECK (schema_version = 1)
);
INSERT INTO experimental_schema(singleton, schema_version) VALUES (true, 1);

CREATE TABLE episode_projections (
    episode_id text NOT NULL,
    projection_digest text NOT NULL CHECK (projection_digest ~ '^sha256:[0-9a-f]{64}$'),
    profile_id text NOT NULL,
    data_class text NOT NULL CHECK (data_class IN ('EXPERIENCE','DEVELOPMENT','JUDGE','DERIVED')),
    anchor_owner_id text NOT NULL,
    anchor_object_kind text NOT NULL,
    anchor_object_id text NOT NULL,
    source_record_digest text NOT NULL CHECK (source_record_digest ~ '^sha256:[0-9a-f]{64}$'),
    ingested_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    PRIMARY KEY (episode_id, projection_digest)
);

CREATE TABLE episode_owner_refs (
    episode_id text NOT NULL,
    projection_digest text NOT NULL,
    owner_id text NOT NULL,
    object_kind text NOT NULL,
    object_id text NOT NULL,
    relation text NOT NULL,
    digest text CHECK (digest IS NULL OR digest ~ '^sha256:[0-9a-f]{64}$'),
    FOREIGN KEY (episode_id, projection_digest)
      REFERENCES episode_projections(episode_id, projection_digest)
      ON DELETE RESTRICT,
    PRIMARY KEY (
      episode_id, projection_digest, owner_id, object_kind, object_id, relation
    )
);

CREATE TABLE episode_evidence_bindings (
    episode_id text NOT NULL,
    projection_digest text NOT NULL,
    kind text NOT NULL,
    evidence_count bigint NOT NULL CHECK (evidence_count >= 0),
    set_digest text NOT NULL CHECK (set_digest ~ '^sha256:[0-9a-f]{64}$'),
    total_bytes bigint CHECK (total_bytes IS NULL OR total_bytes >= 0),
    truncated_count bigint CHECK (truncated_count IS NULL OR truncated_count >= 0),
    FOREIGN KEY (episode_id, projection_digest)
      REFERENCES episode_projections(episode_id, projection_digest)
      ON DELETE RESTRICT,
    PRIMARY KEY (episode_id, projection_digest, kind)
);

CREATE TABLE episode_dimensions (
    episode_id text NOT NULL,
    projection_digest text NOT NULL,
    name text NOT NULL,
    value jsonb,
    FOREIGN KEY (episode_id, projection_digest)
      REFERENCES episode_projections(episode_id, projection_digest)
      ON DELETE RESTRICT,
    PRIMARY KEY (episode_id, projection_digest, name)
);

CREATE TABLE episode_measures (
    episode_id text NOT NULL,
    projection_digest text NOT NULL,
    name text NOT NULL,
    value double precision NOT NULL,
    unit text,
    FOREIGN KEY (episode_id, projection_digest)
      REFERENCES episode_projections(episode_id, projection_digest)
      ON DELETE RESTRICT,
    PRIMARY KEY (episode_id, projection_digest, name)
);

CREATE TABLE projection_ingests (
    ingest_id text PRIMARY KEY,
    corpus_id text NOT NULL,
    profile_id text NOT NULL,
    source_file_digest text NOT NULL CHECK (source_file_digest ~ '^sha256:[0-9a-f]{64}$'),
    projection_set_digest text NOT NULL CHECK (projection_set_digest ~ '^sha256:[0-9a-f]{64}$'),
    schema_digest text NOT NULL CHECK (schema_digest ~ '^sha256:[0-9a-f]{64}$'),
    adapter_digest text NOT NULL CHECK (adapter_digest ~ '^sha256:[0-9a-f]{64}$'),
    episode_count bigint NOT NULL CHECK (episode_count >= 0),
    inserted_projection_count bigint NOT NULL CHECK (inserted_projection_count >= 0),
    standing text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp()
);

CREATE INDEX episode_projections_profile_idx
  ON episode_projections(profile_id, data_class, episode_id);
CREATE INDEX episode_dimensions_name_idx
  ON episode_dimensions(name, episode_id);
CREATE INDEX episode_measures_name_idx
  ON episode_measures(name, episode_id);
CREATE INDEX episode_owner_refs_owner_idx
  ON episode_owner_refs(owner_id, object_kind, object_id);
"""


def upgrade() -> None:
    op.execute(SCHEMA)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS projection_ingests")
    op.execute("DROP TABLE IF EXISTS episode_measures")
    op.execute("DROP TABLE IF EXISTS episode_dimensions")
    op.execute("DROP TABLE IF EXISTS episode_evidence_bindings")
    op.execute("DROP TABLE IF EXISTS episode_owner_refs")
    op.execute("DROP TABLE IF EXISTS episode_projections")
    op.execute("DROP TABLE IF EXISTS experimental_schema")
