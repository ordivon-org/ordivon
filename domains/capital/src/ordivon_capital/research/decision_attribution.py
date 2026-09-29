from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any


class DecisionAttributionError(ValueError):
    pass


def _dt(value: str) -> datetime:
    try:
        out = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError) as exc:
        raise DecisionAttributionError("timestamps must be ISO-8601") from exc
    if out.tzinfo is None:
        raise DecisionAttributionError("timestamps must be timezone-aware")
    return out


def _decimal(value: Any, field: str) -> Decimal:
    try:
        out = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise DecisionAttributionError(f"{field} must be numeric") from exc
    if not out.is_finite():
        raise DecisionAttributionError(f"{field} must be finite")
    return out


def attribute_decision_outcome(*, decision_record: dict[str, Any], outcome: dict[str, Any]) -> dict[str, Any]:
    """Bind later realized outcome to a frozen decision record without causal or skill inference."""

    if decision_record.get("kind") != "ordivon.capital.investment-decision-record":
        raise DecisionAttributionError("unexpected decision record kind")
    required = {"observedAt", "realizedReturn"}
    if not isinstance(outcome, dict) or not required.issubset(outcome):
        raise DecisionAttributionError("outcome missing required fields")
    if _dt(outcome["observedAt"]) <= _dt(decision_record["asOf"]):
        raise DecisionAttributionError("outcome must be strictly post-decision")
    realized = _decimal(outcome["realizedReturn"], "realizedReturn")
    benchmark = outcome.get("benchmarkReturn")
    excess = None
    if benchmark is not None:
        excess = realized - _decimal(benchmark, "benchmarkReturn")
    routes = decision_record["decisionRoute"].get("modelRoutes", [])
    active_models = [row["modelKey"] for row in routes if row.get("route") in {"REQUIRED", "ELIGIBLE", "RESEARCH_ONLY"}]
    return {
        "schemaVersion": 1,
        "kind": "ordivon.capital.investment-decision-outcome-attribution",
        "truthRole": "EX_POST_MEASUREMENT_NOT_CAUSAL_OR_SKILL_ATTRIBUTION",
        "decisionId": decision_record["decisionId"],
        "decisionRecordDigest": decision_record["recordDigest"],
        "decisionAsOf": decision_record["asOf"],
        "outcomeObservedAt": outcome["observedAt"],
        "realizedReturn": str(realized),
        "benchmarkReturn": None if benchmark is None else str(_decimal(benchmark, "benchmarkReturn")),
        "excessReturn": None if excess is None else str(excess),
        "decisionStanding": decision_record["decisionRoute"]["decisionStanding"],
        "stateTags": decision_record["stateProjection"]["stateTags"],
        "activeModelRoutes": active_models,
        "causalAttributionClaimed": False,
        "skillClaimed": False,
        "modelValidatedByOutcome": False,
    }
