from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Any

SEC_COMPANYFACTS = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
USER_AGENT = "OrdivonMarketCapital/0.1 educational-research"

CONCEPTS = {
    "net_income": "NetIncomeLoss",
    "assets": "Assets",
    "stockholders_equity": "StockholdersEquity",
}


def fetch_companyfacts(cik: str, destination: Path) -> dict[str, Any]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    url = SEC_COMPANYFACTS.format(cik=cik)
    subprocess.run(
        [
            "/usr/bin/curl",
            "--location",
            "--fail",
            "--silent",
            "--show-error",
            "--retry",
            "2",
            "--retry-delay",
            "1",
            "--user-agent",
            USER_AGENT,
            url,
            "--output",
            str(destination),
        ],
        check=True,
    )
    time.sleep(0.15)
    return json.loads(destination.read_text())


def select_latest_annual_fact(companyfacts: dict[str, Any], concept: str) -> dict[str, Any]:
    try:
        values = companyfacts["facts"]["us-gaap"][concept]["units"]["USD"]
    except KeyError as exc:
        raise ValueError(f"Missing SEC us-gaap concept {concept}") from exc

    candidates = [
        row
        for row in values
        if row.get("form") == "10-K"
        and row.get("fp") == "FY"
        and isinstance(row.get("fy"), int)
        and row.get("end")
        and row.get("accn")
    ]
    if not candidates:
        raise ValueError(f"No annual 10-K FY fact for {concept}")

    latest_fy = max(row["fy"] for row in candidates)
    latest_fy_rows = [row for row in candidates if row["fy"] == latest_fy]
    selected = max(
        latest_fy_rows,
        key=lambda row: (row["end"], row.get("filed", ""), row.get("accn", "")),
    )
    return selected


def build_fundamental_feature(symbol: str, cik: str, expected_entity: str, companyfacts: dict[str, Any]) -> dict[str, Any]:
    entity_name = companyfacts.get("entityName")
    if entity_name != expected_entity:
        raise ValueError(f"SEC entity mismatch for {symbol}: expected {expected_entity!r}, got {entity_name!r}")

    selected = {
        name: select_latest_annual_fact(companyfacts, concept)
        for name, concept in CONCEPTS.items()
    }
    periods = {(row["fy"], row["end"], row["accn"]) for row in selected.values()}
    if len(periods) != 1:
        raise ValueError(f"Selected SEC facts do not share one annual filing for {symbol}: {sorted(periods)}")

    fy, period_end, accession = next(iter(periods))
    net_income = float(selected["net_income"]["val"])
    assets = float(selected["assets"]["val"])
    equity = float(selected["stockholders_equity"]["val"])
    if assets == 0 or equity == 0:
        raise ValueError(f"Zero denominator in annual fundamentals for {symbol}")

    return {
        "symbol": symbol,
        "cik": cik,
        "entity_name": entity_name,
        "fiscal_year": fy,
        "period_end": period_end,
        "accession": accession,
        "filed": selected["net_income"].get("filed"),
        "concepts": CONCEPTS,
        "net_income": net_income,
        "assets": assets,
        "stockholders_equity": equity,
        "roa_proxy": net_income / assets,
        "roe_proxy": net_income / equity,
        "equity_to_assets": equity / assets,
    }
