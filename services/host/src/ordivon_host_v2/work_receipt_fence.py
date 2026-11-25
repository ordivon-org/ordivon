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


# Exact ordinary PostgreSQL foreign-key trigger contract on the two base tables.
_ROOT_TRIGGER_SIGNATURES = {
    ("command_receipts", "RI_FKey_check_ins", 5),
    ("command_receipts", "RI_FKey_check_upd", 17),
    ("work_snapshots", "RI_FKey_restrict_del", 9),
    ("work_snapshots", "RI_FKey_restrict_upd", 17),
}


def _native_root_enforcement(conn: psycopg.Connection[dict[str, Any]]) -> bool:
    # Catalog declaration alone is insufficient if internal triggers are disabled.
    # This is a local qualification, not protection from a later privileged DDL.
    rows = conn.execute(
        "SELECT CASE WHEN t.tgrelid='command_receipts'::regclass THEN 'command_receipts' "
        "WHEN t.tgrelid='work_snapshots'::regclass THEN 'work_snapshots' END AS relation, "
        "p.proname,t.tgtype,t.tgenabled,t.tgisinternal,t.tgdeferrable,"
        "p.pronamespace='pg_catalog'::regnamespace AS native_function,"
        "current_setting('session_replication_role') AS replication_role "
        "FROM pg_trigger t JOIN pg_constraint c ON t.tgconstraint=c.oid "
        "JOIN pg_proc p ON p.oid=t.tgfoid "
        "WHERE c.conrelid='command_receipts'::regclass "
        "AND c.conname='command_receipt_work_root_fk'"
    ).fetchall()
    return (
        len(rows) == len(_ROOT_TRIGGER_SIGNATURES)
        and {(r["relation"], r["proname"], r["tgtype"]) for r in rows} == _ROOT_TRIGGER_SIGNATURES
        and all(
            r["tgenabled"] in ("O", "A")
            and r["tgisinternal"] is True
            and r["tgdeferrable"] is False
            and r["native_function"] is True
            and r["replication_role"] == "origin"
            for r in rows
        )
    )


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
        or not _native_root_enforcement(conn)
    ):
        raise RuntimeError("native Work receipt roots unqualified")
