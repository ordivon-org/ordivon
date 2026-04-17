from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from pfios.core.db.session import SessionLocal
from pfios.domain.review.repository import ReviewRepository
from pfios.domain.review.service import ReviewService
from pfios.domain.review.models import Review as ReviewModel
from pfios.domain.lessons.repository import LessonRepository
from pfios.domain.lessons.service import LessonService
from pfios.audit.auditor import RiskAuditor
from apps.api.app.schemas.reviews import ReviewCreateRequest, ReviewCompleteRequest


router = APIRouter(prefix="/reviews", tags=["reviews"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/")
def create_review(req: ReviewCreateRequest, db: Session = Depends(get_db)):
    auditor = RiskAuditor()
    lesson_service = LessonService(LessonRepository(db))
    service = ReviewService(ReviewRepository(db), lesson_service, auditor)

    review = ReviewModel(
        recommendation_id=req.recommendation_id,
        review_type=req.review_type,
        expected_outcome=req.expected_outcome,
    )
    row = service.create(review)
    return {"id": row.id, "status": row.status}


@router.post("/{review_id}/complete")
def complete_review(
    review_id: str,
    req: ReviewCompleteRequest,
    db: Session = Depends(get_db)
):
    auditor = RiskAuditor()
    lesson_service = LessonService(LessonRepository(db))
    service = ReviewService(ReviewRepository(db), lesson_service, auditor)

    try:
        review_row, lesson_rows = service.complete_review(
            review_id=review_id,
            observed_outcome=req.observed_outcome,
            verdict=req.verdict,
            variance_summary=req.variance_summary,
            cause_tags=req.cause_tags,
            lessons=req.lessons,
            followup_actions=req.followup_actions,
        )
        return {
            "id": review_row.id,
            "status": review_row.status,
            "lessons_created": len(lesson_rows)
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
