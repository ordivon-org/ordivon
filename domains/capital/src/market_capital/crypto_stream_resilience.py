from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
import time
from typing import Any

import aiohttp

from crypto_public_streaming import BINANCE_URL, KEYS, OKX_URL, evaluate_snapshot


class InjectedDisconnect(RuntimeError):
    pass


async def _okx_supervisor(
    session: aiohttp.ClientSession,
    queue: asyncio.Queue[tuple[str, dict[str, Any]]],
    control: asyncio.Queue[dict[str, Any]],
    inject_now: asyncio.Event,
    target_venue: str,
) -> None:
    generation = 0
    injected = False
    while True:
        generation += 1
        try:
            async with session.ws_connect(OKX_URL, heartbeat=20, receive_timeout=15) as ws:
                await control.put({"type": "CONNECTED", "venue": "OKX", "generation": generation, "monoNs": time.monotonic_ns()})
                await ws.send_json({
                    "id": "mcr3",
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
                        "venue": "OKX", "asset": asset, "generation": generation,
                        "bid": row["bids"][0][0], "ask": row["asks"][0][0],
                        "sourceTimeMs": int(row["ts"]),
                        "recvWallNs": time.time_ns(), "recvMonoNs": time.monotonic_ns(),
                    }
                    await queue.put((f"OKX:{asset}", event))
                    if target_venue == "OKX" and inject_now.is_set() and not injected:
                        injected = True
                        mono = time.monotonic_ns()
                        await control.put({"type": "INJECTED_DISCONNECT", "venue": "OKX", "generation": generation, "monoNs": mono})
                        await ws.close()
                        raise InjectedDisconnect("OKX synthetic public-stream disconnect")
        except InjectedDisconnect:
            await asyncio.sleep(0.1)
            continue
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            await control.put({"type": "CONNECTION_ERROR", "venue": "OKX", "generation": generation, "monoNs": time.monotonic_ns(), "error": f"{type(exc).__name__}: {exc}"})
            await asyncio.sleep(min(2.0, 0.25 * generation))


async def _binance_supervisor(
    session: aiohttp.ClientSession,
    queue: asyncio.Queue[tuple[str, dict[str, Any]]],
    control: asyncio.Queue[dict[str, Any]],
    inject_now: asyncio.Event,
    target_venue: str,
) -> None:
    generation = 0
    injected = False
    while True:
        generation += 1
        try:
            async with session.ws_connect(BINANCE_URL, heartbeat=20, receive_timeout=15) as ws:
                await control.put({"type": "CONNECTED", "venue": "BINANCE", "generation": generation, "monoNs": time.monotonic_ns()})
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
                        "venue": "BINANCE", "asset": asset, "generation": generation,
                        "bid": row["b"], "ask": row["a"],
                        "sourceTimeMs": int(row["E"]),
                        "recvWallNs": time.time_ns(), "recvMonoNs": time.monotonic_ns(),
                    }
                    await queue.put((f"BINANCE:{asset}", event))
                    if target_venue == "BINANCE" and inject_now.is_set() and not injected:
                        injected = True
                        mono = time.monotonic_ns()
                        await control.put({"type": "INJECTED_DISCONNECT", "venue": "BINANCE", "generation": generation, "monoNs": mono})
                        await ws.close()
                        raise InjectedDisconnect("Binance synthetic public-stream disconnect")
        except InjectedDisconnect:
            await asyncio.sleep(0.1)
            continue
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            await control.put({"type": "CONNECTION_ERROR", "venue": "BINANCE", "generation": generation, "monoNs": time.monotonic_ns(), "error": f"{type(exc).__name__}: {exc}"})
            await asyncio.sleep(min(2.0, 0.25 * generation))


def _target_keys(venue: str) -> tuple[str, str]:
    return (f"{venue}:BTC", f"{venue}:ETH")


async def qualify_reconnect(target_venue: str, measured_rounds: int = 3, deadline_seconds: float = 35.0) -> dict[str, Any]:
    target_venue = target_venue.upper()
    if target_venue not in {"OKX", "BINANCE"}:
        raise ValueError("target_venue must be OKX or BINANCE")

    queue: asyncio.Queue[tuple[str, dict[str, Any]]] = asyncio.Queue()
    control: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
    inject_now = asyncio.Event()
    latest: dict[str, dict[str, Any]] = {}
    previous: dict[str, dict[str, Any]] | None = None
    warmup: dict[str, Any] | None = None
    recovery: dict[str, Any] | None = None
    measured: list[dict[str, Any]] = []
    controls: list[dict[str, Any]] = []
    injected_mono: int | None = None
    reconnected_mono: int | None = None
    reconnected_generation: int | None = None
    timeout = aiohttp.ClientTimeout(total=None, connect=10, sock_connect=10, sock_read=20)
    deadline = time.monotonic() + deadline_seconds
    started = time.monotonic_ns()

    async with aiohttp.ClientSession(timeout=timeout) as session:
        tasks = [
            asyncio.create_task(_okx_supervisor(session, queue, control, inject_now, target_venue)),
            asyncio.create_task(_binance_supervisor(session, queue, control, inject_now, target_venue)),
        ]
        try:
            while len(measured) < measured_rounds and time.monotonic() < deadline:
                for task in tasks:
                    if task.done():
                        exc = task.exception()
                        if exc:
                            raise exc
                while True:
                    try:
                        event = control.get_nowait()
                    except asyncio.QueueEmpty:
                        break
                    controls.append(event)
                    if event["type"] == "INJECTED_DISCONNECT" and event["venue"] == target_venue:
                        injected_mono = int(event["monoNs"])
                    if event["type"] == "CONNECTED" and event["venue"] == target_venue and int(event["generation"]) >= 2:
                        reconnected_mono = int(event["monoNs"])
                        reconnected_generation = int(event["generation"])

                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                try:
                    key, quote = await asyncio.wait_for(queue.get(), timeout=min(remaining, 3.0))
                except asyncio.TimeoutError:
                    continue
                latest[key] = quote

                candidate = evaluate_snapshot(latest, previous)
                if warmup is None:
                    if candidate.get("qualified"):
                        candidate["role"] = "WARMUP_BEFORE_INJECTION"
                        warmup = candidate
                        previous = {k: dict(latest[k]) for k in KEYS}
                        inject_now.set()
                    continue

                if recovery is None:
                    if injected_mono is None or reconnected_mono is None or reconnected_generation is None:
                        continue
                    target_keys = _target_keys(target_venue)
                    if not all(k in latest and int(latest[k].get("generation", 0)) >= reconnected_generation for k in target_keys):
                        continue
                    candidate = evaluate_snapshot(latest, previous)
                    if candidate.get("qualified"):
                        candidate["role"] = "RECOVERY"
                        recovery = candidate
                        previous = {k: dict(latest[k]) for k in KEYS}
                    continue

                candidate = evaluate_snapshot(latest, previous)
                if candidate.get("qualified"):
                    candidate["role"] = "MEASURED_AFTER_RECOVERY"
                    candidate["sequence"] = len(measured) + 1
                    measured.append(candidate)
                    previous = {k: dict(latest[k]) for k in KEYS}
        finally:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)

    # Drain final control events so evidence includes the reconnect event even if data arrived immediately.
    while True:
        try:
            event = control.get_nowait()
        except asyncio.QueueEmpty:
            break
        controls.append(event)
        if event["type"] == "INJECTED_DISCONNECT" and event["venue"] == target_venue and injected_mono is None:
            injected_mono = int(event["monoNs"])
        if event["type"] == "CONNECTED" and event["venue"] == target_venue and int(event["generation"]) >= 2 and reconnected_mono is None:
            reconnected_mono = int(event["monoNs"])
            reconnected_generation = int(event["generation"])

    reconnect_latency_ms = None
    if injected_mono is not None and reconnected_mono is not None:
        reconnect_latency_ms = (reconnected_mono - injected_mono) / 1_000_000
    passed = warmup is not None and recovery is not None and len(measured) == measured_rounds and reconnect_latency_ms is not None
    return {
        "schemaVersion": 1,
        "kind": "ordivon.market-capital.crypto-stream-reconnect-qualification",
        "standing": "PASS_PUBLIC_STREAM_RECONNECT" if passed else "PARTIAL_PUBLIC_STREAM_RECONNECT",
        "targetVenue": target_venue,
        "injectedDisconnect": True,
        "reconnectLatencyMs": reconnect_latency_ms,
        "reconnectedGeneration": reconnected_generation,
        "warmup": warmup,
        "recovery": recovery,
        "measured": measured,
        "measuredRoundCountRequired": measured_rounds,
        "sessionDurationMs": (time.monotonic_ns() - started) / 1_000_000,
        "controlEvents": controls,
        "hostWallClockUsedForAdmission": False,
        "brokerCredentialsUsed": False,
        "privateAccountDataUsed": False,
        "externalFinancialWritesAttempted": False,
        "demoExecutionAttempted": False,
        "liveExecutionAttempted": False,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target-venue", required=True, choices=["OKX", "BINANCE"])
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--measured-rounds", type=int, default=3)
    ap.add_argument("--deadline-seconds", type=float, default=35.0)
    args = ap.parse_args()
    try:
        result = asyncio.run(qualify_reconnect(args.target_venue, args.measured_rounds, args.deadline_seconds))
        rc = 0 if result["standing"] == "PASS_PUBLIC_STREAM_RECONNECT" else 2
    except Exception as exc:
        result = {
            "schemaVersion": 1,
            "kind": "ordivon.market-capital.crypto-stream-reconnect-qualification",
            "standing": "STREAM_RECONNECT_SESSION_FAILED",
            "targetVenue": args.target_venue,
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
