from fastapi import APIRouter, HTTPException

from capabilities.recommendations import RecommendationCapability


router = APIRouter(prefix="/recommendations", tags=["recommendations"])
recommendation_capability = RecommendationCapability()


@router.get("/", response_model=list[dict])
def list_recommendations():
    return recommendation_capability.list_recent(limit=20)


@router.get("/{reco_id}", response_model=dict)
def get_recommendation(reco_id: str):
    try:
        return recommendation_capability.get_by_id(reco_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
