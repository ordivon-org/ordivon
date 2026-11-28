"""Behavior of explicit fund-return semantics through the existing CLI."""

import json
import os
import subprocess
import sys
from copy import deepcopy
from decimal import Decimal
from pathlib import Path

import pytest

from ordivon_capital.portfolio.passive_benchmark import (
    PassiveBenchmarkError,
    replay_fund_nav_benchmark,
    replay_passive_benchmark,
)

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples/fund_nav_benchmark_202609_r2.json"


def request():
    return json.loads(EXAMPLE.read_text())


def test_official_reported_rounded_monthly_return_example_through_native_cli():
    payload = request()
    result = subprocess.run(
        [sys.executable, "-m", "ordivon_capital.portfolio.passive_benchmark",
         "--input", str(EXAMPLE)],
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
        text=True, capture_output=True, check=True,
    )
    out = json.loads(result.stdout)
    assert out == replay_fund_nav_benchmark(payload)
    assert Decimal(out["strategyTerminalWealth"]) == Decimal("9943")
    assert Decimal(out["benchmarkTerminalWealth"]) == Decimal("9965")
    assert Decimal(out["terminalWealthDifference"]) == Decimal("-22")
    assert out["dataStanding"] == "CALLER_DECLARED_UNATTESTED"
    assert out["capitalAuthority"] == "NONE"
    assert out["returnEvidence"][0]["strategy"]["sourceRef"]


def test_only_external_costs_are_charged_and_transition_reused():
    payload = request()
    row = payload["periods"][0]
    row.update(depositAtStart="100", strategyExternalExpenseFractionAtStart="0.001",
               strategyExternalFixedFeeAtStart="1")
    out = replay_fund_nav_benchmark(payload)
    old = replay_passive_benchmark(opening_balance="10000", currency="USD", periods=[{
        "periodEndAt": "2026-09-30T00:00:00+00:00",
        "depositAtStart": "100", "strategyGrossReturn": "-0.0057",
        "benchmarkGrossReturn": "-0.0035", "strategyExpenseFractionAtStart": "0.001",
        "benchmarkExpenseFractionAtStart": "0", "strategyFixedFeeAtStart": "1",
        "benchmarkFixedFeeAtStart": "0",
    }])
    assert out["strategyTerminalWealth"] == old["strategyTerminalWealth"]
    assert out["benchmarkTerminalWealth"] == old["benchmarkTerminalWealth"]
    assert Decimal(out["contributedCapital"]) == 10100
    assert out["fundExpenseTreatment"].endswith("NOT_DEDUCTED_AGAIN")


@pytest.mark.parametrize("mutate", [
    lambda d: d["periods"][0]["strategy"].update(returnBasis="PRICE_ONLY"),
    lambda d: d["periods"][0]["benchmark"].update(returnBasis="INDEX_TOTAL_RETURN"),
    lambda d: d["periods"][0]["strategy"].update(currency="EUR"),
    lambda d: d["periods"][0]["strategy"].update(periodStartDate="2026-09-01"),
    lambda d: d["periods"][0]["benchmark"].update(periodEndDate="2026-10-01"),
    lambda d: d["periods"][0]["strategy"].update(sourceRef=""),
    lambda d: d["periods"][0]["strategy"].update(totalReturn="NaN"),
    lambda d: d["periods"][0]["strategy"].update(totalReturn="-1.001"),
    lambda d: d["periods"][0].update(strategyAnnualExpenseFraction="0.0015"),
    lambda d: d["periods"][0].update(distribution="1.25"),
    lambda d: d["periods"][0].update(strategyExternalFixedFeeAtStart="-1"),
    lambda d: d.update(currency="EUR"),
    lambda d: d.update(schemaVersion=True),
])
def test_unsupported_return_and_cost_semantics_rejected(mutate):
    payload = request()
    mutate(payload)
    with pytest.raises(PassiveBenchmarkError):
        replay_fund_nav_benchmark(payload)


@pytest.mark.parametrize("start", ["2026-09-29", "2026-10-01"])
def test_overlapping_or_gapped_periods_rejected(start):
    payload = request()
    row = deepcopy(payload["periods"][0])
    for leg in ("strategy", "benchmark"):
        row[leg].update(periodStartDate=start, periodEndDate="2026-10-31")
    payload["periods"].append(row)
    with pytest.raises(PassiveBenchmarkError, match="contiguous"):
        replay_fund_nav_benchmark(payload)


def test_contiguous_paths_and_matching_drivers_preserve_relative_wealth():
    payload = request()
    first = payload["periods"][0]
    first["strategy"]["totalReturn"] = first["benchmark"]["totalReturn"]
    second = deepcopy(first)
    for leg in ("strategy", "benchmark"):
        second[leg].update(periodStartDate="2026-09-30", periodEndDate="2026-10-31")
    second["depositAtStart"] = "100"
    payload["periods"].append(second)
    out = replay_fund_nav_benchmark(payload)
    assert Decimal(out["terminalWealthDifference"]) == 0
    assert out["periodCount"] == 2
    second["strategy"]["instrument"] = "OTHER"
    with pytest.raises(PassiveBenchmarkError, match="identities"):
        replay_fund_nav_benchmark(payload)
