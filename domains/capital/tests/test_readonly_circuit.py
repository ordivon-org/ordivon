from __future__ import annotations

from copy import deepcopy

import pytest

from ordivon_capital.governance.read_circuit import (
    ReadCircuitError,
    build_circuit_receipt,
    compile_readonly_circuit,
    run_readonly_circuit,
)


def _portfolio():
    return {
        "equityUsd": "100",
        "availableEquityUsd": "40",
        "initialMarginUsd": "30",
        "maintenanceMarginUsd": "5",
        "positions": [
            {
                "instrumentId": "SNDK",
                "signedNotionalUsd": "300",
                "factorLoadings": {"memory": "1", "semiconductor": "0.7"},
            }
        ],
    }


def test_compiler_is_deterministic_and_effect_free():
    goal = {"kind": "PORTFOLIO_RISK_R1", "label": "risk"}
    a = compile_readonly_circuit(goal=goal, context={"cut": "fixed"})
    b = compile_readonly_circuit(goal=goal, context={"cut": "fixed"})
    assert a == b
    assert a["effectClasses"] == []
    assert a["externalFinancialWriteAllowed"] is False
    assert a["authorityGranted"] is False


def test_compiler_rejects_unknown_family():
    with pytest.raises(ReadCircuitError, match="unsupported"):
        compile_readonly_circuit(goal={"kind": "AUTO_TRADE"})


def test_runner_rejects_tampered_circuit():
    circuit = compile_readonly_circuit(goal={"kind": "PORTFOLIO_RISK_R1"})
    bad = deepcopy(circuit)
    bad["terminalClaim"] = "TRADE_APPROVED"
    with pytest.raises(ReadCircuitError, match="digest mismatch"):
        run_readonly_circuit(circuit=bad, inputs={"portfolio": _portfolio()})


def test_portfolio_risk_circuit_preserves_unset_budget():
    circuit = compile_readonly_circuit(goal={"kind": "PORTFOLIO_RISK_R1"})
    result = run_readonly_circuit(
        circuit=circuit,
        inputs={"portfolio": _portfolio(), "returns": [0.01] * 19 + [-0.20]},
    )
    report = result["output"]["riskReport"]
    assert report["nodes"]["riskBudgetRegistration"]["standing"] == "UNSET"
    assert report["nodes"]["riskLimitEvaluation"]["standing"] == "INCOMPLETE"
    assert result["externalFinancialWritesAttempted"] is False


def test_counterfactual_circuit_never_ranks_or_approves():
    circuit = compile_readonly_circuit(goal={"kind": "COUNTERFACTUAL_ANALYSIS_R1"})
    result = run_readonly_circuit(
        circuit=circuit,
        inputs={
            "portfolio": _portfolio(),
            "scenario": {
                "scenarioId": "d25",
                "action": "DE_RISK",
                "instrumentId": "SNDK",
                "reductionFraction": "0.25",
            },
        },
    )
    out = result["output"]
    assert out["evidenceCompletenessGate"]["standing"] == "INCOMPLETE"
    assert "rankingProduced" not in out
    assert "winnerSelected" not in out
    assert result["standing"] == "MECHANICALLY_COMPLETED"


def test_public_market_observation_circuit_is_supplied_data_only():
    circuit = compile_readonly_circuit(goal={"kind": "PUBLIC_MARKET_OBSERVATION_R1"})
    result = run_readonly_circuit(
        circuit=circuit,
        inputs={
            "market": {"kind": "test-market", "instrumentId": "BTC-USDT"},
            "oiSamples": [
                {"instrumentId": "BTC-USDT", "observedAtMs": 1000, "openInterestUsd": "100"},
                {"instrumentId": "BTC-USDT", "observedAtMs": 2000, "openInterestUsd": "110"},
            ],
        },
    )
    obs = result["output"]["marketObservation"]
    assert obs["kind"] == "test-market"
    assert obs["openInterestChangePct"] == "10.000000"
    assert result["externalFinancialWritesAttempted"] is False


def test_receipt_is_identity_bound_and_non_semantic():
    circuit = compile_readonly_circuit(goal={"kind": "PORTFOLIO_RISK_R1"})
    result = run_readonly_circuit(circuit=circuit, inputs={"portfolio": _portfolio()})
    receipt = build_circuit_receipt(circuit=circuit, result=result)
    assert receipt["standing"] == "MECHANICAL_COMPLETION_ONLY"
    assert receipt["semanticCompletionEvaluated"] is False
    assert receipt["authorityGranted"] is False
    assert receipt["receiptDigest"].startswith("sha256:")
