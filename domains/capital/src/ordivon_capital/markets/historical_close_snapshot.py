"""Bounded daily adjusted-close data admission for offline research consumers.

GitHub blob identity and the supplied byte digest are mechanical facts.
The original vendor's publication time, licence, adjustment and data accuracy
remain separate external claims.
"""

from __future__ import annotations

import csv
import hashlib
import io
import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation

_SHA256 = re.compile(r"[0-9a-f]{64}\Z")


class HistoricalCloseError(ValueError):
    """A market data snapshot is not mechanically usable for an exact replay."""


@dataclass(frozen=True)
class DailyCloses:
    session: date
    prices: dict[str, Decimal]


@dataclass(frozen=True)
class AdmittedCloseSeries:
    observations: tuple[DailyCloses, ...]
    no_quote_dates: tuple[str, ...]
    last_source_row: str
    source_sha256: str


def _date(value: str) -> date:
    try:
        result = date.fromisoformat(value)
    except ValueError as exc:
        raise HistoricalCloseError("invalid source ISO session date") from exc
    if result.isoformat() != value:
        raise HistoricalCloseError("noncanonical source ISO date")
    return result


def admit_adjusted_close_csv(
    *,
    raw: bytes,
    expected_sha256: str,
    instruments: frozenset[str],
    start_date: date,
    end_date: date,
) -> AdmittedCloseSeries:
    if (
        type(expected_sha256) is not str
        or not _SHA256.fullmatch(expected_sha256)
        or hashlib.sha256(raw).hexdigest() != expected_sha256
    ):
        raise HistoricalCloseError("source SHA-256 digest mismatch")
    if not 0 < len(raw) <= 16_000_000:
        raise HistoricalCloseError("source size outside supported bounded CSV")
    if not instruments or len(instruments) > 32:
        raise HistoricalCloseError("instrument set must be nonempty and bounded")
    if start_date >= end_date:
        raise HistoricalCloseError("replay requires at least two dated sessions")

    try:
        reader = csv.DictReader(io.StringIO(raw.decode("utf-8"), newline=""))
        columns = reader.fieldnames
        if (
            not columns
            or len(columns) != len(set(columns))
            or not instruments.issubset(columns)
            or "Date" not in columns
        ):
            raise HistoricalCloseError("missing or duplicate required CSV columns")
        observations: list[DailyCloses] = []
        no_quote: list[str] = []
        last_date: date | None = None
        count = 0
        for row in reader:
            count += 1
            if count > 80000 or None in row:
                raise HistoricalCloseError("malformed or unbounded daily CSV")
            session = _date(row["Date"])
            if last_date is not None and session <= last_date:
                raise HistoricalCloseError("source dates must be strictly increasing")
            last_date = session
            if session < start_date or session > end_date:
                continue
            values = [row[symbol] for symbol in sorted(instruments)]
            if all(not value for value in values):
                no_quote.append(session.isoformat())
                continue
            if any(not value for value in values):
                raise HistoricalCloseError(
                    "partially unpriced session; cannot invent missing instrument"
                )
            prices = {}
            for symbol in sorted(instruments):
                try:
                    price = Decimal(row[symbol])
                except InvalidOperation as exc:
                    raise HistoricalCloseError("source price is not a decimal") from exc
                if not price.is_finite() or price <= 0:
                    raise HistoricalCloseError("nonpositive or nonfinite source price")
                prices[symbol] = price
            observations.append(DailyCloses(session=session, prices=prices))
    except UnicodeError as exc:
        raise HistoricalCloseError("invalid source UTF-8 encoding") from exc
    except (csv.Error, TypeError) as exc:
        raise HistoricalCloseError("invalid source CSV structure") from exc
    if len(observations) < 2:
        raise HistoricalCloseError("insufficient priced sessions")
    if observations[0].session != start_date or observations[-1].session != end_date:
        raise HistoricalCloseError("requested first or final session has no prices")
    return AdmittedCloseSeries(
        observations=tuple(observations),
        no_quote_dates=tuple(no_quote),
        last_source_row=last_date.isoformat() if last_date else "",
        source_sha256=expected_sha256,
    )
