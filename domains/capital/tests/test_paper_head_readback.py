"""One real PostgreSQL consumer proof: the Paper head is read-only and tamper-evident.

The database is intentionally disposable; fixture prices are never market claims.
This verifies a persistence boundary, not universal source-level refinement.
"""
from __future__ import annotations

import hashlib
import json
import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from datetime import date
from queue import Queue
from threading import Barrier, Event
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
from ordivon_capital.accounting.substrate import stable_accounting_id


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


def test_pg_rejects_coordinated_predecessor_and_current_receipt_corruption():
    """The newest valid-looking projection cannot inherit a forged predecessor."""
    dsn = os.environ.get("ORDIVON_CAPITAL_PAPER_PG_TEST_DSN")
    if not dsn:
        pytest.skip("disposable PostgreSQL required")
    key = "inherited-audit-" + uuid4().hex
    old_date, new_date = date(2026, 1, 8), date(2026, 1, 9)
    store = PostgresPaperClose(dsn)
    old = store.close_session(key, PaperSession(old_date, None, 1_000_000, 200_000, {}, ()))
    latest = store.close_session(key, PaperSession(new_date, old_date, 0, 0, {}, ()))
    assert latest["previous_request_sha256"] == old["request_sha256"]
    assert read_latest_committed_paper_close(dsn, key) == latest
    with psycopg.connect(dsn) as db:
        db.execute(
            "UPDATE ordivon_paper.daily_close SET receipt=jsonb_set("
            "receipt,'{valuation,protected_minor}','190000'::jsonb) "
            "WHERE account_key=%s",
            (key,),
        )
    with pytest.raises(ValueError, match="stored request disagree"):
        read_latest_committed_paper_close(dsn, key)
    with pytest.raises(ValueError, match="stored request disagree"):
        read_committed_paper_close(dsn, key, new_date)
    with pytest.raises(ValueError, match="stored request disagree"):
        store.close_session(
            key, PaperSession(date(2026, 1, 12), new_date, 0, 0, {}, ())
        )


def test_pg_readback_checks_committed_cash_ledger_and_replay():
    dsn = os.environ.get("ORDIVON_CAPITAL_PAPER_PG_TEST_DSN")
    if not dsn:
        pytest.skip("disposable PostgreSQL required")
    key = "cash-audit-" + uuid4().hex
    day = PaperSession(date(2026, 1, 8), None, 1_000_000, 200_000, {}, ())
    store = PostgresPaperClose(dsn)
    original = store.close_session(key, day)
    assert read_latest_committed_paper_close(dsn, key) == original
    cash_id = stable_accounting_id("ordivon-capital:paper-close:usd:v1", key, "cash")
    with psycopg.connect(dsn) as db:
        db.execute(
            "UPDATE ordivon_capital.accounts SET credits_posted=credits_posted+1 "
            "WHERE id=%s", (str(cash_id),)
        )
    with pytest.raises(ValueError, match="cash ledger"):
        read_latest_committed_paper_close(dsn, key)
    with pytest.raises(ValueError, match="cash ledger"):
        read_committed_paper_close(dsn, key, day.session)
    with pytest.raises(ValueError, match="cash ledger"):
        store.close_session(key, day)


def test_pg_replay_rejects_corrupt_existing_receipt():
    dsn = os.environ.get("ORDIVON_CAPITAL_PAPER_PG_TEST_DSN")
    if not dsn:
        pytest.skip("disposable PostgreSQL required")
    key = "replay-audit-" + uuid4().hex
    day = PaperSession(date(2026, 1, 8), None, 100_000, 0, {}, ())
    store = PostgresPaperClose(dsn)
    store.close_session(key, day)
    with psycopg.connect(dsn) as db:
        db.execute(
            "UPDATE ordivon_paper.daily_close SET receipt=jsonb_set("
            "receipt, '{valuation,nav_minor}', '99999'::jsonb) "
            "WHERE account_key=%s", (key,)
        )
    with pytest.raises(ValueError, match="stored request disagree"):
        store.close_session(key, day)


def test_simulation_run_claim_is_durably_bound_to_paper_request_and_receipt():
    """A forged run/Native provenance on a PG receipt must fail exact readback."""
    dsn = os.environ.get("ORDIVON_CAPITAL_PAPER_PG_TEST_DSN")
    if not dsn:
        pytest.skip("disposable PostgreSQL required for the real-run provenance check")
    key = "sim-readback-" + uuid4().hex
    day = date(2026, 1, 8)
    evidence = {
        "standing": "SIMULATION_ONLY_CALLER_DECLARED",
        "native_account": "SIM-001",
        "model_study_sha256": "a" * 64,
        "prediction_sha256": "b" * 64,
        "native_result_sha256": "c" * 64,
        "sessions_sha256": "d" * 64,
    }
    receipt = PostgresPaperClose(dsn).close_session(
        key, PaperSession(day, None, 1_000_000, 900_000, {}, ()),
        simulation_evidence=evidence,
    )
    assert receipt["simulation_evidence"] == evidence
    assert read_latest_committed_paper_close(dsn, key) == receipt
    with psycopg.connect(dsn) as db:
        db.execute(
            "UPDATE ordivon_paper.daily_close SET receipt = jsonb_set("
            "receipt, '{simulation_evidence,standing}', '\"FORGED_PIT\"'::jsonb) "
            "WHERE account_key = %s AND session = %s",
            (key, day),
        )
    with pytest.raises(ValueError, match="stored request disagree"):
        read_latest_committed_paper_close(dsn, key)


def test_paper_head_is_invisible_until_commit_and_reader_snapshot_is_stable():
    """True PG transaction: even inserted receipt/cash effects stay invisible pre-commit."""
    dsn = os.environ.get("ORDIVON_CAPITAL_PAPER_PG_TEST_DSN")
    if not dsn:
        pytest.skip("isolated, disposable ordivon_paper PostgreSQL is required")
    key = "snapshot-isolation-" + uuid4().hex
    store = PostgresPaperClose(dsn)
    first, second = date(2026, 1, 8), date(2026, 1, 9)
    old = store.close_session(key, PaperSession(first, None, 1_000_000, 200_000, {}, ()))
    entered, may_commit = Event(), Event()
    real_atomic = store._ledger._atomic

    def delay_after_all_writes(fn):
        def delayed(db):
            result = fn(db)
            # Writer has inserted the receipt and cash effects; this transaction
            # has NOT committed yet. Read-only consumers must still see old.
            entered.set()
            if not may_commit.wait(timeout=20):
                raise TimeoutError("isolated PG commit barrier was not released")
            return result

        return real_atomic(delayed)

    store._ledger._atomic = delay_after_all_writes
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(store.close_session, key, PaperSession(second, first, 10_000, 0, {}, ()))
        try:
            assert entered.wait(timeout=20)
            assert read_latest_committed_paper_close(dsn, key) == old
            with pytest.raises(ValueError, match="no committed paper receipt"):
                read_committed_paper_close(dsn, key, second)

            # Keep one PG reader on its original REPEATABLE READ snapshot
            # while the writer commits. Another fresh reader should see v2.
            with psycopg.connect(dsn) as reader:
                reader.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
                old_head = reader.execute(
                    "SELECT session FROM ordivon_paper.daily_close "
                    "WHERE account_key = %s ORDER BY session DESC LIMIT 1",
                    (key,),
                ).fetchone()
                assert old_head == (first,)
                may_commit.set()
                latest = future.result(timeout=30)
                assert (
                    reader.execute(
                        "SELECT session FROM ordivon_paper.daily_close "
                        "WHERE account_key = %s ORDER BY session DESC LIMIT 1",
                        (key,),
                    ).fetchone()
                    == old_head
                )
                assert latest["previous_request_sha256"] == old["request_sha256"]
                assert latest["valuation"]["cash_minor"] == old["valuation"]["cash_minor"] + 10_000
            assert read_latest_committed_paper_close(dsn, key) == latest
            assert read_committed_paper_close(dsn, key, first) == old
        finally:
            may_commit.set()


def test_two_concurrent_paper_writers_cannot_publish_conflicting_versions():
    """Real SERIALIZABLE conflict, exact receipt readback and replay after retry."""
    dsn = os.environ.get("ORDIVON_CAPITAL_PAPER_PG_TEST_DSN")
    if not dsn:
        pytest.skip("isolated, disposable ordivon_paper PostgreSQL is required")
    key = "two-writers-" + uuid4().hex
    first, second = date(2026, 1, 8), date(2026, 1, 9)
    initial = PostgresPaperClose(dsn)
    old = initial.close_session(key, PaperSession(first, None, 1_000_000, 200_000, {}, ()))
    writers = [PostgresPaperClose(dsn), PostgresPaperClose(dsn)]
    gate = Barrier(2)

    def writer(store, contribution):
        real_atomic = store._ledger._atomic
        first_attempt = True

        def synchronize_once(fn):
            def synchronized(db):
                nonlocal first_attempt
                if first_attempt:
                    first_attempt = False
                    gate.wait(timeout=20)
                return fn(db)

            return real_atomic(synchronized)

        store._ledger._atomic = synchronize_once
        try:
            return (
                "COMMITTED",
                store.close_session(key, PaperSession(second, first, contribution, 0, {}, ())),
            )
        except ValueError as error:
            return ("CONFLICT", str(error))

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [
            pool.submit(writer, store, contribution)
            for store, contribution in zip(writers, (0, 10_000), strict=True)
        ]
        outcomes = [future.result(timeout=40) for future in futures]
    assert sorted(state for state, _ in outcomes) == ["COMMITTED", "CONFLICT"]
    conflict = next(value for state, value in outcomes if state == "CONFLICT")
    assert "conflicting inputs for an already closed paper session" in conflict
    winner = next(value for state, value in outcomes if state == "COMMITTED")
    assert winner["previous_request_sha256"] == old["request_sha256"]
    assert read_latest_committed_paper_close(dsn, key) == winner
    assert read_committed_paper_close(dsn, key, first) == old
    with psycopg.connect(dsn) as db:
        assert db.execute(
            "SELECT count(*) FROM ordivon_paper.daily_close "
            "WHERE account_key = %s AND session = %s",
            (key, second),
        ).fetchone() == (1,)


def test_killed_pg_writer_rolls_back_invisible_receipt_and_retry_can_commit():
    """A real terminated PG backend cannot leave a half-published Paper version."""
    dsn = os.environ.get("ORDIVON_CAPITAL_PAPER_PG_TEST_DSN")
    if not dsn:
        pytest.skip("isolated, disposable ordivon_paper PostgreSQL is required")
    key = "killed-writer-" + uuid4().hex
    first, second = date(2026, 1, 8), date(2026, 1, 9)
    store = PostgresPaperClose(dsn)
    old = store.close_session(key, PaperSession(first, None, 1_000_000, 200_000, {}, ()))
    new_session = PaperSession(second, first, 10_000, 0, {}, ())
    victim_pids: Queue[int] = Queue(maxsize=1)
    may_finish = Event()
    real_atomic = store._ledger._atomic

    def delay_while_uncommitted(fn):
        def held(db):
            result = fn(db)
            # All requested Paper rows and ledger effects were written, but
            # none has committed; bind the termination to THIS writer's PID.
            victim_pids.put(db.execute("SELECT pg_backend_pid()").fetchone()[0])
            if not may_finish.wait(timeout=20):
                raise TimeoutError("isolated PG failure witness timed out")
            return result

        return real_atomic(held)

    store._ledger._atomic = delay_while_uncommitted
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(store.close_session, key, new_session)
        try:
            pid = victim_pids.get(timeout=20)
            assert read_latest_committed_paper_close(dsn, key) == old
            with psycopg.connect(dsn) as supervisor:
                assert supervisor.execute("SELECT pg_terminate_backend(%s)", (pid,)).fetchone() == (
                    True,
                )
        finally:
            may_finish.set()
        with pytest.raises(psycopg.OperationalError):
            future.result(timeout=30)

    assert read_latest_committed_paper_close(dsn, key) == old
    with pytest.raises(ValueError, match="no committed paper receipt"):
        read_committed_paper_close(dsn, key, second)
    # The failed writer was not a committed business operation. A fresh exact
    # request must be able to produce its own durable, linked receipt.
    committed = PostgresPaperClose(dsn).close_session(key, new_session)
    assert committed["previous_request_sha256"] == old["request_sha256"]
    assert committed["valuation"]["cash_minor"] == old["valuation"]["cash_minor"] + 10_000
    assert read_latest_committed_paper_close(dsn, key) == committed
    assert read_committed_paper_close(dsn, key, first) == old
