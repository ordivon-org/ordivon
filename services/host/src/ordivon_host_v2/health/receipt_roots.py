"""Read-only history root qualification at the caller's consistent PG cut."""

from __future__ import annotations

from typing import Any

import psycopg

from ..work_receipt_roots import hydrate_native_work_receipt, native_work_receipt_rows


def count_invalid_work_receipt_roots(conn: psycopg.Connection[dict[str, Any]]) -> int:
    """Count invalid receipts, never silently omit a malformed root."""
    invalid = 0
    with native_work_receipt_rows(conn, audit=True) as cursor:
        for row in cursor:
            try:
                hydrate_native_work_receipt(row)
            except RuntimeError, ValueError, TypeError, KeyError:
                invalid += 1
    return invalid
