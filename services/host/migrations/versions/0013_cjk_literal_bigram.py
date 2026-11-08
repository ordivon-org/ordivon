"""Replace ineffective CJK trigram GIN index with upstream PostgreSQL pg_bigm.

Revision ID: 0013
Revises: 0012

Provision the pinned pg_bigm extension as the database owner before running
Alembic. The source is an upstream PostgreSQL C extension, not a Host-owned
search ledger. Index construction and obsolete index removal are concurrent
to avoid blocking Host message writers.
"""

from alembic import op
from sqlalchemy import text

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None

INDEX = "message_body_bigm_idx"
RETIRED_INDEX = "message_body_trgm_idx"


def upgrade() -> None:
    conn = op.get_bind()
    version = conn.execute(
        text("SELECT extversion FROM pg_extension WHERE extname='pg_bigm'")
    ).scalar()
    if version != "1.2":
        raise RuntimeError(
            "Host schema 0013 requires owner-provisioned pg_bigm 1.2 "
            f"(observed={version!r}); see Host Owner Guide"
        )
    invalid = conn.execute(
        text(
            "SELECT NOT indisvalid FROM pg_index "
            "WHERE indexrelid=to_regclass('message_body_bigm_idx')"
        )
    ).scalar()
    with op.get_context().autocommit_block():
        if invalid:
            op.execute(f"DROP INDEX CONCURRENTLY IF EXISTS {INDEX}")
        op.execute(
            f"CREATE INDEX CONCURRENTLY IF NOT EXISTS {INDEX} "
            "ON messages USING GIN (body gin_bigm_ops)"
        )
        op.execute(f"DROP INDEX CONCURRENTLY IF EXISTS {RETIRED_INDEX}")

    op.execute(
        "ALTER TABLE host_v2_schema DROP CONSTRAINT IF EXISTS "
        "host_v2_schema_schema_version_check"
    )
    op.execute(
        "ALTER TABLE host_v2_schema ADD CONSTRAINT "
        "host_v2_schema_schema_version_check "
        "CHECK (schema_version BETWEEN 1 AND 13)"
    )
    op.execute("UPDATE host_v2_schema SET schema_version=13 WHERE singleton")


def downgrade() -> None:
    raise RuntimeError(
        "0013 retires an ineffective trigram index; downgrade requires "
        "explicit schema and installed-release reconciliation"
    )
