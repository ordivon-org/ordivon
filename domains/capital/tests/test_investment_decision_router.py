from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from ordivon_capital.portfolio.decision_router import route_investment_decision
from ordivon_capital.research.investment_model_atlas import (
    InvestmentModelAtlasError,
    validate_investment_model_atlas_document,
)

ROOT = Path(__file__).resolve().parents[1]


def _atlas() -> dict:
    return json.loads((ROOT / "config/investment_model_atlas.json").read_text())


def _context(*, risk: str = "UNSET", tags: list[str] | None = None) -> dict:
    return {
        "decisionId": "decision:test:r1",
        "asOf": "2026-09-27T01:00:00+08:00",
        "objective": "bounded decision-support test",
        "horizon": "months-to-years",
        "riskBudgetStatus": risk,
        "stateTags": tags or [],
    }


def test_atlas_validates_and_has_unique_models() -> None:
    atlas = validate_investment_model_atlas_document(_atlas())
    keys = [row["modelKey"] for row in atlas["models"]]
    assert len(keys) == len(set(keys))
    assert "diversified-strategic-baseline" in keys
    assert "value-valuation" in keys
    assert "dynamic-cost-aware-trading" in keys


def test_conditional_model_must_have_routing_tag() -> None:
    atlas = _atlas()
    broken = copy.deepcopy(atlas)
    row = next(model for model in broken["models"] if model["activation"] == "CONDITIONAL")
    row["requiredTagsAll"] = []
    row["requiredTagsAny"] = []
    with pytest.raises(InvestmentModelAtlasError):
        validate_investment_model_atlas_document(broken)


def test_unset_risk_budget_keeps_system_research_only() -> None:
    result = route_investment_decision(
        _context(tags=["VALUATION_SIGNAL_AVAILABLE", "FUNDAMENTAL_QUALITY_SIGNAL_AVAILABLE"]),
        _atlas(),
    )
    assert result["decisionStanding"] == "RESEARCH_ONLY_RISK_BUDGET_UNSET"
    assert result["externalFinancialEffectAllowed"] is False
    assert "SIZE" not in result["eligibleActions"]
    routes = {row["modelKey"]: row["route"] for row in result["modelRoutes"]}
    assert routes["value-valuation"] == "ELIGIBLE"
    assert routes["quality-profitability"] == "ELIGIBLE"


def test_contested_models_are_research_only() -> None:
    result = route_investment_decision(
        _context(risk="SET", tags=["VOLATILITY_SIGNAL_AVAILABLE", "FACTOR_TIMING_SIGNAL_AVAILABLE"]),
        _atlas(),
    )
    routes = {row["modelKey"]: row["route"] for row in result["modelRoutes"]}
    assert routes["volatility-risk-scaling"] == "RESEARCH_ONLY"
    assert routes["factor-timing"] == "RESEARCH_ONLY"


def test_stress_or_model_conflict_blocks_sizing_escalation() -> None:
    tags = [
        "PAYOFF_DISTRIBUTION_ESTIMATED",
        "RISK_BUDGET_SET",
        "LIQUIDITY_STRESS",
    ]
    result = route_investment_decision(_context(risk="SET", tags=tags), _atlas())
    assert result["decisionStanding"] == "RISK_REVIEW_REQUIRED"
    assert result["riskGovernor"]["stressObserved"] is True
    assert result["riskGovernor"]["sizingPermitted"] is False
    assert "SIZE" not in result["eligibleActions"]


def test_fractional_kelly_only_routes_when_required_inputs_exist() -> None:
    inactive = route_investment_decision(_context(risk="SET"), _atlas())
    active = route_investment_decision(
        _context(risk="SET", tags=["PAYOFF_DISTRIBUTION_ESTIMATED", "RISK_BUDGET_SET"]),
        _atlas(),
    )
    inactive_routes = {row["modelKey"]: row["route"] for row in inactive["modelRoutes"]}
    active_routes = {row["modelKey"]: row["route"] for row in active["modelRoutes"]}
    assert inactive_routes["fractional-kelly-sizing"] == "INACTIVE"
    assert active_routes["fractional-kelly-sizing"] == "ELIGIBLE"
    assert "SIZE" in active["eligibleActions"]


def test_dynamic_execution_requires_frozen_target_and_costs() -> None:
    result = route_investment_decision(
        _context(
            risk="SET",
            tags=["TARGET_PORTFOLIO_EXISTS", "TRANSACTION_COST_ESTIMATES_AVAILABLE"],
        ),
        _atlas(),
    )
    routes = {row["modelKey"]: row["route"] for row in result["modelRoutes"]}
    assert routes["dynamic-cost-aware-trading"] == "ELIGIBLE"
    assert "EXECUTION_PLAN" in result["eligibleActions"]
    assert result["externalFinancialEffectAllowed"] is False
