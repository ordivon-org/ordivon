from __future__ import annotations
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field

class RiskDecision(str, Enum):
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
    version: str = "1.1"

class AuditEvent(BaseModel):
    """审计事件模型"""
    event_id: str
    workflow_name: str
    stage: str
    decision: RiskDecision
    subject_id: str | None = None  # 记录针对的对象 (asset/report/trade ID)
    status: str = "check_only"      # check_only, persisted, blocked, downgraded
    context_summary: str
    details: dict[str, Any]
    report_path: str | None = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

from datetime import datetime
