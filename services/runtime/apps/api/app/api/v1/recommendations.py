from fastapi import APIRouter, HTTPException
from typing import List
from app.schemas.recommendation import RecommendationResponse, RecommendationUpdate, RecommendationListResponse
from pfios.orchestrator.recommendation_tracker import RecommendationTracker
from pfios.domain.recommendation.models import LifecycleStatus

router = APIRouter()

@router.get("/recent", response_model=RecommendationListResponse)
async def get_recent_recommendations(limit: int = 10):
    """获取最近生成的投研建议"""
    try:
        recos = RecommendationTracker.get_recent(limit)
        return {"recommendations": recos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{reco_id}/status", response_model=dict)
async def update_recommendation_status(reco_id: str, update: RecommendationUpdate):
    """更新建议的生命周期状态与用户反馈 (Adopt/Ignore/Close)"""
    try:
        if not update.lifecycle_status:
            raise ValueError("lifecycle_status is required")
        
        status_enum = LifecycleStatus(update.lifecycle_status)
        RecommendationTracker.transition(
            reco_id=reco_id,
            to_status=status_enum,
            user_note=update.user_note
        )
        return {"status": "success", "recommendation_id": reco_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
