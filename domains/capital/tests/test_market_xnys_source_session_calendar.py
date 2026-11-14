"""Markets date-grid qualification: native adversarial source/clock counterexamples."""

from __future__ import annotations

import exchange_calendars as xcals
import pandas as pd
import pytest

from ordivon_capital.markets.equity_session_calendar import (
    MarketSessionQualificationError,
    require_xnys_session_grid,
)

REQUEST_START = "2025-05-20"
REQUEST_END = "2025-06-25"


@pytest.fixture(scope="module")
def source_sessions() -> pd.DatetimeIndex:
    return xcals.get_calendar("XNYS").sessions_in_range(REQUEST_START, REQUEST_END)


def admit(source_sessions, *, start=REQUEST_START, end=REQUEST_END):
    return require_xnys_session_grid(
        source_sessions, symbol="SPY", requested_start=start, requested_end=end
    )


def test_complete_requested_sessions_only_qualify_date_grid(source_sessions):
    report = admit(source_sessions)
    assert report["calendar"] == "exchange_calendars:XNYS"
    assert report["sessions"] == len(source_sessions)
    assert report["requestedStart"] == REQUEST_START
    assert report["requestedEnd"] == REQUEST_END
    assert report["dateStanding"] == "EXCHANGE_SESSION_ALIGNED_SOURCE_UNVERIFIED"
    assert report["historicalPITVerified"] is False
    assert report["priceAdjustmentVerified"] is False
    assert report["capitalAuthority"] is False


@pytest.mark.parametrize("fake", ["2025-05-26", "2025-05-25", "2025-06-19", "2025-06-21"])
def test_exchange_holiday_or_weekend_rejected(source_sessions, fake):
    injected = source_sessions.append(pd.DatetimeIndex([fake])).sort_values()
    with pytest.raises(MarketSessionQualificationError, match="XNYS_SESSION_GRID_MISMATCH"):
        admit(injected)


def test_missing_middle_true_session_rejected(source_sessions):
    with pytest.raises(MarketSessionQualificationError, match="missing="):
        admit(source_sessions.delete(3))


def test_stale_first_session_rejected(source_sessions):
    with pytest.raises(MarketSessionQualificationError, match="missing="):
        admit(source_sessions[1:])


def test_stale_last_session_rejected(source_sessions):
    with pytest.raises(MarketSessionQualificationError, match="missing="):
        admit(source_sessions[:-1])


def test_request_bounds_not_inferred_from_source(source_sessions):
    with pytest.raises(MarketSessionQualificationError, match="missing="):
        admit(source_sessions, start="2025-05-19", end="2025-06-26")


def test_duplicate_session_rejected(source_sessions):
    with pytest.raises(MarketSessionQualificationError, match="duplicate"):
        admit(source_sessions.append(source_sessions[-1:]))


def test_unordered_session_rejected(source_sessions):
    with pytest.raises(MarketSessionQualificationError, match="unordered"):
        admit(source_sessions[::-1])


def test_intraday_label_rejected(source_sessions):
    changed = list(source_sessions)
    changed[3] = changed[3] + pd.Timedelta(hours=1)
    with pytest.raises(MarketSessionQualificationError, match="intraday"):
        admit(changed)


def test_timezone_label_rejected(source_sessions):
    with pytest.raises(MarketSessionQualificationError, match="timezone"):
        admit(source_sessions.tz_localize("UTC"))


def test_one_day_source_rejected(source_sessions):
    with pytest.raises(MarketSessionQualificationError, match="insufficient"):
        admit(source_sessions[:1])


@pytest.mark.parametrize(
    "start,end", [("", ""), ("2025-06-25", "2025-05-20"), ("2025/05/20", REQUEST_END)]
)
def test_missing_invalid_or_reversed_requested_window_rejected(source_sessions, start, end):
    with pytest.raises(MarketSessionQualificationError, match="request bounds"):
        admit(source_sessions, start=start, end=end)
