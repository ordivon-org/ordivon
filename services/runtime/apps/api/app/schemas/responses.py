from pydantic import BaseModel, ConfigDict
from typing import List, Any
from .common import BaseResponse

class AnalyzeResponse(BaseResponse):
    decision: str
    summary: str
    risk_flags: List[str] = []
    recommendations: List[str] = []
    report_path: str | None = None
    audit_event_id: str | None = None
    workflow: str = "analyze_and_suggest"
    metadata: dict[str, Any] = {}

class ReportSummaryResponse(BaseModel):
    report_id: str
    symbol: str
    title: str
    status: str
    report_path: str
    created_at: str

class ReportListResponse(BaseModel):
    reports: List[ReportSummaryResponse]
