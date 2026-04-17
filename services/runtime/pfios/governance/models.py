"""
pfios.governance.models — 治理层核心数据模型
"""
from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class RiskDecision(str, Enum):
    """风险决策结果"""
    ALLOW = "allow"
    WARN = "warn"
    BLOCK = "block"


class RuleResult(BaseModel):
    """单项规则校验结果"""
    name: str
    decision: RiskDecision
    message: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class PolicyCheckResult(BaseModel):
    """策略全案校验报告"""
    decision: RiskDecision
    is_safe: bool
    triggered_rules: list[RuleResult]
    summary: str
    version: str = "2.0"
