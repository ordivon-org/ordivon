SCHEMA_SQL = r"""
CREATE TABLE IF NOT EXISTS host_v2_schema (
    singleton boolean PRIMARY KEY DEFAULT true CHECK (singleton),
    schema_version integer NOT NULL
);
ALTER TABLE host_v2_schema DROP CONSTRAINT IF EXISTS host_v2_schema_schema_version_check;
ALTER TABLE host_v2_schema ADD CONSTRAINT host_v2_schema_schema_version_check CHECK (schema_version BETWEEN 1 AND 3);
INSERT INTO host_v2_schema(singleton, schema_version)
VALUES (true, 3)
ON CONFLICT (singleton) DO UPDATE SET schema_version = EXCLUDED.schema_version;

CREATE TABLE IF NOT EXISTS tasks (
    task_id text PRIMARY KEY,
    goal_id text,
    revision bigint NOT NULL CHECK (revision >= 1),
    state text NOT NULL CHECK (state IN ('open','completed','abandoned')),
    current_checkpoint_digest text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    updated_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS goal_id text;

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

CREATE TABLE IF NOT EXISTS board_messages (
    sequence bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    client_message_id text NOT NULL UNIQUE,
    author_label text NOT NULL,
    message_kind text NOT NULL CHECK (message_kind IN ('note','question','proposal','warning','reply')),
    topic text,
    message text NOT NULL,
    reply_to_client_message_id text REFERENCES board_messages(client_message_id) ON DELETE RESTRICT,
    message_digest text NOT NULL,
    recorded_at_ms bigint NOT NULL,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp()
);

CREATE TABLE IF NOT EXISTS news_publications (
    sequence bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    client_publish_id text NOT NULL UNIQUE,
    edition_id text NOT NULL,
    edition_date text NOT NULL,
    expected_revision bigint NOT NULL CHECK (expected_revision >= 0),
    revision bigint NOT NULL CHECK (revision >= 1),
    edition_digest text NOT NULL,
    edition jsonb NOT NULL,
    recorded_at_ms bigint NOT NULL,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    UNIQUE (edition_id, revision)
);

CREATE TABLE IF NOT EXISTS extension_states (
    task_id text NOT NULL REFERENCES tasks(task_id) ON DELETE RESTRICT,
    namespace text NOT NULL,
    task_revision bigint NOT NULL CHECK (task_revision >= 1),
    payload_digest text NOT NULL,
    payload jsonb NOT NULL,
    updated_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    PRIMARY KEY (task_id, namespace)
);

CREATE TABLE IF NOT EXISTS extension_history (
    task_id text NOT NULL REFERENCES tasks(task_id) ON DELETE RESTRICT,
    namespace text NOT NULL,
    task_revision bigint NOT NULL CHECK (task_revision >= 1),
    payload_digest text NOT NULL,
    payload jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    PRIMARY KEY (task_id, namespace, task_revision)
);

CREATE TABLE IF NOT EXISTS activity_log (
    sequence bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    activity_kind text NOT NULL,
    subject_id text NOT NULL,
    task_revision bigint,
    payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp()
);

CREATE INDEX IF NOT EXISTS tasks_state_updated_idx ON tasks(state, updated_at DESC, task_id);
CREATE INDEX IF NOT EXISTS tasks_goal_updated_idx ON tasks(goal_id, updated_at DESC, task_id);
CREATE INDEX IF NOT EXISTS board_topic_sequence_idx ON board_messages(topic, sequence);
CREATE INDEX IF NOT EXISTS board_reply_sequence_idx ON board_messages(reply_to_client_message_id, sequence);
CREATE INDEX IF NOT EXISTS board_search_fts_idx ON board_messages USING GIN (
    to_tsvector('simple', coalesce(author_label,'') || ' ' || coalesce(topic,'') || ' ' || message)
);
CREATE INDEX IF NOT EXISTS news_edition_revision_idx ON news_publications(edition_id, revision DESC);
CREATE INDEX IF NOT EXISTS news_date_idx ON news_publications(edition_date DESC, edition_id DESC, revision DESC);
CREATE INDEX IF NOT EXISTS activity_sequence_idx ON activity_log(sequence);
"""
