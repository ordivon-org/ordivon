from pydantic import BaseModel, ConfigDict
from typing import List, Any
from .common import BaseResponse

class AnalyzeResponse(BaseResponse):
    decision: str
    summary: str
    risk_flags: List[str] = []
    recommendations: List[str] = []
    analysis_id: str | None = None
    recommendation_id: str | None = None
    report_path: str | None = None
    audit_event_id: str | None = None
    workflow: str = "analyze_and_suggest"
    metadata: dict[str, Any] = {}

class ReportSummaryResponse(BaseModel):
    report_id: str
    symbol: str | None = None
    title: str
    status: str
    report_path: str | None = None
    created_at: str
    metadata: dict[str, Any] = {}

class ReportListResponse(BaseModel):
    reports: List[ReportSummaryResponse]
