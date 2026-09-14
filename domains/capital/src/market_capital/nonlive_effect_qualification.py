from __future__ import annotations

from decimal import Decimal
import math
from typing import Any

from .execution_reconciliation import reconcile_fix_intent


class NonLiveQualificationError(ValueError):
    pass


_NAUTILUS_TO_BINANCE = {
    "FILLED": "FILLED",
    "PARTIALLY_FILLED": "PARTIALLY_FILLED",
    "CANCELED": "CANCELED",
    "DENIED": "REJECTED",
    "REJECTED": "REJECTED",
    "ACCEPTED": "NEW",
    "SUBMITTED": "NEW",
}


def _missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    return str(value).strip().lower() in {"", "nan", "none", "nat"}


def build_fix_intent(*, client_order_id: str, quantity: str, side: str = "BUY") -> dict[str, Any]:
    if not client_order_id:
        raise NonLiveQualificationError("client_order_id required")
    q = Decimal(str(quantity))
    if q <= 0:
        raise NonLiveQualificationError("quantity must be positive")
    return {
        "protocol": "FIX.4.4",
        "msgType": "D",
        "clOrdId": client_order_id,
        "exDestination": "BINANCE",
        "symbol": "BTCUSDT",
        "side": "1" if side.upper() == "BUY" else "2",
        "ordType": "1",
        "orderQty": format(q, "f"),
    }


def nautilus_episode_to_reality(episode: dict[str, Any]) -> dict[str, Any]:
    orders = episode.get("orders") or []
    fills = episode.get("fills") or []
    if not isinstance(orders, list) or not isinstance(fills, list):
        raise NonLiveQualificationError("episode orders/fills must be lists")

    normalized_orders: list[dict[str, Any]] = []
    for row in orders:
        if not isinstance(row, dict):
            continue
        status = str(row.get("status") or "").upper()
        mapped = _NAUTILUS_TO_BINANCE.get(status)
        if mapped is None:
            raise NonLiveQualificationError(f"unsupported Nautilus order status: {status}")
        venue_order_id = row.get("venue_order_id")
        if _missing(venue_order_id):
            venue_order_id = f"LOCAL-DENIAL:{row.get('client_order_id')}"
        avg_px = row.get("avg_px")
        normalized_orders.append({
            "venueOrderId": str(venue_order_id),
            "clientOrderId": str(row.get("client_order_id")),
            "instrumentId": str(row.get("instrument_id") or "BTCUSDT.BINANCE"),
            "side": str(row.get("side") or "BUY"),
            "orderType": str(row.get("type") or "MARKET"),
            "timeInForce": str(row.get("time_in_force") or "GTC"),
            "status": mapped,
            "originalQty": str(row.get("quantity") or "0"),
            "executedQty": str(row.get("filled_qty") or "0"),
            "price": "0" if _missing(avg_px) else str(avg_px),
            "venueTimestampMs": None,
        })

    normalized_fills: list[dict[str, Any]] = []
    order_id_by_client = {r["clientOrderId"]: r["venueOrderId"] for r in normalized_orders}
    for row in fills:
        if not isinstance(row, dict):
            continue
        clid = str(row.get("client_order_id"))
        venue_order_id = row.get("venue_order_id")
        if _missing(venue_order_id):
            venue_order_id = order_id_by_client.get(clid)
        normalized_fills.append({
            "venueTradeId": str(row.get("trade_id")),
            "venueOrderId": str(venue_order_id),
            "instrumentId": str(row.get("instrument_id") or "BTCUSDT.BINANCE"),
            "qty": str(row.get("last_qty") or "0"),
            "price": str(row.get("last_px") or "0"),
            "commission": "0",
            "commissionAsset": "USDT",
            "venueTimestampMs": None,
        })

    return {
        "schemaVersion": 1,
        "kind": "ordivon.market-capital.private-reality-snapshot",
        "venue": "BINANCE",
        "product": "SPOT",
        "sourceAuthority": "NAUTILUS_SIMULATED_EXCHANGE_EPISODE",
        "sourceStatus": "QUALIFIED_NONLIVE_PROVIDER",
        "permissionStanding": "READ_ONLY_VERIFIED",
        "balances": [],
        "positions": [],
        "openOrders": [],
        "orderHistory": normalized_orders,
        "fills": normalized_fills,
        "coverage": {
            "accountComplete": True,
            "openOrdersComplete": True,
            "orderHistoryComplete": True,
            "fillsComplete": True,
        },
        "externalFinancialWriteAttempted": False,
        "nonLiveProviderWriteAttempted": True,
        "realMoney": False,
        "liveEndpoint": False,
    }


def reconcile_nautilus_episode(episode: dict[str, Any]) -> dict[str, Any]:
    orders = episode.get("orders") or []
    if not orders:
        raise NonLiveQualificationError("episode has no order report")
    order = orders[-1]
    intent = build_fix_intent(
        client_order_id=str(order.get("client_order_id")),
        quantity=str(order.get("quantity") or "0"),
        side=str(order.get("side") or "BUY"),
    )
    reality = nautilus_episode_to_reality(episode)
    result = reconcile_fix_intent(intent=intent, reality=reality)
    return {"intent": intent, "reality": reality, "reconciliation": result}


def reconcile_unknown_after_submission(*, client_order_id: str, quantity: str) -> dict[str, Any]:
    intent = build_fix_intent(client_order_id=client_order_id, quantity=quantity)
    reality = {
        "venue": "BINANCE",
        "permissionStanding": "NOT_VERIFIED",
        "openOrders": [],
        "orderHistory": [],
        "fills": [],
        "coverage": {"fillsComplete": False},
        "externalFinancialWriteAttempted": False,
        "nonLiveProviderWriteAttempted": True,
        "realMoney": False,
        "liveEndpoint": False,
    }
    result = reconcile_fix_intent(intent=intent, reality=reality)
    return {"intent": intent, "reality": reality, "reconciliation": result}
