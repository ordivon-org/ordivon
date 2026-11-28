"""Protect exact compact Work receipt roots; leave compact writes disabled.

Revision ID: 0017
Revises: 0016

This migration changes representation only. Existing receipts and snapshots
are not rewritten. Downgrade requires a previously restored legacy-only fence.
"""

from alembic import op
from sqlalchemy import text

revision = "0017"
down_revision = "0016"
branch_labels = None
depends_on = None


def _version(value: int) -> None:
    op.execute("ALTER TABLE host_v2_schema DROP CONSTRAINT host_v2_schema_schema_version_check")
    op.execute(f"UPDATE host_v2_schema SET schema_version={value} WHERE singleton")
    op.execute(
        "ALTER TABLE host_v2_schema ADD CONSTRAINT host_v2_schema_schema_version_check "
        f"CHECK (schema_version BETWEEN 1 AND {value})"
    )


def upgrade() -> None:
    # Fail within the operator's transaction budget rather than waiting forever.
    op.execute("SET LOCAL lock_timeout = '5s'")
    op.execute("""
ALTER TABLE command_receipts
    ADD COLUMN receipt_work_ref text,
    ADD COLUMN receipt_work_revision bigint,
    ADD CONSTRAINT command_receipt_work_root_shape CHECK (
        CASE WHEN (response->>'kind' = 'ordivon.host-work-receipt-ref-v1') IS TRUE
        THEN (
            operation IN ('work.create','work.snapshot.commit')
            AND receipt_work_ref IS NOT NULL
            AND receipt_work_revision BETWEEN 1 AND 9007199254740991
            AND jsonb_typeof(response->'envelope') = 'object'
            AND jsonb_typeof(response->'envelope'->'workRef') = 'string'
            AND jsonb_typeof(response->'envelope'->'revision') = 'number'
            AND response->'envelope'->>'workRef' = receipt_work_ref
            AND response->'envelope'->>'revision' = receipt_work_revision::text
        ) IS TRUE
        ELSE receipt_work_ref IS NULL AND receipt_work_revision IS NULL
        END
    ),
    ADD CONSTRAINT command_receipt_work_root_fk
        FOREIGN KEY (receipt_work_ref,receipt_work_revision)
        REFERENCES work_snapshots(work_ref,revision)
        MATCH FULL ON DELETE RESTRICT ON UPDATE RESTRICT
    """)
    op.execute("""
CREATE INDEX command_receipt_work_root_idx
    ON command_receipts(receipt_work_ref,receipt_work_revision)
    WHERE receipt_work_ref IS NOT NULL
    """)
    op.execute("""
ALTER TABLE command_receipts ADD CONSTRAINT command_receipt_legacy_only
    CHECK (response->>'kind' IS DISTINCT FROM 'ordivon.host-work-receipt-ref-v1')
    """)
    _version(17)


def downgrade() -> None:
    # Explicit rollback preparation is separate from schema removal. Never
    # silently discard a live pin or enable an old reader over compact rows.
    op.execute("SET LOCAL lock_timeout = '5s'")
    op.execute("LOCK TABLE command_receipts IN ACCESS EXCLUSIVE MODE")
    conn = op.get_bind()
    guard = conn.execute(
        text(
            "SELECT convalidated AND pg_get_expr(conbin,conrelid) = "
            "'((response ->> ''kind''::text) IS DISTINCT FROM "
            "''ordivon.host-work-receipt-ref-v1''::text)' FROM pg_constraint "
            "WHERE conrelid='command_receipts'::regclass "
            "AND conname='command_receipt_legacy_only' AND contype='c'"
        )
    ).scalar()
    if guard is not True:
        raise RuntimeError("restore the validated legacy-only receipt fence before downgrade")
    if conn.execute(
        text(
            "SELECT EXISTS (SELECT 1 FROM command_receipts "
            "WHERE receipt_work_ref IS NOT NULL OR receipt_work_revision IS NOT NULL "
            "OR response->>'kind' = 'ordivon.host-work-receipt-ref-v1')"
        )
    ).scalar():
        raise RuntimeError("compact Work receipt roots remain; expand before downgrade")
    op.execute("ALTER TABLE command_receipts DROP CONSTRAINT command_receipt_legacy_only")
    op.execute("ALTER TABLE command_receipts DROP CONSTRAINT command_receipt_work_root_fk")
    op.execute("ALTER TABLE command_receipts DROP CONSTRAINT command_receipt_work_root_shape")
    op.execute("DROP INDEX command_receipt_work_root_idx")
    op.execute(
        "ALTER TABLE command_receipts DROP COLUMN receipt_work_ref, DROP COLUMN receipt_work_revision"
    )
    _version(16)
