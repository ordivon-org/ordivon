"""One real PostgreSQL consumer proof: the Paper head is read-only and tamper-evident.

The database is intentionally disposable; fixture prices are never market claims.
This verifies a persistence boundary, not universal source-level refinement.
"""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from queue import Queue
from threading import Barrier, Event
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
        future = pool.submit(store.close_session, key, PaperSession(second, first, 0, 0, {}, ()))
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
    new_session = PaperSession(second, first, 0, 0, {}, ())
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
    assert read_latest_committed_paper_close(dsn, key) == committed
    assert read_committed_paper_close(dsn, key, first) == old
