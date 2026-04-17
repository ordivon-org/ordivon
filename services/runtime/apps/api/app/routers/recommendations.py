from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from pfios.core.db.session import SessionLocal
from pfios.domain.recommendation.repository import RecommendationRepository
from pfios.domain.recommendation.service import RecommendationService
from pfios.domain.recommendation.models import Recommendation as RecommendationModel


router = APIRouter(prefix="/recommendations", tags=["recommendations"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/", response_model=List[dict])
def list_recommendations(db: Session = Depends(get_db)):
    service = RecommendationService(RecommendationRepository(db))
    rows = service.list_recent()
    return [service.repository.to_model(r).__dict__ for r in rows]


@router.get("/{reco_id}", response_model=dict)
def get_recommendation(reco_id: str, db: Session = Depends(get_db)):
    service = RecommendationService(RecommendationRepository(db))
    try:
        return service.get_model(reco_id).__dict__
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
