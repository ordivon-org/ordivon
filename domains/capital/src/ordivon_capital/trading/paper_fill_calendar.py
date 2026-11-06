"""Validate on-time paper open fills against separately sourced session calendars."""

import json
from collections.abc import Iterable
from datetime import UTC, date, datetime, time, timedelta
from hashlib import sha256
from zoneinfo import ZoneInfo

_NEW_YORK = ZoneInfo("America/New_York")
_ONE_DAY = timedelta(days=1)


def _strict_object(pairs):
    result = dict(pairs)
    if len(result) != len(pairs):
        raise ValueError("duplicate calendar field")
    return result


def _session_bounds(day: date, opening: str | None, closing: str | None):
    if opening is None and closing is None:
        return None
    if not isinstance(opening, str) or not isinstance(closing, str):
        raise ValueError("each market day must have both session times or neither")
    if not opening.endswith("Z") or not closing.endswith("Z"):
        raise ValueError("market session times must be UTC")
    start = datetime.combine(day, time.fromisoformat(opening))
    end = datetime.combine(day, time.fromisoformat(closing))
    if start >= end or any(t.astimezone(_NEW_YORK).date() != day for t in (start, end)):
        raise ValueError("invalid regular market session bounds")
    return start, end


def admit_paper_session_calendar(
    payload: bytes, *, expected_sha256: str, previous_session: date | None,
    trade_session: date, fills: Iterable[tuple[datetime, datetime, date | None]],
) -> dict:
    """Bind an offline close to a consecutive, externally supplied calendar window."""
    if not 0 < len(payload) <= 32_768:
        raise ValueError("paper calendar input is missing or too large")
    digest = sha256(payload).hexdigest()
    if digest != expected_sha256:
        raise ValueError("paper calendar digest mismatch")
    source = json.loads(payload.decode("utf-8"), object_pairs_hook=_strict_object)
    if not isinstance(source, dict) or source.keys() != {"market_source", "clearing_source", "days"}:
        raise ValueError("invalid paper calendar fields")
    for key in ("market_source", "clearing_source"):
        if not isinstance(source[key], str) or not source[key].strip() or len(source[key]) > 256:
            raise ValueError("paper calendar requires market and clearing source references")
    rows = source["days"]
    if not isinstance(rows, list) or not 1 <= len(rows) <= 62:
        raise ValueError("paper calendar requires a bounded day window")
    market = {}
    clearing = []
    prior = None
    for row in rows:
        if not isinstance(row, dict) or row.keys() != {"date", "open", "close", "clears"}:
            raise ValueError("invalid paper calendar day")
        if not isinstance(row["date"], str) or type(row["clears"]) is not bool:
            raise ValueError("invalid date or clearing flag")
        day = date.fromisoformat(row["date"])
        if row["date"] != day.isoformat() or (prior and day - prior != _ONE_DAY):
            raise ValueError("paper calendar requires consecutive calendar dates")
        prior = day
        bounds = _session_bounds(day, row["open"], row["close"])
        if bounds is not None:
            market[day] = bounds
        if row["clears"]:
            clearing.append(day)
    if trade_session not in market:
        raise ValueError("paper trade session must be an open market day")
    if previous_session is not None and (
        previous_session not in market
        or next((day for day in market if day > previous_session), None) != trade_session
    ):
        raise ValueError("paper trade session must be the next open market day")
    opens_at, closes_at = market[trade_session]
    maturity = next((day for day in clearing if day > trade_session), None)
    count = 0
    for decided_at, filled_at, settlement_date in fills:
        if filled_at.utcoffset() is None or filled_at.astimezone(UTC) != opens_at:
            raise ValueError("paper fill must occur at the scheduled opening")
        if (
            previous_session is None or decided_at.utcoffset() is None
            or decided_at.astimezone(_NEW_YORK).date() != previous_session
            or not market[previous_session][1] <= decided_at.astimezone(UTC) < opens_at
        ):
            raise ValueError("paper decision must follow the previous close and precede the open")
        if maturity is None or settlement_date != maturity:
            raise ValueError("paper fill settlement date must match the next clearing day")
        count += 1
    return {
        "standing": "OPERATOR_BOUND_PAPER_CALENDAR",
        "calendar_sha256": digest,
        "market_source": source["market_source"],
        "clearing_source": source["clearing_source"],
        "trade_session": trade_session.isoformat(),
        "previous_session": previous_session.isoformat() if previous_session else None,
        "closes_at": closes_at.isoformat(),
        "settlement_date": maturity.isoformat() if count else None,
        "fill_count": count,
    }
