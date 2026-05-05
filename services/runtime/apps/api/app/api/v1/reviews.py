# WARNING: The review lifecycle (submit/complete) currently operates outside the
# PFIOSOrchestrator. Review submission and completion are handled directly
# through capabilities and adapters rather than through orchestrator workflows.
# This means review operations lack the orchestrator's recoverability guarantees,
# governance gating, and uniform audit trail consistency.
# See docs/architecture/review-workflow-gap.md and docs/audits/phase-4-readiness/
# for the documented gap and remediation plan (P4 Batch 1).
#
from fastapi import APIRouter, HTTPException
from dataclasses import asdict

from apps.api.app.schemas.reviews import (
    PendingReviewListResponse,
    ReviewDetailResponse,
    PendingReviewResponse,
    ReviewCreateRequest,
    ReviewCompleteRequest,
)
from capabilities.reviews import ReviewCapability

router = APIRouter()
review_capability = ReviewCapability()


from fastapi import Depends
from sqlalchemy.orm import Session
from apps.api.app.deps import get_db
from domains.journal.service import ReviewService
from domains.journal.repository import ReviewRepository
from domains.journal.lesson_service import LessonService
from domains.journal.lesson_repository import LessonRepository
from domains.strategy.outcome_repository import OutcomeRepository
from domains.strategy.outcome_service import OutcomeService
from domains.strategy.repository import RecommendationRepository
from domains.strategy.service import RecommendationService
from execution.adapters import ReviewExecutionFailure
from governance_engine.approval import ApprovalRequiredError
from governance_engine.audit.auditor import RiskAuditor
from capabilities.boundary import ActionContext


def build_action_context(raw_action_context, route_name: str, idempotency_key: str) -> ActionContext:
    if raw_action_context is not None:
        return ActionContext(**raw_action_context.model_dump())

    return ActionContext(
        actor="api.v1.reviews",
        context=route_name,
        reason=f"{route_name} executed without caller-supplied action context",
        idempotency_key=idempotency_key,
    )


@router.post("/generate-skeleton", response_model=dict)
async def generate_review_skeleton(report_id: str, reco_id: str | None = None):
    try:
        res = review_capability.generate_skeleton(report_id, reco_id)
        return asdict(res)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pending", response_model=PendingReviewListResponse)
async def get_pending_reviews(limit: int = 10, db: Session = Depends(get_db)):
    try:
        review_service = ReviewService(
            ReviewRepository(db),
            LessonService(LessonRepository(db)),
            outcome_service=OutcomeService(OutcomeRepository(db)),
            recommendation_service=RecommendationService(RecommendationRepository(db)),
        )
        result = review_capability.list_pending(review_service, limit=limit)
        return PendingReviewListResponse(reviews=[PendingReviewResponse(**asdict(review)) for review in result.reviews])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{review_id}", response_model=ReviewDetailResponse)
async def get_review_detail(review_id: str, db: Session = Depends(get_db)):
    try:
        review_service = ReviewService(
            ReviewRepository(db),
            LessonService(LessonRepository(db)),
            outcome_service=OutcomeService(OutcomeRepository(db)),
            recommendation_service=RecommendationService(RecommendationRepository(db)),
        )
        result = review_capability.get_detail(review_service, review_id)
        return ReviewDetailResponse(**asdict(result))
    except Exception as e:
        if "Review not found" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/submit", response_model=dict)
async def submit_performance_review(review: ReviewCreateRequest, db: Session = Depends(get_db)):
    try:
        lesson_service = LessonService(LessonRepository(db))
        review_service = ReviewService(
            ReviewRepository(db),
            lesson_service,
            RiskAuditor(),
            outcome_service=OutcomeService(OutcomeRepository(db)),
            recommendation_service=RecommendationService(RecommendationRepository(db)),
        )
        payload = review.model_dump()
        action_context = build_action_context(
            payload.pop("action_context"),
            "submit_review",
            payload.get("linked_recommendation_id") or payload.get("recommendation_id") or "review-submit",
        )
        res = review_capability.submit_review(review_service, payload, action_context)
        db.commit()
        return asdict(res)
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(e))
    except ReviewExecutionFailure as e:
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


@router.post("/{review_id}/complete", response_model=dict)
async def complete_performance_review(
    review_id: str,
    review: ReviewCompleteRequest,
    db: Session = Depends(get_db),
):
    try:
        lesson_service = LessonService(LessonRepository(db))
        review_service = ReviewService(
            ReviewRepository(db),
            lesson_service,
            RiskAuditor(),
            outcome_service=OutcomeService(OutcomeRepository(db)),
            recommendation_service=RecommendationService(RecommendationRepository(db)),
        )
        payload = review.model_dump()
        action_context = build_action_context(payload.pop("action_context"), "complete_review", review_id)
        res = review_capability.complete_review(
            review_service,
            review_id=review_id,
            observed_outcome=payload["observed_outcome"],
            verdict=payload["verdict"],
            variance_summary=payload["variance_summary"],
            cause_tags=payload["cause_tags"],
            lessons=payload["lessons"],
            followup_actions=payload["followup_actions"],
            action_context=action_context,
            approval_id=payload["approval_id"],
            require_approval=payload["require_approval"],
        )
        db.commit()
        return asdict(res)
    except ApprovalRequiredError as e:
        db.rollback()
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "status": "approval_required",
                "message": e.message,
                "approval_id": e.approval_id,
            },
        )
    except ReviewExecutionFailure as e:
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
