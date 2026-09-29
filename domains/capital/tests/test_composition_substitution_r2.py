from __future__ import annotations

import json
from pathlib import Path

import pytest

from ordivon_capital.governance.circuit_lowering import (
    FinancialCircuitError,
    load_and_lower,
    lower_financial_circuit,
)

ROOT = Path(__file__).resolve().parents[1]


def load(path: str):
    return json.loads((ROOT / path).read_text())


def test_r2_success_cases_match_frozen_r1_migration_oracle():
    oracle = load("acceptance/r2-migration/r1-composition-outcomes.json")
    specs = {
        "PUBLIC_MARKET_OBSERVATION_R2": "circuits/public-market-observation-r2.json",
        "PORTFOLIO_RISK_ANALYSIS_R2": "circuits/portfolio-risk-analysis-r2.json",
        "COUNTERFACTUAL_ANALYSIS_R2": "circuits/counterfactual-analysis-r2.json",
        "NONLIVE_EFFECT_QUALIFICATION_R2": "circuits/nonlive-effect-qualification-r2.json",
    }
    by_id = {row["id"]: row for row in oracle["successCases"]}
    for circuit_id, path in specs.items():
        expected = by_id[circuit_id]
        actual = load_and_lower(path)
        assert actual["legoIds"] == expected["legoIds"]
        assert actual["effectClasses"] == expected["effectClasses"]
        assert actual["unresolvedEvidenceObligations"] == expected["unresolvedEvidenceObligations"]
        assert actual["authorityGranted"] == expected["authorityGranted"] is False
        assert actual["executionPerformed"] == expected["executionPerformed"] is False
        assert actual["semanticCompletionEvaluated"] == expected["semanticCompletionEvaluated"] is False


def test_r2_preserves_r1_rejection_classes_after_local_compiler_deletion():
    private = load("circuits/public-market-observation-r2.json")
    private["circuitId"] = "PRIVATE_BLOCKED"
    private["stages"][0]["legoId"] = "capital.trading.okx-readonly-client"
    private["authorityBindings"] = [{"authorityClass": "PRIVATE_READ", "authorityOwnerId": "capital.governance", "contractPath": "config/private_reality_policy.json"}]
    prohibited = load("circuits/portfolio-risk-analysis-r2.json")
    prohibited["requestedUse"] = "automatic trade sizing"
    challenger = load("circuits/nonlive-effect-qualification-r2.json")
    challenger["stages"][1]["legoId"] = "capital.candidate.nautilus-nonlive-effect"
    missing_reserve = load("circuits/nonlive-effect-qualification-r2.json")
    missing_reserve["stages"] = [row for row in missing_reserve["stages"] if row["id"] != "reserve"]
    missing_reserve["stages"][0]["dependsOn"] = []
    unknown = load("circuits/portfolio-risk-analysis-r2.json")
    unknown["stages"][0]["legoId"] = "capital.unknown.nope"
    retired = load("circuits/portfolio-risk-analysis-r2.json")
    retired["stages"][0]["legoId"] = "capital.retired.regime-card"
    duplicate = load("circuits/counterfactual-analysis-r2.json")
    duplicate["stages"][1]["legoId"] = duplicate["stages"][0]["legoId"]

    cases = [
        (private, "blocked by independent authority"),
        (prohibited, "explicitly prohibited"),
        (challenger, "challenger"),
        (missing_reserve, "Reserve LEGO"),
        (unknown, "unregistered LEGO"),
        (retired, "retired LEGO"),
        (duplicate, "duplicate LEGO identities"),
    ]
    for spec, pattern in cases:
        with pytest.raises(FinancialCircuitError, match=pattern):
            lower_financial_circuit(spec)
