"""Qualify an already-captured US equity daily DATE GRID, not a price publisher.

Reuse the mature exchange_calendars XNYS calendar. This single boundary
prevents a vendor's pseudo-trading rows or missing sessions from silently
redefining Research labels and the Portfolio backtest clock. Calendar
alignment is NOT source authenticity, historical PIT, total return or order
permission.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from typing import Any

MAX_SOURCE_ROWS = 10000


class MarketSessionQualificationError(ValueError):
    """The exchange-session index is incomplete, invented, or ambiguous."""


def require_xnys_session_grid(
    source_dates: Iterable[Any], *, symbol: str, requested_start: str, requested_end: str
) -> dict[str, Any]:
    """Fail closed on missing, duplicate, extra or non-midnight XNYS sessions.

    The caller must separately verify immutable captured bytes, instrument
    identity, source rights, issuer revisions and historical availability.
    """
    if not isinstance(symbol, str) or not (1 <= len(symbol) <= 30):
        raise MarketSessionQualificationError("symbol: invalid identity")
    raw = list(source_dates)
    if len(raw) < 2 or len(raw) > MAX_SOURCE_ROWS:
        raise MarketSessionQualificationError(f"{symbol}: unbounded or insufficient session rows")
    # Delay scientific calendar imports until the source consumer needs them.
    import exchange_calendars as xcals
    import pandas as pd

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
    # The declared request window, NOT the source's self-reported endpoints,
    # owns expected completeness. Inference from observed first/last would
    # accept a stale source missing the latest exchange session.
    if (
        type(requested_start) is not str
        or type(requested_end) is not str
        or len(requested_start) != 10
        or len(requested_end) != 10
    ):
        raise MarketSessionQualificationError(f"{symbol}: missing explicit source request bounds")
    try:
        left = pd.Timestamp(requested_start)
        right = pd.Timestamp(requested_end)
        if (
            left.strftime("%Y-%m-%d") != requested_start
            or right.strftime("%Y-%m-%d") != requested_end
            or left > right
        ):
            raise ValueError("noncanonical or reversed request dates")
        expected = xcals.get_calendar("XNYS").sessions_in_range(left, right)
    except (TypeError, ValueError, OverflowError) as exc:
        raise MarketSessionQualificationError(f"{symbol}: invalid source request bounds") from exc
    if len(expected) < 2 or len(expected) > MAX_SOURCE_ROWS:
        raise MarketSessionQualificationError(f"{symbol}: no bounded exchange sessions requested")
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
        "requestedStart": requested_start,
        "requestedEnd": requested_end,
        "dateStanding": "EXCHANGE_SESSION_ALIGNED_SOURCE_UNVERIFIED",
        "historicalPITVerified": False,
        "priceAdjustmentVerified": False,
        "capitalAuthority": False,
    }


def require_xnys_eod_session_closes(
    expected_closes: Mapping[str, datetime],
) -> None:
    """Require actual scheduled XNYS session dates AND precise regular closes.

    Caller-supplied exchange-close declarations can be hash-consistent but
    physically false, e.g. Memorial Day or the Friday after Thanksgiving.
    This only authenticates the public exchange calendar rule; it does NOT
    certify an ETF price, provider publication/capture instant, adjustment,
    rights, or corporate-action coverage.
    """
    if not expected_closes or len(expected_closes) > 366:
        raise MarketSessionQualificationError("XNYS expected EOD sessions must be bounded")
    # Keep non-market Accounting and other Capital imports lightweight.
    import exchange_calendars as xcals
    import pandas as pd

    cal = xcals.get_calendar("XNYS")
    for day, supplied in expected_closes.items():
        try:
            stamp = pd.Timestamp(day)
            if (
                type(day) is not str
                or stamp.strftime("%Y-%m-%d") != day
                or stamp.tzinfo is not None
                or type(supplied) is not datetime
                or supplied.tzinfo is None
                or supplied.utcoffset() is None
            ):
                raise ValueError("not a canonical UTC-bound session close")
            if not cal.is_session(stamp):
                raise MarketSessionQualificationError(
                    f"XNYS closed on supplied session {day}"
                )
            official = cal.session_close(stamp)
        except MarketSessionQualificationError:
            raise
        except (ValueError, TypeError, OverflowError) as exc:
            raise MarketSessionQualificationError(
                f"XNYS invalid supplied session {day}"
            ) from exc
        if supplied.astimezone(UTC) != official.to_pydatetime():
            raise MarketSessionQualificationError(
                f"XNYS official close disagrees with supplied session {day}"
            )
