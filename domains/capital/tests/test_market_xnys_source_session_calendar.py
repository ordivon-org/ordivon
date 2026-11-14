"""False-date and missing-session counterexamples through the native Markets guard."""
from __future__ import annotations

import exchange_calendars as xcals
import pandas as pd
import pytest

from ordivon_capital.markets.equity_session_calendar import (
    MarketSessionQualificationError,
    require_xnys_session_grid,
)


@pytest.fixture(scope="module")
def source_sessions() -> pd.DatetimeIndex:
    return xcals.get_calendar("XNYS").sessions_in_range("2025-05-20", "2025-06-25")


def test_valid_sessions_are_readonly_date_qualified(source_sessions):
    qualified = require_xnys_session_grid(source_sessions, symbol="QQQ")
    assert qualified["calendar"] == "exchange_calendars:XNYS"
    assert qualified["sessions"] == len(source_sessions)
    assert qualified["dateStanding"] == "EXCHANGE_SESSION_ALIGNED_SOURCE_UNVERIFIED"
    assert qualified["historicalPITVerified"] is False
    assert qualified["priceAdjustmentVerified"] is False
    assert qualified["capitalAuthority"] is False


@pytest.mark.parametrize(
    "bad_date",
    ["2025-05-26", "2025-05-25", "2025-06-19", "2025-06-21"],
)
def test_exchange_holiday_or_weekend_rejected(source_sessions, bad_date):
    injected = source_sessions.append(pd.DatetimeIndex([bad_date])).sort_values()
    with pytest.raises(MarketSessionQualificationError, match="XNYS_SESSION_GRID_MISMATCH"):
        require_xnys_session_grid(injected, symbol="SPY")


def test_missing_real_session_rejected(source_sessions):
    removed = source_sessions.delete(3)
    with pytest.raises(MarketSessionQualificationError, match="missing="):
        require_xnys_session_grid(removed, symbol="SPY")


def test_duplicate_session_rejected(source_sessions):
    with pytest.raises(MarketSessionQualificationError, match="duplicate"):
        require_xnys_session_grid(source_sessions.append(source_sessions[-1:]), symbol="SPY")


def test_unordered_session_rejected(source_sessions):
    with pytest.raises(MarketSessionQualificationError, match="unordered"):
        require_xnys_session_grid(source_sessions[::-1], symbol="SPY")


def test_intraday_label_rejected(source_sessions):
    changed = list(source_sessions)
    changed[3] = changed[3] + pd.Timedelta(hours=1)
    with pytest.raises(MarketSessionQualificationError, match="intraday"):
        require_xnys_session_grid(changed, symbol="SPY")


def test_timezone_label_rejected(source_sessions):
    with pytest.raises(MarketSessionQualificationError, match="timezone"):
        require_xnys_session_grid(source_sessions.tz_localize("UTC"), symbol="SPY")


def test_one_day_source_rejected(source_sessions):
    with pytest.raises(MarketSessionQualificationError, match="insufficient"):
        require_xnys_session_grid(source_sessions[:1], symbol="SPY")


def test_arbitrary_client_source_dates_do_not_prove_pit(source_sessions):
    report = require_xnys_session_grid(source_sessions, symbol="QQQ")
    assert report["historicalPITVerified"] is False
    assert report["capitalAuthority"] is False
