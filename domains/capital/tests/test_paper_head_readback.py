"""One real PostgreSQL consumer proof: the Paper head is read-only and tamper-evident.

The database is intentionally disposable; fixture prices are never market claims.
This verifies a persistence boundary, not universal source-level refinement.
"""
from __future__ import annotations

import os
from datetime import date
from uuid import uuid4

import psycopg
import pytest

from ordivon_capital.accounting.paper_close import PaperSession
from ordivon_capital.accounting.postgres_paper_close import (
    PostgresPaperClose,
    read_committed_paper_close,
    read_latest_committed_paper_close,
)


def test_latest_paper_head_readback_preserves_history_and_rejects_tampering():
    dsn = os.environ.get("ORDIVON_CAPITAL_PAPER_PG_TEST_DSN")
    if not dsn:
        pytest.skip("isolated, disposable ordivon_paper PostgreSQL is required")
    key = "head-audit-" + uuid4().hex
    first = date(2026, 1, 8)
    second = date(2026, 1, 9)
    store = PostgresPaperClose(dsn)
    assert read_latest_committed_paper_close(dsn, key) is None
    opening = PaperSession(first, None, 1_000_000, 200_000, {}, ())
    next_day = PaperSession(second, first, 0, 0, {}, ())
    old = store.close_session(key, opening)
    assert read_latest_committed_paper_close(dsn, key) == old
    head = store.close_session(key, next_day)
    assert head["previous_request_sha256"] == old["request_sha256"]
    assert read_latest_committed_paper_close(dsn, key) == head
    assert read_committed_paper_close(dsn, key, first) == old
    assert store.close_session(key, next_day) == head
    assert read_latest_committed_paper_close(dsn, key) == head

    # If a stored market-provenance claim is changed without changing its
    # request binding, readers must not issue a trustworthy-looking receipt.
    with psycopg.connect(dsn) as db:
        db.execute(
            "UPDATE ordivon_paper.daily_close SET receipt = jsonb_set("
            "receipt, '{market_evidence,standing}', "
            "'\"COUNTERFEIT_MARKET_EVIDENCE\"'::jsonb) "
            "WHERE account_key = %s AND session = %s",
            (key, second),
        )
    with pytest.raises(ValueError, match="stored request disagree"):
        read_latest_committed_paper_close(dsn, key)
    with pytest.raises(ValueError, match="stored request disagree"):
        read_committed_paper_close(dsn, key, second)

    # History cannot be silently relinked to an unrelated predecessor.
    with psycopg.connect(dsn) as db:
        db.execute(
            "UPDATE ordivon_paper.daily_close SET receipt = jsonb_set("
            "jsonb_set(receipt, '{market_evidence,standing}', "
            "'\"CALLER_SUPPLIED_MARKS\"'::jsonb), "
            "'{previous_request_sha256}', '\"forged\"'::jsonb) "
            "WHERE account_key = %s AND session = %s",
            (key, second),
        )
    with pytest.raises(ValueError, match="stored request disagree"):
        read_latest_committed_paper_close(dsn, key)


def test_paper_readonly_head_has_no_implicit_database_or_account_creation():
    with pytest.raises(ValueError, match="explicit paper database DSN"):
        read_latest_committed_paper_close("", "example")
    with pytest.raises(ValueError, match="invalid paper account key"):
        read_latest_committed_paper_close("not-a-real-dsn", "../escape")
