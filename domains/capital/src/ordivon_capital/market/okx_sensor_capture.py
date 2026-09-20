from __future__ import annotations

import argparse
import concurrent.futures
import json
import subprocess
import time
from decimal import Decimal
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from .market_sensors import open_interest_change, repeated_microstructure

BASE_URL = "https://openapi.okx.com"
ENDPOINTS = {
    "openInterest": "/api/v5/public/open-interest",
    "books": "/api/v5/market/books",
    "trades": "/api/v5/market/trades",
    "ticker": "/api/v5/market/ticker",
    "openInterestHistory": "/api/v5/rubik/stat/contracts/open-interest-history",
}


class OkxSensorCaptureError(RuntimeError):
    pass


def _d(value: Any, label: str) -> Decimal:
    try:
        return Decimal(str(value))
    except Exception as exc:
        raise OkxSensorCaptureError(f"invalid decimal for {label}") from exc


def _okx_rows(payload: Any, label: str) -> list[dict[str, Any]]:
    if not isinstance(payload, dict) or payload.get("code") != "0":
        raise OkxSensorCaptureError(f"{label}: OKX response code is not zero")
    rows = payload.get("data")
    if not isinstance(rows, list) or not rows:
        raise OkxSensorCaptureError(f"{label}: OKX data rows missing")
    if not all(isinstance(x, dict) for x in rows):
        raise OkxSensorCaptureError(f"{label}: OKX data row is not an object")
    return rows


def parse_round(
    *,
    instrument_id: str,
    observed_at_ms: int,
    open_interest_payload: dict[str, Any],
    books_payload: dict[str, Any],
    trades_payload: dict[str, Any],
    ticker_payload: dict[str, Any],
) -> dict[str, Any]:
    instrument_id = instrument_id.strip()
    if not instrument_id:
        raise OkxSensorCaptureError("instrument_id is required")
    if not isinstance(observed_at_ms, int) or observed_at_ms < 0:
        raise OkxSensorCaptureError("observed_at_ms must be a non-negative integer")

    oi_row = _okx_rows(open_interest_payload, "openInterest")[0]
    book_row = _okx_rows(books_payload, "books")[0]
    trade_rows = _okx_rows(trades_payload, "trades")
    ticker_row = _okx_rows(ticker_payload, "ticker")[0]

    for label, row in (("openInterest", oi_row), ("ticker", ticker_row)):
        if row.get("instId") not in (None, instrument_id):
            raise OkxSensorCaptureError(f"{label}: instrument mismatch")

    oi_usd = _d(oi_row.get("oiUsd"), "openInterest.oiUsd")
    if oi_usd < 0:
        raise OkxSensorCaptureError("open interest cannot be negative")

    bids = book_row.get("bids")
    asks = book_row.get("asks")
    if not isinstance(bids, list) or not bids or not isinstance(asks, list) or not asks:
        raise OkxSensorCaptureError("books: bids/asks missing")

    try:
        bid_total = sum((_d(row[1], "books.bidSize") for row in bids), Decimal("0"))
        ask_total = sum((_d(row[1], "books.askSize") for row in asks), Decimal("0"))
        best_bid = _d(bids[0][0], "books.bestBid")
        best_ask = _d(asks[0][0], "books.bestAsk")
    except (IndexError, TypeError) as exc:
        raise OkxSensorCaptureError("books: malformed level") from exc

    depth_total = bid_total + ask_total
    if depth_total <= 0:
        raise OkxSensorCaptureError("books: aggregate depth must be positive")
    if best_bid <= 0 or best_ask <= 0 or best_ask < best_bid:
        raise OkxSensorCaptureError("books: invalid best bid/ask")

    book_imbalance = (bid_total - ask_total) / depth_total
    midpoint = (best_bid + best_ask) / Decimal("2")
    spread_bps = (best_ask - best_bid) / midpoint * Decimal("10000")

    buy_size = Decimal("0")
    sell_size = Decimal("0")
    max_trade_ts = 0
    for row in trade_rows:
        if row.get("instId") not in (None, instrument_id):
            raise OkxSensorCaptureError("trades: instrument mismatch")
        size = _d(row.get("sz"), "trades.sz")
        if size < 0:
            raise OkxSensorCaptureError("trades: size cannot be negative")
        side = row.get("side")
        if side == "buy":
            buy_size += size
        elif side == "sell":
            sell_size += size
        else:
            raise OkxSensorCaptureError("trades: side must be buy or sell")
        if row.get("ts") is not None:
            max_trade_ts = max(max_trade_ts, int(row["ts"]))

    total_trade_size = buy_size + sell_size
    trade_buy_share = buy_size / total_trade_size if total_trade_size > 0 else Decimal("0.5")

    last = _d(ticker_row.get("last"), "ticker.last")
    if last <= 0:
        raise OkxSensorCaptureError("ticker.last must be positive")

    return {
        "instrumentId": instrument_id,
        "observedAtMs": observed_at_ms,
        "openInterest": {
            "instrumentId": instrument_id,
            "observedAtMs": observed_at_ms,
            "openInterestUsd": str(oi_usd),
            "sourceTimeMs": int(oi_row["ts"]) if oi_row.get("ts") is not None else None,
        },
        "microstructure": {
            "instrumentId": instrument_id,
            "observedAtMs": observed_at_ms,
            "bookImbalance": str(book_imbalance),
            "tradeBuyShare": str(trade_buy_share),
            "spreadBps": str(spread_bps),
            "bookSourceTimeMs": int(book_row["ts"]) if book_row.get("ts") is not None else None,
            "latestTradeSourceTimeMs": max_trade_ts or None,
            "bidDepthSize": str(bid_total),
            "askDepthSize": str(ask_total),
            "recentBuySize": str(buy_size),
            "recentSellSize": str(sell_size),
        },
        "marketReference": {
            "instrumentId": instrument_id,
            "observedAtMs": observed_at_ms,
            "last": str(last),
            "bid": ticker_row.get("bidPx"),
            "ask": ticker_row.get("askPx"),
            "tickerSourceTimeMs": int(ticker_row["ts"]) if ticker_row.get("ts") is not None else None,
        },
    }


def parse_open_interest_history(
    *,
    instrument_id: str,
    payload: dict[str, Any],
) -> list[dict[str, Any]]:
    if not isinstance(payload, dict) or payload.get("code") != "0":
        raise OkxSensorCaptureError("openInterestHistory: OKX response code is not zero")
    rows = payload.get("data")
    if not isinstance(rows, list) or len(rows) < 2:
        raise OkxSensorCaptureError("openInterestHistory: at least two rows are required")

    result: list[dict[str, Any]] = []
    for i, row in enumerate(rows):
        if not isinstance(row, list) or len(row) < 4:
            raise OkxSensorCaptureError(f"openInterestHistory[{i}]: malformed row")
        try:
            ts = int(row[0])
        except (TypeError, ValueError) as exc:
            raise OkxSensorCaptureError(f"openInterestHistory[{i}]: invalid timestamp") from exc
        oi_usd = _d(row[3], f"openInterestHistory[{i}].oiUsd")
        if ts < 0 or oi_usd < 0:
            raise OkxSensorCaptureError("open-interest history values must be non-negative")
        result.append({
            "instrumentId": instrument_id,
            "observedAtMs": ts,
            "openInterestUsd": str(oi_usd),
        })

    result.sort(key=lambda x: x["observedAtMs"])
    for previous, current in zip(result, result[1:]):
        if current["observedAtMs"] <= previous["observedAtMs"]:
            raise OkxSensorCaptureError("open-interest history timestamps must be unique")
    return result


def completed_open_interest_change(
    *,
    instrument_id: str,
    payload: dict[str, Any],
    period_ms: int,
    as_of_ms: int,
) -> dict[str, Any]:
    if not isinstance(period_ms, int) or period_ms <= 0:
        raise OkxSensorCaptureError("period_ms must be positive")
    if not isinstance(as_of_ms, int) or as_of_ms < 0:
        raise OkxSensorCaptureError("as_of_ms must be non-negative")

    rows = parse_open_interest_history(instrument_id=instrument_id, payload=payload)
    completed = [row for row in rows if row["observedAtMs"] + period_ms <= as_of_ms]
    if len(completed) < 2:
        raise OkxSensorCaptureError("fewer than two completed open-interest history buckets")

    change = open_interest_change(completed[-2:], minimum_span_ms=period_ms)
    change["historyPeriodMs"] = period_ms
    change["completedBucketsOnly"] = True
    change["asOfMs"] = as_of_ms
    return change


def _request(proxy: str, path: str, params: dict[str, str]) -> dict[str, Any]:
    url = BASE_URL + path + "?" + urlencode(params)
    proc = subprocess.run(
        [
            "/usr/bin/curl",
            "-fsS",
            "--proxy",
            proxy,
            "--connect-timeout",
            "4",
            "--max-time",
            "15",
            url,
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise OkxSensorCaptureError(f"curl failed rc={proc.returncode}: {proc.stderr.strip()}")
    try:
        value = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise OkxSensorCaptureError("OKX returned invalid JSON") from exc
    if not isinstance(value, dict):
        raise OkxSensorCaptureError("OKX response must be an object")
    return value


def capture_round(*, instrument_id: str, proxy: str) -> dict[str, Any]:
    requests = {
        "openInterest": (
            ENDPOINTS["openInterest"],
            {"instType": "SWAP", "instId": instrument_id},
        ),
        "books": (ENDPOINTS["books"], {"instId": instrument_id, "sz": "50"}),
        "trades": (ENDPOINTS["trades"], {"instId": instrument_id, "limit": "100"}),
        "ticker": (ENDPOINTS["ticker"], {"instId": instrument_id}),
    }

    started_mono_ns = time.monotonic_ns()
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(requests)) as pool:
        futures = {
            name: pool.submit(_request, proxy, path, params)
            for name, (path, params) in requests.items()
        }
        payloads = {name: future.result() for name, future in futures.items()}
    ended_mono_ns = time.monotonic_ns()
    observed_at_ms = time.time_ns() // 1_000_000

    parsed = parse_round(
        instrument_id=instrument_id,
        observed_at_ms=observed_at_ms,
        open_interest_payload=payloads["openInterest"],
        books_payload=payloads["books"],
        trades_payload=payloads["trades"],
        ticker_payload=payloads["ticker"],
    )
    parsed["captureDurationMs"] = (ended_mono_ns - started_mono_ns) / 1_000_000
    return parsed


def capture_window(
    *,
    instrument_id: str,
    proxy: str,
    rounds: int = 5,
    interval_seconds: float = 1.0,
) -> dict[str, Any]:
    if not instrument_id.strip():
        raise OkxSensorCaptureError("instrument_id is required")
    if not proxy.startswith("http://127.0.0.1:"):
        raise OkxSensorCaptureError("proxy must be a loopback Network v2 HTTP proxy")
    if not isinstance(rounds, int) or rounds < 3 or rounds > 60:
        raise OkxSensorCaptureError("rounds must be in [3, 60]")
    if interval_seconds < 0 or interval_seconds > 60:
        raise OkxSensorCaptureError("interval_seconds must be in [0, 60]")

    captured: list[dict[str, Any]] = []
    for i in range(rounds):
        row = capture_round(instrument_id=instrument_id, proxy=proxy)
        if captured and row["observedAtMs"] <= captured[-1]["observedAtMs"]:
            row["observedAtMs"] = captured[-1]["observedAtMs"] + 1
            row["openInterest"]["observedAtMs"] = row["observedAtMs"]
            row["microstructure"]["observedAtMs"] = row["observedAtMs"]
            row["marketReference"]["observedAtMs"] = row["observedAtMs"]
        captured.append(row)
        if i + 1 < rounds and interval_seconds:
            time.sleep(interval_seconds)

    capture_oi = open_interest_change([x["openInterest"] for x in captured])
    micro = repeated_microstructure(
        [x["microstructure"] for x in captured],
        minimum_samples=3,
    )

    as_of_ms = captured[-1]["observedAtMs"]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        history_futures = {
            "5m": pool.submit(
                _request,
                proxy,
                ENDPOINTS["openInterestHistory"],
                {"instId": instrument_id, "period": "5m"},
            ),
            "1H": pool.submit(
                _request,
                proxy,
                ENDPOINTS["openInterestHistory"],
                {"instId": instrument_id, "period": "1H"},
            ),
        }
        history_payloads = {name: future.result() for name, future in history_futures.items()}

    oi_5m = completed_open_interest_change(
        instrument_id=instrument_id,
        payload=history_payloads["5m"],
        period_ms=5 * 60 * 1000,
        as_of_ms=as_of_ms,
    )
    oi_1h = completed_open_interest_change(
        instrument_id=instrument_id,
        payload=history_payloads["1H"],
        period_ms=60 * 60 * 1000,
        as_of_ms=as_of_ms,
    )

    return {
        "schemaVersion": 1,
        "kind": "ordivon.capital.market.okx-public-sensor-window",
        "standing": "PASS_OKX_REPEATED_SENSOR_WINDOW",
        "instrumentId": instrument_id,
        "sampleCount": len(captured),
        "proxyAuthorityClass": "NETWORK_V2_OKX_PUBLIC_REST",
        "samples": captured,
        "openInterestChangeCaptureWindow": capture_oi,
        "openInterestChange5mCompleted": oi_5m,
        "openInterestChange1HCompleted": oi_1h,
        "repeatedMicrostructure": micro,
        "latestMarketReference": captured[-1]["marketReference"],
        "brokerCredentialsUsed": False,
        "privateAccountDataUsed": False,
        "externalFinancialWritesAttempted": False,
        "demoExecutionAttempted": False,
        "liveExecutionAttempted": False,
        "claimBoundary": "public read-only repeated observation; no forecast, causal, fill, order, or execution claim",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instrument", required=True)
    parser.add_argument("--proxy", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--rounds", type=int, default=5)
    parser.add_argument("--interval-seconds", type=float, default=1.0)
    args = parser.parse_args()

    result = capture_window(
        instrument_id=args.instrument,
        proxy=args.proxy,
        rounds=args.rounds,
        interval_seconds=args.interval_seconds,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "standing": result["standing"],
        "instrumentId": result["instrumentId"],
        "sampleCount": result["sampleCount"],
        "output": str(args.output),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
