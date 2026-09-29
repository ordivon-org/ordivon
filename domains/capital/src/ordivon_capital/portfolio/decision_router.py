from __future__ import annotations

from typing import Any

from ordivon_capital.research.investment_model_atlas import validate_investment_model_atlas_document

_RISK_STRESS_TAGS = {"LIQUIDITY_STRESS", "FUNDING_STRESS"}


class InvestmentDecisionContextError(ValueError):
    pass


def _validate_context(context: Any) -> dict[str, Any]:
    if not isinstance(context, dict):
        raise InvestmentDecisionContextError("context must be an object")
    required = {"decisionId", "asOf", "objective", "horizon", "riskBudgetStatus", "stateTags"}
    if set(context) != required:
        raise InvestmentDecisionContextError("context keys mismatch")
    for field in ("decisionId", "asOf", "objective", "horizon"):
        if not isinstance(context[field], str) or not context[field]:
            raise InvestmentDecisionContextError(f"{field} must be non-empty")
    if context["riskBudgetStatus"] not in {"SET", "UNSET"}:
        raise InvestmentDecisionContextError("riskBudgetStatus must be SET or UNSET")
    tags = context["stateTags"]
    if not isinstance(tags, list) or any(not isinstance(tag, str) or not tag for tag in tags):
        raise InvestmentDecisionContextError("stateTags must contain non-empty strings")
    if len(tags) != len(set(tags)):
        raise InvestmentDecisionContextError("stateTags must be unique")
    return context


def _route_model(model: dict[str, Any], tags: set[str]) -> str:
    if set(model["blockedTagsAny"]) & tags:
        return "BLOCKED_BY_STATE"
    if model["activation"] == "ALWAYS":
        return "REQUIRED"
    if not set(model["requiredTagsAll"]).issubset(tags):
        return "INACTIVE"
    required_any = set(model["requiredTagsAny"])
    if required_any and not required_any.intersection(tags):
        return "INACTIVE"
    if model["standing"] == "CONTESTED_CONDITIONAL":
        return "RESEARCH_ONLY"
    return "ELIGIBLE"


def route_investment_decision(context: dict[str, Any], atlas: dict[str, Any]) -> dict[str, Any]:
    """Route mature models into bounded decision support without granting financial effects."""

    current = _validate_context(context)
    validate_investment_model_atlas_document(atlas)
    tags = set(current["stateTags"])
    risk_budget_set = current["riskBudgetStatus"] == "SET"
    if risk_budget_set:
        tags.add("RISK_BUDGET_SET")
    else:
        tags.discard("RISK_BUDGET_SET")
    routes: list[dict[str, str]] = []
    eligible_actions: set[str] = {"INFORM", "ATTRIBUTION"}
    conditional_eligible = False

    for model in atlas["models"]:
        route = _route_model(model, tags)
        routes.append(
            {
                "modelKey": model["modelKey"],
                "standing": model["standing"],
                "route": route,
                "role": model["role"],
            }
        )
        if route in {"REQUIRED", "ELIGIBLE"}:
            eligible_actions.update(model["allowedActions"])
        if route == "ELIGIBLE" and set(model["allowedActions"]) & {"TILT", "SIZE"}:
            conditional_eligible = True

    risk_stress = bool(_RISK_STRESS_TAGS & tags)
    model_conflict = "MODEL_CONFLICT" in tags

    if not risk_budget_set or risk_stress or model_conflict:
        eligible_actions.discard("SIZE")

    ordered_actions = [
        action
        for action in (
            "INFORM",
            "BASELINE",
            "TILT",
            "SIZE",
            "RISK_REVIEW",
            "EXECUTION_PLAN",
            "ATTRIBUTION",
        )
        if action in eligible_actions
    ]

    if not risk_budget_set:
        decision_standing = "RESEARCH_ONLY_RISK_BUDGET_UNSET"
    elif risk_stress:
        decision_standing = "RISK_REVIEW_REQUIRED"
    elif model_conflict:
        decision_standing = "MODEL_CONFLICT_REVIEW"
    elif conditional_eligible:
        decision_standing = "CONDITIONAL_OVERLAY_REVIEW"
    else:
        decision_standing = "BASELINE_ONLY"

    return {
        "schemaVersion": 1,
        "kind": "ordivon.capital.investment-decision-route",
        "truthRole": "DECISION_SUPPORT_NOT_INVESTMENT_OR_EXECUTION_TRUTH",
        "decisionId": current["decisionId"],
        "asOf": current["asOf"],
        "objective": current["objective"],
        "horizon": current["horizon"],
        "riskBudgetStatus": current["riskBudgetStatus"],
        "decisionStanding": decision_standing,
        "riskGovernor": {
            "stressObserved": risk_stress,
            "modelConflict": model_conflict,
            "sizingPermitted": "SIZE" in ordered_actions,
        },
        "eligibleActions": ordered_actions,
        "modelRoutes": routes,
        "externalFinancialEffectAllowed": False,
        "prohibitions": [
            "do not infer owner risk appetite",
            "do not generate or submit orders",
            "do not treat model eligibility as investment truth",
            "do not convert contested models into default authority",
        ],
    }
