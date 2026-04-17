"""
pfios.governance.validators.logic_validators — 分析引擎的逻辑校验
"""
from __future__ import annotations
from typing import Any

from pfios.governance.models import RuleResult, RiskDecision


def check_completeness(data: dict[str, Any]) -> RuleResult:
    required_fields = ["summary", "evidence_for", "evidence_against", "recommendations", "next_actions"]
    missing = [f for f in required_fields if not data.get(f)]
    
    if "summary" in missing:
        return RuleResult(
            name="completeness_summary",
            decision=RiskDecision.BLOCK,
            message="Critical field 'summary' is missing."
        )
    if missing:
        return RuleResult(
            name="completeness_warning",
            decision=RiskDecision.WARN,
            message=f"Missing non-critical fields: {', '.join(missing)}"
        )
    return RuleResult(
        name="completeness_integrity",
        decision=RiskDecision.ALLOW,
        message="All required fields are present."
    )


def check_counter_evidence(data: dict[str, Any]) -> RuleResult:
    against = data.get("evidence_against")
    if not against or (isinstance(against, list) and len(against) == 0):
        return RuleResult(
            name="cognitive_balance",
            decision=RiskDecision.WARN,
            message="No 'evidence_against' provided. Analysis might be biased."
        )
    return RuleResult(
        name="cognitive_balance",
        decision=RiskDecision.ALLOW,
        message="Counter-evidence found."
    )


def check_confidence_threshold(confidence: float, min_threshold: float = 0.5) -> RuleResult:
    if confidence < min_threshold:
        return RuleResult(
            name="confidence_low",
            decision=RiskDecision.BLOCK,
            message=f"Confidence {confidence} is below minimum threshold of {min_threshold}."
        )
    return RuleResult(
        name="confidence_ok",
        decision=RiskDecision.ALLOW,
        message="Confidence is acceptable."
    )


def check_no_trade_zone(context_symbol: str | None, forbidden_configs: list[dict[str, Any]]) -> RuleResult:
    for rule in forbidden_configs:
        if rule.get("symbol") == context_symbol:
            return RuleResult(
                name="no_trade_zone",
                decision=RiskDecision.BLOCK,
                message=f"Trading {context_symbol} blocked: {rule.get('reason', 'Policy restriction')}"
            )
    return RuleResult(
        name="no_trade_zone",
        decision=RiskDecision.ALLOW,
        message="Not in a no-trade zone."
    )
