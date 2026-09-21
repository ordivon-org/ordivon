from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .binance_usdm_reference import normalize_exchange_symbol


def _dump(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if isinstance(value, list):
        return [_dump(v) for v in value]
    return value


def _oneof(value: Any) -> Any:
    data = _dump(value)
    if isinstance(data, dict) and "actual_instance" in data:
        return data["actual_instance"]
    return data


def _current_and_next_session(schedule: dict[str, Any], now_ms: int) -> dict[str, Any]:
    market = schedule.get("market_schedules") or {}
    equity = market.get("equity") or {}
    sessions = equity.get("sessions") or []
    normalized = []
    for row in sessions:
        if not isinstance(row, dict):
            continue
        start = row.get("start_time", row.get("startTime"))
        end = row.get("end_time", row.get("endTime"))
        kind = row.get("type")
        if start is None or end is None:
            continue
        normalized.append({"startTime": int(start), "endTime": int(end), "type": kind})
    normalized.sort(key=lambda r: r["startTime"])
    current = next(
        (r for r in normalized if r["startTime"] <= now_ms < r["endTime"]),
        None,
    )
    upcoming = next((r for r in normalized if r["startTime"] > now_ms), None)
    return {
        "current": current,
        "next": upcoming,
        "sessionCount": len(normalized),
    }


def _book_summary(book: dict[str, Any]) -> dict[str, Any]:
    bids = book.get("bids") or []
    asks = book.get("asks") or []
    if not bids or not asks:
        raise RuntimeError("Binance order book has no bid/ask")
    best_bid = float(bids[0][0])
    best_ask = float(asks[0][0])
    mid = (best_bid + best_ask) / 2
    bid_qty = sum(float(row[1]) for row in bids)
    ask_qty = sum(float(row[1]) for row in asks)
    return {
        "bestBid": format(best_bid, ".8f"),
        "bestAsk": format(best_ask, ".8f"),
        "mid": format(mid, ".8f"),
        "spreadBps": format((best_ask - best_bid) / mid * 10_000, ".6f"),
        "returnedBidQty": format(bid_qty, ".8f"),
        "returnedAskQty": format(ask_qty, ".8f"),
        "returnedDepthLevels": min(len(bids), len(asks)),
        "eventTime": book.get("E"),
        "transactionTime": book.get("T"),
    }


def capture(symbol: str) -> dict[str, Any]:
    from binance_common.configuration import ConfigurationRestAPI
    from binance_sdk_derivatives_trading_usds_futures.derivatives_trading_usds_futures import (
        DerivativesTradingUsdsFutures,
    )

    api = DerivativesTradingUsdsFutures(
        config_rest_api=ConfigurationRestAPI(api_key="", api_secret="", timeout=10_000)
    ).rest_api

    exchange = _dump(api.exchange_information().data())
    contract = normalize_exchange_symbol(exchange, symbol)
    mark = _oneof(api.mark_price(symbol=symbol).data())
    funding_rows = _dump(api.get_funding_rate_info().data())
    funding = next(
        (row for row in funding_rows if isinstance(row, dict) and row.get("symbol") == symbol),
        None,
    )
    oi = _dump(api.open_interest(symbol=symbol).data())
    book = _dump(api.order_book(symbol=symbol, limit=100).data())
    schedule = _dump(api.trading_schedule().data())
    adl = _oneof(api.adl_risk(symbol=symbol).data())
    insurance = _oneof(api.query_insurance_fund_balance_snapshot(symbol=symbol).data())
    constituents = _dump(api.query_index_price_constituents(symbol=symbol).data())

    now_ms = int(mark["time"])
    constituent_rows = constituents.get("constituents") or []

    return {
        "schemaVersion": 2,
        "kind": "ordivon.capital.markets.binance-usdm-public-capture",
        "provider": "BINANCE",
        "sourceAuthority": "BINANCE_OFFICIAL_USDM_API",
        "officialSdk": "binance-sdk-derivatives-trading-usds-futures==17.4.0",
        "symbol": symbol,
        "observedAtMs": now_ms,
        "contract": contract,
        "markFunding": {
            "markPrice": mark.get("mark_price"),
            "indexPrice": mark.get("index_price"),
            "estimatedSettlePrice": mark.get("estimated_settle_price"),
            "lastFundingRate": mark.get("last_funding_rate"),
            "interestRate": mark.get("interest_rate"),
            "nextFundingTime": mark.get("next_funding_time"),
            "fundingInfo": funding,
        },
        "openInterest": oi,
        "book": _book_summary(book),
        "equityTradingSchedule": _current_and_next_session(schedule, now_ms),
        "adlRisk": adl,
        "insuranceFund": insurance,
        "indexConstituents": {
            "count": len(constituent_rows),
            "reported": constituent_rows,
            "hiddenPriceCount": sum(
                1 for row in constituent_rows if str(row.get("price")) == "-1"
            ),
        },
        "apiRateLimits": exchange.get("rate_limits") or [],
        "credentialsLoaded": False,
        "privateAccountDataUsed": False,
        "externalFinancialWriteAttempted": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="SNDKUSDT")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = capture(args.symbol)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
