from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from apps.api.app.schemas.common import StatusResponse
from apps.api.app.deps import get_db
from intelligence.runtime.hermes_client import HermesClient, HermesUnavailableError
from infra.monitoring import MonitoringService
from shared.config.settings import settings

router = APIRouter()

@router.get("/health", response_model=StatusResponse)
async def health_check(db: Session = Depends(get_db)):
    hermes_status = None
    hermes_detail = None
    runtime_provider = None
    runtime_model = None
    monitoring_status = None
    monitoring_detail = None
    monitoring_window_hours = None
    recent_failed_workflow_count = None
    recent_failed_execution_count = None
    last_workflow_at = None
    last_audit_at = None

    if settings.reasoning_provider == "hermes":
        try:
            health = HermesClient().health_check()
            hermes_status = health.get("status", "ok")
            runtime_provider = health.get("provider")
            runtime_model = health.get("model")
        except HermesUnavailableError as exc:
            hermes_status = "unavailable"
            hermes_detail = str(exc)
        except Exception:
            hermes_status = "unavailable"
            hermes_detail = "Hermes health check failed unexpectedly."

    try:
        snapshot = MonitoringService(db).get_snapshot()
        monitoring_status = snapshot.monitoring_status
        monitoring_window_hours = snapshot.monitoring_window_hours
        recent_failed_workflow_count = snapshot.recent_failed_workflow_count
        recent_failed_execution_count = snapshot.recent_failed_execution_count
        last_workflow_at = snapshot.last_workflow_at
        last_audit_at = snapshot.last_audit_at
    except Exception:
        monitoring_status = "unavailable"
        monitoring_detail = "Monitoring snapshot could not be confirmed."

    return StatusResponse(
        status=(
            "degraded"
            if (settings.reasoning_provider == "hermes" and hermes_status != "ok")
            or monitoring_status == "unavailable"
            else "ok"
        ),
        reasoning_provider=settings.reasoning_provider,
        hermes_status=hermes_status,
        hermes_detail=hermes_detail,
        hermes_base_url=settings.hermes_base_url if settings.reasoning_provider == "hermes" else None,
        runtime_provider=runtime_provider,
        runtime_model=runtime_model,
        monitoring_status=monitoring_status,
        monitoring_detail=monitoring_detail,
        monitoring_window_hours=monitoring_window_hours,
        recent_failed_workflow_count=recent_failed_workflow_count,
        recent_failed_execution_count=recent_failed_execution_count,
        last_workflow_at=last_workflow_at,
        last_audit_at=last_audit_at,
    )

@router.get("/version", response_model=StatusResponse)
async def get_version():
    return StatusResponse(status="ok", version="0.1.0", reasoning_provider=settings.reasoning_provider)
