from dataclasses import replace
from datetime import UTC, date, datetime
from hashlib import sha256
from json import dumps, loads

import pytest

from ordivon_capital.trading import paper_fill_calendar


def calendar_payload(omit=False):
    calendar = {
        "market_source": "fixture:exchange",
        "clearing_source": "fixture:dtc",
        "days": [
            {"date": "2026-11-09", "open": "14:30:00Z", "close": "21:00:00Z", "clears": True},
            {"date": "2026-11-10", "open": "14:30:00Z", "close": "21:00:00Z", "clears": True},
            {"date": "2026-11-11", "open": "14:30:00Z", "close": "21:00:00Z", "clears": False},
            {"date": "2026-11-12", "open": "14:30:00Z", "close": "21:00:00Z", "clears": True},
        ],
    }
    if omit:
        del calendar["days"][2]
    return dumps(calendar).encode()


def run(*, maturity="2026-11-12", filled="2026-11-10T14:30:00Z", omit=False):
    payload = calendar_payload(omit)
    return paper_fill_calendar.admit_paper_session_calendar(
        payload, expected_sha256=sha256(payload).hexdigest(),
        previous_session=date(2026, 11, 9), trade_session=date(2026, 11, 10),
        fills=((datetime(2026, 11, 9, 22, tzinfo=UTC),
        datetime.fromisoformat(filled), date.fromisoformat(maturity)),),
    )


def test_open_but_nonsettling_day_does_not_advance_cash():
    receipt = run()
    assert receipt["trade_session"] == "2026-11-10"
    assert receipt["settlement_date"] == "2026-11-12"
    assert receipt["clearing_source"] == "fixture:dtc"


@pytest.mark.parametrize(("options", "reason"), [
    ({"maturity": "2026-11-11"}, "next clearing day"),
    ({"filled": "2026-11-11T14:30:00Z"}, "scheduled opening"),
    ({"omit": True}, "consecutive calendar dates"),
])
def test_does_not_fallback_to_open_days_or_skip_missing_evidence(options, reason):
    with pytest.raises(ValueError, match=reason):
        run(**options)


def test_calendar_evidence_is_committed_in_paper_receipt():
    from os import environ
    from uuid import uuid4

    from ordivon_capital.accounting.paper_close import PaperBuy, PaperSession
    from ordivon_capital.accounting.postgres_paper_close import (
        PostgresPaperClose,
        read_committed_paper_close,
    )

    if not (dsn := environ.get("ORDIVON_CAPITAL_PAPER_PG_TEST_DSN")):
        pytest.skip("disposable paper PostgreSQL DSN required")
    session = date(2026, 11, 10)
    previous = date(2026, 11, 9)
    buy = PaperBuy(
        "buy1", "ETF", 1, 100, 0, datetime(2026, 11, 9, 22, tzinfo=UTC),
        datetime(2026, 11, 10, 14, 30, tzinfo=UTC), date(2026, 11, 12),
    )
    account = "calendar-" + uuid4().hex
    store = PostgresPaperClose(dsn)
    store.close_session(account, PaperSession(previous, None, 10_000, 0, {}, ()))
    payload = calendar_payload()
    arguments = {"calendar_bytes": payload, "calendar_sha256": sha256(payload).hexdigest()}
    day = PaperSession(session, previous, 0, 0, {"ETF": 100}, (buy,))
    from ordivon_capital.markets.etf_eod_snapshot import AdmittedEtfEodSnapshot, EtfCloseMark

    captured = datetime(2026, 11, 10, 22, tzinfo=UTC)
    wrong_prior = AdmittedEtfEodSnapshot(
        "sha256:" + "1" * 64, "fixture", "fixture", "fixture", captured, captured, None,
        (
            EtfCloseMark(previous.isoformat(), "ETF", 100,
                         datetime(2026, 11, 9, 20, tzinfo=UTC), captured, "FIRST_OBSERVED"),
            EtfCloseMark(session.isoformat(), "ETF", 100,
                         datetime(2026, 11, 10, 21, tzinfo=UTC), captured, "FIRST_OBSERVED"),
        ),
    )
    with pytest.raises(ValueError, match="disagree on session closes"):
        store.close_session(account, replace(day, marks={}), mark_snapshot=wrong_prior, **arguments)
    closed = store.close_session(account, day, **arguments)
    assert closed["execution_evidence"]["calendar_sha256"] == arguments["calendar_sha256"]
    assert closed["execution_evidence"]["settlement_date"] == "2026-11-12"
    assert read_committed_paper_close(dsn, account_key=account, session=session) == closed
    assert store.close_session(account, day, **arguments) == closed
    with pytest.raises(ValueError, match="conflicting inputs"):
        store.close_session(account, day)

    revised = loads(payload)
    revised["days"][-1]["clears"] = False
    revision = dumps(revised).encode()
    next_day = PaperSession(date(2026, 11, 11), session, 0, 0, {"ETF": 100}, ())
    with pytest.raises(ValueError, match="disagree on clearing days"):
        store.close_session(
            account, next_day, calendar_bytes=revision, calendar_sha256=sha256(revision).hexdigest(),
        )
