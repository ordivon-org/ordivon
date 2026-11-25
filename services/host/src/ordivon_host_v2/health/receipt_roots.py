"""Read-only history root qualification at the caller's consistent PG cut."""

from __future__ import annotations

from typing import Any

import psycopg

from ..work_receipts import replay_pinned_work_receipt


def count_invalid_work_receipt_roots(conn: psycopg.Connection[dict[str, Any]]) -> int:
    """Count invalid receipts, never silently omit a malformed root.

    Stream one native association, rather than re-querying the same snapshot
    per receipt. The caller owns the transaction/isolation. Legacy full
    receipts without pins are self-contained and excluded from this audit.
    """
    invalid = 0
    with conn.cursor(name="host_work_receipt_root_scan") as cursor:
        cursor.itersize = 128
        cursor.execute(
            "SELECT r.operation,r.response,r.receipt_work_ref,r.receipt_work_revision,"
            "s.snapshot_digest,s.payload,s.writer_actor_ref "
            "FROM command_receipts r LEFT JOIN work_snapshots s "
            "ON (s.work_ref,s.revision)=(r.receipt_work_ref,r.receipt_work_revision) "
            "WHERE (r.operation IN ('work.create','work.snapshot.commit') "
            "AND r.response IS NOT NULL "
            "AND r.response->>'kind' IS DISTINCT FROM 'ordivon.host-work') "
            "OR r.receipt_work_ref IS NOT NULL OR r.receipt_work_revision IS NOT NULL "
            "OR r.response->>'kind'='ordivon.host-work-receipt-ref-v1'"
        )
        for row in cursor:
            try:
                response = row["response"]
                if not isinstance(response, dict) or row["operation"] not in (
                    "work.create",
                    "work.snapshot.commit",
                ):
                    raise ValueError("invalid Work receipt operation or format")
                replay_pinned_work_receipt(
                    response,
                    work_ref=row["receipt_work_ref"],
                    revision=row["receipt_work_revision"],
                    target=row,
                )
            except RuntimeError, ValueError, TypeError, KeyError:
                invalid += 1
    return invalid
