from __future__ import annotations

import argparse
import asyncio
from decimal import Decimal
import json
from pathlib import Path
import time
from typing import Any

import aiohttp

OKX_URL = "wss://ws.okx.com:8443/ws/v5/public"
BINANCE_URL = "wss://data-stream.binance.vision/stream?streams=btcusdt@ticker/ethusdt@ticker"
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


async def _okx_reader(session: aiohttp.ClientSession, queue: asyncio.Queue[tuple[str, dict[str, Any]]]) -> None:
    async with session.ws_connect(OKX_URL, heartbeat=20, receive_timeout=15) as ws:
        await ws.send_json({
            "id": "mcr2",
            "op": "subscribe",
            "args": [
                {"channel": "bbo-tbt", "instId": "BTC-USDT"},
                {"channel": "bbo-tbt", "instId": "ETH-USDT"},
            ],
        })
        async for msg in ws:
            if msg.type != aiohttp.WSMsgType.TEXT:
                continue
            obj = json.loads(msg.data)
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
                "venue": "OKX", "asset": asset,
                "bid": row["bids"][0][0], "ask": row["asks"][0][0],
                "sourceTimeMs": int(row["ts"]),
                "recvWallNs": time.time_ns(), "recvMonoNs": time.monotonic_ns(),
            }
            await queue.put((f"OKX:{asset}", event))


async def _binance_reader(session: aiohttp.ClientSession, queue: asyncio.Queue[tuple[str, dict[str, Any]]]) -> None:
    async with session.ws_connect(BINANCE_URL, heartbeat=20, receive_timeout=15) as ws:
        async for msg in ws:
            if msg.type != aiohttp.WSMsgType.TEXT:
                continue
            obj = json.loads(msg.data)
            row = obj.get("data", obj)
            symbol = row.get("s")
            asset = "BTC" if symbol == "BTCUSDT" else "ETH" if symbol == "ETHUSDT" else None
            if asset is None or not row.get("b") or not row.get("a") or not row.get("E"):
                continue
            event = {
                "venue": "BINANCE", "asset": asset,
                "bid": row["b"], "ask": row["a"],
                "sourceTimeMs": int(row["E"]),
                "recvWallNs": time.time_ns(), "recvMonoNs": time.monotonic_ns(),
            }
            await queue.put((f"BINANCE:{asset}", event))


async def capture_streaming(rounds: int = 3, warmup_rounds: int = 1, deadline_seconds: float = 25.0) -> dict[str, Any]:
    needed = rounds + warmup_rounds
    queue: asyncio.Queue[tuple[str, dict[str, Any]]] = asyncio.Queue()
    latest: dict[str, dict[str, Any]] = {}
    accepted: list[dict[str, Any]] = []
    previous: dict[str, dict[str, Any]] | None = None
    timeout = aiohttp.ClientTimeout(total=None, connect=10, sock_connect=10, sock_read=20)
    started_wall_ns = time.time_ns()
    started_mono_ns = time.monotonic_ns()
    deadline = time.monotonic() + deadline_seconds

    async with aiohttp.ClientSession(timeout=timeout) as session:
        tasks = [
            asyncio.create_task(_okx_reader(session, queue)),
            asyncio.create_task(_binance_reader(session, queue)),
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
                key, event = await asyncio.wait_for(queue.get(), timeout=min(remaining, 5.0))
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
        "kind": "ordivon.market-capital.crypto-public-streaming-r2",
        "standing": standing,
        "endpoints": {"okx": OKX_URL, "binance": BINANCE_URL},
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
            "kind": "ordivon.market-capital.crypto-public-streaming-r2",
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
