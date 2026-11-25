"""Native receipt-root association for replay, audit and maintenance."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import psycopg

from .command_receipts import try_claim_command_receipt, validate_command_receipt_replay
from .work_receipts import replay_pinned_work_receipt, replay_work_receipt

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


def claim_work_receipt(
    conn: psycopg.Connection[dict[str, Any]],
    client_request_id: str,
    operation: str,
    request_digest: str,
    *,
    work_ref: str,
    work_kind: str | None = None,
    revision: int | None = None,
    snapshot_digest: str | None = None,
    actor_ref: str | None = None,
    state: str | None = None,
) -> dict[str, Any] | None:
    """Reuse the claim arbiter; qualify the persisted native root before point replay.

    A whole-row receipt projection keeps the explicit schema-16 rollback
    reader usable without referring to columns removed by downgrade.
    No JSON conversion, schema fallback on SQL errors, or extra roundtrip.
    """
    if try_claim_command_receipt(conn, client_request_id, operation, request_digest):
        return None
    row = conn.execute(
        "SELECT r.*, (SELECT schema_version FROM host_v2_schema) AS receipt_schema "
        "FROM command_receipts r WHERE r.client_request_id=%s",
        (client_request_id,),
    ).fetchone()
    replay = validate_command_receipt_replay(row, operation, request_digest)
    if row is None:
        raise RuntimeError("idempotency claim disappeared")
    columns = ("receipt_work_ref", "receipt_work_revision")
    schema = row["receipt_schema"]
    if type(schema) is not int:
        raise RuntimeError("native Work receipt root schema unobservable")
    if schema >= 17:
        if not all(column in row for column in columns):
            raise RuntimeError("native Work receipt root columns missing")
    elif any(column in row for column in columns):
        raise RuntimeError("native Work receipt root schema differs")
    native_ref, native_revision = (row.get(column) for column in columns)
    if replay.get("kind") == "ordivon.host-work":
        if native_ref is not None or native_revision is not None:
            raise RuntimeError("invalid native Work receipt root for legacy response")
        return replay
    if (
        schema < 17
        or not isinstance(native_ref, str)
        or type(native_revision) is not int
        or native_ref != work_ref
        or (revision is not None and native_revision != revision)
    ):
        raise RuntimeError("native Work receipt root reference differs from request")
    # The native pin and requested context must both match the envelope.
    # The same immutable target lookup/digest codec is used by the writer.
    return replay_work_receipt(
        conn,
        replay,
        work_ref=native_ref,
        revision=native_revision,
        work_kind=work_kind,
        snapshot_digest=snapshot_digest,
        actor_ref=actor_ref,
        state=state,
    )


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
