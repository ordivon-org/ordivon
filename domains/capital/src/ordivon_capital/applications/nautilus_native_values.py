"""Precise value and timestamp validation for native Nautilus report ingestion."""
from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any
from zoneinfo import ZoneInfo

_NY = ZoneInfo("America/New_York")
_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)


class NautilusPaperBridgeError(ValueError):
    """The native execution evidence cannot refine a next-open paper close."""


def _required(row: Mapping[str, Any], field: str) -> str:
    value = row.get(field)
    if not isinstance(value, str) or not value.strip():
        raise NautilusPaperBridgeError(f"missing string {field}")
    return value


def _instant(value: Any, field: str) -> datetime:
    if isinstance(value, bool):
        raise NautilusPaperBridgeError(f"{field}: boolean is not a timestamp")
    if isinstance(value, int):
        if value < 0:
            raise NautilusPaperBridgeError(f"{field}: negative timestamp")
        # Native Nautilus ts_init / ts_event are Unix nanoseconds.
        seconds, ns = divmod(value, 1_000_000_000)
        if ns % 1_000:
            raise NautilusPaperBridgeError(f"{field}: nanosecond precision not representable")
        try:
            value = _EPOCH + timedelta(seconds=seconds, microseconds=ns // 1_000)
        except OverflowError as exc:
            raise NautilusPaperBridgeError(f"{field}: timestamp out of range") from exc
    elif isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise NautilusPaperBridgeError(f"{field}: invalid timestamp") from exc
    if not isinstance(value, datetime) or value.utcoffset() is None:
        raise NautilusPaperBridgeError(f"{field}: timezone-aware timestamp required")
    return value.astimezone(UTC)


def _positive_integer(value: Any, field: str, *, allow_zero: bool = False) -> int:
    if isinstance(value, bool):
        raise NautilusPaperBridgeError(f"{field}: boolean not accepted")
    try:
        number = Decimal(str(value))
    except InvalidOperation as exc:
        raise NautilusPaperBridgeError(f"{field}: invalid decimal") from exc
    if (not number.is_finite() or (number < 0 if allow_zero else number <= 0)
        or number != number.to_integral_value()):
        raise NautilusPaperBridgeError(f"{field}: nonnegative integral share quantity required")
    result = int(number)
    if result >= 2**63:
        raise NautilusPaperBridgeError(f"{field}: quantity exceeds bounded paper model")
    return result


def _cents(value: Any, field: str) -> int:
    if isinstance(value, bool):
        raise NautilusPaperBridgeError(f"{field}: boolean not accepted")
    try:
        d = Decimal(str(value))
    except InvalidOperation as exc:
        raise NautilusPaperBridgeError(f"{field}: invalid decimal") from exc
    cents = d * 100
    if not d.is_finite() or cents != cents.to_integral_value() or cents < 0 or cents >= 2**63:
        raise NautilusPaperBridgeError(f"{field}: exact nonnegative USD cents required")
    return int(cents)


def _fee_cents(value: Any) -> int:
    if not isinstance(value, str):
        raise NautilusPaperBridgeError("commission: missing native Money and currency")
    parts = value.strip().split()
    if len(parts) != 2 or parts[1] != "USD":
        raise NautilusPaperBridgeError("commission: explicit USD Money required")
    return _cents(parts[0], "commission")
