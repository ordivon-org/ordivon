"""retire unconsumed external-news storage from Host authority

Revision ID: 0011
Revises: 0010

The external-news surface was removed before Social Work Fabric R2.
There is no active Host reader, mutation or publication API. The legacy
projection script targets a different, retired Host v1 database layout.
"""

from alembic import op

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DROP TABLE news_publications")
    op.execute(
        "ALTER TABLE host_v2_schema DROP CONSTRAINT IF EXISTS "
        "host_v2_schema_schema_version_check"
    )
    op.execute(
        "ALTER TABLE host_v2_schema ADD CONSTRAINT "
        "host_v2_schema_schema_version_check "
        "CHECK (schema_version BETWEEN 1 AND 11)"
    )
    op.execute("UPDATE host_v2_schema SET schema_version=11 WHERE singleton")


def downgrade() -> None:
    raise RuntimeError(
        "0011 retires an unused Host news product surface; restore the "
        "original pre-retirement archive to an isolated recovery database "
        "rather than recreating obsolete live Host storage"
    )
