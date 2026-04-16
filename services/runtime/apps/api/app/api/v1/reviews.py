from fastapi import APIRouter, HTTPException
from app.schemas.review import ReviewCreate, ReviewResponse, ReviewListResponse
from app.services.review_service import ReviewService

router = APIRouter()

@router.post("/generate-skeleton", response_model=dict)
async def generate_review_skeleton(report_id: str, reco_id: str = None):
    """为指定报告/建议生成复盘骨架"""
    try:
        skeleton = ReviewService.generate_review_skeleton(report_id, reco_id)
        return skeleton
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/submit", response_model=dict)
async def submit_performance_review(review: ReviewCreate):
    """提交事后复盘并同步至 Wiki"""
    try:
        review_id = ReviewService.submit_review(review.model_dump())
        return {"status": "success", "review_id": review_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
