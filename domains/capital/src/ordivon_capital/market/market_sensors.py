from __future__ import annotations

from decimal import Decimal, InvalidOperation
from statistics import median
from typing import Any, Iterable, Mapping, Sequence


class MarketSensorError(ValueError):
    """Fail-closed validation error for read-only market sensors."""


def _d(value: Any, label: str) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise MarketSensorError(f"invalid decimal for {label}") from exc
    if not result.is_finite():
        raise MarketSensorError(f"non-finite decimal for {label}")
    return result


def _fmt(value: Decimal, places: str = "0.000001") -> str:
    return format(value.quantize(Decimal(places)), "f")


def _validate_timestamp(value: Any, label: str) -> int:
    if not isinstance(value, int) or value < 0:
        raise MarketSensorError(f"{label} must be a non-negative integer")
    return value


def open_interest_change(
    samples: Sequence[Mapping[str, Any]],
    *,
    minimum_span_ms: int = 1,
) -> dict[str, Any]:
    """Derive OI change from an ordered same-instrument observation window."""

    if len(samples) < 2:
        raise MarketSensorError("open-interest change requires at least two samples")
    if not isinstance(minimum_span_ms, int) or minimum_span_ms < 1:
        raise MarketSensorError("minimum_span_ms must be a positive integer")

    instrument_id: str | None = None
    rows: list[tuple[int, Decimal]] = []
    previous_ts = -1
    for i, sample in enumerate(samples):
        inst = str(sample.get("instrumentId") or "").strip()
        if not inst:
            raise MarketSensorError(f"samples[{i}].instrumentId is required")
        if instrument_id is None:
            instrument_id = inst
        elif inst != instrument_id:
            raise MarketSensorError("open-interest samples must use one instrument")

        ts = _validate_timestamp(sample.get("observedAtMs"), f"samples[{i}].observedAtMs")
        if ts <= previous_ts:
            raise MarketSensorError("open-interest sample timestamps must be strictly increasing")
        previous_ts = ts

        oi = _d(sample.get("openInterestUsd"), f"samples[{i}].openInterestUsd")
        if oi < 0:
            raise MarketSensorError("open interest cannot be negative")
        rows.append((ts, oi))

    start_ts, start_oi = rows[0]
    end_ts, end_oi = rows[-1]
    span_ms = end_ts - start_ts
    if span_ms < minimum_span_ms:
        raise MarketSensorError("open-interest observation span is below minimum")
    if start_oi == 0:
        change_pct = None
    else:
        change_pct = (end_oi / start_oi - Decimal("1")) * Decimal("100")

    return {
        "schemaVersion": 1,
        "kind": "ordivon.capital.market.open-interest-change",
        "componentId": "open-interest-change",
        "instrumentId": instrument_id,
        "sampleCount": len(rows),
        "startObservedAtMs": start_ts,
        "endObservedAtMs": end_ts,
        "spanMs": span_ms,
        "startOpenInterestUsd": _fmt(start_oi),
        "endOpenInterestUsd": _fmt(end_oi),
        "openInterestChangeUsd": _fmt(end_oi - start_oi),
        "openInterestChangePct": _fmt(change_pct) if change_pct is not None else None,
    }


def repeated_microstructure(
    samples: Sequence[Mapping[str, Any]],
    *,
    minimum_samples: int = 3,
) -> dict[str, Any]:
    """Summarize persistence across repeated microstructure snapshots.

    Directional labels describe the observation window only. They are not price
    forecasts or reversal/continuation claims.
    """

    if not isinstance(minimum_samples, int) or minimum_samples < 2:
        raise MarketSensorError("minimum_samples must be at least two")
    if len(samples) < minimum_samples:
        raise MarketSensorError("insufficient repeated microstructure samples")

    instrument_id: str | None = None
    previous_ts = -1
    rows: list[tuple[int, Decimal, Decimal, Decimal]] = []
    for i, sample in enumerate(samples):
        inst = str(sample.get("instrumentId") or "").strip()
        if not inst:
            raise MarketSensorError(f"samples[{i}].instrumentId is required")
        if instrument_id is None:
            instrument_id = inst
        elif inst != instrument_id:
            raise MarketSensorError("microstructure samples must use one instrument")

        ts = _validate_timestamp(sample.get("observedAtMs"), f"samples[{i}].observedAtMs")
        if ts <= previous_ts:
            raise MarketSensorError("microstructure sample timestamps must be strictly increasing")
        previous_ts = ts

        imbalance = _d(sample.get("bookImbalance"), f"samples[{i}].bookImbalance")
        buy_share = _d(sample.get("tradeBuyShare"), f"samples[{i}].tradeBuyShare")
        spread_bps = _d(sample.get("spreadBps"), f"samples[{i}].spreadBps")
        if imbalance < -1 or imbalance > 1:
            raise MarketSensorError("bookImbalance must be in [-1, 1]")
        if buy_share < 0 or buy_share > 1:
            raise MarketSensorError("tradeBuyShare must be in [0, 1]")
        if spread_bps < 0:
            raise MarketSensorError("spreadBps cannot be negative")
        rows.append((ts, imbalance, buy_share, spread_bps))

    count = Decimal(len(rows))
    neg_book_ratio = Decimal(sum(1 for _, x, _, _ in rows if x < 0)) / count
    pos_book_ratio = Decimal(sum(1 for _, x, _, _ in rows if x > 0)) / count
    sell_trade_ratio = Decimal(sum(1 for _, _, x, _ in rows if x < Decimal("0.5"))) / count
    buy_trade_ratio = Decimal(sum(1 for _, _, x, _ in rows if x > Decimal("0.5"))) / count

    mean_book = sum((x for _, x, _, _ in rows), Decimal("0")) / count
    mean_buy_share = sum((x for _, _, x, _ in rows), Decimal("0")) / count
    spreads = [x for _, _, _, x in rows]
    median_spread = Decimal(str(median(spreads)))

    return {
        "schemaVersion": 1,
        "kind": "ordivon.capital.market.repeated-microstructure",
        "componentId": "repeated-microstructure-summary",
        "instrumentId": instrument_id,
        "sampleCount": len(rows),
        "startObservedAtMs": rows[0][0],
        "endObservedAtMs": rows[-1][0],
        "spanMs": rows[-1][0] - rows[0][0],
        "meanBookImbalance": _fmt(mean_book),
        "negativeBookImbalanceRatio": _fmt(neg_book_ratio),
        "positiveBookImbalanceRatio": _fmt(pos_book_ratio),
        "meanTradeBuyShare": _fmt(mean_buy_share),
        "tradeBuyShareBelowHalfRatio": _fmt(sell_trade_ratio),
        "tradeBuyShareAboveHalfRatio": _fmt(buy_trade_ratio),
        "medianSpreadBps": _fmt(median_spread),
        "maxSpreadBps": _fmt(max(spreads)),
    }


def reconcile_underlying_reopen(
    *,
    instrument_id: str,
    weekend_perp_price: Any,
    weekend_observed_at_ms: int,
    validation_tolerance_bps: Any | None = None,
    underlying_reopen_price: Any | None = None,
    underlying_observed_at_ms: int | None = None,
    post_open_perp_price: Any | None = None,
    post_open_perp_observed_at_ms: int | None = None,
) -> dict[str, Any]:
    """Compare out-of-hours derivative price discovery with reopened underlying cash.

    The caller owns the tolerance. This function intentionally has no universal
    built-in definition of "validated."
    """

    instrument_id = instrument_id.strip()
    if not instrument_id:
        raise MarketSensorError("instrument_id is required")
    weekend_ts = _validate_timestamp(weekend_observed_at_ms, "weekend_observed_at_ms")
    weekend_price = _d(weekend_perp_price, "weekend_perp_price")
    tolerance = (
        _d(validation_tolerance_bps, "validation_tolerance_bps")
        if validation_tolerance_bps is not None
        else None
    )
    if weekend_price <= 0:
        raise MarketSensorError("weekend_perp_price must be positive")
    if tolerance is not None and tolerance < 0:
        raise MarketSensorError("validation_tolerance_bps cannot be negative")

    base = {
        "schemaVersion": 1,
        "kind": "ordivon.capital.market.underlying-reopen-reconciliation",
        "componentId": "underlying-reopen-reconciliation",
        "instrumentId": instrument_id,
        "weekendPerpPrice": _fmt(weekend_price),
        "weekendObservedAtMs": weekend_ts,
        "validationToleranceBps": _fmt(tolerance) if tolerance is not None else None,
    }

    if underlying_reopen_price is None:
        return {
            **base,
            "standing": "RECONCILIATION_PENDING",
            "underlyingReopenPrice": None,
            "weekendToUnderlyingGapBps": None,
            "postOpenPerpPrice": None,
            "postOpenPerpToUnderlyingGapBps": None,
            "convergenceFraction": None,
        }

    if tolerance is None:
        raise MarketSensorError("validation_tolerance_bps is required once underlying_reopen_price is observed")
    if underlying_observed_at_ms is None:
        raise MarketSensorError("underlying_observed_at_ms is required with underlying_reopen_price")
    underlying_ts = _validate_timestamp(underlying_observed_at_ms, "underlying_observed_at_ms")
    if underlying_ts <= weekend_ts:
        raise MarketSensorError("underlying reopen observation must occur after weekend observation")

    underlying_price = _d(underlying_reopen_price, "underlying_reopen_price")
    if underlying_price <= 0:
        raise MarketSensorError("underlying_reopen_price must be positive")
    initial_gap_bps = abs((underlying_price / weekend_price - Decimal("1")) * Decimal("10000"))

    post_price: Decimal | None = None
    final_gap_bps: Decimal | None = None
    convergence: Decimal | None = None
    if post_open_perp_price is not None:
        if post_open_perp_observed_at_ms is None:
            raise MarketSensorError("post_open_perp_observed_at_ms is required with post_open_perp_price")
        post_ts = _validate_timestamp(post_open_perp_observed_at_ms, "post_open_perp_observed_at_ms")
        if post_ts < underlying_ts:
            raise MarketSensorError("post-open perp observation cannot precede underlying reopen observation")
        post_price = _d(post_open_perp_price, "post_open_perp_price")
        if post_price <= 0:
            raise MarketSensorError("post_open_perp_price must be positive")
        final_gap_bps = abs((post_price / underlying_price - Decimal("1")) * Decimal("10000"))
        if initial_gap_bps == 0:
            convergence = Decimal("1") if final_gap_bps == 0 else Decimal("0")
        else:
            convergence = (initial_gap_bps - final_gap_bps) / initial_gap_bps

    if initial_gap_bps <= tolerance:
        standing = "UNDERLYING_VALIDATED_WEEKEND_REGION"
    elif post_price is None:
        standing = "UNDERLYING_REOPEN_DISAGREEMENT"
    elif final_gap_bps is not None and final_gap_bps <= tolerance:
        standing = "PERP_REANCHORED_TO_UNDERLYING"
    elif convergence is not None and convergence > 0:
        standing = "PARTIAL_CONVERGENCE"
    else:
        standing = "DISAGREEMENT_PERSISTS"

    return {
        **base,
        "standing": standing,
        "underlyingReopenPrice": _fmt(underlying_price),
        "underlyingObservedAtMs": underlying_ts,
        "weekendToUnderlyingGapBps": _fmt(initial_gap_bps),
        "postOpenPerpPrice": _fmt(post_price) if post_price is not None else None,
        "postOpenPerpObservedAtMs": post_open_perp_observed_at_ms,
        "postOpenPerpToUnderlyingGapBps": _fmt(final_gap_bps) if final_gap_bps is not None else None,
        "convergenceFraction": _fmt(convergence) if convergence is not None else None,
    }


def merge_market_observations(
    market: Mapping[str, Any],
    *,
    oi_change: Mapping[str, Any] | None = None,
    microstructure: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Merge derived observations into a downstream market-risk observation record."""

    result = dict(market)
    instrument_id = str(result.get("instrumentId") or "").strip()
    if not instrument_id:
        raise MarketSensorError("market.instrumentId is required")

    if oi_change is not None:
        if oi_change.get("kind") != "ordivon.capital.market.open-interest-change":
            raise MarketSensorError("unexpected OI sensor kind")
        if oi_change.get("instrumentId") != instrument_id:
            raise MarketSensorError("OI sensor instrument does not match market")
        result["openInterestChangePct"] = oi_change.get("openInterestChangePct")
        result["openInterestChangeSpanMs"] = oi_change.get("spanMs")
        result["openInterestChangeSampleCount"] = oi_change.get("sampleCount")

    if microstructure is not None:
        if microstructure.get("kind") != "ordivon.capital.market.repeated-microstructure":
            raise MarketSensorError("unexpected microstructure sensor kind")
        if microstructure.get("instrumentId") != instrument_id:
            raise MarketSensorError("microstructure sensor instrument does not match market")
        result["bookImbalance"] = microstructure.get("meanBookImbalance")
        result["tradeBuyShare"] = microstructure.get("meanTradeBuyShare")
        result["microstructureSampleCount"] = microstructure.get("sampleCount")
        result["negativeBookImbalanceRatio"] = microstructure.get("negativeBookImbalanceRatio")
        result["positiveBookImbalanceRatio"] = microstructure.get("positiveBookImbalanceRatio")
        result["tradeBuyShareBelowHalfRatio"] = microstructure.get("tradeBuyShareBelowHalfRatio")
        result["tradeBuyShareAboveHalfRatio"] = microstructure.get("tradeBuyShareAboveHalfRatio")
        result["medianSpreadBps"] = microstructure.get("medianSpreadBps")
        result["maxSpreadBps"] = microstructure.get("maxSpreadBps")

    return result
