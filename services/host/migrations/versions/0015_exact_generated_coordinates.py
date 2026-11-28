"""Keep both generated cursor coordinates inside the exact JSON integer domain.

Revision ID: 0015
Revises: 0014

Do not reset or truncate a sequence, rewrite historical rows, or change the
ordering mechanism. Existing unrepresentable rows make this migration fail.
"""

from alembic import op

revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None

# Historical migration constants must not import mutable runtime code.
MAX_EXACT = 9007199254740991
CHANGE_TABLES = (
    "actor_refs",
    "works",
    "work_snapshots",
    "work_relations",
    "spaces",
    "space_subjects",
    "participations",
    "topics",
    "messages",
    "message_relations",
    "coordination_intents",
    "subscriptions",
)


def _version(value: int) -> None:
    op.execute("ALTER TABLE host_v2_schema DROP CONSTRAINT host_v2_schema_schema_version_check")
    op.execute(f"UPDATE host_v2_schema SET schema_version={value} WHERE singleton")
    op.execute(
        "ALTER TABLE host_v2_schema ADD CONSTRAINT host_v2_schema_schema_version_check "
        f"CHECK (schema_version BETWEEN 1 AND {value})"
    )


def upgrade() -> None:
    op.execute(f"ALTER TABLE messages ALTER COLUMN sequence SET MAXVALUE {MAX_EXACT}")
    op.execute(
        "ALTER TABLE messages ADD CONSTRAINT messages_exact_sequence "
        f"CHECK (sequence BETWEEN 1 AND {MAX_EXACT})"
    )
    op.execute(
        "ALTER TABLE swf_change_clock ADD CONSTRAINT swf_exact_change_clock "
        f"CHECK (value BETWEEN 0 AND {MAX_EXACT})"
    )
    for table in CHANGE_TABLES:
        op.execute(
            f"ALTER TABLE {table} ADD CONSTRAINT {table}_exact_change_sequence "
            f"CHECK (change_sequence BETWEEN 1 AND {MAX_EXACT})"
        )
    _version(15)


def downgrade() -> None:
    for table in reversed(CHANGE_TABLES):
        op.execute(f"ALTER TABLE {table} DROP CONSTRAINT {table}_exact_change_sequence")
    op.execute("ALTER TABLE swf_change_clock DROP CONSTRAINT swf_exact_change_clock")
    op.execute("ALTER TABLE messages DROP CONSTRAINT messages_exact_sequence")
    op.execute("ALTER TABLE messages ALTER COLUMN sequence SET NO MAXVALUE")
    _version(14)
