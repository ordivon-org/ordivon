from fastapi import APIRouter, HTTPException

from apps.api.app.schemas.audit import AuditEventResponse, AuditListResponse
from capabilities.audits import AuditCapability

router = APIRouter()
audit_capability = AuditCapability()


from fastapi import Depends
from sqlalchemy.orm import Session
from apps.api.app.deps import get_db
from governance.audit.repository import AuditEventRepository
from governance.audit.service import AuditService


@router.get("/recent", response_model=AuditListResponse)
async def get_recent_audits(limit: int = 10, db: Session = Depends(get_db)):
    try:
        service = AuditService(AuditEventRepository(db))
        records = audit_capability.list_recent(service, limit=limit)
        return AuditListResponse(
            status="success",
            message=None,
            audits=[AuditEventResponse(**record) for record in records],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
