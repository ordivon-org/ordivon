from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from apps.api.app.schemas.common import ActionContextInput


class UsageLog(BaseModel):
    date: str  # YYYY-MM-DD
    analysis_runs: int
    recommendations_updated: int
    reviews_completed: int
    blocking_issue_count: int
    notes: Optional[str] = None


class IssueBase(BaseModel):
    severity: str  # P0|P1|P2
    area: str  # dashboard|analyze|audits|reports|recommendation|review|reasoning
    description: str


class IssueCreate(IssueBase):
    action_context: Optional[ActionContextInput] = None


class IssueResponse(IssueBase):
    issue_id: str
    status: str  # open|fixed|deferred
    created_at: datetime


class WeeklyValidationSummary(BaseModel):
    period_id: Optional[str] = None
    days_active: int
    total_analyses: int
    total_recommendations: int
    open_critical_issues: int
    system_go_no_go: str
    metrics: Optional[dict] = None
    metadata: dict
