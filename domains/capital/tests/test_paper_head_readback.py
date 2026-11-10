"""One real PostgreSQL consumer proof: the Paper head is read-only and tamper-evident.

The database is intentionally disposable; fixture prices are never market claims.
This verifies a persistence boundary, not universal source-level refinement.
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict
from datetime import date
from unittest.mock import MagicMock
from uuid import uuid4

import psycopg
import pytest

from ordivon_capital.accounting.paper_close import PaperSession, value_session
from ordivon_capital.accounting.postgres_paper_close import (
    PostgresPaperClose,
    _read_committed_paper_receipt,
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

    # Neither the unchanged request hash nor a valid predecessor permits
    # independent changes to the protected-cash projection.
    with psycopg.connect(dsn) as db:
        db.execute(
            "UPDATE ordivon_paper.daily_close SET receipt = jsonb_set("
            "receipt, '{valuation,protected_minor}', '199999'::jsonb) "
            "WHERE account_key = %s AND session = %s",
            (key, second),
        )
    with pytest.raises(ValueError, match="stored request disagree"):
        read_latest_committed_paper_close(dsn, key)
    with pytest.raises(ValueError, match="stored request disagree"):
        read_committed_paper_close(dsn, key, second)
    with psycopg.connect(dsn) as db:
        db.execute(
            "UPDATE ordivon_paper.daily_close SET receipt = jsonb_set("
            "receipt, '{valuation,protected_minor}', '200000'::jsonb) "
            "WHERE account_key = %s AND session = %s",
            (key, second),
        )

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


@pytest.mark.parametrize("field,forged", [
    ("cash_minor", 1_000_001),
    ("protected_minor", 199_999),
    ("nav_minor", 999_999),
])
def test_readback_rejects_forged_valuation_without_mutating_request(field, forged):
    """Even a matching request digest cannot legitimate a modified receipt value."""
    opening = PaperSession(date(2026, 1, 8), None, 1_000_000, 200_000, {}, ())
    request = {
        "session": "2026-01-08",
        "previous_session": None,
        "contribution_minor": 1_000_000,
        "reserve_contribution_minor": 200_000,
        "marks": {},
        "buys": [],
        "market_evidence": {"standing": "CALLER_SUPPLIED_MARKS"},
    }
    digest = hashlib.sha256(
        json.dumps(request, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    valuation = asdict(value_session(None, opening)) | {"session": "2026-01-08"}
    for key in ("pending_sales", "sale_settlement_dates", "receivable_minor"):
        valuation.pop(key)
    receipt = {
        "schema_version": 1,
        "mode": "PAPER",
        "request_sha256": digest,
        "previous_request_sha256": None,
        "account_key": "forged-readback",
        "market_evidence": request["market_evidence"],
        "valuation": valuation,
    }
    db = MagicMock()
    db.execute.return_value.fetchone.side_effect = [
        (digest, request, receipt), None,
    ]
    assert _read_committed_paper_receipt(
        db, "forged-readback", opening.session
    ) == receipt
    receipt["valuation"][field] = forged
    db.execute.return_value.fetchone.side_effect = [
        (digest, request, receipt), None,
    ]
    with pytest.raises(ValueError, match="stored request disagree"):
        _read_committed_paper_receipt(db, "forged-readback", opening.session)

def test_readback_recomputes_non_genesis_close_against_previous_valuation():
    """A plausible current receipt cannot rewrite the inherited protected reserve."""
    genesis = PaperSession(date(2026, 1, 8), None, 1_000_000, 200_000, {}, ())
    current_day = PaperSession(date(2026, 1, 9), genesis.session, 150_000, 5_000, {}, ())
    prior_valuation = value_session(None, genesis)
    current_valuation = value_session(prior_valuation, current_day)

    def stored(day, valuation, predecessor=None):
        request = {
            "session": day.session.isoformat(),
            "previous_session": day.previous_session.isoformat()
            if day.previous_session else None,
            "contribution_minor": day.contribution_minor,
            "reserve_contribution_minor": day.reserve_contribution_minor,
            "marks": day.marks,
            "buys": [],
            "market_evidence": {"standing": "CALLER_SUPPLIED_MARKS"},
        }
        digest = hashlib.sha256(
            json.dumps(request, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        projected = asdict(valuation) | {"session": day.session.isoformat()}
        for key in ("pending_sales", "sale_settlement_dates", "receivable_minor"):
            projected.pop(key)
        receipt = {
            "schema_version": 1,
            "mode": "PAPER",
            "request_sha256": digest,
            "previous_request_sha256": predecessor,
            "account_key": "linked-readback",
            "market_evidence": request["market_evidence"],
            "valuation": projected,
        }
        return digest, request, receipt

    prior_digest, _, prior_receipt = stored(genesis, prior_valuation)
    digest, request, current = stored(current_day, current_valuation, prior_digest)
    prior_row = (prior_digest, prior_receipt, genesis.session)
    db = MagicMock()
    db.execute.return_value.fetchone.side_effect = [
        (digest, request, current), prior_row,
    ]
    assert _read_committed_paper_receipt(
        db, "linked-readback", current_day.session
    ) == current

    current["valuation"]["protected_minor"] = 200_000
    db.execute.return_value.fetchone.side_effect = [
        (digest, request, current), prior_row,
    ]
    with pytest.raises(ValueError, match="stored request disagree"):
        _read_committed_paper_receipt(db, "linked-readback", current_day.session)
