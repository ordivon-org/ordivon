from fastapi import APIRouter, HTTPException

from apps.api.app.schemas.responses import ReportListResponse, ReportSummaryResponse
from capabilities.reports import ReportCapability

router = APIRouter()
report_capability = ReportCapability()


from dataclasses import asdict
from fastapi import Depends
from sqlalchemy.orm import Session
from apps.api.app.deps import get_db
from domains.research.service import AnalysisService
from domains.research.repository import AnalysisRepository


@router.get("/latest", response_model=ReportListResponse)
async def get_latest_reports(limit: int = 10, db: Session = Depends(get_db)):
    try:
        service = AnalysisService(AnalysisRepository(db))
        records = report_capability.list_latest(service, limit=limit)
        reports = [ReportSummaryResponse(**asdict(record)) for record in records]
        return ReportListResponse(reports=reports)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
