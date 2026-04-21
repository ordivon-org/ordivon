from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from apps.api.app.deps import get_db
from apps.api.app.schemas.agent_actions import AgentActionListResponse, TraceabilityResponse
from apps.api.app.schemas.common import AgentActionSummaryResponse
from domains.ai_actions.repository import AgentActionRepository
from domains.ai_actions.service import AgentActionService
from state.trace import TraceService

router = APIRouter()


def _to_summary(action) -> AgentActionSummaryResponse:
    return AgentActionSummaryResponse(
        id=action.id,
        task_type=action.task_type,
        status=action.status,
        actor_runtime=action.actor_runtime,
        provider=action.provider,
        model=action.model,
        reason=action.reason,
        idempotency_key=action.idempotency_key,
        trace_id=action.trace_id,
        input_summary=action.input_summary,
        output_summary=action.output_summary,
        input_refs=action.input_refs,
        output_refs=action.output_refs,
        usage=action.usage,
        error=action.error,
        started_at=action.started_at,
        completed_at=action.completed_at,
        created_at=action.created_at,
    )


@router.get("/latest", response_model=AgentActionListResponse)
async def list_latest_agent_actions(limit: int = 10, db: Session = Depends(get_db)):
    try:
        service = AgentActionService(AgentActionRepository(db))
        return AgentActionListResponse(actions=[_to_summary(action) for action in service.list_recent(limit=limit)])
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/trace/recommendations/{recommendation_id}", response_model=TraceabilityResponse)
async def trace_recommendation(recommendation_id: str, db: Session = Depends(get_db)):
    try:
        bundle = TraceService(db).trace_recommendation(recommendation_id)
        if bundle is None:
            raise HTTPException(status_code=404, detail=f"Recommendation not found: {recommendation_id}")

        return TraceabilityResponse(
            recommendation_id=recommendation_id,
            analysis_id=bundle.analysis.object_id,
            agent_action_id=bundle.agent_action.object_id,
            report_path=bundle.report_artifact.detail.get("path"),
            audit_event_ids=[reference.object_id for reference in bundle.latest_audit_events if reference.object_id],
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{action_id}", response_model=AgentActionSummaryResponse)
async def get_agent_action(action_id: str, db: Session = Depends(get_db)):
    try:
        action = AgentActionService(AgentActionRepository(db)).get_model(action_id)
        if action is None:
            raise HTTPException(status_code=404, detail=f"AgentAction not found: {action_id}")
        return _to_summary(action)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
