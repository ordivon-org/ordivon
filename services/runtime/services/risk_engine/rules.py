from __future__ import annotations
import yaml
from pathlib import Path
from typing import Any
from app.core.config import settings
from services.risk_engine.models import RiskDecision, RuleResult, PolicyCheckResult
from services.risk_engine.validators import (
    check_completeness, check_leverage, check_stop_loss,
    check_counter_evidence, check_confidence_threshold, check_no_trade_zone
)

class RiskEngine:
    """风控规则引擎 (Governance Layer) - 规则解释与调度中心"""

    def __init__(self):
        self.limits_path = settings.trading_limits_abs_path
        self.limits = self._load_limits()

    def _load_limits(self) -> dict[str, Any]:
        if not self.limits_path.exists():
            return {}
        with open(self.limits_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            # 平刷 v1.0 结构 (提取 risk_limits, operational, compliance 到一级供快捷访问)
            flat_limits = {}
            if "risk_limits" in data: flat_limits.update(data["risk_limits"])
            if "operational" in data: flat_limits.update(data["operational"])
            if "compliance" in data: flat_limits.update(data["compliance"])
            return flat_limits

    def validate_thesis_and_action(self, thesis: dict, action: dict | None = None) -> PolicyCheckResult:
        """
        全案校验：综合评估推理结果与行动建议 (Pure Logic)
        """
        results: list[RuleResult] = []
        
        # 1. 认知质量校验 (Cognitive Quality)
        results.append(check_completeness(thesis))
        results.append(check_counter_evidence(thesis))
        
        # 2. 机器纪律校验 (Machine Discipline)
        min_conf = self.limits.get("min_confidence_score", 5.0)
        results.append(check_confidence_threshold(thesis.get("confidence", 0.0), min_conf))
        
        # 3. 禁区校验 (Generalized No-Trade Zone)
        forbidden_configs = self.limits.get("forbidden_configs", [])
        if "forbidden_symbols" in self.limits:
             # 兼容旧版单一符号列表
             for sym in self.limits["forbidden_symbols"]:
                 forbidden_configs.append({"symbol": sym, "reason": "Manually blacklisted"})
        results.append(check_no_trade_zone(thesis, forbidden_configs))
        
        # 4. 行动建议校验 (Action Discipline)
        if action:
            # 杠杆限制
            max_lev = self.limits.get("max_leverage", 10)
            results.append(check_leverage(action.get("leverage", 1), max_lev))
            
            # 强制止损
            if self.limits.get("mandatory_sl_required", True):
                results.append(check_stop_loss(action))

        # 5. 结果汇总决策
        final_decision = RiskDecision.ALLOW
        if any(r.decision == RiskDecision.BLOCK for r in results):
            final_decision = RiskDecision.BLOCK
        elif any(r.decision == RiskDecision.WARN for r in results):
            final_decision = RiskDecision.WARN
            
        return PolicyCheckResult(
            decision=final_decision,
            is_safe=(final_decision != RiskDecision.BLOCK),
            triggered_rules=results,
            summary=f"PFIOS Risk Check: {final_decision.value.upper()}"
        )
