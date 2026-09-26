from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_investment_decision_system_acceptance_preserves_authority_boundary():
    doc = json.loads((ROOT / "acceptance/investment-decision-system-r1.json").read_text())
    assert doc["standing"] == "PASS"
    assert doc["system"]["registeredExternalModels"] == 13
    assert doc["system"]["readOnlyCircuit"] == "INVESTMENT_DECISION_SUPPORT_R1"
    assert doc["authorityBoundary"]["portfolioRiskBudget"] == "UNSET"
    assert doc["authorityBoundary"]["externalFinancialEffectAllowed"] is False
    assert doc["authorityBoundary"]["riskAppetiteInferred"] is False
    assert doc["authorityBoundary"]["orderGenerationAdmitted"] is False
    assert doc["canary"]["decisionStanding"] == "RESEARCH_ONLY_RISK_BUDGET_UNSET"
