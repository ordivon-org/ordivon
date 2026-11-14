"""Qualify an already-captured US equity daily DATE GRID, not a price publisher.

Reuse the mature exchange_calendars XNYS calendar. This single boundary
prevents a vendor's pseudo-trading rows or missing sessions from silently
redefining Research labels and the Portfolio backtest clock. Calendar
alignment is NOT source authenticity, historical PIT, total return or order
permission.
"""
from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import exchange_calendars as xcals
import pandas as pd

MAX_SOURCE_ROWS = 10000


class MarketSessionQualificationError(ValueError):
    """The exchange-session index is incomplete, invented, or ambiguous."""


def require_xnys_session_grid(source_dates: Iterable[Any], *, symbol: str) -> dict[str, Any]:
    """Fail closed on missing, duplicate, extra or non-midnight XNYS sessions.

    The caller must separately verify immutable captured bytes, instrument
    identity, source rights, issuer revisions and historical availability.
    """
    if not isinstance(symbol, str) or not (1 <= len(symbol) <= 30):
        raise MarketSessionQualificationError("symbol: invalid identity")
    raw = list(source_dates)
    if len(raw) < 2 or len(raw) > MAX_SOURCE_ROWS:
        raise MarketSessionQualificationError(f"{symbol}: unbounded or insufficient session rows")
    try:
        sessions = pd.DatetimeIndex(pd.to_datetime(raw, errors="raise"))
    except (TypeError, ValueError, OverflowError) as exc:
        raise MarketSessionQualificationError(f"{symbol}: invalid session date") from exc
    if sessions.tz is not None:
        raise MarketSessionQualificationError(f"{symbol}: timezone-qualified daily labels")
    if not sessions.equals(sessions.normalize()):
        raise MarketSessionQualificationError(f"{symbol}: intraday timestamp as EOD session")
    if sessions.has_duplicates:
        raise MarketSessionQualificationError(f"{symbol}: duplicate session date")
    if not sessions.is_monotonic_increasing:
        raise MarketSessionQualificationError(f"{symbol}: unordered session dates")
    expected = xcals.get_calendar("XNYS").sessions_in_range(sessions[0], sessions[-1])
    if not sessions.equals(expected):
        invented = sessions.difference(expected)
        missing = expected.difference(sessions)
        raise MarketSessionQualificationError(
            f"{symbol}: XNYS_SESSION_GRID_MISMATCH"
            f" invented={[str(x.date()) for x in invented[:4]]}"
            f" missing={[str(x.date()) for x in missing[:4]]}"
        )
    return {
        "kind": "ordivon.capital.markets.xnys-daily-session-grid",
        "calendar": "exchange_calendars:XNYS",
        "firstSession": str(sessions[0].date()),
        "lastSession": str(sessions[-1].date()),
        "sessions": len(sessions),
        "dateStanding": "EXCHANGE_SESSION_ALIGNED_SOURCE_UNVERIFIED",
        "historicalPITVerified": False,
        "priceAdjustmentVerified": False,
        "capitalAuthority": False,
    }
