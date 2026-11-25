"""Maintenance-only atomic expansion; no service endpoint or new authority."""

from __future__ import annotations

from typing import Any

import psycopg

from .canonical_json import canonical_bytes
from .work_receipt_fence import legacy_receipt_fence_present
from .work_receipt_roots import (
    ROOT_BATCH_SIZE,
    hydrate_native_work_receipt,
    native_work_receipt_rows,
)

# Batch transport budget, not an admission or historical payload limit.
# A single larger response is still processed independently.
_UPDATE_BATCH_BYTES = 4 * 1024 * 1024


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
    if legacy_receipt_fence_present(conn):
        remaining = conn.execute(
            "SELECT EXISTS (SELECT 1 FROM command_receipts "
            "WHERE receipt_work_ref IS NOT NULL OR receipt_work_revision IS NOT NULL "
            "OR response->>'kind' = 'ordivon.host-work-receipt-ref-v1') AS present"
        ).fetchone()
        if remaining is None or remaining["present"] is not False:
            raise RuntimeError("compact Work receipt roots remain under legacy-only fence")
        return 0

    count = 0
    keys: list[str] = []
    responses: list[str] = []
    payload_bytes = 0
    with native_work_receipt_rows(conn, audit=False) as cursor:
        for row in cursor:
            # Validate before staging. The exclusive receipt lock and
            # enclosing savepoint span all batches.
            payload = canonical_bytes(hydrate_native_work_receipt(row))
            if keys and (
                len(keys) >= ROOT_BATCH_SIZE or payload_bytes + len(payload) > _UPDATE_BATCH_BYTES
            ):
                count += _update_batch(conn, keys, responses)
                keys, responses, payload_bytes = [], [], 0
            keys.append(row["client_request_id"])
            responses.append(payload.decode("utf-8"))
            payload_bytes += len(payload)
        if keys:
            count += _update_batch(conn, keys, responses)
    conn.execute(
        "ALTER TABLE command_receipts ADD CONSTRAINT command_receipt_legacy_only "
        "CHECK (response->>'kind' IS DISTINCT FROM 'ordivon.host-work-receipt-ref-v1')"
    )
    return count


def _update_batch(
    conn: psycopg.Connection[dict[str, Any]], keys: list[str], responses: list[str]
) -> int:
    # Text arrays avoid reserializing canonical JSON; native JSONB is the
    # existing storage representation. Verify the exact updated ID set.
    changed = conn.execute(
        "UPDATE command_receipts AS r "
        "SET response=v.response::jsonb,receipt_work_ref=NULL,receipt_work_revision=NULL "
        "FROM unnest(%s::text[],%s::text[]) AS v(client_request_id,response) "
        "WHERE r.client_request_id=v.client_request_id "
        "AND r.receipt_work_ref IS NOT NULL RETURNING r.client_request_id",
        (keys, responses),
    ).fetchall()
    if len(changed) != len(keys) or {r["client_request_id"] for r in changed} != set(keys):
        raise RuntimeError("compact Work receipt root disappeared")
    return len(keys)
