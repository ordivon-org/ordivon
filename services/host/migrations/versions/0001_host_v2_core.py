"""host v2 core tables

Revision ID: 0001
Revises:
"""
from alembic import op

from ordivon_host_v2.schema import SCHEMA_SQL

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.get_bind().exec_driver_sql(SCHEMA_SQL)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS command_receipts")
    op.execute("DROP TABLE IF EXISTS task_events")
    op.execute("DROP TABLE IF EXISTS checkpoints")
    op.execute("DROP TABLE IF EXISTS tasks")
    op.execute("DROP TABLE IF EXISTS host_v2_schema")
