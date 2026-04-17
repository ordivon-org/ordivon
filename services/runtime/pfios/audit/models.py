"""
pfios.audit.models — 审计事件数据模型
"""
from __future__ import annotations

from datetime import datetime, UTC
from typing import Any, Optional

from pydantic import BaseModel, Field



class AuditEvent(BaseModel):
    """审计事件模型"""
    event_id: str
    workflow_name: str
    stage: str
    decision: str  # "allow" | "warn" | "block" — 存储字符串，审计层不持有枚举语义
    subject_id: Optional[str] = None  # 记录针对的对象 (asset/report/trade ID)
    status: str = "check_only"      # check_only, persisted, blocked, downgraded
    context_summary: str
    details: dict[str, Any]
    report_path: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
