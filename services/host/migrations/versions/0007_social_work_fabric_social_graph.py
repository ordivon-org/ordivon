"""introduce Social Work Fabric Social Graph

Revision ID: 0007
Revises: 0006
"""

from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None

_SCHEMA_V7_DELTA = r"""
CREATE TABLE spaces (
    space_ref text PRIMARY KEY,
    purpose text NOT NULL,
    created_by_actor_ref text NOT NULL REFERENCES actor_refs(actor_ref) ON DELETE RESTRICT,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp()
);

CREATE TABLE space_subjects (
    space_ref text NOT NULL REFERENCES spaces(space_ref) ON DELETE RESTRICT,
    subject_ref text NOT NULL,
    PRIMARY KEY (space_ref, subject_ref)
);

CREATE TABLE participations (
    space_ref text NOT NULL REFERENCES spaces(space_ref) ON DELETE RESTRICT,
    actor_ref text NOT NULL REFERENCES actor_refs(actor_ref) ON DELETE RESTRICT,
    standing text NOT NULL CHECK (standing IN ('joined','left','observer')),
    updated_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    PRIMARY KEY (space_ref, actor_ref)
);

CREATE TABLE topics (
    topic_ref text PRIMARY KEY,
    space_ref text NOT NULL REFERENCES spaces(space_ref) ON DELETE RESTRICT,
    title text NOT NULL,
    state text NOT NULL CHECK (state IN ('open','closed')),
    created_by_actor_ref text NOT NULL REFERENCES actor_refs(actor_ref) ON DELETE RESTRICT,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    updated_at timestamptz NOT NULL DEFAULT clock_timestamp()
);

CREATE TABLE messages (
    sequence bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    message_ref text NOT NULL UNIQUE,
    client_request_id text NOT NULL UNIQUE,
    space_ref text NOT NULL REFERENCES spaces(space_ref) ON DELETE RESTRICT,
    topic_ref text NOT NULL REFERENCES topics(topic_ref) ON DELETE RESTRICT,
    author_actor_ref text NOT NULL REFERENCES actor_refs(actor_ref) ON DELETE RESTRICT,
    message_kind text NOT NULL CHECK (message_kind IN ('note','question','proposal','warning','finding','handoff')),
    body text NOT NULL,
    message_digest text NOT NULL,
    recorded_at_ms bigint NOT NULL,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp()
);

CREATE TABLE message_relations (
    source_message_ref text NOT NULL REFERENCES messages(message_ref) ON DELETE RESTRICT,
    relation text NOT NULL CHECK (relation IN ('reply_to','mentions','references','acknowledges','supersedes','about')),
    target_ref text NOT NULL,
    created_by_actor_ref text NOT NULL REFERENCES actor_refs(actor_ref) ON DELETE RESTRICT,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    PRIMARY KEY (source_message_ref, relation, target_ref)
);

CREATE TABLE coordination_intents (
    intent_ref text PRIMARY KEY,
    actor_ref text NOT NULL REFERENCES actor_refs(actor_ref) ON DELETE RESTRICT,
    subject_ref text NOT NULL,
    work_ref text REFERENCES works(work_ref) ON DELETE RESTRICT,
    space_ref text REFERENCES spaces(space_ref) ON DELETE RESTRICT,
    operation text NOT NULL,
    standing text NOT NULL CHECK (standing IN ('active','released')),
    observed_at_ms bigint NOT NULL,
    expires_at_ms bigint,
    updated_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    CHECK (expires_at_ms IS NULL OR expires_at_ms > observed_at_ms)
);

CREATE INDEX space_subject_ref_idx ON space_subjects(subject_ref, space_ref);
CREATE INDEX participation_actor_idx ON participations(actor_ref, standing, space_ref);
CREATE INDEX topic_space_idx ON topics(space_ref, state, topic_ref);
CREATE INDEX message_topic_sequence_idx ON messages(topic_ref, sequence);
CREATE INDEX message_space_sequence_idx ON messages(space_ref, sequence);
CREATE INDEX message_author_sequence_idx ON messages(author_actor_ref, sequence);
CREATE INDEX message_search_fts_idx ON messages USING GIN (to_tsvector('simple', body));
CREATE INDEX message_relation_target_idx ON message_relations(relation, target_ref, source_message_ref);
CREATE INDEX coordination_subject_idx ON coordination_intents(subject_ref, standing, intent_ref);
CREATE INDEX coordination_work_idx ON coordination_intents(work_ref, standing, intent_ref) WHERE work_ref IS NOT NULL;
CREATE INDEX coordination_space_idx ON coordination_intents(space_ref, standing, intent_ref) WHERE space_ref IS NOT NULL;

ALTER TABLE host_v2_schema DROP CONSTRAINT IF EXISTS host_v2_schema_schema_version_check;
ALTER TABLE host_v2_schema ADD CONSTRAINT host_v2_schema_schema_version_check CHECK (schema_version BETWEEN 1 AND 7);
UPDATE host_v2_schema SET schema_version=7 WHERE singleton;
"""


def upgrade() -> None:
    op.execute(_SCHEMA_V7_DELTA)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS coordination_intents")
    op.execute("DROP TABLE IF EXISTS message_relations")
    op.execute("DROP TABLE IF EXISTS messages")
    op.execute("DROP TABLE IF EXISTS topics")
    op.execute("DROP TABLE IF EXISTS participations")
    op.execute("DROP TABLE IF EXISTS space_subjects")
    op.execute("DROP TABLE IF EXISTS spaces")
    op.execute(
        "ALTER TABLE host_v2_schema DROP CONSTRAINT IF EXISTS host_v2_schema_schema_version_check"
    )
    op.execute("UPDATE host_v2_schema SET schema_version=6 WHERE singleton")
    op.execute(
        "ALTER TABLE host_v2_schema ADD CONSTRAINT host_v2_schema_schema_version_check "
        "CHECK (schema_version BETWEEN 1 AND 6)"
    )
