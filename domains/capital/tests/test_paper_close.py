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


def test_paper_cash_formal_equations_refine_mixed_buy_sell_settlement() -> None:
    """Actual value_session consumer witnesses the one-step SMT field map.

    The SMT model proves aggregate integer algebra; this test witnesses one
    concrete code path with old/new payables and receivables simultaneously.
    It is not a universal Python-to-SMT refinement theorem.
    """
    start = date(2026, 1, 6)
    buy_day = date(2026, 1, 7)
    sale_day = date(2026, 1, 8)
    both_due = date(2026, 1, 9)

    def buy(fill_id: str, prev_date: date, day: date, amount: int, due: date):
        return paper_close.PaperBuy(
            fill_id, "ETF", amount, 10_000, 100,
            datetime.fromisoformat(f"{prev_date}T16:15:00-05:00"),
            datetime.fromisoformat(f"{day}T09:30:00-05:00"),
            settlement_date=due,
        )

    def sell(fill_id: str, prev_date: date, day: date, due: date):
        return paper_close.PaperSell(
            fill_id, "ETF", 1, 12_000, 100,
            datetime.fromisoformat(f"{prev_date}T16:15:00-05:00"),
            datetime.fromisoformat(f"{day}T09:30:00-05:00"),
            settlement_date=due,
        )

    opening = paper_close.value_session(
        None, paper_close.PaperSession(start, None, 150_000, 20_000, {}, ())
    )
    first = paper_close.value_session(
        opening, paper_close.PaperSession(
            buy_day, start, 0, 0, {"ETF": 10_000},
            (buy("buy-old", start, buy_day, 5, both_due),),
        )
    )
    before = paper_close.value_session(
        first, paper_close.PaperSession(
            sale_day, buy_day, 0, 0, {"ETF": 12_000}, (),
            sells=(sell("sale-old", buy_day, sale_day, both_due),),
        )
    )
    day = paper_close.PaperSession(
        both_due, sale_day, 0, 0, {"ETF": 12_000},
        (buy("buy-new", sale_day, both_due, 1, date(2026, 1, 13)),),
        sells=(sell("sale-new", sale_day, both_due, date(2026, 1, 13)),),
    )
    after = paper_close.value_session(before, day)
    due_buy = sum(before.payable_due_on(day.session).values())
    due_sale = sum(before.receivable_due_on(day.session).values())
    new_buy = sum(fill.cost_minor for fill in day.buys)
    new_sale = sum(fill.proceeds_minor for fill in day.sells)
    before_mark = before.nav_minor - before.cash_minor + before.payable_minor - before.receivable_minor
    after_mark = sum(shares * day.marks[symbol] for symbol, shares in after.positions.items())

    assert due_buy == 50_100 and due_sale == 11_900
    assert after.cash_minor == before.cash_minor - due_buy + due_sale
    assert after.payable_minor == before.payable_minor - due_buy + new_buy
    assert after.receivable_minor == before.receivable_minor - due_sale + new_sale
    assert after.protected_minor == before.protected_minor
    assert (
        after.nav_minor - before.nav_minor
        == -new_buy + new_sale + after_mark - before_mark
    )
    assert after.cash_minor - after.payable_minor - due_sale >= after.protected_minor
    # The incorrect guard would admit this buy using 11,900 cents settling
    # today, even though they were not buying power at the intraday fill.
    too_early = buy("buy-too-early", sale_day, both_due, 9, date(2026, 1, 13))
    hypothetical_cash = before.cash_minor - due_buy + due_sale
    hypothetical_payable = before.payable_minor - due_buy + too_early.cost_minor
    assert hypothetical_cash - hypothetical_payable >= before.protected_minor
    assert hypothetical_cash - hypothetical_payable - due_sale < before.protected_minor
    with pytest.raises(ValueError, match="protected cash"):
        paper_close.value_session(
            before, replace(day, buys=(too_early,), sells=())
        )


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


def test_postgres_paper_rejects_a_non_durable_receipt_table():
    dsn = environ.get("ORDIVON_CAPITAL_PAPER_PG_TEST_DSN")
    if not dsn:
        pytest.skip("disposable paper PostgreSQL DSN required")
    from psycopg import connect

    from ordivon_capital.accounting.postgres_paper_close import PostgresPaperClose

    store = PostgresPaperClose(dsn)
    with connect(dsn, autocommit=True) as db:
        db.execute("ALTER TABLE ordivon_paper.daily_close SET UNLOGGED")
        try:
            with pytest.raises(RuntimeError, match="paper receipt table"):
                PostgresPaperClose(dsn)
            with pytest.raises(RuntimeError, match="paper receipt table"):
                store.close_session("non-durable-" + uuid4().hex, inputs()[0])
        finally:
            db.execute("ALTER TABLE ordivon_paper.daily_close SET LOGGED")


def test_postgres_paper_receipt_binds_admitted_market_bytes():
    dsn = environ.get("ORDIVON_CAPITAL_PAPER_PG_TEST_DSN")
    if not dsn:
        pytest.skip("disposable paper PostgreSQL DSN required")
    from hashlib import sha256
    from json import dumps

    from ordivon_capital.accounting.postgres_paper_close import PostgresPaperClose
    from ordivon_capital.markets.etf_eod_snapshot import admit_etf_eod_snapshot

    close_at = "2026-01-09T21:00:00Z"
    observed_at = "2026-01-09T21:10:00Z"
    raw = dumps({
        "schemaVersion": 1,
        "kind": "ordivon.finance.markets.etf-eod-snapshot",
        "sourceId": "synthetic-fixture",
        "currency": "USD",
        "priceBasis": "RAW_UNADJUSTED_CLOSE",
        "rights": {"status": "AUTHORIZED_PRIVATE_PAPER_USE", "evidenceRef": "fixture"},
        "corporateActions": {"coverage": "COMPLETE", "evidenceRef": "fixture", "events": []},
        "capturedAt": observed_at,
        "supersedesSha256": None,
        "marks": [{
            "sessionDate": "2026-01-09", "instrumentId": "ETF", "priceMinor": 10_200,
            "availableAt": observed_at, "availabilityBasis": "FIRST_OBSERVED",
        }],
    }).encode()
    digest = "sha256:" + sha256(raw).hexdigest()
    def admit(bound_close):
        return admit_etf_eod_snapshot(
            raw, expected_sha256=digest, expected_source_id="synthetic-fixture",
            expected_rights_ref="fixture", expected_corporate_actions_ref="fixture",
            expected_instruments=["ETF"], expected_session_closes={"2026-01-09": bound_close},
            decision_at=observed_at,
        )

    snapshot = admit(close_at)
    day0, day1, _ = inputs()
    account = "paper-test-" + uuid4().hex
    store = PostgresPaperClose(dsn)
    store.close_session(account, day0)
    receipt = store.close_session(account, replace(day1, marks={}), mark_snapshot=snapshot)
    assert receipt["market_evidence"]["sha256"] == digest
    assert receipt["valuation"]["nav_minor"] == 1_001_900
    with pytest.raises(ValueError, match="inline marks"):
        store.close_session(account, day1, mark_snapshot=snapshot)
    changed_binding = admit("2026-01-09T18:00:00Z")
    with pytest.raises(ValueError, match="conflicting"):
        store.close_session(account, replace(day1, marks={}), mark_snapshot=changed_binding)


def test_postgres_carries_buy_payable_over_a_market_only_session():
    dsn = environ.get("ORDIVON_CAPITAL_PAPER_PG_TEST_DSN")
    if not dsn:
        pytest.skip("disposable paper PostgreSQL DSN required")
    from ordivon_capital.accounting.postgres_paper_close import PostgresPaperClose

    # Markets can open on a day when the securities settlement service is closed.
    before = date(2026, 11, 9)
    trade = date(2026, 11, 10)
    market_only = date(2026, 11, 11)
    settlement = date(2026, 11, 12)
    fill = paper_close.PaperBuy(
        "after-holiday", "ETF", 10, 10_000, 100,
        datetime.fromisoformat("2026-11-09T16:15:00-05:00"),
        datetime.fromisoformat("2026-11-10T09:30:00-05:00"),
        settlement_date=settlement,
    )
    account = "paper-test-" + uuid4().hex
    store = PostgresPaperClose(dsn)
    store.close_session(account, paper_close.PaperSession(before, None, 1_000_000, 0, {}, ()))
    marks = {"ETF": 10_200}
    store.close_session(account, paper_close.PaperSession(trade, before, 0, 0, marks, (fill,)))
    open_payable = store.close_session(
        account, paper_close.PaperSession(market_only, trade, 0, 0, marks, ()),
    )["valuation"]
    assert open_payable["cash_minor"] == 1_000_000
    assert open_payable["payable_minor"] == 100_100
    after = PostgresPaperClose(dsn).close_session(
        account, paper_close.PaperSession(settlement, market_only, 0, 0, marks, ()),
    )["valuation"]
    assert after["cash_minor"] == 899_900
    assert after["payable_minor"] == 0
    assert open_payable["nav_minor"] == after["nav_minor"] == 1_001_900


def test_postgres_paper_sell_reduces_positions_and_carries_receivable():
    dsn = environ.get("ORDIVON_CAPITAL_PAPER_PG_TEST_DSN")
    if not dsn:
        pytest.skip("disposable paper PostgreSQL DSN required")
    from ordivon_capital.accounting.postgres_paper_close import PostgresPaperClose

    day0, day1, day2 = inputs()
    trade = date(2026, 1, 13)
    pending_day = date(2026, 1, 14)
    clearing_day = date(2026, 1, 15)
    sale = paper_close.PaperSell(
        "sale-1", "ETF", 10, 10_300, 100,
        datetime.fromisoformat("2026-01-12T16:15:00-05:00"),
        datetime.fromisoformat("2026-01-13T09:30:00-05:00"),
        settlement_date=clearing_day,
    )
    account = "paper-test-" + uuid4().hex
    store = PostgresPaperClose(dsn)
    for day in (day0, day1, day2):
        store.close_session(account, day)
    sell_day = paper_close.PaperSession(trade, day2.session, 0, 0, {}, (), sells=(sale,))
    with pytest.raises(ValueError, match="held shares"):
        store.close_session(account, replace(sell_day, sells=(replace(sale, shares=11),)))
    with pytest.raises(ValueError, match="already used for the opposite side"):
        store.close_session(
            account, replace(sell_day, sells=(replace(sale, fill_id=day1.buys[0].fill_id),)),
        )

    from ordivon_capital.markets.etf_eod_snapshot import AdmittedEtfEodSnapshot, EtfCloseMark

    close_at = datetime.fromisoformat("2026-01-13T21:00:00+00:00")
    captured = datetime.fromisoformat("2026-01-13T21:10:00+00:00")
    other_symbol = AdmittedEtfEodSnapshot(
        "sha256:" + "1" * 64, "fixture", "fixture", "fixture", captured, captured, None,
        (EtfCloseMark(trade.isoformat(), "OTHER", 10_000, close_at, captured, "FIRST_OBSERVED"),),
    )
    with pytest.raises(ValueError, match="does not cover every held or traded"):
        store.close_session(account, sell_day, mark_snapshot=other_symbol)
    receipt = store.close_session(account, sell_day)
    assert receipt["valuation"]["positions"] == {}
    assert receipt["valuation"]["cash_minor"] == 899_900
    assert receipt["valuation"]["receivable_minor"] == 102_900
    assert receipt["valuation"]["nav_minor"] == 1_002_800
    pending = paper_close.PaperSession(pending_day, trade, 0, 0, {}, ())
    assert store.close_session(account, pending)["valuation"]["receivable_minor"] == 102_900

    clearing = paper_close.PaperSession(clearing_day, pending_day, 0, 0, {}, ())
    buy = replace(
        day1.buys[0], fill_id="large-buy", shares=65,
        decided_at=datetime.fromisoformat("2026-01-14T16:15:00-05:00"),
        filled_at=datetime.fromisoformat("2026-01-15T09:30:00-05:00"),
    )
    with pytest.raises(ValueError, match="protected cash"):
        store.close_session(account, replace(clearing, marks={"ETF": 10_000}, buys=(buy,)))

    final = PostgresPaperClose(dsn).close_session(account, clearing)["valuation"]
    assert final["receivable_minor"] == 0
    assert final["cash_minor"] == final["nav_minor"] == 1_002_800
    assert store.close_session(account, sell_day) == receipt

    following = paper_close.PaperSession(
        date(2026, 1, 16), clearing_day, 0, 0, {"ETF": 10_000},
        (replace(
            buy,
            decided_at=datetime.fromisoformat("2026-01-15T16:15:00-05:00"),
            filled_at=datetime.fromisoformat("2026-01-16T09:30:00-05:00"),
        ),),
    )
    assert store.close_session(account, following)["valuation"]["positions"] == {"ETF": 65}


def test_paper_pure_valuation_and_postgres_share_fill_side_identity_contract():
    """Same fill cannot represent both buy and sell, even before PG admission."""
    day0, day1, day2 = inputs()
    opening = paper_close.value_session(None, day0)
    purchased = paper_close.value_session(opening, day1)
    t0 = datetime.fromisoformat("2026-01-09T16:15:00-05:00")
    t1 = datetime.fromisoformat("2026-01-12T09:30:00-05:00")
    buy = paper_close.PaperBuy("shared-fill", "ETF", 1, 10_000, 0, t0, t1)
    sell = paper_close.PaperSell(
        "shared-fill", "ETF", 1, 10_000, 0, t0, t1,
        settlement_date=date(2026, 1, 14),
    )
    # Both fills are independently plausible, and aggregate cash/shares
    # would balance. The identity is invalid *before* ledger posting.
    contradictory = replace(
        day2, buys=(buy,), sells=(sell,),
    )
    with pytest.raises(ValueError, match="opposite side"):
        paper_close.value_session(purchased, contradictory)


def test_paper_open_payable_cannot_be_reidentified_as_sale_receivable():
    """Cross-side identity is disjoint across sessions until settlement."""
    day0, day1, day2 = inputs()
    opening = paper_close.value_session(None, day0)
    deferred = replace(
        day1.buys[0], settlement_date=date(2026, 1, 15),
    )
    purchased = paper_close.value_session(opening, replace(day1, buys=(deferred,)))
    assert "order-1" in purchased.pending
    sale = paper_close.PaperSell(
        "order-1", "ETF", 10, 10_300, 100,
        datetime.fromisoformat("2026-01-09T16:15:00-05:00"),
        datetime.fromisoformat("2026-01-12T09:30:00-05:00"),
        settlement_date=date(2026, 1, 14),
    )
    with pytest.raises(ValueError, match="opposite side"):
        paper_close.value_session(
            purchased, replace(day2, sells=(sale,), marks={}),
        )
