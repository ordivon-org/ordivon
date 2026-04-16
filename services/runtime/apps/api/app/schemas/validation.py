from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

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
    pass

class IssueResponse(IssueBase):
    issue_id: str
    status: str  # open|fixed|deferred
    created_at: datetime

class WeeklyValidationSummary(BaseModel):
    week_id: str
    days_used: int
    analysis_count: int
    recommendations_count: int
    reviews_count: int
    open_p0_count: int
    open_p1_count: int
    key_lessons: List[str]
    go_no_go: str  # continue|stabilize_more
