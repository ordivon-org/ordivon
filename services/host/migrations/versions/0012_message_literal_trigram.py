"""Index literal CJK substring search with PostgreSQL pg_trgm.

Revision ID: 0012
Revises: 0011

CREATE INDEX CONCURRENTLY prevents blocking message writers during index
construction. An interrupted concurrent build can leave an invalid index;
remove only that invalid named index before retrying.
"""

from alembic import op
from sqlalchemy import text

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None

INDEX = "message_body_trgm_idx"


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    invalid = op.get_bind().execute(
        text(
            "SELECT 1 FROM pg_class c JOIN pg_index i ON i.indexrelid=c.oid "
            "WHERE c.oid=to_regclass('message_body_trgm_idx') AND NOT i.indisvalid"
        )
    ).scalar()
    with op.get_context().autocommit_block():
        if invalid:
            op.execute(f"DROP INDEX CONCURRENTLY IF EXISTS {INDEX}")
        op.execute(
            f"CREATE INDEX CONCURRENTLY IF NOT EXISTS {INDEX} "
            "ON messages USING GIN (body gin_trgm_ops)"
        )
    op.execute(
        "ALTER TABLE host_v2_schema DROP CONSTRAINT IF EXISTS "
        "host_v2_schema_schema_version_check"
    )
    op.execute(
        "ALTER TABLE host_v2_schema ADD CONSTRAINT "
        "host_v2_schema_schema_version_check "
        "CHECK (schema_version BETWEEN 1 AND 12)"
    )
    op.execute("UPDATE host_v2_schema SET schema_version=12 WHERE singleton")


def downgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute(f"DROP INDEX CONCURRENTLY IF EXISTS {INDEX}")
    op.execute("UPDATE host_v2_schema SET schema_version=11 WHERE singleton")
    op.execute(
        "ALTER TABLE host_v2_schema DROP CONSTRAINT IF EXISTS "
        "host_v2_schema_schema_version_check"
    )
    op.execute(
        "ALTER TABLE host_v2_schema ADD CONSTRAINT "
        "host_v2_schema_schema_version_check "
        "CHECK (schema_version BETWEEN 1 AND 11)"
    )
