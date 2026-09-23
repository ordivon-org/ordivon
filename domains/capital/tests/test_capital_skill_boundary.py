from __future__ import annotations

import json
from pathlib import Path

CAPITAL = Path(__file__).resolve().parents[1]


def load(rel: str):
    return json.loads((CAPITAL / rel).read_text())


def test_capital_skill_contract_is_advisory_and_path_independent():
    contract = load("contracts/capital-skill-boundary-v1.json")
    assert contract["canonicalSkillStandard"] == "Agent Skills"
    assert contract["truthRole"] == "ADVISORY_SKILL_BOUNDARY_NOT_FINANCIAL_AUTHORITY"
    assert (
        contract["bindingTruthRole"]
        == "EXTERNAL_PROJECT_SCOPE_ADVISORY_BINDING_NOT_CAPITAL_SOURCE_DEPENDENCY"
    )
    assert set(contract["skills"]) == {
        "capital-observe",
        "capital-risk",
        "capital-reconcile",
    }
    for name, row in contract["skills"].items():
        assert row["skillId"] == name
        assert "path" not in row


def test_skill_contract_cannot_infer_risk_or_initiate_effects():
    contract = load("contracts/capital-skill-boundary-v1.json")
    risk = contract["skills"]["capital-risk"]
    observe = contract["skills"]["capital-observe"]
    reconcile = contract["skills"]["capital-reconcile"]
    assert "risk appetite inference" in risk["mustNotOwn"]
    assert "provider write" in observe["mustNotOwn"]
    assert "order submission" in reconcile["mustNotOwn"]
    assert "blind resend" in reconcile["mustNotOwn"]
    production = load("contracts/production-authorization.json")
    assert production["state"] == "BLOCK_NOT_GRANTED"
    assert production["externalFinancialWriteAllowed"] is False
