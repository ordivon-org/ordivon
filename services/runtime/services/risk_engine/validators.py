from __future__ import annotations
from typing import Any
from services.risk_engine.models import RuleResult, RiskDecision

def check_completeness(data: dict[str, Any]) -> RuleResult:
    """检查输出结果的完整性"""
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

def check_leverage(proposed_leverage: int, max_leverage: int = 10) -> RuleResult:
    """检查杠杆倍数环比是否超限"""
    if proposed_leverage > max_leverage:
        return RuleResult(
            name="leverage_limit",
            decision=RiskDecision.BLOCK,
            message=f"Leverage {proposed_leverage} exceeds machine limit of {max_leverage}"
        )
    if proposed_leverage > max_leverage / 2:
        return RuleResult(
            name="leverage_warning",
            decision=RiskDecision.WARN,
            message=f"High leverage ({proposed_leverage}x) detected. Proceed with caution."
        )
    return RuleResult(
        name="leverage_safe",
        decision=RiskDecision.ALLOW,
        message="Leverage is within safe bounds."
    )

def check_stop_loss(action: dict[str, Any]) -> RuleResult:
    """检查是否包含强制止损"""
    if not action.get("sl"):
        return RuleResult(
            name="mandatory_sl",
            decision=RiskDecision.BLOCK,
            message="Action Plan MUST specify a Stop Loss (SL)."
        )
    return RuleResult(
        name="sl_present",
        decision=RiskDecision.ALLOW,
        message="Stop Loss present."
    )

def check_counter_evidence(data: dict[str, Any]) -> RuleResult:
    """检查是否存在反证 (Cognitive Quality)"""
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

def check_confidence_threshold(confidence: float, min_threshold: float = 5.0) -> RuleResult:
    """检查置信度是否低于阈值 (Machine Discipline)"""
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

def check_no_trade_zone(context: dict[str, Any], forbidden_configs: list[dict[str, Any]]) -> RuleResult:
    """高度概括的禁区校验 (Generalized No-Trade Zone)"""
    # 示例：forbidden_configs 可以包含 { "symbol": "BTC", "reason": "High Volatility Event" }
    symbol = context.get("symbol")
    for rule in forbidden_configs:
        if rule.get("symbol") == symbol:
            return RuleResult(
                name="no_trade_zone",
                decision=RiskDecision.BLOCK,
                message=f"Trading {symbol} blocked: {rule.get('reason', 'Policy restriction')}"
            )
    return RuleResult(
        name="no_trade_zone",
        decision=RiskDecision.ALLOW,
        message="Not in a no-trade zone."
    )
