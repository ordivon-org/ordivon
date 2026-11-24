"""Economic behavior at the existing agent CLI, plus exact reserve invariants."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from ordivon_capital.applications.goal_funded_contribution import plan_goal_funded_contribution
from ordivon_capital.portfolio.strategic_contribution import AllocationPolicyError

ROOT = Path(__file__).resolve().parents[1]


def example():
    return json.loads((ROOT / "examples/goal_funded_contribution_r1.json").read_text())


def test_actual_cli_caps_contribution_without_consuming_future_liability_cash():
    raw = example()
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/strategic_contribution_brief.py")],
        input=json.dumps(raw), text=True, capture_output=True,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")}, check=True,
    )
    out = json.loads(result.stdout)
    assert out == plan_goal_funded_contribution(raw)
    assert out["standing"] == "CONTRIBUTION_CAPPED"
    assert out["projectedContributionMinor"] == 10000
    assert out["allocationPlan"]["cashAfterMinor"] == 40000
    assert out["liquidityReserve"]["outsideHorizonObligationsMinor"] == 80000
    assert out["executionAuthorized"] is False


def test_overdue_and_inclusive_horizon_are_protected_and_shortfall_visible():
    raw = example()
    raw["cashMinor"] = 30000
    raw["obligations"][0]["dueDate"] = "2026-11-23"
    raw["obligations"][1].update(dueDate=raw["reserveThroughDate"], amountMinor=100)
    out = plan_goal_funded_contribution(raw)
    assert out["standing"] == "RESERVE_SHORTFALL"
    assert out["allocationPlan"] is None
    assert out["projectedContributionMinor"] == 0
    assert out["liquidityReserve"]["overdueMinor"] == 30000
    assert out["liquidityReserve"]["reserveShortfallMinor"] == 10100


@pytest.mark.parametrize("cash", [0, 39999, 40000, 40001, 60000, 90000])
@pytest.mark.parametrize("desired", [0, 1, 20000, 50000])
def test_reserve_and_contribution_conservation(cash, desired):
    raw = example()
    raw.update(cashMinor=cash, contributionMinor=desired)
    out = plan_goal_funded_contribution(raw)
    amount = out["projectedContributionMinor"]
    assert 0 <= amount <= desired
    assert amount == min(desired, max(0, cash - 40000))
    if cash < 40000:
        assert out["allocationPlan"] is None
    else:
        assert cash - amount >= 40000
        assert sum(out["allocationPlan"]["allocationsMinor"].values()) == amount
    assert out["executionAuthorized"] is False


@pytest.mark.parametrize("mutation", [
    lambda x: x.update(asOfDate="2028-01-01"),
    lambda x: x.update(reserveThroughDate="20271124"),
    lambda x: x.update(emergencyReserveMinor=True),
    lambda x: x["obligations"].append(x["obligations"][0]),
    lambda x: x["obligations"][0].update(amountMinor=-1),
    lambda x: x["obligations"][0].update(dueDate="2027-02-29"),
    lambda x: x["obligations"][0].update(amountMinor=2**63-1),
    lambda x: x.update(currency="EUR"),
    lambda x: x.update(projectedIncomeMinor=100000),
])
def test_bad_or_unmodeled_inputs_do_not_produce_projection(mutation):
    raw = example()
    mutation(raw)
    with pytest.raises(AllocationPolicyError):
        plan_goal_funded_contribution(raw)
