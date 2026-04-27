from fastapi import APIRouter, HTTPException
from dataclasses import asdict

from apps.api.app.schemas.validation import IssueCreate, WeeklyValidationSummary
from capabilities.validation import ValidationCapability

router = APIRouter()
validation_capability = ValidationCapability()


from fastapi import Depends
from sqlalchemy.orm import Session
from apps.api.app.deps import get_db
from domains.journal.issue_repository import IssueRepository
from domains.journal.issue_service import IssueService
from state.usage.repository import UsageSnapshotRepository
from state.usage.service import UsageService
from governance.audit.auditor import RiskAuditor
from capabilities.boundary import ActionContext
from execution.adapters import ValidationExecutionFailure


def build_issue_action_context(raw_action_context, severity: str, area: str) -> ActionContext:
    if raw_action_context is not None:
        return ActionContext(**raw_action_context.model_dump())

    return ActionContext(
        actor="api.v1.validation",
        context="validation_issue_route",
        reason=f"report validation issue {severity}:{area}",
        idempotency_key=f"{severity}:{area}",
    )


@router.get("/summary", response_model=WeeklyValidationSummary)
async def get_validation_summary(db: Session = Depends(get_db)):
    try:
        usage_service = UsageService(UsageSnapshotRepository(db))
        issue_repo = IssueRepository(db)
        return WeeklyValidationSummary(**asdict(validation_capability.get_summary(usage_service, issue_repo)))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/usage/sync")
async def sync_usage(db: Session = Depends(get_db)):
    try:
        usage_service = UsageService(UsageSnapshotRepository(db))
        stats = validation_capability.sync_usage(
            usage_service,
            ActionContext(
                actor="api.validation.sync",
                context="manual_sync_endpoint",
                reason="manual validation usage sync",
                idempotency_key="api.validation.sync",
            ),
        )
        db.commit()
        return {"status": "success", "stats": asdict(stats)}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/issue", response_model=dict)
async def report_validation_issue(issue: IssueCreate, db: Session = Depends(get_db)):
    try:
        issue_service = IssueService(IssueRepository(db), RiskAuditor())
        result = validation_capability.report_issue(
            issue_service=issue_service,
            severity=issue.severity,
            area=issue.area,
            description=issue.description,
            action_context=build_issue_action_context(issue.action_context, issue.severity, issue.area),
        )
        db.commit()
        return {"status": "success", **result}
    except ValidationExecutionFailure as e:
        db.commit()
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "status": "error",
                "message": e.message,
                "execution_request_id": e.execution_request_id,
                "execution_receipt_id": e.execution_receipt_id,
            },
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
