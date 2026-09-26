from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any

from ordivon_capital.governance.circuit_lowering import load_and_lower
from ordivon_capital.markets.market_sensors import (
    merge_market_observations,
    open_interest_change,
    repeated_microstructure,
)
from ordivon_capital.portfolio.portfolio_counterfactuals import (
    build_action_counterfactual,
    evaluate_constraint_gate,
)
from ordivon_capital.risk.portfolio_risk import (
    build_exposure_ledger,
    build_portfolio_risk_report,
    evaluate_risk_budget,
    historical_expected_shortfall,
)


class ReadCircuitError(ValueError):
    """Fail-closed error for bounded read-only Capital circuits."""


_FAMILIES: dict[str, str] = {
    "PUBLIC_MARKET_OBSERVATION_R1": "circuits/public-market-observation-r2.json",
    "PORTFOLIO_RISK_R1": "circuits/portfolio-risk-analysis-r2.json",
    "COUNTERFACTUAL_ANALYSIS_R1": "circuits/counterfactual-analysis-r2.json",
}


def _family_definition(kind: str) -> tuple[dict[str, Any], dict[str, Any]]:
    relative = _FAMILIES.get(kind)
    if relative is None:
        raise ReadCircuitError(f"unsupported read-only circuit kind: {kind or '<blank>'}")
    lowering = load_and_lower(relative)
    capital_spec = json.loads((__import__("pathlib").Path(__file__).resolve().parents[3] / relative).read_text())
    return capital_spec, lowering



def _json_clone(value: Any, label: str) -> Any:
    try:
        return json.loads(json.dumps(value, sort_keys=True, separators=(",", ":")))
    except (TypeError, ValueError) as exc:
        raise ReadCircuitError(f"{label} must be JSON-serializable") from exc


def _digest(value: Any) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode()
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _portfolio_input(value: Mapping[str, Any]) -> dict[str, Any]:
    required = ("equityUsd", "availableEquityUsd", "positions")
    missing = [key for key in required if key not in value]
    if missing:
        raise ReadCircuitError(f"portfolio missing required fields: {missing}")
    return {
        "equity_usd": value["equityUsd"],
        "available_equity_usd": value["availableEquityUsd"],
        "positions": value["positions"],
        "initial_margin_usd": value.get("initialMarginUsd"),
        "maintenance_margin_usd": value.get("maintenanceMarginUsd"),
    }


def compile_readonly_circuit(
    *,
    goal: Mapping[str, Any],
    context: Mapping[str, Any] | None = None,
    available_authorities: set[str] | frozenset[str] | None = None,
) -> dict[str, Any]:
    """Compile one bounded effect-free Capital circuit.

    The goal kind is explicit. R1 intentionally does not infer investment intent,
    risk appetite, private-data permission, or effect authority from free text.
    """
    if not isinstance(goal, Mapping):
        raise ReadCircuitError("goal must be an object")
    kind = str(goal.get("kind") or "").strip().upper()
    family, lowering = _family_definition(kind)

    normalized_goal = _json_clone(dict(goal), "goal")
    normalized_goal["kind"] = kind
    normalized_context = _json_clone(dict(context or {}), "context")
    authorities = set(available_authorities or set())
    if lowering["effectClasses"]:
        raise ReadCircuitError("read-only circuit cannot contain provider effect classes")
    nodes = [
        {
            "nodeId": stage["id"],
            "legoId": stage["legoId"],
            "operation": stage["operation"],
            "dependsOn": list(stage["dependsOn"]),
        }
        for stage in family["stages"]
    ]

    circuit: dict[str, Any] = {
        "schemaVersion": 1,
        "kind": "ordivon.capital.readonly-circuit",
        "family": kind,
        "goal": normalized_goal,
        "context": normalized_context,
        "availableAuthorities": sorted(authorities),
        "nodes": _json_clone(nodes, "nodes"),
        "terminalClaim": family["terminalClaim"],
        "compositionStanding": "ADMITTED_COMPOSITION_ONLY",
        "unresolvedEvidenceObligations": lowering["unresolvedEvidenceObligations"],
        "effectClasses": [],
        "externalFinancialWriteAllowed": False,
        "authorityGranted": False,
        "semanticCompletionEvaluated": False,
    }
    circuit["circuitDigest"] = _digest(circuit)
    return circuit


def _validate_circuit(circuit: Mapping[str, Any]) -> dict[str, Any]:
    value = _json_clone(dict(circuit), "circuit")
    digest = value.pop("circuitDigest", None)
    if value.get("kind") != "ordivon.capital.readonly-circuit":
        raise ReadCircuitError("unexpected circuit kind")
    if digest != _digest(value):
        raise ReadCircuitError("circuit digest mismatch")
    value["circuitDigest"] = digest
    if value.get("effectClasses") != [] or value.get("externalFinancialWriteAllowed") is not False:
        raise ReadCircuitError("read-only circuit effect boundary violated")
    return value


def _run_market(inputs: Mapping[str, Any]) -> dict[str, Any]:
    market = inputs.get("market")
    if not isinstance(market, Mapping):
        raise ReadCircuitError("market input must be an object")
    oi = None
    micro = None
    if "oiSamples" in inputs:
        samples = inputs["oiSamples"]
        if not isinstance(samples, Sequence) or isinstance(samples, (str, bytes)):
            raise ReadCircuitError("oiSamples must be a sequence")
        oi = open_interest_change(samples)
    if "microstructureSamples" in inputs:
        samples = inputs["microstructureSamples"]
        if not isinstance(samples, Sequence) or isinstance(samples, (str, bytes)):
            raise ReadCircuitError("microstructureSamples must be a sequence")
        micro = repeated_microstructure(samples)
    merged = merge_market_observations(market, oi_change=oi, microstructure=micro)
    return {"marketObservation": merged}


def _run_risk(inputs: Mapping[str, Any]) -> dict[str, Any]:
    portfolio = inputs.get("portfolio")
    if not isinstance(portfolio, Mapping):
        raise ReadCircuitError("portfolio input must be an object")
    ledger = build_exposure_ledger(**_portfolio_input(portfolio))
    tail = None
    if "returns" in inputs:
        returns = inputs["returns"]
        if not isinstance(returns, Sequence) or isinstance(returns, (str, bytes)):
            raise ReadCircuitError("returns must be a sequence")
        tail = historical_expected_shortfall(returns)
    risk_budget = inputs.get("riskBudget")
    if risk_budget is not None and not isinstance(risk_budget, Mapping):
        raise ReadCircuitError("riskBudget must be an object")
    report = build_portfolio_risk_report(
        exposure_ledger=ledger,
        risk_budget=risk_budget,
        tail_risk_report=tail,
    )
    return {"exposureLedger": ledger, "riskReport": report}


def _run_counterfactual(inputs: Mapping[str, Any]) -> dict[str, Any]:
    portfolio = inputs.get("portfolio")
    scenario = inputs.get("scenario")
    if not isinstance(portfolio, Mapping):
        raise ReadCircuitError("portfolio input must be an object")
    if not isinstance(scenario, Mapping):
        raise ReadCircuitError("scenario input must be an object")
    ledger = build_exposure_ledger(**_portfolio_input(portfolio))
    risk_budget = inputs.get("riskBudget")
    if risk_budget is None:
        risk_report = build_portfolio_risk_report(exposure_ledger=ledger)
        risk_eval = risk_report["nodes"]["riskLimitEvaluation"]
    else:
        if not isinstance(risk_budget, Mapping):
            raise ReadCircuitError("riskBudget must be an object")
        risk_eval = evaluate_risk_budget(exposure_ledger=ledger, budget=risk_budget)
    counterfactual = build_action_counterfactual(
        exposure_ledger=ledger,
        scenario=scenario,
    )
    evidence = inputs.get("evidence")
    if evidence is not None and not isinstance(evidence, Mapping):
        raise ReadCircuitError("evidence must be an object")
    gate = evaluate_constraint_gate(
        counterfactual=counterfactual,
        risk_budget_evaluation=risk_eval,
        evidence=evidence,
    )
    return {
        "exposureLedger": ledger,
        "riskBudgetEvaluation": risk_eval,
        "counterfactual": counterfactual,
        "evidenceCompletenessGate": gate,
    }


_RUNNERS = {
    "PUBLIC_MARKET_OBSERVATION_R1": _run_market,
    "PORTFOLIO_RISK_R1": _run_risk,
    "COUNTERFACTUAL_ANALYSIS_R1": _run_counterfactual,
}


def run_readonly_circuit(
    *,
    circuit: Mapping[str, Any],
    inputs: Mapping[str, Any],
) -> dict[str, Any]:
    """Run one compiled read-only circuit using current owner-native primitives."""
    checked = _validate_circuit(circuit)
    if not isinstance(inputs, Mapping):
        raise ReadCircuitError("inputs must be an object")
    runner = _RUNNERS.get(checked["family"])
    if runner is None:
        raise ReadCircuitError("no R1 runner for circuit family")
    output = runner(inputs)
    node_receipts = [
        {
            "nodeId": node["nodeId"],
            "legoId": node["legoId"],
            "operation": node["operation"],
            "standing": "MECHANICALLY_EXECUTED",
        }
        for node in checked["nodes"]
    ]
    result = {
        "schemaVersion": 1,
        "kind": "ordivon.capital.readonly-circuit-result",
        "circuitDigest": checked["circuitDigest"],
        "family": checked["family"],
        "standing": "MECHANICALLY_COMPLETED",
        "nodeReceipts": node_receipts,
        "output": output,
        "outputDigest": _digest(output),
        "externalFinancialWritesAttempted": False,
        "semanticCompletionEvaluated": False,
    }
    return result


def build_circuit_receipt(
    *,
    circuit: Mapping[str, Any],
    result: Mapping[str, Any],
) -> dict[str, Any]:
    checked = _validate_circuit(circuit)
    result_value = _json_clone(dict(result), "result")
    if result_value.get("kind") != "ordivon.capital.readonly-circuit-result":
        raise ReadCircuitError("unexpected result kind")
    if result_value.get("circuitDigest") != checked["circuitDigest"]:
        raise ReadCircuitError("result/circuit identity mismatch")
    if result_value.get("externalFinancialWritesAttempted") is not False:
        raise ReadCircuitError("read-only result claims external financial write")
    receipt: dict[str, Any] = {
        "schemaVersion": 1,
        "kind": "ordivon.capital.readonly-circuit-receipt",
        "circuitDigest": checked["circuitDigest"],
        "family": checked["family"],
        "resultDigest": _digest(result_value),
        "nodeReceipts": result_value["nodeReceipts"],
        "outputDigest": result_value["outputDigest"],
        "terminalClaim": checked["terminalClaim"],
        "unresolvedEvidenceObligations": checked["unresolvedEvidenceObligations"],
        "standing": "MECHANICAL_COMPLETION_ONLY",
        "authorityGranted": False,
        "externalFinancialWritesAttempted": False,
        "semanticCompletionEvaluated": False,
    }
    receipt["receiptDigest"] = _digest(receipt)
    return receipt
