"""migrate Host product surfaces to PostgreSQL

Revision ID: 0003
Revises: 0002
"""
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

_SCHEMA_V3_DELTA = r"""
ALTER TABLE host_v2_schema DROP CONSTRAINT IF EXISTS host_v2_schema_schema_version_check;
ALTER TABLE host_v2_schema ADD CONSTRAINT host_v2_schema_schema_version_check CHECK (schema_version BETWEEN 1 AND 3);
UPDATE host_v2_schema SET schema_version=3 WHERE singleton;
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS goal_id text;
CREATE TABLE board_messages (
    sequence bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    client_message_id text NOT NULL UNIQUE, author_label text NOT NULL,
    message_kind text NOT NULL CHECK (message_kind IN ('note','question','proposal','warning','reply')),
    topic text, message text NOT NULL,
    reply_to_client_message_id text REFERENCES board_messages(client_message_id) ON DELETE RESTRICT,
    message_digest text NOT NULL, recorded_at_ms bigint NOT NULL,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
CREATE TABLE news_publications (
    sequence bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    client_publish_id text NOT NULL UNIQUE, edition_id text NOT NULL, edition_date text NOT NULL,
    expected_revision bigint NOT NULL CHECK (expected_revision >= 0),
    revision bigint NOT NULL CHECK (revision >= 1), edition_digest text NOT NULL,
    edition jsonb NOT NULL, recorded_at_ms bigint NOT NULL,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(), UNIQUE (edition_id, revision)
);
CREATE TABLE extension_states (
    task_id text NOT NULL REFERENCES tasks(task_id) ON DELETE RESTRICT, namespace text NOT NULL,
    task_revision bigint NOT NULL CHECK (task_revision >= 1), payload_digest text NOT NULL,
    payload jsonb NOT NULL, updated_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    PRIMARY KEY (task_id, namespace)
);
CREATE TABLE extension_history (
    task_id text NOT NULL REFERENCES tasks(task_id) ON DELETE RESTRICT, namespace text NOT NULL,
    task_revision bigint NOT NULL CHECK (task_revision >= 1), payload_digest text NOT NULL,
    payload jsonb NOT NULL, created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    PRIMARY KEY (task_id, namespace, task_revision)
);
CREATE TABLE activity_log (
    sequence bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, activity_kind text NOT NULL,
    subject_id text NOT NULL, task_revision bigint, payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
CREATE INDEX tasks_goal_updated_idx ON tasks(goal_id, updated_at DESC, task_id);
CREATE INDEX board_topic_sequence_idx ON board_messages(topic, sequence);
CREATE INDEX board_reply_sequence_idx ON board_messages(reply_to_client_message_id, sequence);
CREATE INDEX board_search_fts_idx ON board_messages USING GIN (to_tsvector('simple', coalesce(author_label,'') || ' ' || coalesce(topic,'') || ' ' || message));
CREATE INDEX news_edition_revision_idx ON news_publications(edition_id, revision DESC);
CREATE INDEX news_date_idx ON news_publications(edition_date DESC, edition_id DESC, revision DESC);
CREATE INDEX activity_sequence_idx ON activity_log(sequence);
"""

def upgrade() -> None:
    op.execute(_SCHEMA_V3_DELTA)

def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS activity_log")
    op.execute("DROP TABLE IF EXISTS extension_history")
    op.execute("DROP TABLE IF EXISTS extension_states")
    op.execute("DROP TABLE IF EXISTS news_publications")
    op.execute("DROP TABLE IF EXISTS board_messages")
    op.execute("ALTER TABLE tasks DROP COLUMN IF EXISTS goal_id")
    op.execute("UPDATE host_v2_schema SET schema_version=1 WHERE singleton")
