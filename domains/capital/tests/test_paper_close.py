"""Observable paper cash, fill and valuation invariants across a restart."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import date, datetime
from os import environ
from uuid import uuid4

import pytest

from ordivon_capital.accounting import paper_close


def inputs():
    first = date(2026, 1, 8)
    second = date(2026, 1, 9)
    third = date(2026, 1, 12)
    fill = paper_close.PaperBuy(
        "order-1", "ETF", 10, 10_000, 100,
        datetime.fromisoformat("2026-01-08T16:15:00-05:00"),
        datetime.fromisoformat("2026-01-09T09:30:00-05:00"),
    )
    return (
        paper_close.PaperSession(first, None, 1_000_000, 300_000, {}, ()),
        paper_close.PaperSession(second, first, 0, 0, {"ETF": 10_200}, (fill,)),
        paper_close.PaperSession(third, second, 0, 0, {"ETF": 10_200}, ()),
    )


def test_paper_cash_settlement_does_not_create_or_destroy_nav():
    day0, day1, day2 = inputs()
    opening = paper_close.value_session(None, day0)
    trade = paper_close.value_session(opening, day1)
    settled = paper_close.value_session(trade, day2)
    assert opening.nav_minor == 1_000_000
    assert trade.cash_minor == 1_000_000
    assert trade.payable_minor == 100_100
    assert trade.nav_minor == settled.nav_minor == 1_001_900
    assert settled.cash_minor == 899_900
    assert settled.payable_minor == 0
    assert settled.protected_minor == 300_000


def test_paper_invalid_evidence_has_no_valuation():
    day0, day1, _ = inputs()
    opening = paper_close.value_session(None, day0)
    fill = day1.buys[0]
    for session, message in (
        (replace(day1, marks={}), "missing closing mark"),
        (replace(day1, buys=(replace(fill, price_minor=70_000),)), "protected cash"),
        (replace(day1, buys=(replace(fill, decided_at=fill.filled_at),)), "time boundary"),
    ):
        with pytest.raises(ValueError, match=message):
            paper_close.value_session(opening, session)


def test_postgres_paper_close_is_atomic_replayable_and_conflict_checked():
    dsn = environ.get("ORDIVON_CAPITAL_PAPER_PG_TEST_DSN")
    if not dsn:
        pytest.skip("disposable paper PostgreSQL DSN required")
    from ordivon_capital.accounting.postgres_paper_close import PostgresPaperClose

    day0, day1, day2 = inputs()
    account = "paper-test-" + uuid4().hex
    store = PostgresPaperClose(dsn)
    store.close_session(account, day0)

    with pytest.raises(ValueError, match="missing closing mark"):
        store.close_session(account, replace(day1, marks={}))

    with ThreadPoolExecutor(max_workers=4) as pool:
        receipts = list(pool.map(
            lambda _: PostgresPaperClose(dsn).close_session(account, day1),
            range(4),
        ))
    assert receipts[1:] == receipts[:1] * 3
    assert receipts[0]["valuation"]["nav_minor"] == 1_001_900
    with pytest.raises(ValueError, match="conflicting"):
        store.close_session(account, replace(day1, marks={"ETF": 11_000}))
    with pytest.raises(ValueError, match="previous"):
        store.close_session(account, replace(day2, previous_session=day0.session))

    # A repeated fill ID on a later day fails after the earlier payable was
    # provisionally settled. The subsequent valid close must still settle it.
    old = day1.buys[0]
    repeated = replace(old, decided_at=old.filled_at, filled_at=old.filled_at.replace(day=12))
    with pytest.raises(ValueError, match="paper cash posting rejected"):
        store.close_session(account, replace(day2, buys=(repeated,)))

    settled = PostgresPaperClose(dsn).close_session(account, day2)
    assert settled["previous_request_sha256"] == receipts[0]["request_sha256"]
    assert settled["valuation"]["cash_minor"] == 899_900
    assert settled["valuation"]["nav_minor"] == receipts[0]["valuation"]["nav_minor"]
    assert store.close_session(account, day1) == receipts[0]
