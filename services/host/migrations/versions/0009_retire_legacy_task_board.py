"""retire legacy Task and Board active storage

Revision ID: 0009
Revises: 0008

This migration is intentionally irreversible: production legacy rows must be archived
and restore-verified before applying it. Historical recovery belongs to the external
archive, not to an active compatibility schema.
"""

from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DROP TABLE board_messages")
    op.execute("DROP TABLE task_events")
    op.execute("DROP TABLE checkpoints")
    op.execute("DROP TABLE tasks")
    op.execute(
        "ALTER TABLE host_v2_schema DROP CONSTRAINT IF EXISTS host_v2_schema_schema_version_check"
    )
    op.execute(
        "ALTER TABLE host_v2_schema ADD CONSTRAINT host_v2_schema_schema_version_check "
        "CHECK (schema_version BETWEEN 1 AND 9)"
    )
    op.execute("UPDATE host_v2_schema SET schema_version=9 WHERE singleton")


def downgrade() -> None:
    raise RuntimeError(
        "0009 is a destructive legacy-retirement boundary; restore archived schema-8 legacy data "
        "into a separate recovery database instead of recreating active Task/Board storage"
    )
