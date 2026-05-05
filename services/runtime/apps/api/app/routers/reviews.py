from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from apps.api.app.deps import get_db
from apps.api.app.schemas.reviews import ReviewCompleteRequest, ReviewCreateRequest
from capabilities.boundary import ActionContext
from capabilities.reviews import ReviewCapability
from domains.journal.lesson_repository import LessonRepository
from domains.journal.lesson_service import LessonService
from domains.journal.repository import ReviewRepository
from domains.journal.service import ReviewService
from governance_engine.audit.auditor import RiskAuditor


router = APIRouter(prefix="/reviews", tags=["reviews"])
review_capability = ReviewCapability()


@router.post("/")
def create_review(req: ReviewCreateRequest, db: Session = Depends(get_db)):
    try:
        lesson_service = LessonService(LessonRepository(db))
        review_service = ReviewService(ReviewRepository(db), lesson_service, RiskAuditor())
        result = review_capability.create_review(
            service=review_service,
            recommendation_id=req.recommendation_id,
            action_context=ActionContext(**req.action_context.model_dump()),
            review_type=req.review_type,
            expected_outcome=req.expected_outcome,
            outcome_ref_type=req.outcome_ref_type,
            outcome_ref_id=req.outcome_ref_id,
        )
        db.commit()
        return asdict(result)
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{review_id}/complete")
def complete_review(review_id: str, req: ReviewCompleteRequest, db: Session = Depends(get_db)):
    try:
        lesson_service = LessonService(LessonRepository(db))
        review_service = ReviewService(ReviewRepository(db), lesson_service, RiskAuditor())
        result = review_capability.complete_review(
            service=review_service,
            review_id=review_id,
            observed_outcome=req.observed_outcome,
            verdict=req.verdict,
            variance_summary=req.variance_summary,
            cause_tags=req.cause_tags,
            lessons=req.lessons,
            followup_actions=req.followup_actions,
            action_context=ActionContext(**req.action_context.model_dump()),
        )
        db.commit()
        return asdict(result)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(e))
