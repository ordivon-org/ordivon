from __future__ import annotations

import csv
import io
import json
import subprocess
import time
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DCOILBRENTEU,DCOILWTICO"
SERIES = {"brent": "DCOILBRENTEU", "wti": "DCOILWTICO"}


class FredEnergyError(RuntimeError):
    pass


def _decimal(value: str, label: str) -> Decimal:
    try:
        out = Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise FredEnergyError(f"invalid decimal for {label}") from exc
    if not out.is_finite():
        raise FredEnergyError(f"non-finite decimal for {label}")
    return out


def _fmt(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.01")), "f")


def parse_csv(text: str) -> dict[str, dict[str, str]]:
    reader = csv.DictReader(io.StringIO(text))
    required = {"observation_date", *SERIES.values()}
    if not reader.fieldnames or not required.issubset(reader.fieldnames):
        raise FredEnergyError("FRED CSV missing required columns")
    rows: dict[str, dict[str, str]] = {}
    for row in reader:
        date = (row.get("observation_date") or "").strip()
        if not date:
            continue
        values: dict[str, str] = {}
        for label, series in SERIES.items():
            raw = (row.get(series) or "").strip()
            if raw and raw != ".":
                _decimal(raw, f"{date}.{label}")
                values[label] = raw
        if values:
            rows[date] = values
    if not rows:
        raise FredEnergyError("FRED CSV contains no usable energy rows")
    return rows


def compose_capture(csv_text: str, observed_at_ms: int) -> dict[str, Any]:
    rows = parse_csv(csv_text)
    common = sorted(date for date, values in rows.items() if set(values) == {"brent", "wti"})
    if len(common) < 2:
        raise FredEnergyError("fewer than two common Brent/WTI observations")
    previous_date, latest_date = common[-2], common[-1]
    latest = rows[latest_date]
    previous = rows[previous_date]
    b = _decimal(latest["brent"], "brent")
    w = _decimal(latest["wti"], "wti")
    pb = _decimal(previous["brent"], "previous.brent")
    pw = _decimal(previous["wti"], "previous.wti")
    return {
        "schemaVersion": 1,
        "kind": "ordivon.capital.markets.fred-eia-origin-energy-daily-capture",
        "aggregator": "FRED",
        "originOwner": "U.S. Energy Information Administration",
        "sourceAuthority": "FRED_PUBLIC_CSV_EIA_ORIGIN_MIRROR",
        "observedAtMs": observed_at_ms,
        "latestCommonDate": latest_date,
        "previousCommonDate": previous_date,
        "series": SERIES,
        "latestUsdPerBarrel": latest,
        "previousUsdPerBarrel": previous,
        "change": {
            "brentUsd": _fmt(b - pb),
            "wtiUsd": _fmt(w - pw),
            "brentPct": _fmt((b / pb - 1) * Decimal("100")),
            "wtiPct": _fmt((w / pw - 1) * Decimal("100")),
            "brentMinusWtiUsd": _fmt(b - w),
            "previousBrentMinusWtiUsd": _fmt(pb - pw),
        },
        "credentialsLoaded": False,
        "privateAccountDataUsed": False,
        "externalFinancialWriteAttempted": False,
        "claimBoundary": "FRED public CSV is a secondary aggregator/mirror for EIA-origin daily spot series; not direct EIA API truth, exchange futures settlement, intraday executable price, or trading signal",
    }


def capture(*, proxy: str) -> dict[str, Any]:
    if not proxy.startswith("http://127.0.0.1:"):
        raise FredEnergyError("proxy must be a loopback Network v2 HTTP proxy")
    proc = subprocess.run(
        ["/usr/bin/curl", "-4", "-fsS", "--proxy", proxy, "--connect-timeout", "5", "--max-time", "30", URL],
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise FredEnergyError(f"FRED curl failed rc={proc.returncode}: {proc.stderr.strip()}")
    return compose_capture(proc.stdout, time.time_ns() // 1_000_000)


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--proxy", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = capture(proxy=args.proxy)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
