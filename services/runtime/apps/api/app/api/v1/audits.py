import json
from fastapi import APIRouter, HTTPException
from typing import List
from app.schemas.audit import AuditListResponse, AuditEventResponse
from services.risk_engine.audit import RiskAuditor

router = APIRouter()
auditor = RiskAuditor()

@router.get("/recent", response_model=AuditListResponse)
async def get_recent_audits(limit: int = 10):
    """获取最近的治理审计轨迹"""
    try:
        records = auditor.get_recent_audits(limit=limit)
        # 转换为 Pydantic 模型列表
        audits = [
            AuditEventResponse(
                event_id=r["event_id"],
                workflow_name=r["workflow_name"],
                stage=r["stage"],
                decision=r["decision"],
                subject_id=r["subject_id"],
                status=r["status"],
                context_summary=r["context_summary"],
                details=json.loads(r["details_json"]) if isinstance(r["details_json"], str) else r["details_json"],
                report_path=r["report_path"],
                created_at=str(r["created_at"])
            )
            for r in records
        ]
        return AuditListResponse(audits=audits)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
