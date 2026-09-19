"""replace synthetic Board route anchors with explicit Task foreign key

Revision ID: 0005
Revises: 0004
"""

from alembic import op
from sqlalchemy import text

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None

_LEGACY_PREFIX = "TASK COORDINATION ANCHOR v1 / exact Task identity " + chr(96)
_LEGACY_SUFFIX = (
    chr(96)
    + ". This Board root is a deterministic navigation coordinate only. It is not Task standing, "
    "priority, ownership, delegation, delivery, unread state, execution authority, or proof that "
    "any reply was consumed. Callers targeting this Task may post direct replies while preserving "
    "their own domain topic."
)


def upgrade() -> None:
    op.execute(
        "ALTER TABLE board_messages ADD COLUMN task_id text "
        "REFERENCES tasks(task_id) ON DELETE RESTRICT"
    )
    bind = op.get_bind()
    rows = bind.execute(
        text(
            "SELECT client_message_id,author_label,message_kind,topic,message,"
            "reply_to_client_message_id FROM board_messages "
            "WHERE client_message_id LIKE 'task-route-anchor-v1:%'"
        )
    ).mappings()
    for row in rows:
        message = row["message"]
        if (
            row["author_label"] != "task-routing-anchor-v1"
            or row["message_kind"] != "note"
            or row["topic"] != "agent-native-collaboration-routing"
            or row["reply_to_client_message_id"] is not None
            or not isinstance(message, str)
            or not message.startswith(_LEGACY_PREFIX)
            or not message.endswith(_LEGACY_SUFFIX)
        ):
            continue
        task_id = message[len(_LEGACY_PREFIX) : -len(_LEGACY_SUFFIX)]
        exists = bind.execute(
            text("SELECT 1 FROM tasks WHERE task_id=:task_id"), {"task_id": task_id}
        ).first()
        if exists is None:
            continue
        bind.execute(
            text(
                "UPDATE board_messages SET task_id=:task_id "
                "WHERE client_message_id=:client_message_id"
            ),
            {"task_id": task_id, "client_message_id": row["client_message_id"]},
        )

    op.execute(
        """
        WITH RECURSIVE routed(client_message_id, task_id) AS (
            SELECT client_message_id, task_id
            FROM board_messages
            WHERE task_id IS NOT NULL
          UNION ALL
            SELECT child.client_message_id, routed.task_id
            FROM board_messages AS child
            JOIN routed ON child.reply_to_client_message_id = routed.client_message_id
            WHERE child.task_id IS NULL
        )
        UPDATE board_messages AS target
        SET task_id = routed.task_id
        FROM routed
        WHERE target.client_message_id = routed.client_message_id
          AND target.task_id IS NULL
        """
    )
    op.execute("CREATE INDEX board_task_sequence_idx ON board_messages(task_id, sequence)")
    op.execute(
        "ALTER TABLE host_v2_schema DROP CONSTRAINT IF EXISTS "
        "host_v2_schema_schema_version_check"
    )
    op.execute(
        "ALTER TABLE host_v2_schema ADD CONSTRAINT host_v2_schema_schema_version_check "
        "CHECK (schema_version BETWEEN 1 AND 5)"
    )
    op.execute("UPDATE host_v2_schema SET schema_version=5 WHERE singleton")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS board_task_sequence_idx")
    op.execute("ALTER TABLE board_messages DROP COLUMN IF EXISTS task_id")
    op.execute(
        "ALTER TABLE host_v2_schema DROP CONSTRAINT IF EXISTS "
        "host_v2_schema_schema_version_check"
    )
    op.execute(
        "ALTER TABLE host_v2_schema ADD CONSTRAINT host_v2_schema_schema_version_check "
        "CHECK (schema_version BETWEEN 1 AND 4)"
    )
    op.execute("UPDATE host_v2_schema SET schema_version=4 WHERE singleton")
