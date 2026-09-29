from __future__ import annotations

import json
from pathlib import Path

import pytest

from ordivon_capital.governance.owner_authority import (
    OwnerAuthorityValidationError,
    assert_capital_constitution_schema_identity,
    assert_delegation_grant_schema_identity,
    project_owner_governance_envelope,
    validate_capital_constitution_document,
    validate_delegation_grant_document,
)
from ordivon_capital.portfolio.decision_router import route_investment_decision
from ordivon_capital.research.investment_model_atlas import (
    validate_investment_model_atlas_document,
)
from ordivon_capital.risk.risk_capacity_validation import (
    RiskCapacityValidationError,
    assert_risk_capacity_schema_identity,
    validate_risk_capacity_document,
)

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "planning/r3/examples"


def _load(path: Path) -> dict:
    return json.loads(path.read_text())


def _constitution() -> dict:
    return _load(EXAMPLES / "constitution-example.json")


def _delegation() -> dict:
    return _load(EXAMPLES / "delegation-example.json")


def _capacity() -> dict:
    return _load(EXAMPLES / "risk-capacity-example.json")


def _risk_budget() -> dict:
    return _load(ROOT / "config/portfolio_risk_budget.json")


def _atlas() -> dict:
    return _load(ROOT / "config/investment_model_atlas.json")


def test_r3_owner_authority_schemas_are_exact_digest_bound():
    assert_capital_constitution_schema_identity(
        ROOT / "schema/capital-constitution-v1.schema.json"
    )
    assert_delegation_grant_schema_identity(
        ROOT / "schema/capital-delegation-grant-v1.schema.json"
    )
    assert_risk_capacity_schema_identity(ROOT / "schema/capital-risk-capacity-v1.schema.json")


def test_r3_examples_pass_local_fail_closed_validators():
    validate_capital_constitution_document(_constitution())
    validate_delegation_grant_document(_delegation())
    validate_risk_capacity_document(_capacity())


def test_model_or_agent_cannot_mint_owner_preference():
    constitution = _constitution()
    constitution["riskAppetite"] = [
        {
            "preferenceId": "risk.inferred",
            "scope": "financial",
            "statement": "model inferred willingness to lose capital",
            "preferenceSource": "MODEL_INFERRED",
        }
    ]
    with pytest.raises(OwnerAuthorityValidationError, match="EXPLICIT_PRINCIPAL"):
        validate_capital_constitution_document(constitution)


def test_risk_capacity_cannot_mint_appetite_budget_or_effect_authority():
    for field in (
        "riskAppetiteInferred",
        "riskBudgetGranted",
        "externalEffectAuthorityGranted",
    ):
        capacity = _capacity()
        capacity[field] = True
        with pytest.raises(RiskCapacityValidationError):
            validate_risk_capacity_document(capacity)


def test_l5_requires_explicit_constitution_change_grant():
    delegation = _delegation()
    delegation["level"] = "L5_CHANGE_CONSTITUTION"
    with pytest.raises(OwnerAuthorityValidationError, match="explicit"):
        validate_delegation_grant_document(delegation)

    delegation["constitutionalChangeAllowed"] = True
    validate_delegation_grant_document(delegation)


def test_current_unset_risk_budget_stays_unset_even_with_capacity_and_delegation():
    envelope = project_owner_governance_envelope(
        constitution=_constitution(),
        delegation=_delegation(),
        risk_capacity=_capacity(),
        registered_risk_budget=_risk_budget(),
        required_level="L2_RECOMMEND",
    )
    assert envelope["standing"] == "RESEARCH_ONLY_RISK_BUDGET_UNSET"
    assert envelope["riskBudgetStanding"] == "UNSET"
    assert envelope["riskBudgetSynthesized"] is False
    assert envelope["sizingEligibleForDownstreamPolicy"] is False
    assert envelope["ownerRiskAppetiteInferred"] is False
    assert envelope["providerPermissionGranted"] is False
    assert envelope["credentialAuthorityGranted"] is False
    assert envelope["externalEffectAuthorityGranted"] is False


def test_capacity_can_block_but_never_expand_owner_budget():
    active_budget = _risk_budget()
    active_budget["standing"] = "ACTIVE"
    active_budget["limits"] = {
        "maxGrossToEquity": 1.0,
        "maxLargestPositionGrossShare": 0.2,
        "minAvailableEquityRatio": 0.3,
        "shockMagnitudePct": 10.0,
        "maxEquityLossPctAtShock": 10.0,
    }
    delegation = _delegation()
    delegation["level"] = "L3_PREPARE"

    insufficient = _capacity()
    insufficient["standing"] = "INSUFFICIENT"
    blocked = project_owner_governance_envelope(
        constitution=_constitution(),
        delegation=delegation,
        risk_capacity=insufficient,
        registered_risk_budget=active_budget,
        required_level="L3_PREPARE",
    )
    assert blocked["standing"] == "CAPACITY_BLOCKED"
    assert blocked["sizingEligibleForDownstreamPolicy"] is False

    supported = _capacity()
    supported["standing"] = "SUPPORTED"
    ready = project_owner_governance_envelope(
        constitution=_constitution(),
        delegation=delegation,
        risk_capacity=supported,
        registered_risk_budget=active_budget,
        required_level="L3_PREPARE",
    )
    assert ready["standing"] == "READY_FOR_BOUNDED_DOWNSTREAM_POLICY"
    assert ready["sizingEligibleForDownstreamPolicy"] is True
    assert ready["externalEffectAuthorityGranted"] is False


def test_l4_delegation_still_does_not_mint_provider_or_effect_authority():
    active_budget = _risk_budget()
    active_budget["standing"] = "ACTIVE"
    for key in active_budget["limits"]:
        active_budget["limits"][key] = 1
    delegation = _delegation()
    delegation["level"] = "L4_EXECUTE_BOUNDED"
    delegation["effectClasses"] = ["SIMULATED_EXCHANGE_ORDER_EFFECT"]
    capacity = _capacity()
    capacity["standing"] = "SUPPORTED"

    envelope = project_owner_governance_envelope(
        constitution=_constitution(),
        delegation=delegation,
        risk_capacity=capacity,
        registered_risk_budget=active_budget,
        required_level="L4_EXECUTE_BOUNDED",
    )
    assert envelope["standing"] == "DOWNSTREAM_PROVIDER_AUTHORITY_REQUIRED"
    assert envelope["providerPermissionGranted"] is False
    assert envelope["credentialAuthorityGranted"] is False
    assert envelope["externalEffectAuthorityGranted"] is False
    assert envelope["externalEffectCommitted"] is False


def test_existing_investment_router_remains_research_only_when_registered_budget_unset():
    atlas = _atlas()
    validate_investment_model_atlas_document(atlas)
    route = route_investment_decision(
        {
            "decisionId": "r3-regression",
            "asOf": "2026-09-29T00:00:00Z",
            "objective": "preserve current authority boundary",
            "horizon": "research-only",
            "riskBudgetStatus": "UNSET",
            "stateTags": [],
        },
        atlas,
    )
    assert route["decisionStanding"] == "RESEARCH_ONLY_RISK_BUDGET_UNSET"
    assert "SIZE" not in route["eligibleActions"]
    assert route["externalFinancialEffectAllowed"] is False


def test_schema_identity_drift_requires_requalification(tmp_path: Path):
    cases = [
        (
            ROOT / "schema/capital-constitution-v1.schema.json",
            assert_capital_constitution_schema_identity,
        ),
        (
            ROOT / "schema/capital-delegation-grant-v1.schema.json",
            assert_delegation_grant_schema_identity,
        ),
        (
            ROOT / "schema/capital-risk-capacity-v1.schema.json",
            assert_risk_capacity_schema_identity,
        ),
    ]
    for index, (source, validator) in enumerate(cases):
        changed = tmp_path / f"changed-{index}.json"
        changed.write_text(source.read_text() + "\n")
        with pytest.raises(ValueError, match="requalification required"):
            validator(changed)


def test_r3_owner_authority_runtime_source_does_not_import_jsonschema():
    sources = [
        ROOT / "src/ordivon_capital/governance/owner_authority.py",
        ROOT / "src/ordivon_capital/risk/risk_capacity_validation.py",
    ]
    for path in sources:
        assert "jsonschema" not in path.read_text()
