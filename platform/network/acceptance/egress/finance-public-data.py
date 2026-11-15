#!/usr/bin/env python3
"""Finance data-read acceptance through installed Network-v2 scoped lanes.

Actual read-only public market-data JSON/CSV payloads, not just CONNECT 200.
Use upstream curl, existing sing-box lanes and independent Carrier observer.
No trading calls, credentials, new VPN, firewall changes or long-running agents.
"""
from __future__ import annotations

import csv
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import io
import json
from pathlib import Path
import runpy
import subprocess
import time

NETWORK = Path(__file__).resolve().parents[2]
SOURCE = NETWORK / "consumers/finance/config/egress.json"
INSTALLED = Path("/etc/network-v2/finance/egress.json")
CARRIER = ("10.252.246.2", 19680)

# Public, no-credential read operations. Hosts/routes must also match the
# installed Finance policy, so a future domain/port change fails before I/O.
SAMPLES = (
    ("okx-spot", "finance-okx", "openapi.okx.com", 443,
     "/api/v5/market/ticker?instId=BTC-USDT", "provider-carrier"),
    ("binance-spot", "finance-binance-spot-public", "data-api.binance.vision", 443,
     "/api/v3/ticker/price?symbol=BTCUSDT", "provider-carrier"),
    ("binance-usdm", "finance-binance-usdm", "fapi.binance.com", 443,
     "/fapi/v1/ticker/price?symbol=BTCUSDT", "provider-carrier"),
    ("fred-dgs10", "finance-fred-public-csv", "fred.stlouisfed.org", 443,
     "/graph/fredgraph.csv?id=DGS10", "public-direct"),
)


def validate_contract(source_bytes: bytes, installed_bytes: bytes) -> dict[str, int]:
    if source_bytes != installed_bytes:
        raise ValueError("FINANCE_SOURCECUT_DRIFT")
    cfg = json.loads(source_bytes)
    bounds = cfg["outbounds"]
    if bounds != [
        {"type": "http", "tag": "provider-carrier",
         "server": CARRIER[0], "server_port": CARRIER[1]},
        {"type": "direct", "tag": "public-direct"},
    ]:
        raise ValueError("OUTBOUND_CONTRACT_CHANGED")
    route = cfg.get("route")
    if not isinstance(route, dict) or route.get("final") != "provider-carrier":
        raise ValueError("OPEN_PROVIDER_DEFAULT_MISSING")
    ports = {x["tag"]: int(x["listen_port"]) for x in cfg["inbounds"]
             if x.get("listen") == "127.0.0.1"}
    if len(ports) != 9 or len(cfg["inbounds"]) != 9:
        raise ValueError("NINE_FINANCE_LANES_REQUIRED")
    expected_direct = {"finance-us-treasury-public", "finance-fred-public-csv"}
    direct = route.get("rules")
    if not isinstance(direct, list) or len(direct) != 2 or (
        {tuple(x.get("inbound", [])) for x in direct}
        != {(tag,) for tag in expected_direct}
    ) or any(x.get("outbound") != "public-direct"
             or x.get("action") != "route"
             or set(x) != {"inbound", "action", "outbound"} for x in direct):
        raise ValueError("SAMPLE_ROUTE_NOT_INSTALLED")
    # Business sample endpoints stay independent of open networking.
    for _id, tag, host, dstport, _path, expected in SAMPLES:
        actual = ("public-direct" if tag in expected_direct else "provider-carrier")
        if (tag not in ports or not 1 <= ports[tag] <= 65535
                or dstport != 443 or actual != expected):
            raise ValueError("SAMPLE_ROUTE_NOT_INSTALLED")
    return ports


def positive_decimal(text: str) -> str:
    value = Decimal(text)
    if not value.is_finite() or value <= 0:
        raise ValueError("NONPOSITIVE_OR_NONFINITE_MARKET_VALUE")
    return str(value)


def parse_business_payload(name: str, body: str) -> dict:
    """Public market data only; no arbitrary origin content leaves the process."""
    if name == "okx-spot":
        j = json.loads(body)
        if j.get("code") != "0" or not isinstance(j.get("data"), list):
            raise ValueError("OKX_API_STATUS_OR_SHAPE")
        entry = j["data"][0]
        if entry.get("instId") != "BTC-USDT":
            raise ValueError("OKX_INSTRUMENT_MISMATCH")
        return {
            "instrument": "BTC-USDT",
            "priceUsd": positive_decimal(entry["last"]),
            "sourceEpochMs": int(entry["ts"]),
        }
    if name in {"binance-spot", "binance-usdm"}:
        j = json.loads(body)
        if j.get("symbol") != "BTCUSDT":
            raise ValueError("BINANCE_INSTRUMENT_MISMATCH")
        result = {
            "instrument": "BTCUSDT",
            "priceUsd": positive_decimal(j["price"]),
        }
        if name == "binance-usdm":
            result["sourceEpochMs"] = int(j["time"])
        return result
    if name == "fred-dgs10":
        reader = csv.reader(io.StringIO(body))
        header = next(reader, None)
        if header not in (["DATE", "DGS10"], ["observation_date", "DGS10"]):
            raise ValueError("FRED_CSV_HEADER_MISMATCH")
        valid = []
        for row in reader:
            if len(row) == 2 and row[1].strip() not in ("", "."):
                day = datetime.strptime(row[0], "%Y-%m-%d").date()
                number = positive_decimal(row[1])
                valid.append((day, number))
        if not valid:
            raise ValueError("FRED_HAS_NO_DATA")
        day, rate = max(valid)
        return {
            "series": "DGS10",
            "sourceDate": day.isoformat(),
            "yieldPct": rate,
            "validRows": len(valid),
        }
    raise ValueError("UNKNOWN_BUSINESS_SAMPLE")


def fetch_public_data(host: str, path: str, proxy_port: int,
                      runner=subprocess.run) -> tuple[int, str, int]:
    args = [
        "curl", "-q", "-4", "--noproxy", "", "--proxy",
        f"http://127.0.0.1:{proxy_port}", "--connect-timeout", "6",
        "--max-time", "18", "--max-filesize", "1000000", "--silent",
        "--show-error", "--output", "-", "--write-out",
        "\n__HTTP__:%{http_code}", f"https://{host}{path}",
    ]
    result = runner(args, capture_output=True, text=True, timeout=22, check=False)
    body, marker, status = result.stdout.rpartition("\n__HTTP__:")
    if not marker:
        return result.returncode, "", 0
    return result.returncode, body, int(status) if status.strip().isdigit() else 0


def main() -> int:
    observer = None
    receipt = {
        "schemaVersion": 1,
        "kind": "ordivon.network.finance-real-public-data",
        "observedAtUtc": datetime.now(timezone.utc).isoformat(),
        "standing": "UNKNOWN",
        "scope": "Four read-only public Finance API payloads through installed per-lane proxy",
        "financialWriteOperations": 0,
        "tradingOperations": 0,
        "unproved": [
            "future data feed availability and time synchronization",
            "all-protocol/IPv6/DNS egress or every Finance lane's business API",
            "real-order execution or financial model decision correctness",
        ],
        "results": [],
    }
    try:
        source = SOURCE.read_bytes()
        ports = validate_contract(source, INSTALLED.read_bytes())
        native = runpy.run_path(str(Path(__file__).with_name("live-carrier-witness.py")))
        pid = native["pid"]
        finance_before = pid("network-v2-finance-egress.service")
        provider_before = pid("network-v2-gluetun-owned.service")
        observer = native["Observer"]("host")
        time.sleep(1.2)
        observer.assert_live()
        for name, tag, host, port, path, route in SAMPLES:
            target = f"{host}:{port}"
            before = observer.count(target)
            result = {"sample": name, "lane": tag, "expectedRoute": route}
            try:
                curl_exit, body, status = fetch_public_data(host, path, ports[tag])
                time.sleep(0.35)
                observed = observer.count(target) - before
                result.update({
                    "curlExit": curl_exit,
                    "originHttp": status,
                    "carrierConnects": observed,
                    "routeMatched": observed > 0 if route == "provider-carrier"
                    else observed == 0,
                })
                if curl_exit != 0 or status != 200 or len(body.encode()) > 1000000:
                    raise ValueError("ORIGIN_DATA_REQUEST_FAILED")
                result["business"] = parse_business_payload(name, body)
                result["passed"] = bool(result["routeMatched"])
            except (ValueError, TypeError, IndexError, KeyError, InvalidOperation,
                    subprocess.TimeoutExpired, OSError) as exc:
                result["passed"] = False
                result["errorCategory"] = type(exc).__name__
            receipt["results"].append(result)
            observer.assert_live()
        if SOURCE.read_bytes() != source or INSTALLED.read_bytes() != source:
            raise ValueError("FINANCE_SOURCECUT_CHANGED_DURING_SAMPLE")
        if pid("network-v2-finance-egress.service") != finance_before or (
                pid("network-v2-gluetun-owned.service") != provider_before):
            raise ValueError("FINANCE_OR_PROVIDER_PID_CHANGED")
        receipt["observerContinuity"] = True
        receipt["standing"] = (
            "PASS" if len(receipt["results"]) == len(SAMPLES)
            and all(x["passed"] for x in receipt["results"]) else "FAIL"
        )
    except (ValueError, TypeError, OSError, AssertionError, KeyError, json.JSONDecodeError) as exc:
        receipt["standing"] = "UNKNOWN"
        receipt["errorCategory"] = type(exc).__name__
    finally:
        if observer is not None:
            observer.close()
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True,
                     separators=(",", ":")))
    return 0 if receipt["standing"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
