"""Native receipt-root association shared by read-only audit and maintenance."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import psycopg

from .work_receipts import replay_pinned_work_receipt

ROOT_BATCH_SIZE = 128

_PIN_OR_TAG = (
    "r.receipt_work_ref IS NOT NULL OR r.receipt_work_revision IS NOT NULL "
    "OR r.response->>'kind'='ordivon.host-work-receipt-ref-v1'"
)
_AUDIT_WORK_RECEIPT = (
    "r.operation IN ('work.create','work.snapshot.commit') "
    "AND r.response IS NOT NULL "
    "AND r.response->>'kind' IS DISTINCT FROM 'ordivon.host-work'"
)
_ROOT_SELECT = (
    "SELECT r.client_request_id,r.operation,r.response,r.receipt_work_ref,"
    "r.receipt_work_revision,s.snapshot_digest,s.payload,s.writer_actor_ref "
    "FROM command_receipts r LEFT JOIN work_snapshots s "
    "ON (s.work_ref,s.revision)=(r.receipt_work_ref,r.receipt_work_revision)"
)


@contextmanager
def native_work_receipt_rows(
    conn: psycopg.Connection[dict[str, Any]], *, audit: bool
) -> Iterator[psycopg.ServerCursor[dict[str, Any]]]:
    """Stream exact native roots; audit additionally inspects malformed unpinned Work receipts.

    The caller owns the transaction cut and maintenance lock. Only fixed
    predicates are composed, and maintenance visits deterministic key order.
    """
    if audit:
        name = "host_work_receipt_root_scan"
        query = f"{_ROOT_SELECT} WHERE ({_AUDIT_WORK_RECEIPT}) OR ({_PIN_OR_TAG})"
    else:
        name = "host_work_receipt_expand"
        query = f"{_ROOT_SELECT} WHERE {_PIN_OR_TAG} ORDER BY r.client_request_id"
    with conn.cursor(name=name) as cursor:
        cursor.itersize = ROOT_BATCH_SIZE
        cursor.execute(query)
        yield cursor


def hydrate_native_work_receipt(row: dict[str, Any]) -> dict[str, Any]:
    """Validate operation and exact pin before reusing the shared pure codec."""
    response = row["response"]
    if not isinstance(response, dict) or row["operation"] not in (
        "work.create",
        "work.snapshot.commit",
    ):
        raise RuntimeError("invalid Work receipt operation or format")
    return replay_pinned_work_receipt(
        response,
        work_ref=row["receipt_work_ref"],
        revision=row["receipt_work_revision"],
        target=row,
    )
