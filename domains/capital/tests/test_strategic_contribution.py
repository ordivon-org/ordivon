"""Read-only contribution-first investment consumer and integer conservation laws."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from ordivon_capital.portfolio.strategic_contribution import (
    AllocationPolicyError,
    plan_strategic_contribution,
)

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples/strategic_contribution_r1.json"


def request() -> dict:
    return json.loads(EXAMPLE.read_text(encoding="utf-8"))


def run_cli(raw: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT / "src")
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts/strategic_contribution_brief.py")],
        input=raw,
        text=True,
        capture_output=True,
        cwd=ROOT,
        env=env,
        check=False,
    )


def test_existing_portfolio_is_not_sold_to_chase_target_weights() -> None:
    result = plan_strategic_contribution(request())
    assert result["kind"] == "ordivon.finance.portfolio.strategic-contribution-plan"
    assert result["allocationsMinor"] == {"BOND_CORE": 10000, "INDEX_CORE": 0}
    assert result["projectedHoldingsMinor"] == {"BOND_CORE": 30000, "INDEX_CORE": 80000}
    assert result["cashAfterMinor"] == 40000
    assert result["protectedReserveMinor"] == 30000
    assert result["executionAuthorized"] is False
    assert result["riskStanding"] == "NOT_EVALUATED"
    assert result["dataStanding"] == "CALLER_SUPPLIED_UNATTESTED"


@pytest.mark.parametrize("contribution", [0, 1, 2, 99, 101, 10001, 19999])
@pytest.mark.parametrize(
    "holdings",
    [
        {"INDEX_CORE": 60000, "BOND_CORE": 40000},
        {"INDEX_CORE": 100000, "BOND_CORE": 0},
        {"INDEX_CORE": 0, "BOND_CORE": 0},
        {"INDEX_CORE": 33333, "BOND_CORE": 66667},
    ],
)
def test_exact_conservation_and_no_sell_under_drift(
    contribution: int, holdings: dict[str, int]
) -> None:
    source = request()
    source["holdingsMinor"] = holdings
    source["contributionMinor"] = contribution
    source["targetWeightsBps"] = {"INDEX_CORE": 6000, "BOND_CORE": 4000}
    result = plan_strategic_contribution(source)
    allocated = result["allocationsMinor"]
    assert sum(allocated.values()) == contribution
    assert all(x >= 0 for x in allocated.values())
    assert all(
        result["projectedHoldingsMinor"][k] == holdings[k] + allocated[k]
        for k in holdings
    )
    assert result["projectedInvestmentMinor"] == sum(holdings.values()) + contribution
    assert result["cashAfterMinor"] == source["cashMinor"] - contribution
    assert result["cashAfterMinor"] >= source["protectedReserveMinor"]



def test_native_consumer_breaks_equal_deficit_ties_by_asset_id() -> None:
    """A fourth overweight asset makes the three-way 1-cent tie attainable."""
    source = request()
    source.update(
        cashMinor=3,
        protectedReserveMinor=2,
        contributionMinor=1,
        holdingsMinor={"ASSET_A": 0, "ASSET_B": 0, "ASSET_C": 0, "ASSET_D": 3},
        targetWeightsBps={
            "ASSET_A": 2500, "ASSET_B": 2500, "ASSET_C": 2500, "ASSET_D": 2500
        },
    )
    projection = plan_strategic_contribution(source)
    assert projection["allocationsMinor"] == {
        "ASSET_A": 1, "ASSET_B": 0, "ASSET_C": 0, "ASSET_D": 0
    }
    assert projection["cashAfterMinor"] == 2
    assert projection["executionAuthorized"] is False
    observed = run_cli(json.dumps(source))
    assert observed.returncode == 0, observed.stderr
    assert json.loads(observed.stdout) == projection


def test_deterministic_instrument_order_and_rounding() -> None:
    source = request()
    source["holdingsMinor"] = {"BOND_CORE": 0, "INDEX_CORE": 0}
    source["targetWeightsBps"] = {"BOND_CORE": 5000, "INDEX_CORE": 5000}
    source["contributionMinor"] = 1
    result = plan_strategic_contribution(source)
    assert result["allocationsMinor"] == {"BOND_CORE": 1, "INDEX_CORE": 0}
    assert result == plan_strategic_contribution(source)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda d: d.update({"cashMinor": -1}),
        lambda d: d.update({"cashMinor": True}),
        lambda d: d.update({"cashMinor": 12.0}),
        lambda d: d.update({"contributionMinor": 20001}),
        lambda d: d.update({"protectedReserveMinor": 50001}),
        lambda d: d.update({"unrecognized": 1}),
        lambda d: d.update({"currency": "EUR"}),
        lambda d: d.update({"schemaVersion": True}),
        lambda d: d["holdingsMinor"].update({"OTHER": 1}),
        lambda d: d["holdingsMinor"].update({"INDEX_CORE": -1}),
        lambda d: d["targetWeightsBps"].update({"BOND_CORE": 9000}),
        lambda d: d["targetWeightsBps"].update({"INDEX_CORE": True}),
        lambda d: d["holdingsMinor"].update({"../unsafe": 0}),
    ],
)
def test_invalid_policy_cannot_produce_a_plan(mutation) -> None:
    source = request()
    mutation(source)
    with pytest.raises(AllocationPolicyError):
        plan_strategic_contribution(source)


def test_real_agent_cli_consumes_native_portfolio_lego() -> None:
    observed = run_cli(EXAMPLE.read_text(encoding="utf-8"))
    assert observed.returncode == 0, observed.stderr
    result = json.loads(observed.stdout)
    assert result["allocationsMinor"]["BOND_CORE"] == 10000
    assert result["contributionMinor"] == 10000
    assert result["executionAuthorized"] is False
    assert not any(key in result for key in ("orders", "broker", "credentials"))


@pytest.mark.parametrize(
    "raw",
    [
        '{"schemaVersion":1,"schemaVersion":2}',
        '{"schemaVersion":1,"cashMinor":NaN}',
        '{"schemaVersion":1,"cashMinor":Infinity}',
        'not-json',
    ],
)
def test_invalid_cli_never_emits_a_success_receipt(raw: str) -> None:
    observed = run_cli(raw)
    assert observed.returncode != 0
    assert observed.stdout == ""
