"""Maintenance-only atomic expansion; no service endpoint or new authority."""

from __future__ import annotations

from typing import Any

import psycopg
from psycopg.types.json import Jsonb

from .work_receipts import replay_work_receipt


def expand_work_receipts_and_fence(
    conn: psycopg.Connection[dict[str, Any]],
) -> int:
    """Expand every compact receipt, preserving its historical response.

    Caller supplies an isolated, authorized maintenance transaction, with
    bounded lock/statement timeouts. Commit is caller-owned. An error must
    roll back the entire transaction. The exclusive lock prevents concurrent
    claims or finalization until the persistent legacy-only guard is installed.
    On ambiguous commit, inspect the actual constraint and remaining roots
    before retry; do not automatically rerun the operation.
    """
    conn.execute("LOCK TABLE command_receipts IN ACCESS EXCLUSIVE MODE")
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
