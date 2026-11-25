"""Native schema-17 receipt format fence; no process cache or DDL authority."""

from __future__ import annotations

from typing import Any

import psycopg

LEGACY_ONLY_CONSTRAINT = "command_receipt_legacy_only"
# PostgreSQL 18's exact deparsed schema-17 contracts. These are independent
# qualification oracles, not another schema writer. Unexpected forms fail closed.
_LEGACY_ONLY = "CHECK (((response ->> 'kind'::text) IS DISTINCT FROM 'ordivon.host-work-receipt-ref-v1'::text))"
_ROOT_FK = (
    "FOREIGN KEY (receipt_work_ref, receipt_work_revision) REFERENCES "
    "work_snapshots(work_ref, revision) MATCH FULL ON UPDATE RESTRICT ON DELETE RESTRICT"
)
_ROOT_SHAPE = """CHECK (
CASE
    WHEN (((response ->> 'kind'::text) = 'ordivon.host-work-receipt-ref-v1'::text) IS TRUE) THEN (((operation = ANY (ARRAY['work.create'::text, 'work.snapshot.commit'::text])) AND (receipt_work_ref IS NOT NULL) AND ((receipt_work_revision >= 1) AND (receipt_work_revision <= '9007199254740991'::bigint)) AND (jsonb_typeof((response -> 'envelope'::text)) = 'object'::text) AND (jsonb_typeof(((response -> 'envelope'::text) -> 'workRef'::text)) = 'string'::text) AND (jsonb_typeof(((response -> 'envelope'::text) -> 'revision'::text)) = 'number'::text) AND (((response -> 'envelope'::text) ->> 'workRef'::text) = receipt_work_ref) AND (((response -> 'envelope'::text) ->> 'revision'::text) = (receipt_work_revision)::text)) IS TRUE)
    ELSE ((receipt_work_ref IS NULL) AND (receipt_work_revision IS NULL))
END)"""


def _contract_matches(row: dict[str, Any], kind: str, definition: str) -> bool:
    return (
        row["contype"] == kind
        and row["convalidated"] is True
        and row["conenforced"] is True
        and row["condeferrable"] is False
        and row["definition"] == definition
    )


def legacy_receipt_fence_present(conn: psycopg.Connection[dict[str, Any]]) -> bool:
    """Observe the exact fence while the caller owns the native table lock."""
    row = conn.execute(
        "SELECT contype,convalidated,conenforced,condeferrable,"
        "pg_get_constraintdef(oid) AS definition FROM pg_constraint "
        "WHERE conrelid='command_receipts'::regclass AND conname=%s",
        (LEGACY_ONLY_CONSTRAINT,),
    ).fetchone()
    if row is None:
        return False
    if not _contract_matches(row, "c", _LEGACY_ONLY):
        raise RuntimeError("existing legacy-only receipt fence differs")
    return True


def require_native_receipt_roots(conn: psycopg.Connection[dict[str, Any]]) -> None:
    rows = {
        row["conname"]: row
        for row in conn.execute(
            "SELECT conname,contype,convalidated,conenforced,condeferrable,"
            "confrelid='work_snapshots'::regclass AS exact_target,"
            "pg_get_constraintdef(oid) AS definition FROM pg_constraint "
            "WHERE conrelid='command_receipts'::regclass AND conname IN "
            "('command_receipt_work_root_fk','command_receipt_work_root_shape')"
        ).fetchall()
    }
    fk = rows.get("command_receipt_work_root_fk")
    shape = rows.get("command_receipt_work_root_shape")
    if (
        fk is None
        or shape is None
        or fk["exact_target"] is not True
        or not _contract_matches(fk, "f", _ROOT_FK)
        or not _contract_matches(shape, "c", _ROOT_SHAPE)
    ):
        raise RuntimeError("native Work receipt roots unqualified")
