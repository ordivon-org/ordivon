"""Pure Portfolio LEGO: evaluate scenario evidence, not financial effect admission.

PASS means the caller supplied fields sufficient for this structural review;
it is never independent market-source attestation or trade authorization.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

DECISION_IMPLEMENTATION = "LOCAL_DETERMINISTIC_PYTHON"


class ScenarioEvidenceError(ValueError):
    """Invalid scenario evidence and numerical facts."""


def _amount(value: Any) -> Decimal:
    try:
        result = Decimal(str(value))
        if not result.is_finite():
            raise InvalidOperation
        return result
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ScenarioEvidenceError(f"invalid decimal scenario fact: {value!r}") from exc


def _evidence_statuses(facts: dict[str, Any]) -> dict[str, str]:
    standing = facts.get("riskBudgetStanding")
    if standing == "SATISFIED":
        risk = "PASS"
    elif standing == "BREACHED":
        risk = "FAIL"
    else:
        risk = "INCOMPLETE"

    action = facts["action"]
    if action == "DE_RISK":
        gross = (
            "PASS" if facts["projectedGrossToEquity"] < facts["baselineGrossToEquity"] else "FAIL"
        )
    elif action in {"HOLD", "RECONCILE"}:
        gross = (
            "PASS" if facts["projectedGrossToEquity"] == facts["baselineGrossToEquity"] else "FAIL"
        )
    else:
        gross = "PASS"

    needs_new = facts["needsNewPositionEvidence"]
    margin = (
        "PASS"
        if needs_new and facts["marginMeasured"]
        else "INCOMPLETE"
        if needs_new
        else "NOT_REQUIRED"
    )
    carry = (
        "PASS"
        if needs_new and facts["carryMeasured"]
        else "INCOMPLETE"
        if needs_new
        else "NOT_REQUIRED"
    )
    changes = facts["changesPosition"]
    liquidity = (
        "PASS"
        if changes and facts["liquidityMeasured"]
        else "INCOMPLETE"
        if changes
        else "NOT_REQUIRED"
    )

    if action == "HEDGE":
        factor = facts.get("targetFactorStanding")
        target = (
            "PASS"
            if factor == "TARGET_FACTOR_ABSOLUTE_EXPOSURE_REDUCED"
            else "FAIL"
            if factor
            in {
                "TARGET_FACTOR_ABSOLUTE_EXPOSURE_INCREASED",
                "TARGET_FACTOR_ABSOLUTE_EXPOSURE_UNCHANGED",
            }
            else "INCOMPLETE"
        )
        if (
            facts.get("dependenceComponentId") == "portfolio-dependence-analysis"
            and facts.get("dependenceSampleCountPresent") is True
        ):
            dependence = "PASS"
        elif (
            facts.get("dependencePresent") is True
            and facts.get("dependenceComponentId") != "portfolio-dependence-analysis"
        ):
            dependence = "FAIL"
        else:
            dependence = "INCOMPLETE"
    else:
        target = "NOT_REQUIRED"
        dependence = "NOT_REQUIRED"

    if action == "DIVERSIFY":
        if facts.get("diversificationComponentId") == "portfolio-dependence-analysis":
            diversification = "PASS"
        elif (
            facts.get("diversificationPresent") is True
            and facts.get("diversificationComponentId") != "portfolio-dependence-analysis"
        ):
            diversification = "FAIL"
        else:
            diversification = "INCOMPLETE"
    else:
        diversification = "NOT_REQUIRED"

    reconciliation = (
        "PASS"
        if action == "RECONCILE" and facts.get("reconciliationSignpostDefined") is True
        else "INCOMPLETE"
        if action == "RECONCILE"
        else "NOT_REQUIRED"
    )
    return {
        "RISK_BUDGET": risk,
        "GROSS_DIRECTION": gross,
        "MARGIN_DELTA": margin,
        "FUNDING_BASIS_CARRY": carry,
        "LIQUIDITY_COST": liquidity,
        "TARGET_FACTOR_MECHANICS": target,
        "DEPENDENCE_EVIDENCE": dependence,
        "DIVERSIFICATION_EVIDENCE": diversification,
        "RECONCILIATION_SIGNPOST": reconciliation,
    }


def evaluate_scenario_evidence(
    *,
    counterfactual: dict[str, Any],
    risk_budget_evaluation: dict[str, Any] | None = None,
    evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Evaluate evidence completeness only; a PASS never authorizes trading."""

    evidence = evidence or {}
    action = str(counterfactual.get("action") or "").upper()
    allowed_actions = {"DE_RISK", "HEDGE", "DIVERSIFY", "HOLD", "RECONCILE"}
    if action not in allowed_actions:
        raise ScenarioEvidenceError("counterfactual action is invalid")
    baseline = counterfactual.get("baseline") or {}
    projected = counterfactual.get("projected") or {}
    mechanics = counterfactual.get("hedgeMechanics") or {}
    dependence = evidence.get("dependence")
    diversification = evidence.get("diversification")
    facts = {
        "action": action,
        "riskBudgetStanding": (risk_budget_evaluation or {}).get("standing"),
        "baselineGrossToEquity": _amount(baseline.get("grossToEquity")),
        "projectedGrossToEquity": _amount(projected.get("grossToEquity")),
        "changesPosition": action in {"DE_RISK", "HEDGE", "DIVERSIFY"},
        "needsNewPositionEvidence": action in {"HEDGE", "DIVERSIFY"},
        "marginMeasured": isinstance(evidence.get("margin"), dict)
        and evidence["margin"].get("measured") is True,
        "carryMeasured": isinstance(evidence.get("carry"), dict)
        and evidence["carry"].get("measured") is True,
        "liquidityMeasured": isinstance(evidence.get("liquidity"), dict)
        and evidence["liquidity"].get("measured") is True,
        "targetFactorStanding": mechanics.get("standing"),
        "dependencePresent": isinstance(dependence, dict),
        "dependenceComponentId": (
            dependence.get("componentId") if isinstance(dependence, dict) else None
        ),
        "dependenceSampleCountPresent": isinstance(dependence, dict)
        and dependence.get("overlapReturnCount") is not None,
        "diversificationPresent": isinstance(diversification, dict),
        "diversificationComponentId": (
            diversification.get("componentId") if isinstance(diversification, dict) else None
        ),
        "reconciliationSignpostDefined": isinstance(evidence.get("reconciliationSignpost"), dict)
        and evidence["reconciliationSignpost"].get("defined") is True,
    }
    statuses = _evidence_statuses(facts)
    order = [
        "RISK_BUDGET",
        "GROSS_DIRECTION",
        "MARGIN_DELTA",
        "FUNDING_BASIS_CARRY",
        "LIQUIDITY_COST",
        "TARGET_FACTOR_MECHANICS",
        "DEPENDENCE_EVIDENCE",
        "DIVERSIFICATION_EVIDENCE",
        "RECONCILIATION_SIGNPOST",
    ]
    detail = {
        "RISK_BUDGET": "explicit risk-limit evaluation",
        "GROSS_DIRECTION": "action exposure-direction constraint",
        "MARGIN_DELTA": "incremental margin evidence",
        "FUNDING_BASIS_CARRY": "funding/basis carry evidence",
        "LIQUIDITY_COST": "spread/impact evidence",
        "TARGET_FACTOR_MECHANICS": "named target-factor mechanics",
        "DEPENDENCE_EVIDENCE": "registered dependence evidence",
        "DIVERSIFICATION_EVIDENCE": "registered diversification evidence",
        "RECONCILIATION_SIGNPOST": "explicit next reconciliation evidence boundary",
    }
    checks = [
        {"id": check_id, "status": statuses[check_id], "detail": detail[check_id]}
        for check_id in order
    ]
    failures = [row["id"] for row in checks if row["status"] == "FAIL"]
    incomplete = [row["id"] for row in checks if row["status"] == "INCOMPLETE"]
    standing = "FAIL" if failures else "INCOMPLETE" if incomplete else "PASS"
    return {
        "schemaVersion": 2,
        "kind": "ordivon.capital.governance.pre-trade-evidence-control",
        "componentId": "pre-trade-evidence-control",
        "decisionImplementation": DECISION_IMPLEMENTATION,
        "scenarioId": counterfactual.get("scenarioId"),
        "action": action,
        "standing": standing,
        "checks": checks,
        "failedChecks": failures,
        "incompleteChecks": incomplete,
    }
