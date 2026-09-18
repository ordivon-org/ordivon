from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Mapping


class RegimeCardError(ValueError):
    """Fail-closed validation error for bounded regime analysis."""


def _d(value: Any, label: str) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise RegimeCardError(f"invalid decimal for {label}") from exc


def _maybe_d(value: Any, label: str) -> Decimal | None:
    if value is None:
        return None
    return _d(value, label)


def _pct_change(last: Decimal, reference: Decimal) -> Decimal:
    if reference <= 0:
        raise RegimeCardError("reference price must be positive")
    return (last / reference - Decimal("1")) * Decimal("100")


def _bps(delta: Decimal, reference: Decimal) -> Decimal:
    if reference <= 0:
        raise RegimeCardError("basis reference must be positive")
    return delta / reference * Decimal("10000")


def _fmt(value: Decimal, places: str = "0.000001") -> str:
    return format(value.quantize(Decimal(places)), "f")


def _level_state(last: Decimal, level: Decimal) -> str:
    if last > level:
        return "ABOVE"
    if last < level:
        return "BELOW"
    return "AT"


def _position_pnl(quantity: Decimal, average_price: Decimal, level: Decimal) -> str:
    return _fmt((level - average_price) * quantity)


def build_regime_card(
    *,
    market: Mapping[str, Any],
    context: Mapping[str, Any],
    position: Mapping[str, Any] | None = None,
    signposts: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a bounded, non-predictive regime-analysis projection.

    The function intentionally does not fetch data, infer trade authority, estimate
    probabilities, or recommend an order. Provider/domain observations remain
    authoritative; this output is analysis evidence only.
    """

    instrument_id = str(market.get("instrumentId") or "").strip()
    if not instrument_id:
        raise RegimeCardError("instrumentId is required")

    observed_at_ms = market.get("observedAtMs")
    if not isinstance(observed_at_ms, int) or observed_at_ms < 0:
        raise RegimeCardError("observedAtMs must be a non-negative integer")

    last = _d(market.get("last"), "market.last")
    mark = _d(market.get("mark"), "market.mark")
    index = _d(market.get("index"), "market.index")
    open_24h = _d(market.get("open24h"), "market.open24h")
    high_24h = _d(market.get("high24h"), "market.high24h")
    low_24h = _d(market.get("low24h"), "market.low24h")
    funding = _d(market.get("fundingCurrent"), "market.fundingCurrent")
    oi_usd = _d(market.get("openInterestUsd"), "market.openInterestUsd")

    for label, value in (
        ("last", last),
        ("mark", mark),
        ("index", index),
        ("open24h", open_24h),
        ("high24h", high_24h),
        ("low24h", low_24h),
    ):
        if value <= 0:
            raise RegimeCardError(f"{label} must be positive")
    if low_24h > high_24h:
        raise RegimeCardError("24h low cannot exceed 24h high")
    if oi_usd < 0:
        raise RegimeCardError("open interest cannot be negative")

    tradfi_open = context.get("underlyingMarketOpen")
    if not isinstance(tradfi_open, bool):
        raise RegimeCardError("context.underlyingMarketOpen must be boolean")

    index_source_mode = str(context.get("indexSourceMode") or "UNKNOWN").strip().upper()
    if not index_source_mode:
        index_source_mode = "UNKNOWN"

    regime_identity = (
        "UNDERLYING_AND_DERIVATIVE_CO_DISCOVERY"
        if tradfi_open
        else "DERIVATIVE_LED_OUT_OF_HOURS_DISCOVERY"
    )

    oi_change_pct = _maybe_d(market.get("openInterestChangePct"), "market.openInterestChangePct")
    book_imbalance = _maybe_d(market.get("bookImbalance"), "market.bookImbalance")
    trade_buy_share = _maybe_d(market.get("tradeBuyShare"), "market.tradeBuyShare")
    funding_mean = _maybe_d(market.get("fundingRecentMean"), "market.fundingRecentMean")

    gaps: list[str] = []
    if oi_change_pct is None:
        gaps.append("OPEN_INTEREST_CHANGE_MISSING")
    if book_imbalance is None:
        gaps.append("REPEATED_MICROSTRUCTURE_EVIDENCE_MISSING")
    if trade_buy_share is None:
        gaps.append("RECENT_TRADE_FLOW_MISSING")
    if not tradfi_open and context.get("lastUnderlyingReferencePrice") is None:
        gaps.append("LAST_UNDERLYING_REFERENCE_PRICE_MISSING")

    basis_bps = _bps(mark - index, index)
    change_24h_pct = _pct_change(last, open_24h)

    technical = market.get("technical") or {}
    if not isinstance(technical, Mapping):
        raise RegimeCardError("market.technical must be an object")

    short_horizon_extended = False
    long_horizon_extended = False
    for key in ("1H", "4H"):
        row = technical.get(key)
        if isinstance(row, Mapping) and row.get("rsi14") is not None:
            if _d(row["rsi14"], f"technical.{key}.rsi14") >= Decimal("70"):
                short_horizon_extended = True
    day = technical.get("1D")
    if isinstance(day, Mapping) and day.get("rsi14") is not None:
        long_horizon_extended = _d(day["rsi14"], "technical.1D.rsi14") >= Decimal("70")

    divergences: list[str] = []
    if change_24h_pct > 0 and book_imbalance is not None and book_imbalance < 0:
        divergences.append("PRICE_UP_WHILE_BOOK_IMBALANCE_NEGATIVE")
    if change_24h_pct > 0 and trade_buy_share is not None and trade_buy_share < Decimal("0.5"):
        divergences.append("PRICE_UP_WHILE_RECENT_TRADE_BUY_SHARE_BELOW_HALF")
    if short_horizon_extended and not long_horizon_extended:
        divergences.append("SHORT_HORIZON_MOMENTUM_EXTENDED_WITHOUT_DAILY_EXTENSION")

    crowding_evidence: list[str] = []
    if funding > Decimal("0.001"):
        crowding_evidence.append("ELEVATED_POSITIVE_FUNDING")
    if basis_bps > Decimal("25"):
        crowding_evidence.append("ELEVATED_POSITIVE_MARK_BASIS")
    if oi_change_pct is not None and oi_change_pct > Decimal("10"):
        crowding_evidence.append("RAPID_OPEN_INTEREST_EXPANSION")

    if crowding_evidence:
        crowding_standing = "CROWDING_SIGNALS_PRESENT"
    elif oi_change_pct is None:
        crowding_standing = "NOT_IDENTIFIED_MISSING_OI_CHANGE"
    else:
        crowding_standing = "NO_STRONG_CROWDING_SIGNAL_IN_BOUND_INPUTS"

    hypotheses = [
        {
            "id": "H0_STATIONARY_HIGH_VOLATILITY",
            "claim": "Observed movement remains ordinary high-volatility variation within the current regime.",
            "falsifier": "Persistent acceptance outside the recent range across multiple observation cuts.",
        },
        {
            "id": "H1_TREND_ACCELERATION",
            "claim": "The existing directional regime is accelerating without a mechanism change.",
            "falsifier": "Underlying-market reopening rejects the out-of-hours price region and higher-horizon trend structure fails.",
        },
        {
            "id": "H2_OUT_OF_HOURS_DERIVATIVE_DISLOCATION",
            "claim": "Out-of-hours derivative price discovery has moved materially ahead of the underlying market.",
            "falsifier": "The underlying market reopens and promptly validates the derivative price region.",
        },
        {
            "id": "H3_EVENT_EXHAUSTION",
            "claim": "A known event has been substantially anticipated and realized flow may exhaust after the event boundary.",
            "falsifier": "Post-event price acceptance persists with orderly basis/funding and underlying confirmation.",
        },
        {
            "id": "H4_EXOGENOUS_FACTOR_DOMINANCE",
            "claim": "Sector, macro, liquidity, or geopolitical factors dominate instrument-specific mechanisms.",
            "falsifier": "Instrument returns remain strongly idiosyncratic against appropriate external factors.",
        },
    ]

    if tradfi_open:
        hypotheses = [h for h in hypotheses if h["id"] != "H2_OUT_OF_HOURS_DERIVATIVE_DISLOCATION"]

    signpost_rows: list[dict[str, Any]] = []
    if signposts:
        if not isinstance(signposts, Mapping):
            raise RegimeCardError("signposts must be an object")
        quantity = average_price = None
        if position is not None:
            quantity = _d(position.get("quantity"), "position.quantity")
            average_price = _d(position.get("averagePrice"), "position.averagePrice")
        for name, raw_level in signposts.items():
            level = _d(raw_level, f"signposts.{name}")
            if level <= 0:
                raise RegimeCardError(f"signpost {name} must be positive")
            row: dict[str, Any] = {
                "name": str(name),
                "level": _fmt(level),
                "state": _level_state(last, level),
            }
            if quantity is not None and average_price is not None:
                row["approxGrossPositionPnlAtLevel"] = _position_pnl(quantity, average_price, level)
            signpost_rows.append(row)

    position_projection = None
    if position is not None:
        quantity = _d(position.get("quantity"), "position.quantity")
        average_price = _d(position.get("averagePrice"), "position.averagePrice")
        if average_price <= 0:
            raise RegimeCardError("position.averagePrice must be positive")
        position_projection = {
            "quantity": _fmt(quantity),
            "averagePrice": _fmt(average_price),
            "approxGrossPnlAtLast": _position_pnl(quantity, average_price, last),
            "leverage": str(position.get("leverage")) if position.get("leverage") is not None else None,
            "marginMode": position.get("marginMode"),
            "liquidationPriceObserved": (
                _fmt(_d(position.get("liquidationPrice"), "position.liquidationPrice"))
                if position.get("liquidationPrice") is not None
                else None
            ),
            "liquidationPriceDynamic": True,
        }

    return {
        "schemaVersion": 1,
        "kind": "ordivon.market-capital.regime-card",
        "truthRole": "analysis-evidence-not-forecast-truth",
        "instrumentId": instrument_id,
        "observedAtMs": observed_at_ms,
        "regimeIdentity": regime_identity,
        "underlyingMarketOpen": tradfi_open,
        "indexSourceMode": index_source_mode,
        "observedState": {
            "last": _fmt(last),
            "change24hPct": _fmt(change_24h_pct),
            "basisBps": _fmt(basis_bps),
            "fundingCurrent": _fmt(funding),
            "fundingRecentMean": _fmt(funding_mean) if funding_mean is not None else None,
            "openInterestUsd": _fmt(oi_usd),
            "openInterestChangePct": _fmt(oi_change_pct) if oi_change_pct is not None else None,
            "shortHorizonMomentumExtended": short_horizon_extended,
            "dailyMomentumExtended": long_horizon_extended,
        },
        "divergences": divergences,
        "crowding": {
            "standing": crowding_standing,
            "evidence": crowding_evidence,
        },
        "competingHypotheses": hypotheses,
        "signposts": signpost_rows,
        "positionProjection": position_projection,
        "evidenceGaps": gaps,
        "causalStanding": "NOT_IDENTIFIED_FROM_OBSERVATIONAL_CARD",
        "forecastProbabilityProduced": False,
        "tradeRecommendationProduced": False,
        "externalFinancialWriteAttempted": False,
    }
