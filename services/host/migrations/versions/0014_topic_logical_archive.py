"""Archive closed Topic discussions without copying or deleting Message rows.

Revision ID: 0014
Revises: 0013

Archived topics remain addressable by explicit TopicRef/MessageRef. Existing
active Topic inventory hides them by default; explicit inventory can include
them. This is a logical cold tier, not a physical deletion or off-host backup.
"""

from alembic import op
from sqlalchemy import text

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE topics DROP CONSTRAINT topics_state_check")
    op.execute(
        "ALTER TABLE topics ADD CONSTRAINT topics_state_check "
        "CHECK (state IN ('open','closed','archived'))"
    )
    op.execute(
        "ALTER TABLE host_v2_schema DROP CONSTRAINT IF EXISTS "
        "host_v2_schema_schema_version_check"
    )
    op.execute(
        "ALTER TABLE host_v2_schema ADD CONSTRAINT "
        "host_v2_schema_schema_version_check "
        "CHECK (schema_version BETWEEN 1 AND 14)"
    )
    op.execute("UPDATE host_v2_schema SET schema_version=14 WHERE singleton")


def downgrade() -> None:
    present = op.get_bind().execute(
        text("SELECT EXISTS(SELECT 1 FROM topics WHERE state='archived')")
    ).scalar_one()
    if present:
        raise RuntimeError("restore archived topics before downgrading to schema 13")
    op.execute("ALTER TABLE topics DROP CONSTRAINT topics_state_check")
    op.execute(
        "ALTER TABLE topics ADD CONSTRAINT topics_state_check "
        "CHECK (state IN ('open','closed'))"
    )
    op.execute("UPDATE host_v2_schema SET schema_version=13 WHERE singleton")
    op.execute(
        "ALTER TABLE host_v2_schema DROP CONSTRAINT IF EXISTS "
        "host_v2_schema_schema_version_check"
    )
    op.execute(
        "ALTER TABLE host_v2_schema ADD CONSTRAINT "
        "host_v2_schema_schema_version_check "
        "CHECK (schema_version BETWEEN 1 AND 13)"
    )
