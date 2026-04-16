from pydantic import BaseModel
from typing import List, Any
from .common import BaseResponse

class AuditEventResponse(BaseModel):
    event_id: str
    workflow_name: str
    stage: str
    decision: str
    subject_id: str | None
    status: str
    context_summary: str
    details: dict[str, Any]
    report_path: str | None
    created_at: str

class AuditListResponse(BaseResponse):
    audits: List[AuditEventResponse]
