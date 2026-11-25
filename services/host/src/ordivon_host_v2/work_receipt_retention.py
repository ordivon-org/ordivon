"""Maintenance-only atomic expansion; no service endpoint or new authority."""

from __future__ import annotations

from typing import Any

import psycopg
from psycopg.types.json import Jsonb

from .work_receipts import replay_work_receipt


def expand_work_receipts_and_fence(
    conn: psycopg.Connection[dict[str, Any]],
) -> int:
    """Expand exact receipts and restore the legacy-only fence.

    Caller owns the outer transaction and its bounded lock/statement timeouts.
    The operation uses a native savepoint: a caught exception cannot commit
    a partial expansion. A validated existing fence with no roots is a no-op
    (zero newly expanded rows, not a replay of the previous count).
    """
    if conn.autocommit:
        raise RuntimeError("Work receipt maintenance requires caller-owned transaction")
    # Start the outer transaction when necessary, without committing it here.
    # Acquire the fence inside a savepoint so failure also releases its locks.
    conn.execute("SELECT 1")
    with conn.transaction():
        conn.execute("LOCK TABLE command_receipts IN ACCESS EXCLUSIVE MODE")
        return _expand_locked(conn)


def _expand_locked(conn: psycopg.Connection[dict[str, Any]]) -> int:
    guard = conn.execute(
        "SELECT contype='c' AND convalidated AND pg_get_expr(conbin,conrelid) = "
        "'((response ->> ''kind''::text) IS DISTINCT FROM "
        "''ordivon.host-work-receipt-ref-v1''::text)' AS valid "
        "FROM pg_constraint WHERE conrelid='command_receipts'::regclass "
        "AND conname='command_receipt_legacy_only'"
    ).fetchone()
    if guard is not None:
        if guard["valid"] is not True:
            raise RuntimeError("existing legacy-only receipt fence differs")
        remaining = conn.execute(
            "SELECT EXISTS (SELECT 1 FROM command_receipts "
            "WHERE receipt_work_ref IS NOT NULL OR receipt_work_revision IS NOT NULL "
            "OR response->>'kind' = 'ordivon.host-work-receipt-ref-v1') AS present"
        ).fetchone()
        if remaining is None or remaining["present"] is not False:
            raise RuntimeError("compact Work receipt roots remain under legacy-only fence")
        return 0

    count = 0
    with conn.cursor(name="host_work_receipt_expand") as cursor:
        cursor.itersize = 128
        cursor.execute(
            "SELECT client_request_id,response,receipt_work_ref "
            "FROM command_receipts WHERE receipt_work_ref IS NOT NULL "
            "ORDER BY client_request_id FOR UPDATE"
        )
        for row in cursor:
            result = replay_work_receipt(conn, row["response"], work_ref=row["receipt_work_ref"])
            changed = conn.execute(
                "UPDATE command_receipts "
                "SET response=%s,receipt_work_ref=NULL,receipt_work_revision=NULL "
                "WHERE client_request_id=%s AND receipt_work_ref IS NOT NULL "
                "RETURNING client_request_id",
                (Jsonb(result), row["client_request_id"]),
            ).fetchone()
            if changed is None:
                raise RuntimeError("compact Work receipt root disappeared")
            count += 1
    conn.execute(
        "ALTER TABLE command_receipts ADD CONSTRAINT command_receipt_legacy_only "
        "CHECK (response->>'kind' IS DISTINCT FROM 'ordivon.host-work-receipt-ref-v1')"
    )
    return count
