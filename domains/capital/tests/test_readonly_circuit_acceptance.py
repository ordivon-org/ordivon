from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_readonly_circuit_acceptance_is_three_family_effect_free():
    doc = json.loads(
        (ROOT / "acceptance/capital-circuit-readonly-r1.json").read_text()
    )
    assert doc["standing"] == "PASS"
    assert doc["assertions"]["familyCount"] == 3
    assert doc["assertions"]["allMechanicallyCompleted"] is True
    assert doc["assertions"]["allReceiptsMechanicalOnly"] is True
    assert doc["assertions"]["externalFinancialWritesAttempted"] is False
    assert doc["assertions"]["semanticCompletionEvaluated"] is False
    assert doc["assertions"]["riskBudgetInferred"] is False
    assert doc["assertions"]["scenarioRankingProduced"] is False
    assert {row["family"] for row in doc["families"]} == {
        "PUBLIC_MARKET_OBSERVATION_R1",
        "PORTFOLIO_RISK_R1",
        "COUNTERFACTUAL_ANALYSIS_R1",
    }
