from __future__ import annotations

from typing import Any

import psycopg
from psycopg.types.json import Jsonb

from .errors import ConflictError

# Caller-owned Host PostgreSQL transaction; no independent connection or writer.


def claim_command_receipt(
    conn: psycopg.Connection[dict[str, Any]],
    client_request_id: str,
    operation: str,
    request_digest: str,
) -> dict[str, Any] | None:
    claimed = conn.execute(
        "INSERT INTO command_receipts(client_request_id,operation,request_digest,response) "
        "VALUES (%s,%s,%s,NULL) ON CONFLICT (client_request_id) DO NOTHING RETURNING client_request_id",
        (client_request_id, operation, request_digest),
    ).fetchone()
    if claimed is not None:
        return None
    row = conn.execute(
        "SELECT operation,request_digest,response FROM command_receipts WHERE client_request_id=%s",
        (client_request_id,),
    ).fetchone()
    if row is None:
        raise RuntimeError("idempotency claim disappeared")
    if row["operation"] != operation or row["request_digest"] != request_digest:
        raise ConflictError("client_request_id was already used for different content")
    response = row["response"]
    if response is None:
        raise RuntimeError("committed idempotency claim is missing its response")
    if not isinstance(response, dict):
        raise RuntimeError("idempotency response is not a PostgreSQL jsonb object")
    replay = dict(response)
    replay["admission"] = "existing"
    return replay


def record_command_receipt(
    conn: psycopg.Connection[dict[str, Any]],
    client_request_id: str,
    operation: str,
    request_digest: str,
    result: dict[str, Any],
) -> None:
    updated = conn.execute(
        "UPDATE command_receipts SET response=%s "
        "WHERE client_request_id=%s AND operation=%s AND request_digest=%s AND response IS NULL "
        "RETURNING client_request_id",
        (Jsonb(result), client_request_id, operation, request_digest),
    ).fetchone()
    if updated is None:
        raise RuntimeError("idempotency claim could not be finalized")
