from fastapi import APIRouter, HTTPException
from typing import List, Dict
from app.schemas.validation import UsageLog, IssueCreate, IssueResponse, WeeklyValidationSummary
from app.services.validation_service import ValidationService

router = APIRouter()

@router.get("/summary")
async def get_validation_summary():
    """获取当前验证周期汇总 (Step 11)"""
    try:
        summary = ValidationService.get_weekly_validation_summary()
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/usage/sync")
async def sync_usage():
    """手动触发当日指标同步"""
    try:
        stats = ValidationService.sync_daily_usage()
        return {"status": "success", "stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/issue", response_model=dict)
async def report_validation_issue(issue: IssueCreate):
    """上报验证过程中发现的缺陷 (P0/P1/P2)"""
    try:
        issue_id = ValidationService.report_issue(
            severity=issue.severity,
            area=issue.area,
            description=issue.description
        )
        return {"status": "success", "issue_id": issue_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
