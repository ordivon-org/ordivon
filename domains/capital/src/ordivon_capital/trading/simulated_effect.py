from __future__ import annotations

from decimal import Decimal
from typing import Any

SCENARIOS = {
    "FILL",
    "PARTIAL_FILL_SLICES",
    "CANCEL",
    "DENY",
    "UNKNOWN_AFTER_SUBMISSION",
}


class SimulatedEffectError(ValueError):
    """Invalid bounded simulated-exchange episode."""


def _quantity(intent: dict[str, Any]) -> Decimal:
    try:
        value = Decimal(str(intent.get("orderQty") or "0"))
    except Exception as exc:
        raise SimulatedEffectError("invalid orderQty") from exc
    if value <= 0:
        raise SimulatedEffectError("orderQty must be positive")
    return value


def _status(venue: str, *, filled: bool = False, partial: bool = False, canceled: bool = False) -> str:
    if venue == "BINANCE":
        if filled:
            return "FILLED"
        if partial:
            return "PARTIALLY_FILLED"
        if canceled:
            return "CANCELED"
        return "NEW"
    if venue == "OKX":
        if filled:
            return "filled"
        if partial:
            return "partially_filled"
        if canceled:
            return "canceled"
        return "live"
    raise SimulatedEffectError(f"unsupported simulated venue profile: {venue}")


def simulate_exchange_episode(
    *,
    intent: dict[str, Any],
    scenario: str,
) -> dict[str, Any]:
    """Return bounded provider-neutral simulated reality; never performs an external write."""
    scenario = str(scenario).strip().upper()
    if scenario not in SCENARIOS:
        raise SimulatedEffectError(f"unsupported scenario: {scenario}")
    if intent.get("protocol") != "FIX.4.4" or intent.get("msgType") != "D":
        raise SimulatedEffectError("intent must be FIX 4.4 NewOrderSingle")
    venue = str(intent.get("exDestination") or "").upper()
    clid = str(intent.get("clOrdId") or "").strip()
    if not clid:
        raise SimulatedEffectError("ClOrdID required")
    qty = _quantity(intent)
    venue_order_id = f"SIM-{clid}"
    base = {
        "venue": venue,
        "permissionStanding": "READ_ONLY_VERIFIED",
        "openOrders": [],
        "orderHistory": [],
        "fills": [],
        "coverage": {"fillsComplete": True},
        "externalFinancialWriteAttempted": False,
    }
    exact_lookup = None

    if scenario == "FILL":
        base["orderHistory"] = [{
            "venueOrderId": venue_order_id,
            "clientOrderId": clid,
            "instrumentId": intent.get("symbol"),
            "status": _status(venue, filled=True),
            "originalQty": format(qty, "f"),
            "executedQty": format(qty, "f"),
            "price": "1",
        }]
        base["fills"] = [{
            "venueTradeId": f"SIM-TRADE-{clid}",
            "venueOrderId": venue_order_id,
            "instrumentId": intent.get("symbol"),
            "qty": format(qty, "f"),
            "price": "1",
        }]
    elif scenario == "PARTIAL_FILL_SLICES":
        partial = qty / Decimal("2")
        base["openOrders"] = [{
            "venueOrderId": venue_order_id,
            "clientOrderId": clid,
            "instrumentId": intent.get("symbol"),
            "status": _status(venue, partial=True),
            "originalQty": format(qty, "f"),
            "executedQty": format(partial, "f"),
            "price": "1",
        }]
        base["fills"] = [{
            "venueTradeId": f"SIM-TRADE-{clid}-1",
            "venueOrderId": venue_order_id,
            "instrumentId": intent.get("symbol"),
            "qty": format(partial, "f"),
            "price": "1",
        }]
    elif scenario == "CANCEL":
        base["orderHistory"] = [{
            "venueOrderId": venue_order_id,
            "clientOrderId": clid,
            "instrumentId": intent.get("symbol"),
            "status": _status(venue, canceled=True),
            "originalQty": format(qty, "f"),
            "executedQty": "0",
            "price": "1",
        }]
    elif scenario == "DENY":
        exact_lookup = {
            "venue": venue,
            "clientOrderId": clid,
            "authoritative": True,
            "querySucceeded": True,
            "orderFound": False,
            "fillFound": False,
        }
    elif scenario == "UNKNOWN_AFTER_SUBMISSION":
        base["coverage"]["fillsComplete"] = False

    return {
        "schemaVersion": 1,
        "kind": "ordivon.capital.trading.simulated-exchange-episode",
        "providerClass": "SIMULATED_EXCHANGE",
        "scenario": scenario,
        "intent": dict(intent),
        "reality": base,
        "exactLookup": exact_lookup,
        "externalFinancialWritesAttempted": False,
        "realMoney": False,
    }
