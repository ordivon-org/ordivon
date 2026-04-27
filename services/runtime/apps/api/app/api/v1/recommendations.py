from fastapi import APIRouter, HTTPException

from apps.api.app.schemas.recommendation import (
    RecommendationListResponse,
    RecommendationResponse,
    RecommendationUpdate,
)
from capabilities.recommendations import RecommendationCapability

router = APIRouter()
recommendation_capability = RecommendationCapability()


from dataclasses import asdict
from fastapi import Depends
from sqlalchemy.orm import Session
from apps.api.app.deps import get_db
from domains.strategy.service import RecommendationService
from domains.strategy.repository import RecommendationRepository
from execution.adapters import RecommendationExecutionFailure

from capabilities.boundary import ActionContext


def build_action_context(raw_action_context, recommendation_id: str, lifecycle_status: str) -> ActionContext:
    if raw_action_context is not None:
        return ActionContext(**raw_action_context.model_dump())

    return ActionContext(
        actor="api.v1.recommendations",
        context="recommendation_status_route",
        reason=f"update recommendation lifecycle to {lifecycle_status}",
        idempotency_key=f"{recommendation_id}:{lifecycle_status}",
    )


@router.get("/recent", response_model=RecommendationListResponse)
async def get_recent_recommendations(limit: int = 10, db: Session = Depends(get_db)):
    try:
        service = RecommendationService(RecommendationRepository(db), None)
        recos = recommendation_capability.list_recent(service, limit)
        return RecommendationListResponse(recommendations=[RecommendationResponse(**asdict(reco)) for reco in recos])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{reco_id}", response_model=RecommendationResponse)
async def get_recommendation_detail(reco_id: str, db: Session = Depends(get_db)):
    try:
        service = RecommendationService(RecommendationRepository(db), None)
        reco = recommendation_capability.get_by_id(service, reco_id)
        return RecommendationResponse(**asdict(reco))
    except Exception as e:
        if "Recommendation not found" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{reco_id}/status", response_model=dict)
async def update_recommendation_status(reco_id: str, update: RecommendationUpdate, db: Session = Depends(get_db)):
    try:
        if not update.lifecycle_status:
            raise ValueError("lifecycle_status is required")
        service = RecommendationService(RecommendationRepository(db), None)
        res = recommendation_capability.update_status(
            service,
            reco_id,
            update.lifecycle_status,
            build_action_context(update.action_context, reco_id, update.lifecycle_status),
        )
        db.commit()
        return res
    except RecommendationExecutionFailure as e:
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
