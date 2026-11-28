"""Work receipt finalization in the existing idempotency claim transaction."""

from __future__ import annotations

from typing import Any

import psycopg
from psycopg.types.json import Jsonb

from .command_receipts import record_command_receipt
from .work_receipt_fence import legacy_receipt_fence_present, require_native_receipt_roots
from .work_receipts import encode_work_receipt, replay_work_receipt


def record_work_receipt(
    conn: psycopg.Connection[dict[str, Any]],
    client_request_id: str,
    operation: str,
    request_digest: str,
    result: dict[str, Any],
    *,
    compact_requested: bool = False,
) -> None:
    """Default legacy writes; explicitly opted-in writers obey the native fence.

    The preceding INSERT claim already holds ROW EXCLUSIVE through commit.
    Exclusive maintenance/DDL cannot cross that admission. No mode is cached.
    """
    if not compact_requested or legacy_receipt_fence_present(conn):
        record_command_receipt(conn, client_request_id, operation, request_digest, result)
        return
    require_native_receipt_roots(conn)
    if operation not in ("work.create", "work.snapshot.commit"):
        raise RuntimeError("invalid compact Work receipt operation")
    tag = encode_work_receipt(result)
    # Read the exact immutable target, never today's current Work pointer.
    restored = replay_work_receipt(conn, tag, work_ref=result["workRef"])
    if restored != {**result, "admission": "existing"}:
        raise RuntimeError("compact Work receipt replay differs")
    updated = conn.execute(
        "UPDATE command_receipts SET response=%s,receipt_work_ref=%s,receipt_work_revision=%s "
        "WHERE client_request_id=%s AND operation=%s AND request_digest=%s "
        "AND response IS NULL AND receipt_work_ref IS NULL AND receipt_work_revision IS NULL "
        "RETURNING client_request_id",
        (
            Jsonb(tag),
            result["workRef"],
            result["revision"],
            client_request_id,
            operation,
            request_digest,
        ),
    ).fetchone()
    if updated is None or updated["client_request_id"] != client_request_id:
        raise RuntimeError("idempotency claim could not be finalized")
