from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_investment_decision_r2_acceptance_closes_evidence_state_record_seam() -> None:
    doc = json.loads((ROOT / "acceptance/investment-decision-system-r2.json").read_text())
    assert doc["standing"] == "PASS_R2"
    assert doc["system"]["registeredExternalModels"] == 13
    assert doc["system"]["registeredStateClaims"] == 13
    assert doc["system"]["callerAuthoredStateTagsAdmittedByReadCircuit"] is False
    assert doc["authorityBoundary"]["portfolioRiskBudget"] == "UNSET"
    assert doc["authorityBoundary"]["externalFinancialEffectAllowed"] is False
    assert doc["authorityBoundary"]["causalAttributionClaimed"] is False
    assert doc["authorityBoundary"]["skillClaimed"] is False
    assert doc["canary"]["decisionStanding"] == "RESEARCH_ONLY_RISK_BUDGET_UNSET"
    assert doc["canary"]["externalFinancialWritesAttempted"] is False
