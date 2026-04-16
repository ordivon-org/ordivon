from fastapi import APIRouter, HTTPException
from typing import List
from app.schemas.recommendation import RecommendationResponse, RecommendationUpdate, RecommendationListResponse
from app.services.recommendation_service import RecommendationService

router = APIRouter()

@router.get("/recent", response_model=RecommendationListResponse)
async def get_recent_recommendations(limit: int = 10):
    """获取最近生成的投研建议"""
    try:
        recos = RecommendationService.get_recent(limit)
        return {"recommendations": recos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{reco_id}/status", response_model=dict)
async def update_recommendation_status(reco_id: str, update: RecommendationUpdate):
    """更新建议的生命周期状态与用户反馈 (Adopt/Ignore/Close)"""
    try:
        RecommendationService.update_status(
            reco_id=reco_id,
            lifecycle_status=update.lifecycle_status,
            adopted=update.adopted,
            user_note=update.user_note
        )
        return {"status": "success", "recommendation_id": reco_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
