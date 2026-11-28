"""Finance use-case tests assert observable economic behavior, never module paths."""

from __future__ import annotations

from pathlib import Path

import pytest

from ordivon_capital.portfolio.portfolio_counterfactuals import evaluate_constraint_gate
from ordivon_capital.risk.portfolio_risk import evaluate_risk_budget


def test_risk_and_scenario_analysis_are_pure_even_if_all_file_reads_fail(monkeypatch):
    def forbid_io(*args, **kwargs):
        raise AssertionError("read-only financial arithmetic consulted filesystem")

    monkeypatch.setattr(Path, "read_text", forbid_io)
    ledger = {
        "grossToEquity": "1.50",
        "largestPositionGrossShare": "0.50",
        "availableEquityRatio": "0.50",
        "positions": [{"equityMultiple": "0.5"}],
    }
    budget = {
        "maxGrossToEquity": "2",
        "maxLargestPositionGrossShare": "0.8",
        "minAvailableEquityRatio": "0.3",
        "shockMagnitudePct": "10",
        "maxEquityLossPctAtShock": "20",
    }
    risk = evaluate_risk_budget(exposure_ledger=ledger, budget=budget)
    assert risk["standing"] == "SATISFIED"
    scenario = {
        "scenarioId": "hold",
        "action": "HOLD",
        "baseline": {"grossToEquity": "1.5"},
        "projected": {"grossToEquity": "1.5"},
        "hedgeMechanics": None,
    }
    control = evaluate_constraint_gate(counterfactual=scenario, risk_budget_evaluation=risk)
    assert control["standing"] == "PASS"
    assert control["failedChecks"] == []
    assert control["incompleteChecks"] == []
    assert "orderSubmissionAllowed" not in control


def test_missing_risk_limits_are_incomplete_not_silently_approved():
    result = evaluate_risk_budget(exposure_ledger={}, budget={})
    assert result["standing"] == "INCOMPLETE"
    assert "maxGrossToEquity" in result["missingBudgetInputs"]


@pytest.mark.parametrize(
    "field,invalid",
    [
        ("maxGrossToEquity", "-1"),
        ("maxLargestPositionGrossShare", "1.01"),
        ("minAvailableEquityRatio", "-0.01"),
        ("shockMagnitudePct", "0"),
        ("maxEquityLossPctAtShock", "101"),
    ],
)
def test_bad_risk_limits_are_rejected_by_effective_behavior(field, invalid):
    budget = {
        "maxGrossToEquity": "2",
        "maxLargestPositionGrossShare": "0.8",
        "minAvailableEquityRatio": "0.3",
        "shockMagnitudePct": "10",
        "maxEquityLossPctAtShock": "20",
    }
    budget[field] = invalid
    with pytest.raises(ValueError):
        evaluate_risk_budget(exposure_ledger={}, budget=budget)
