"""Pure, caller-supplied, source-unattested paper portfolio mark-to-market.

Not an accounting ledger, execution engine, historical total-return feed or
settlement authority. Designed to be a thin research projection consumed by
Finance Portfolio; no external financial effects.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation, localcontext
from typing import Any

_AMOUNT_MAX = Decimal("100000000000000")
_PRICE_MAX = Decimal("1000000000")
_QTY_MAX = Decimal("1000000000")
_CENT = Decimal("0.01")
_RETURN_PRECISION = Decimal("0.000000000000000001")
_IDENT = re.compile(r"[A-Z][A-Z0-9._-]{0,63}\Z")
_PORTFOLIO = re.compile(r"[A-Z0-9][A-Z0-9._-]{0,63}\Z")
_ROOT_FIELDS = {
    "schemaVersion", "kind", "portfolioId", "currency",
    "sessionCloseAt", "evaluatedAt", "openingNav", "externalCashFlowAtStart",
    "cashAtClose", "protectedCash", "pricesStanding", "positions",
}
_POSITION_FIELDS = {
    "instrumentId", "quantity", "closePrice", "priceAsOf", "availableAt", "sourceId",
}


class DailyValuationError(ValueError):
    """Caller-supplied valuation observations are inconsistent or unsupported."""


def _money(raw: Any, name: str, *, signed: bool = False) -> Decimal:
    if type(raw) is not str:
        raise DailyValuationError(f"{name}: expected decimal string")
    try:
        number = Decimal(raw)
    except InvalidOperation as exc:
        raise DailyValuationError(f"{name}: invalid decimal") from exc
    if (not number.is_finite()
            or number.as_tuple().exponent < -2
            or abs(number) > _AMOUNT_MAX
            or (not signed and number < 0)):
        raise DailyValuationError(f"{name}: invalid bounded cents")
    return number.quantize(_CENT)


def _positive_decimal(
    raw: Any, name: str, *, maximum: Decimal, decimal_places: int
) -> Decimal:
    if type(raw) is not str:
        raise DailyValuationError(f"{name}: expected decimal string")
    try:
        number = Decimal(raw)
    except InvalidOperation as exc:
        raise DailyValuationError(f"{name}: invalid decimal") from exc
    if (not number.is_finite() or not 0 < number <= maximum
            or number.as_tuple().exponent < -decimal_places):
        raise DailyValuationError(f"{name}: invalid bounded positive decimal")
    return number


def _utc(raw: Any, name: str) -> datetime:
    if type(raw) is not str:
        raise DailyValuationError(f"{name}: required timezone-aware timestamp string")
    try:
        date = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise DailyValuationError(f"{name}: invalid timestamp") from exc
    if date.tzinfo is None or date.utcoffset() is None:
        raise DailyValuationError(f"{name}: timezone required")
    return date.astimezone(UTC)


def _format_money(value: Decimal) -> str:
    return format(value.quantize(_CENT), ".2f")


def value_paper_portfolio(request: dict[str, Any]) -> dict[str, Any]:
    """Calculate one synthetic/unverified close without creating capital effects.

    All deposits/withdrawals must occur at *period start*; closing cash and
    quantities must already reflect trades, fees, dividends and flows. This
    function neither verifies those accounting facts nor manufactures them.
    Each instrument uses a caller-specified EOD mark available by evaluation.
    """
    if type(request) is not dict or set(request) != _ROOT_FIELDS:
        raise DailyValuationError("request: exact root field set required")
    if type(request["schemaVersion"]) is not int or request["schemaVersion"] != 1:
        raise DailyValuationError("request: schemaVersion must be 1")
    if request["kind"] != "ordivon.capital.finance.paper-daily-valuation-input":
        raise DailyValuationError("request: unsupported kind")
    if request["currency"] != "USD":
        raise DailyValuationError("daily portfolio R1 supports only USD")
    portfolio_id = request["portfolioId"]
    if type(portfolio_id) is not str or not _PORTFOLIO.fullmatch(portfolio_id):
        raise DailyValuationError("portfolioId: invalid")
    prices_standing = request["pricesStanding"]
    if prices_standing not in ("SYNTHETIC_FIXTURE", "CALLER_SUPPLIED_UNATTESTED"):
        raise DailyValuationError("pricesStanding: cannot claim provider verification")

    close_at = _utc(request["sessionCloseAt"], "sessionCloseAt")
    evaluated_at = _utc(request["evaluatedAt"], "evaluatedAt")
    if evaluated_at < close_at:
        raise DailyValuationError("cannot value at a time before the market close")
    opening = _money(request["openingNav"], "openingNav")
    external = _money(
        request["externalCashFlowAtStart"], "externalCashFlowAtStart", signed=True
    )
    cash = _money(request["cashAtClose"], "cashAtClose")
    reserve = _money(request["protectedCash"], "protectedCash")
    if cash < reserve:
        raise DailyValuationError("closing cash is below protected cash")
    initial = opening + external
    if initial < 0:
        raise DailyValuationError("external withdrawal exceeds opening net assets")

    rows = request["positions"]
    if type(rows) is not list or len(rows) > 128:
        raise DailyValuationError("positions: expected at most 128 entries")
    positions = []
    seen: set[str] = set()
    with localcontext() as ctx:
        ctx.prec = 50
        for index, raw in enumerate(rows):
            if type(raw) is not dict or set(raw) != _POSITION_FIELDS:
                raise DailyValuationError(f"positions[{index}]: invalid field set")
            symbol = raw["instrumentId"]
            if type(symbol) is not str or not _IDENT.fullmatch(symbol) or symbol in seen:
                raise DailyValuationError(f"positions[{index}]: duplicate or invalid instrument")
            seen.add(symbol)
            source = raw["sourceId"]
            if type(source) is not str or not _IDENT.fullmatch(source):
                raise DailyValuationError(f"positions[{index}]: invalid sourceId")
            if prices_standing == "SYNTHETIC_FIXTURE" and source != "SYNTHETIC_FIXTURE":
                raise DailyValuationError("fixture price source must be declared synthetic")
            price_asof = _utc(raw["priceAsOf"], f"{symbol}.priceAsOf")
            available_at = _utc(raw["availableAt"], f"{symbol}.availableAt")
            if price_asof != close_at or not price_asof <= available_at <= evaluated_at:
                raise DailyValuationError(f"{symbol}: invalid end-of-day data timing")
            quantity = _positive_decimal(
                raw["quantity"], f"{symbol}.quantity",
                maximum=_QTY_MAX, decimal_places=6,
            )
            price = _positive_decimal(
                raw["closePrice"], f"{symbol}.closePrice",
                maximum=_PRICE_MAX, decimal_places=4,
            )
            value = (quantity * price).quantize(_CENT, rounding=ROUND_HALF_EVEN)
            positions.append({
                "instrumentId": symbol,
                "quantity": format(quantity, "f"),
                "closePrice": format(price, "f"),
                "marketValue": _format_money(value),
                "sourceId": source,
                "availableAt": available_at.isoformat(),
            })
        positions.sort(key=lambda item: item["instrumentId"])
        positions_value = sum(
            (Decimal(position["marketValue"]) for position in positions),
            Decimal(0),
        )
        closing = positions_value + cash
        if closing > _AMOUNT_MAX:
            raise DailyValuationError("closing value exceeds bounded amount")
        economic_gain = closing - initial
        period_return = (
            format((economic_gain / initial).quantize(
                _RETURN_PRECISION, rounding=ROUND_HALF_EVEN
            ).normalize(), "f") if initial > 0 else None
        )
    return {
        "schemaVersion": 1,
        "kind": "ordivon.capital.finance.paper-daily-valuation",
        "portfolioId": portfolio_id,
        "standing": (
            "SYNTHETIC_RESEARCH_ONLY"
            if prices_standing == "SYNTHETIC_FIXTURE"
            else "UNATTESTED_RESEARCH_ONLY"
        ),
        "currency": "USD",
        "sessionCloseAt": close_at.isoformat(),
        "evaluatedAt": evaluated_at.isoformat(),
        "openingNav": _format_money(opening),
        "externalCashFlowAtStart": _format_money(external),
        "cashAtClose": _format_money(cash),
        "protectedCash": _format_money(reserve),
        "positions": positions,
        "positionsValue": _format_money(positions_value),
        "closingCash": _format_money(cash),
        "closingNav": _format_money(closing),
        "periodEconomicGain": _format_money(economic_gain),
        "periodReturn": period_return,
        "cashFlowConvention": "EXTERNAL_FLOW_AT_PERIOD_START",
        "markConvention": "EOD_PRICE_MULTIPLIED_BY_QUANTITY_ROUND_HALF_EVEN_PER_INSTRUMENT",
        "corporateActionsVerified": False,
        "marketSourceVerified": False,
        "accountingSourceVerified": False,
        "realCapitalAuthority": "NONE",
        "executionAuthorized": False,
    }
