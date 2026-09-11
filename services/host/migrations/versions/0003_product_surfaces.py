"""migrate Host product surfaces to PostgreSQL

Revision ID: 0003
Revises: 0002
"""

from alembic import op

from ordivon_host_v2.schema import SCHEMA_SQL

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.get_bind().exec_driver_sql(SCHEMA_SQL)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS activity_log")
    op.execute("DROP TABLE IF EXISTS extension_history")
    op.execute("DROP TABLE IF EXISTS extension_states")
    op.execute("DROP TABLE IF EXISTS news_publications")
    op.execute("DROP TABLE IF EXISTS board_messages")
    op.execute("ALTER TABLE tasks DROP COLUMN IF EXISTS goal_id")
    op.execute("UPDATE host_v2_schema SET schema_version=2 WHERE singleton")
