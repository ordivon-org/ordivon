from __future__ import annotations

import argparse
import asyncio
import json
import os
import time
from decimal import Decimal
from pathlib import Path
from typing import Any

from websockets.asyncio.client import connect

from ordivon_capital.market.websocket_proxy_lifecycle import (
    NetworkV2ProxyClientConnection,
)

OKX_URL = "wss://ws.okx.com:8443/ws/v5/public"
BINANCE_URL = "wss://data-stream.binance.vision/stream?streams=btcusdt@ticker/ethusdt@ticker"


def network_v2_ws_proxies() -> tuple[str, str]:
    okx = os.environ.get("ORDIVON_MC_OKX_WS_PROXY")
    binance = os.environ.get("ORDIVON_MC_BINANCE_SPOT_WS_PROXY")
    if not okx or not binance:
        raise RuntimeError("Ordivon Capital Market-domain public streaming requires exact Network v2 OKX/Binance Spot WS proxy bindings")
    return okx, binance
KEYS = ("OKX:BTC", "OKX:ETH", "BINANCE:BTC", "BINANCE:ETH")
SOURCE_SPAN_MAX_MS = 1200
RECEIVE_SPAN_MAX_MS = 1200


def _d(v: Any) -> Decimal:
    return Decimal(str(v))


def _bps(num: Decimal, den: Decimal) -> str:
    return format((num / den) * Decimal(10_000), ".6f")


def evaluate_snapshot(
    latest: dict[str, dict[str, Any]],
    previous: dict[str, dict[str, Any]] | None = None,
    source_span_max_ms: int = SOURCE_SPAN_MAX_MS,
    receive_span_max_ms: int = RECEIVE_SPAN_MAX_MS,
) -> dict[str, Any]:
    missing = [k for k in KEYS if k not in latest]
    if missing:
        return {"qualified": False, "reason": "MISSING_STREAMS", "missing": missing}
    if previous is not None:
        stale = [k for k in KEYS if int(latest[k]["sourceTimeMs"]) <= int(previous[k]["sourceTimeMs"])]
        if stale:
            return {"qualified": False, "reason": "NOT_ALL_STREAMS_ADVANCED", "stale": stale}

    source_times = [int(latest[k]["sourceTimeMs"]) for k in KEYS]
    recv_times = [int(latest[k]["recvMonoNs"]) for k in KEYS]
    source_span = max(source_times) - min(source_times)
    receive_span = (max(recv_times) - min(recv_times)) / 1_000_000
    qualified = source_span <= source_span_max_ms and receive_span <= receive_span_max_ms

    comparisons: dict[str, Any] = {}
    for asset in ("BTC", "ETH"):
        oq = latest[f"OKX:{asset}"]
        bq = latest[f"BINANCE:{asset}"]
        omid = (_d(oq["bid"]) + _d(oq["ask"])) / Decimal(2)
        bmid = (_d(bq["bid"]) + _d(bq["ask"])) / Decimal(2)
        comparisons[asset] = {
            "okxBid": str(oq["bid"]),
            "okxAsk": str(oq["ask"]),
            "binanceBid": str(bq["bid"]),
            "binanceAsk": str(bq["ask"]),
            "sourceTimeDeltaMs": abs(int(oq["sourceTimeMs"]) - int(bq["sourceTimeMs"])),
            "receiveTimeDeltaMs": abs(int(oq["recvMonoNs"]) - int(bq["recvMonoNs"])) / 1_000_000,
            "midDifferenceBpsOkxMinusBinance": _bps(omid - bmid, bmid),
            "crossBuyBinanceSellOkxGrossBps": _bps(_d(oq["bid"]) - _d(bq["ask"]), _d(bq["ask"])),
            "crossBuyOkxSellBinanceGrossBps": _bps(_d(bq["bid"]) - _d(oq["ask"]), _d(oq["ask"])),
            "claimBoundary": "observation only; not an arbitrage, fill, fee, transfer, latency-to-venue, or execution claim",
        }

    return {
        "qualified": qualified,
        "reason": "PASS" if qualified else "SPAN_GATE_FAILED",
        "sourceTimeSpanMs": source_span,
        "receiveTimeSpanMs": receive_span,
        "sourceTimeSpanLimitMs": source_span_max_ms,
        "receiveTimeSpanLimitMs": receive_span_max_ms,
        "quotes": {k: dict(latest[k]) for k in KEYS},
        "comparisons": comparisons,
    }


class EstablishedPublicStreamLost(RuntimeError):
    pass


async def _okx_reader(queue: asyncio.Queue[tuple[str, dict[str, Any]]], proxy: str) -> None:
    async for ws in connect(
        OKX_URL,
        proxy=proxy,
        open_timeout=10,
        ping_interval=20,
        ping_timeout=20,
        close_timeout=5,
        max_size=2**20,
        create_connection=NetworkV2ProxyClientConnection,
    ):
        try:
            await ws.send(
                json.dumps(
                    {
                        "id": "mcr2",
                        "op": "subscribe",
                        "args": [
                            {"channel": "bbo-tbt", "instId": "BTC-USDT"},
                            {"channel": "bbo-tbt", "instId": "ETH-USDT"},
                        ],
                    },
                    separators=(",", ":"),
                )
            )
            async for raw in ws:
                if not isinstance(raw, str):
                    continue
                obj = json.loads(raw)
                if obj.get("event") == "error":
                    raise RuntimeError(f"OKX public stream error: {obj}")
                if "data" not in obj or obj.get("arg", {}).get("channel") != "bbo-tbt":
                    continue
                inst = obj["arg"].get("instId")
                asset = "BTC" if inst == "BTC-USDT" else "ETH" if inst == "ETH-USDT" else None
                if asset is None:
                    continue
                row = obj["data"][0]
                if not row.get("bids") or not row.get("asks") or not row.get("ts"):
                    continue
                event = {
                    "venue": "OKX",
                    "asset": asset,
                    "bid": row["bids"][0][0],
                    "ask": row["asks"][0][0],
                    "sourceTimeMs": int(row["ts"]),
                    "recvWallNs": time.time_ns(),
                    "recvMonoNs": time.monotonic_ns(),
                }
                await queue.put((f"OKX:{asset}", event))
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            raise EstablishedPublicStreamLost(
                f"OKX established public stream lost: {type(exc).__name__}: {exc}"
            ) from exc
        raise EstablishedPublicStreamLost("OKX established public stream ended")


async def _binance_reader(queue: asyncio.Queue[tuple[str, dict[str, Any]]], proxy: str) -> None:
    async for ws in connect(
        BINANCE_URL,
        proxy=proxy,
        open_timeout=10,
        ping_interval=20,
        ping_timeout=20,
        close_timeout=5,
        max_size=2**20,
        create_connection=NetworkV2ProxyClientConnection,
    ):
        try:
            async for raw in ws:
                if not isinstance(raw, str):
                    continue
                obj = json.loads(raw)
                row = obj.get("data", obj)
                symbol = row.get("s")
                asset = "BTC" if symbol == "BTCUSDT" else "ETH" if symbol == "ETHUSDT" else None
                if asset is None or not row.get("b") or not row.get("a") or not row.get("E"):
                    continue
                event = {
                    "venue": "BINANCE",
                    "asset": asset,
                    "bid": row["b"],
                    "ask": row["a"],
                    "sourceTimeMs": int(row["E"]),
                    "recvWallNs": time.time_ns(),
                    "recvMonoNs": time.monotonic_ns(),
                }
                await queue.put((f"BINANCE:{asset}", event))
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            raise EstablishedPublicStreamLost(
                f"Binance established public stream lost: {type(exc).__name__}: {exc}"
            ) from exc
        raise EstablishedPublicStreamLost("Binance established public stream ended")


async def capture_streaming(rounds: int = 3, warmup_rounds: int = 1, deadline_seconds: float = 25.0) -> dict[str, Any]:
    needed = rounds + warmup_rounds
    queue: asyncio.Queue[tuple[str, dict[str, Any]]] = asyncio.Queue()
    latest: dict[str, dict[str, Any]] = {}
    accepted: list[dict[str, Any]] = []
    previous: dict[str, dict[str, Any]] | None = None
    started_wall_ns = time.time_ns()
    started_mono_ns = time.monotonic_ns()
    deadline = time.monotonic() + deadline_seconds

    okx_proxy, binance_proxy = network_v2_ws_proxies()
    tasks = [
        asyncio.create_task(_okx_reader(queue, okx_proxy)),
        asyncio.create_task(_binance_reader(queue, binance_proxy)),
    ]
    try:
        while len(accepted) < needed:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            for task in tasks:
                if task.done():
                    exc = task.exception()
                    if exc is not None:
                        raise exc
            try:
                key, event = await asyncio.wait_for(
                    queue.get(), timeout=min(remaining, 5.0)
                )
            except TimeoutError:
                for task in tasks:
                    if task.done():
                        exc = task.exception()
                        if exc is not None:
                            raise exc
                continue
            latest[key] = event
            candidate = evaluate_snapshot(latest, previous)
            if candidate.get("qualified"):
                candidate["sequence"] = len(accepted) + 1
                candidate["role"] = "WARMUP" if len(accepted) < warmup_rounds else "MEASURED"
                accepted.append(candidate)
                previous = {k: dict(latest[k]) for k in KEYS}
    finally:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    ended_mono_ns = time.monotonic_ns()
    measured = accepted[warmup_rounds:]
    standing = "PASS_STREAMING_REPEATED_PUBLIC_SHADOW" if len(measured) == rounds else "PARTIAL_STREAMING_PUBLIC_SHADOW"
    return {
        "schemaVersion": 1,
        "kind": "ordivon.capital.market.crypto-public-streaming-r2",
        "standing": standing,
        "endpoints": {"okx": OKX_URL, "binance": BINANCE_URL},
        "networkV2Proxies": {"okx": okx_proxy, "binance": binance_proxy},
        "protocol": {
            "okxChannel": "bbo-tbt",
            "binanceStreams": ["btcusdt@ticker", "ethusdt@ticker"],
            "warmupRoundCount": warmup_rounds,
            "measuredRoundCountRequired": rounds,
            "sourceTimeSpanMaxMs": SOURCE_SPAN_MAX_MS,
            "receiveTimeSpanMaxMs": RECEIVE_SPAN_MAX_MS,
            "allStreamsMustAdvanceBetweenAcceptedSnapshots": True,
        },
        "sessionDurationMs": (ended_mono_ns - started_mono_ns) / 1_000_000,
        "sessionStartedWallNs": started_wall_ns,
        "acceptedSnapshotCount": len(accepted),
        "warmup": accepted[:warmup_rounds],
        "measured": measured,
        "allMeasuredQualified": len(measured) == rounds and all(x["qualified"] for x in measured),
        "samePersistentConnections": True,
        "hostWallClockUsedForAdmission": False,
        "brokerCredentialsUsed": False,
        "privateAccountDataUsed": False,
        "externalFinancialWritesAttempted": False,
        "demoExecutionAttempted": False,
        "liveExecutionAttempted": False,
        "claimBoundary": "bounded public streaming quote observation only; no alpha, arbitrage, fill, fee, transfer, ownership, or execution claim",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--warmup-rounds", type=int, default=1)
    ap.add_argument("--deadline-seconds", type=float, default=25.0)
    args = ap.parse_args()
    try:
        result = asyncio.run(capture_streaming(args.rounds, args.warmup_rounds, args.deadline_seconds))
        rc = 0 if result["standing"] == "PASS_STREAMING_REPEATED_PUBLIC_SHADOW" else 2
    except Exception as exc:
        result = {
            "schemaVersion": 1,
            "kind": "ordivon.capital.market.crypto-public-streaming-r2",
            "standing": "STREAMING_SESSION_FAILED",
            "error": f"{type(exc).__name__}: {exc}",
            "brokerCredentialsUsed": False,
            "privateAccountDataUsed": False,
            "externalFinancialWritesAttempted": False,
            "demoExecutionAttempted": False,
            "liveExecutionAttempted": False,
        }
        rc = 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
