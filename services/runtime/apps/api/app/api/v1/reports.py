from fastapi import APIRouter, HTTPException
from typing import List
from app.schemas.responses import ReportSummaryResponse, ReportListResponse
from app.services.object_service import ObjectService

router = APIRouter()

@router.get("/latest", response_model=ReportListResponse)
async def get_latest_reports(limit: int = 10):
    """获取最近生成的投研报告列表"""
    try:
        records = ObjectService.get_recent_reports(limit=limit)
        reports = [
            ReportSummaryResponse(
                report_id=r["report_id"],
                symbol=r["symbol"],
                title=r["title"],
                status=r["status"],
                report_path=r["report_path"],
                created_at=str(r["created_at"])
            )
            for r in records
        ]
        return ReportListResponse(reports=reports)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
