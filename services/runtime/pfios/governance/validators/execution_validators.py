"""
pfios.governance.validators.execution_validators — 执行引擎的量化风控校验
"""
from __future__ import annotations
from typing import Any

from pfios.governance.models import RuleResult, RiskDecision


def check_leverage(proposed_leverage: float, max_leverage: float = 10.0) -> RuleResult:
    if proposed_leverage > max_leverage:
        return RuleResult(
            name="leverage_limit",
            decision=RiskDecision.BLOCK,
            message=f"Leverage {proposed_leverage}x exceeds machine limit of {max_leverage}x"
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


def check_stop_loss_presence(action: dict[str, Any]) -> RuleResult:
    """检查是否包含强制止损"""
    if not action.get("stop_loss") and not action.get("sl"):
        return RuleResult(
            name="mandatory_sl",
            decision=RiskDecision.BLOCK,
            message="Execution Plan MUST specify a Stop Loss (stop_loss or sl)."
        )
    return RuleResult(
        name="sl_present",
        decision=RiskDecision.ALLOW,
        message="Stop Loss present."
    )


def check_exposure_limits(
    planned_symbol_notional: float,
    planned_total_notional: float,
    quote_equity: float,
    max_symbol_pct: float,
    max_total_pct: float
) -> list[RuleResult]:
    """暴露头寸占比限制"""
    results = []
    
    # 限制极小资金导致的除数为 0
    safe_equity = max(quote_equity, 1.0)
    
    if (planned_symbol_notional / safe_equity) > max_symbol_pct:
        results.append(RuleResult(
            name="symbol_exposure_limit",
            decision=RiskDecision.BLOCK,
            message=f"Planned symbol notional exceeds {max_symbol_pct*100}% of equity."
        ))
    else:
        results.append(RuleResult(
            name="symbol_exposure_limit",
            decision=RiskDecision.ALLOW,
            message="Symbol exposure within limits."
        ))

    if (planned_total_notional / safe_equity) > max_total_pct:
        results.append(RuleResult(
            name="total_exposure_limit",
            decision=RiskDecision.BLOCK,
            message=f"Planned total notional exceeds {max_total_pct*100}% of equity."
        ))
    else:
        results.append(RuleResult(
            name="total_exposure_limit",
            decision=RiskDecision.ALLOW,
            message="Total exposure within limits."
        ))
        
    return results


def check_same_side_reentry(block_same_side: bool, existing_same_side_position: bool) -> RuleResult:
    if block_same_side and existing_same_side_position:
        return RuleResult(
            name="same_side_reentry",
            decision=RiskDecision.BLOCK,
            message="Existing position on the same side is already open."
        )
    return RuleResult(
        name="same_side_reentry",
        decision=RiskDecision.ALLOW,
        message="No conflicting open positions."
    )


def check_drawdown_pause(
    realized_pnl: float,
    max_drawdown_quote: float
) -> RuleResult:
    if max_drawdown_quote > 0 and realized_pnl < 0 and abs(realized_pnl) > max_drawdown_quote:
        return RuleResult(
            name="drawdown_pause",
            decision=RiskDecision.BLOCK,
            message="Maximum absolute drawdown reached. System paused."
        )
    return RuleResult(
        name="drawdown_pause",
        decision=RiskDecision.ALLOW,
        message="Drawdown within limits."
    )


def check_consecutive_losses(
    recent_pnls: list[float],
    max_consecutive_losses: int
) -> RuleResult:
    if len(recent_pnls) >= max_consecutive_losses and all(p < 0 for p in recent_pnls[:max_consecutive_losses]):
        return RuleResult(
            name="consecutive_loss_pause",
            decision=RiskDecision.BLOCK,
            message=f"Suffered {max_consecutive_losses} consecutive losses. System paused."
        )
    return RuleResult(
        name="consecutive_loss_pause",
        decision=RiskDecision.ALLOW,
        message="Consecutive loss limit not breached."
    )
