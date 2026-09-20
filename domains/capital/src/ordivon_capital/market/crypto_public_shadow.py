from __future__ import annotations

import argparse
import hashlib
import json
from decimal import Decimal
from pathlib import Path
from typing import Any

PRICE_KEYS = ("okx_btc", "okx_eth", "binance_books")


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def _mid_ns(req: dict[str, Any], clock: str) -> Decimal:
    return (Decimal(req[f"{clock}StartNs"]) + Decimal(req[f"{clock}EndNs"])) / Decimal(2)


def _ms(ns: Decimal) -> Decimal:
    return ns / Decimal(1_000_000)


def _d(value: Any) -> Decimal:
    return Decimal(str(value))


def _okx_quote(capture: dict[str, Any], key: str) -> dict[str, Any]:
    rows = capture["requests"][key]["payload"].get("data", [])
    if len(rows) != 1:
        raise RuntimeError(f"{key}: expected one OKX ticker row")
    row = rows[0]
    if not row.get("bidPx") or not row.get("askPx") or not row.get("ts"):
        raise RuntimeError(f"{key}: incomplete OKX quote")
    return {
        "bid": _d(row["bidPx"]),
        "ask": _d(row["askPx"]),
        "sourceTimeMs": int(row["ts"]),
    }


def _binance_quotes(capture: dict[str, Any]) -> dict[str, dict[str, Decimal]]:
    rows = capture["requests"]["binance_books"]["payload"]
    if not isinstance(rows, list):
        raise RuntimeError("binance_books: expected list")
    result: dict[str, dict[str, Decimal]] = {}
    for row in rows:
        symbol = row.get("symbol")
        if symbol in {"BTCUSDT", "ETHUSDT"}:
            result[symbol] = {"bid": _d(row["bidPrice"]), "ask": _d(row["askPrice"])}
    if set(result) != {"BTCUSDT", "ETHUSDT"}:
        raise RuntimeError("binance_books: BTCUSDT/ETHUSDT missing")
    return result


def _bps(numerator: Decimal, denominator: Decimal) -> str:
    return format((numerator / denominator) * Decimal(10_000), ".6f")


def analyze(capture_path: Path, transport_binding_path: Path) -> dict[str, Any]:
    capture = _load(capture_path)
    binding = _load(transport_binding_path)

    if capture.get("kind") != "ordivon.capital.market.crypto-public-rest-capture":
        raise RuntimeError("unexpected capture kind")
    for field in ("credentialsUsed", "privateAccountDataUsed", "externalFinancialWritesAttempted"):
        if capture.get(field) is not False:
            raise RuntimeError(f"{field} must remain false")

    requests = capture["requests"]
    if not set(PRICE_KEYS).issubset(requests):
        raise RuntimeError("price requests missing")

    starts = [int(requests[k]["monotonicStartNs"]) for k in PRICE_KEYS]
    ends = [int(requests[k]["monotonicEndNs"]) for k in PRICE_KEYS]
    intersection_ns = min(ends) - max(starts)
    union_ns = max(ends) - min(starts)
    max_rtt_ms = max(Decimal(str(requests[k]["durationMs"])) for k in PRICE_KEYS)

    okx_time_rows = requests["okx_time"]["payload"].get("data", [])
    if len(okx_time_rows) != 1:
        raise RuntimeError("OKX server time unavailable")
    okx_server_ms = Decimal(str(okx_time_rows[0]["ts"]))
    binance_server_ms = Decimal(str(requests["binance_time"]["payload"]["serverTime"]))
    okx_local_mid_ms = _ms(_mid_ns(requests["okx_time"], "wall"))
    binance_local_mid_ms = _ms(_mid_ns(requests["binance_time"], "wall"))
    okx_offset_ms = okx_server_ms - okx_local_mid_ms
    binance_offset_ms = binance_server_ms - binance_local_mid_ms
    venue_clock_agreement_ms = abs(okx_offset_ms - binance_offset_ms)
    host_clock_offset_abs_ms = max(abs(okx_offset_ms), abs(binance_offset_ms))

    bounded_comparison = (
        intersection_ns > 0
        and max_rtt_ms <= Decimal("1500")
        and venue_clock_agreement_ms <= Decimal("250")
    )
    host_clock_good_for_private = host_clock_offset_abs_ms <= Decimal("1000")

    okx = {
        "BTC": _okx_quote(capture, "okx_btc"),
        "ETH": _okx_quote(capture, "okx_eth"),
    }
    binance = _binance_quotes(capture)
    pairs = {"BTC": "BTCUSDT", "ETH": "ETHUSDT"}
    comparisons: dict[str, Any] = {}
    if bounded_comparison:
        for asset, bsymbol in pairs.items():
            oq = okx[asset]
            bq = binance[bsymbol]
            omid = (oq["bid"] + oq["ask"]) / Decimal(2)
            bmid = (bq["bid"] + bq["ask"]) / Decimal(2)
            comparisons[asset] = {
                "okxBid": str(oq["bid"]),
                "okxAsk": str(oq["ask"]),
                "binanceBid": str(bq["bid"]),
                "binanceAsk": str(bq["ask"]),
                "midDifferenceBpsOkxMinusBinance": _bps(omid - bmid, bmid),
                "crossBuyBinanceSellOkxGrossBps": _bps(oq["bid"] - bq["ask"], bq["ask"]),
                "crossBuyOkxSellBinanceGrossBps": _bps(bq["bid"] - oq["ask"], oq["ask"]),
            }

    if binding.get("kind") != "ordivon.capital.market.network-v2-public-data-binding":
        raise RuntimeError("unexpected Network v2 transport binding")
    if binding.get("directFallback") is not False or binding.get("publicReadOnly") is not True:
        raise RuntimeError("Network v2 transport binding is not fail-closed public-read-only")
    for field in ("brokerCredentialsUsed", "privateAccountDataUsed", "externalFinancialWritesAttempted", "demoExecutionAttempted", "liveExecutionAttempted"):
        if binding.get(field) is not False:
            raise RuntimeError(f"transport binding {field} must remain false")
    expected_authorities={"okxRest","okxWs","binanceSpotRest","binanceSpotWs"}
    if set(binding.get("authorities") or {}) != expected_authorities:
        raise RuntimeError("Network v2 transport binding does not contain the exact four public-data authorities")

    standing = (
        "PASS_BOUNDED_DUAL_VENUE_PUBLIC_SHADOW_HOST_CLOCK_WARN"
        if bounded_comparison and not host_clock_good_for_private
        else "PASS_BOUNDED_DUAL_VENUE_PUBLIC_SHADOW"
        if bounded_comparison
        else "PARTIAL_PUBLIC_CAPTURE_NO_CROSS_VENUE_CLAIM"
    )

    return {
        "schemaVersion": 1,
        "kind": "ordivon.capital.market.crypto-public-shadow-observation",
        "componentId": "public-market-risk-data-quality",
        "standing": standing,
        "transport": {
            "kind": "network-v2-exact-authority-set",
            "bindingDigest": binding.get("bindingDigest"),
            "providerSelection": binding.get("providerSelection"),
            "directFallback": False,
            "authorityDigests": {k:v.get("authorityDigest") for k,v in sorted(binding["authorities"].items())},
            "pointInTimeOnly": True,
        },
        "capture": {
            "rawSha256": hashlib.sha256(capture_path.read_bytes()).hexdigest(),
            "priceRequestIntersectionMs": float(Decimal(intersection_ns) / Decimal(1_000_000)),
            "priceRequestUnionMs": float(Decimal(union_ns) / Decimal(1_000_000)),
            "maxPriceRequestRttMs": float(max_rtt_ms),
            "boundedContemporaneousComparisonAllowed": bounded_comparison,
        },
        "clockQuality": {
            "okxServerMinusLocalMidpointMs": float(okx_offset_ms),
            "binanceServerMinusLocalMidpointMs": float(binance_offset_ms),
            "venueClockAgreementMs": float(venue_clock_agreement_ms),
            "hostClockOffsetAbsMaxMs": float(host_clock_offset_abs_ms),
            "hostClockWithinPrivateExecutionGate1000Ms": host_clock_good_for_private,
            "privateExecutionConsequence": "BLOCK until host clock is within gate; public shadow uses monotonic capture intervals",
        },
        "quotes": {
            "OKX": {
                "BTC-USDT": {k: str(v) for k, v in okx["BTC"].items()},
                "ETH-USDT": {k: str(v) for k, v in okx["ETH"].items()},
            },
            "BINANCE": {
                "BTCUSDT": {k: str(v) for k, v in binance["BTCUSDT"].items()},
                "ETHUSDT": {k: str(v) for k, v in binance["ETHUSDT"].items()},
            },
        },
        "comparisons": comparisons,
        "riskDataQuality": {
            "frameworkReference": "BCBS239_PROPORTIONAL_REFERENCE",
            "sourceAuthorityBound": True,
            "requiredInputsComplete": True,
            "comparisonScope": "BOUNDED_CONTEMPORANEOUS_BBO",
            "timeliness": {
                "priceRequestIntersectionMs": float(Decimal(intersection_ns) / Decimal(1_000_000)),
                "priceRequestUnionMs": float(Decimal(union_ns) / Decimal(1_000_000)),
                "maxPriceRequestRttMs": float(max_rtt_ms),
                "venueClockAgreementMs": float(venue_clock_agreement_ms),
                "boundedComparisonAllowed": bounded_comparison,
            },
            "lineage": {
                "captureSha256": hashlib.sha256(capture_path.read_bytes()).hexdigest(),
                "transportBindingDigest": binding.get("bindingDigest"),
                "authorityDigests": {k:v.get("authorityDigest") for k,v in sorted(binding["authorities"].items())},
            },
        },
        "brokerCredentialsUsed": False,
        "privateAccountDataUsed": False,
        "externalFinancialWritesAttempted": False,
        "demoExecutionAttempted": False,
        "liveExecutionAttempted": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", required=True, type=Path)
    parser.add_argument("--transport-binding", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = analyze(args.capture, args.transport_binding)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
