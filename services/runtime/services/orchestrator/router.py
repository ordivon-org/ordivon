from __future__ import annotations
from enum import Enum

class WorkflowType(Enum):
    ANALYZE = "analyze"
    REVIEW = "review"
    PORTFOLIO_CHECK = "portfolio_check"
    UNKNOWN = "unknown"

class TaskRouter:
    """任务路由器 (Orchestration Support) - 决定分发哪个工作流"""

    @staticmethod
    def route_query(query: str) -> WorkflowType:
        q = query.lower()
        if any(w in q for w in ["analyze", "suggest", "opinion", "think"]):
            return WorkflowType.ANALYZE
        if any(w in q for w in ["review", "journal", "pnl"]):
            return WorkflowType.REVIEW
        if any(w in q for w in ["portfolio", "balance", "holdings"]):
            return WorkflowType.PORTFOLIO_CHECK
        return WorkflowType.UNKNOWN
