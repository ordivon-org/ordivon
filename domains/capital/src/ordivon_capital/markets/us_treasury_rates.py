from __future__ import annotations

import argparse
import json
import subprocess
import time
import xml.etree.ElementTree as ET
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

BASE_URL = "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml"
ATOM = "http://www.w3.org/2005/Atom"
META = "http://schemas.microsoft.com/ado/2007/08/dataservices/metadata"
DATA = "http://schemas.microsoft.com/ado/2007/08/dataservices"

NOMINAL_FIELDS = {
    "1m": "BC_1MONTH",
    "3m": "BC_3MONTH",
    "6m": "BC_6MONTH",
    "1y": "BC_1YEAR",
    "2y": "BC_2YEAR",
    "3y": "BC_3YEAR",
    "5y": "BC_5YEAR",
    "7y": "BC_7YEAR",
    "10y": "BC_10YEAR",
    "20y": "BC_20YEAR",
    "30y": "BC_30YEAR",
}
REAL_FIELDS = {
    "5y": "TC_5YEAR",
    "7y": "TC_7YEAR",
    "10y": "TC_10YEAR",
    "20y": "TC_20YEAR",
    "30y": "TC_30YEAR",
}


class TreasuryRatesError(RuntimeError):
    pass


def _decimal(value: str | None, label: str) -> Decimal:
    try:
        out = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise TreasuryRatesError(f"invalid decimal for {label}") from exc
    if not out.is_finite():
        raise TreasuryRatesError(f"non-finite decimal for {label}")
    return out


def parse_feed(xml_text: str, fields: dict[str, str]) -> dict[str, Any]:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise TreasuryRatesError("Treasury XML is not well-formed") from exc

    if root.tag != f"{{{ATOM}}}feed":
        raise TreasuryRatesError("Treasury XML root is not Atom feed")
    updated = root.findtext(f"{{{ATOM}}}updated")
    rows: dict[str, dict[str, str]] = {}
    for entry in root.findall(f"{{{ATOM}}}entry"):
        props = entry.find(f"{{{ATOM}}}content/{{{META}}}properties")
        if props is None:
            continue
        raw_date = props.findtext(f"{{{DATA}}}NEW_DATE")
        if not raw_date:
            continue
        date = raw_date[:10]
        values: dict[str, str] = {}
        for tenor, tag in fields.items():
            value = props.findtext(f"{{{DATA}}}{tag}")
            if value not in (None, ""):
                _decimal(value, f"{date}.{tenor}")
                values[tenor] = value
        if values:
            if date in rows:
                raise TreasuryRatesError(f"duplicate Treasury date: {date}")
            rows[date] = values
    if not rows:
        raise TreasuryRatesError("Treasury XML contains no usable rate rows")
    return {"feedUpdated": updated, "rows": rows}


def _fmt(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.01")), "f")


def _curve_change_bp(current: dict[str, str], previous: dict[str, str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for tenor in sorted(set(current) & set(previous)):
        out[tenor] = _fmt((_decimal(current[tenor], tenor) - _decimal(previous[tenor], tenor)) * Decimal("100"))
    return out


def _breakevens(nominal: dict[str, str], real: dict[str, str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for tenor in sorted(set(nominal) & set(real)):
        out[tenor] = _fmt(_decimal(nominal[tenor], tenor) - _decimal(real[tenor], tenor))
    return out


def _slopes(nominal: dict[str, str]) -> dict[str, str | None]:
    def slope(a: str, b: str) -> str | None:
        if a not in nominal or b not in nominal:
            return None
        return _fmt((_decimal(nominal[b], b) - _decimal(nominal[a], a)) * Decimal("100"))
    return {
        "2s10sBp": slope("2y", "10y"),
        "2s30sBp": slope("2y", "30y"),
        "5s30sBp": slope("5y", "30y"),
    }


def compose_capture(*, nominal_xml: str, real_xml: str, observed_at_ms: int) -> dict[str, Any]:
    nominal = parse_feed(nominal_xml, NOMINAL_FIELDS)
    real = parse_feed(real_xml, REAL_FIELDS)
    common_dates = sorted(set(nominal["rows"]) & set(real["rows"]))
    if len(common_dates) < 2:
        raise TreasuryRatesError("fewer than two common nominal/real Treasury dates")
    previous_date, latest_date = common_dates[-2], common_dates[-1]
    latest_nominal = nominal["rows"][latest_date]
    previous_nominal = nominal["rows"][previous_date]
    latest_real = real["rows"][latest_date]
    previous_real = real["rows"][previous_date]
    latest_be = _breakevens(latest_nominal, latest_real)
    previous_be = _breakevens(previous_nominal, previous_real)
    return {
        "schemaVersion": 1,
        "kind": "ordivon.capital.markets.us-treasury-daily-rates-capture",
        "provider": "US_DEPARTMENT_OF_THE_TREASURY",
        "sourceAuthority": "US_TREASURY_OFFICIAL_DAILY_INTEREST_RATE_XML",
        "observedAtMs": observed_at_ms,
        "latestCommonDate": latest_date,
        "previousCommonDate": previous_date,
        "feedUpdated": {
            "nominal": nominal["feedUpdated"],
            "real": real["feedUpdated"],
        },
        "latest": {
            "nominalParYieldPct": latest_nominal,
            "realParYieldPct": latest_real,
            "nominalMinusRealPct": latest_be,
            "nominalCurveSlopes": _slopes(latest_nominal),
        },
        "previous": {
            "nominalParYieldPct": previous_nominal,
            "realParYieldPct": previous_real,
            "nominalMinusRealPct": previous_be,
        },
        "changeBp": {
            "nominal": _curve_change_bp(latest_nominal, previous_nominal),
            "real": _curve_change_bp(latest_real, previous_real),
            "nominalMinusReal": _curve_change_bp(latest_be, previous_be),
        },
        "credentialsLoaded": False,
        "privateAccountDataUsed": False,
        "externalFinancialWriteAttempted": False,
        "claimBoundary": "official daily Treasury par nominal and real curves; nominal-minus-real is arithmetic same-maturity spread, not an intraday TIPS quote, inflation forecast, or trading signal",
    }


def _request(proxy: str, data_key: str, year: int) -> str:
    if not proxy.startswith("http://127.0.0.1:"):
        raise TreasuryRatesError("proxy must be a loopback Network v2 HTTP proxy")
    query = urlencode({"data": data_key, "field_tdr_date_value": str(year)})
    proc = subprocess.run(
        [
            "/usr/bin/curl", "-4", "-fsS", "--proxy", proxy,
            "--connect-timeout", "5", "--max-time", "60",
            f"{BASE_URL}?{query}",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise TreasuryRatesError(f"Treasury curl failed rc={proc.returncode}: {proc.stderr.strip()}")
    return proc.stdout


def capture(*, proxy: str, year: int) -> dict[str, Any]:
    nominal_xml = _request(proxy, "daily_treasury_yield_curve", year)
    real_xml = _request(proxy, "daily_treasury_real_yield_curve", year)
    return compose_capture(
        nominal_xml=nominal_xml,
        real_xml=real_xml,
        observed_at_ms=time.time_ns() // 1_000_000,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--proxy", required=True)
    parser.add_argument("--year", type=int, default=time.gmtime().tm_year)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = capture(proxy=args.proxy, year=args.year)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
