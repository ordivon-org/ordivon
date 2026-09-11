"""allow transactional idempotency claim reservation

Revision ID: 0002
Revises: 0001
"""

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE command_receipts ALTER COLUMN response DROP NOT NULL")


def downgrade() -> None:
    op.execute("DELETE FROM command_receipts WHERE response IS NULL")
    op.execute("ALTER TABLE command_receipts ALTER COLUMN response SET NOT NULL")
