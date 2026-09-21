from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from typing import Any


class BinanceUsdmReferenceError(RuntimeError):
    pass


def _value(row: Mapping[str, Any], camel: str, snake: str | None = None) -> Any:
    if camel in row:
        return row[camel]
    key = snake or camel
    if key in row:
        return row[key]
    return None


def _filter(symbol: Mapping[str, Any], name: str) -> Mapping[str, Any]:
    for row in symbol.get("filters", []):
        if isinstance(row, Mapping) and _value(row, "filterType", "filter_type") == name:
            return row
    raise BinanceUsdmReferenceError(f"missing {name} filter")


def normalize_exchange_symbol(exchange_info: Mapping[str, Any], symbol_id: str) -> dict[str, Any]:
    """Normalize official Binance exchangeInfo without inventing trading rules."""
    rows = exchange_info.get("symbols")
    if not isinstance(rows, list):
        raise BinanceUsdmReferenceError("exchangeInfo.symbols must be a list")
    symbol = next((row for row in rows if row.get("symbol") == symbol_id), None)
    if symbol is None:
        raise BinanceUsdmReferenceError(f"symbol not found: {symbol_id}")

    price = _filter(symbol, "PRICE_FILTER")
    lot = _filter(symbol, "LOT_SIZE")
    market_lot = next(
        (row for row in symbol.get("filters", []) if row.get("filterType") == "MARKET_LOT_SIZE"),
        None,
    )
    min_notional = _filter(symbol, "MIN_NOTIONAL")

    tick = Decimal(str(_value(price, "tickSize", "tick_size")))
    step = Decimal(str(_value(lot, "stepSize", "step_size")))
    market_step = Decimal(str(_value(market_lot or lot, "stepSize", "step_size")))
    notional = Decimal(str(_value(min_notional, "notional")))
    if tick <= 0 or step <= 0 or market_step <= 0 or notional <= 0:
        raise BinanceUsdmReferenceError("non-positive exchange rule")

    return {
        "schemaVersion": 1,
        "kind": "ordivon.capital.market.binance-usdm-symbol-contract",
        "provider": "BINANCE",
        "symbol": symbol_id,
        "status": symbol.get("status"),
        "contractType": _value(symbol, "contractType", "contract_type"),
        "baseAsset": _value(symbol, "baseAsset", "base_asset"),
        "quoteAsset": _value(symbol, "quoteAsset", "quote_asset"),
        "marginAsset": _value(symbol, "marginAsset", "margin_asset"),
        "underlyingType": _value(symbol, "underlyingType", "underlying_type"),
        "underlyingSubType": _value(symbol, "underlyingSubType", "underlying_sub_type"),
        "tickSize": format(tick, "f"),
        "stepSize": format(step, "f"),
        "marketStepSize": format(market_step, "f"),
        "minNotional": format(notional, "f"),
        "orderTypes": list(_value(symbol, "orderTypes", "order_types") or []),
        "timeInForce": list(_value(symbol, "timeInForce", "time_in_force") or []),
        "triggerProtect": _value(symbol, "triggerProtect", "trigger_protect"),
        "liquidationFee": _value(symbol, "liquidationFee", "liquidation_fee"),
        "marketTakeBound": _value(symbol, "marketTakeBound", "market_take_bound"),
        "pricePrecisionInformationalOnly": _value(symbol, "pricePrecision", "price_precision"),
        "quantityPrecisionInformationalOnly": _value(symbol, "quantityPrecision", "quantity_precision"),
    }
