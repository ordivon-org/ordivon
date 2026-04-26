from __future__ import annotations

from dataclasses import asdict
from typing import TYPE_CHECKING, Any

from capabilities.boundary import ActionContext, require_action_context
from capabilities.contracts import (
    PendingReviewItemResult,
    PendingReviewListResult,
    ReviewDetailResult,
    ReviewResult,
    ReviewSkeletonResult,
)
from domains.journal.models import Review
from domains.finance_outcome.repository import FinanceManualOutcomeRepository
from domains.research.repository import AnalysisRepository
from domains.knowledge_feedback.repository import KnowledgeFeedbackPacketRepository
from domains.strategy.outcome_repository import OutcomeRepository
from execution.adapters import build_default_execution_adapter_registry
from knowledge.extraction import LessonExtractionService
from shared.time.clock import utc_now

if TYPE_CHECKING:
    from domains.journal.service import ReviewService


class ReviewCapability:
    """Workflow capability for review drafting and completion."""

    abstraction_type = "workflow"

    def generate_skeleton(self, report_id: str, recommendation_id: str | None = None) -> ReviewSkeletonResult:
        sections = [
            "expected_outcome",
            "actual_outcome",
            "deviation",
            "mistake_tags",
            "lessons",
            "new_rule_candidate",
        ]
        return ReviewSkeletonResult(
            id=None,
            status="draft",
            created_at=utc_now().isoformat(),
            recommendation_id=recommendation_id,
            review_type="recommendation_postmortem",
            sections=sections,
            metadata={
                "linked_report_id": report_id,
            },
        )

    def list_pending(self, service: "ReviewService", limit: int = 10) -> PendingReviewListResult:
        rows = service.list_pending(limit=limit)
        analysis_repository = AnalysisRepository(service.review_repository.db)
        outcome_repository = OutcomeRepository(service.review_repository.db)
        extraction_service = LessonExtractionService(service.review_repository.db)
        return PendingReviewListResult(
            reviews=[
                PendingReviewItemResult(
                    id=row.id,
                    recommendation_id=row.recommendation_id,
                    review_type=row.review_type,
                    status=row.status,
                    expected_outcome=row.expected_outcome or None,
                    created_at=row.created_at.isoformat()
                    if hasattr(row.created_at, "isoformat")
                    else str(row.created_at),
                    workflow_run_id=self._analysis_metadata(service, analysis_repository, row.recommendation_id).get("workflow_run_id"),
                    intelligence_run_id=self._analysis_metadata(service, analysis_repository, row.recommendation_id).get("intelligence_run_id"),
                    recommendation_generate_receipt_id=self._analysis_metadata(service, analysis_repository, row.recommendation_id).get("recommendation_generate_receipt_id"),
                    latest_outcome_status=self._latest_outcome_status(outcome_repository, row.recommendation_id),
                    latest_outcome_reason=self._latest_outcome_reason(outcome_repository, row.recommendation_id),
                    knowledge_hint_count=self._knowledge_hint_count(extraction_service, row.recommendation_id),
                )
                for row in rows
            ]
        )

    def get_detail(self, service: "ReviewService", review_id: str) -> ReviewDetailResult:
        review = service.get_model(review_id)
        outcome_repository = OutcomeRepository(service.review_repository.db)
        packet_repository = KnowledgeFeedbackPacketRepository(service.review_repository.db)
        latest_outcome_status = self._latest_outcome_status(outcome_repository, review.recommendation_id)
        latest_outcome_reason = self._latest_outcome_reason(outcome_repository, review.recommendation_id)
        packet = (
            packet_repository.get(review.knowledge_feedback_packet_id)
            if review.knowledge_feedback_packet_id
            else packet_repository.latest_for_review(review_id)
        )
        packet_model = packet_repository.to_model(packet) if packet is not None else None

        return ReviewDetailResult(
            id=review.id,
            recommendation_id=review.recommendation_id,
            review_type=review.review_type,
            status=review.status.value if hasattr(review.status, "value") else str(review.status),
            expected_outcome=review.expected_outcome or None,
            observed_outcome=review.observed_outcome,
            verdict=review.verdict.value if hasattr(review.verdict, "value") else review.verdict,
            variance_summary=review.variance_summary,
            cause_tags=list(review.cause_tags),
            lessons=list(review.lessons),
            followup_actions=list(review.followup_actions),
            created_at=review.created_at,
            completed_at=review.completed_at,
            submit_execution_request_id=review.submit_execution_request_id,
            submit_execution_receipt_id=review.submit_execution_receipt_id,
            complete_execution_request_id=review.complete_execution_request_id,
            complete_execution_receipt_id=review.complete_execution_receipt_id,
            latest_outcome_status=latest_outcome_status,
            latest_outcome_reason=latest_outcome_reason,
            knowledge_feedback_packet_id=review.knowledge_feedback_packet_id or (packet_model.id if packet_model is not None else None),
            governance_hint_count=len(packet_model.governance_hints) if packet_model is not None else 0,
            intelligence_hint_count=len(packet_model.intelligence_hints) if packet_model is not None else 0,
            outcome_ref_type=review.outcome_ref_type,
            outcome_ref_id=review.outcome_ref_id,
            metadata={
                "trace_path": f"/api/v1/traces/reviews/{review.id}",
                "knowledge_feedback_status": "prepared" if packet_model is not None else "not_prepared_yet",
            },
        )

    def submit_review(
        self,
        service: ReviewService,
        payload: dict[str, Any],
        action_context: ActionContext | None,
    ) -> ReviewResult:
        context = require_action_context("review submission", action_context)
        outcome_ref_type = payload.get("outcome_ref_type")
        outcome_ref_id = payload.get("outcome_ref_id")
        self._validate_outcome_ref(service.review_repository.db, outcome_ref_type, outcome_ref_id)
        review = Review(
            recommendation_id=payload.get("linked_recommendation_id") or payload.get("recommendation_id"),
            review_type="recommendation_postmortem",
            expected_outcome=payload.get("expected_outcome", ""),
            observed_outcome=payload.get("actual_outcome"),
            variance_summary=payload.get("deviation"),
            cause_tags=self._split_tags(payload.get("mistake_tags")),
            lessons=[lesson["lesson_text"] for lesson in payload.get("lessons", [])],
            followup_actions=[payload["new_rule_candidate"]] if payload.get("new_rule_candidate") else [],
            outcome_ref_type=outcome_ref_type,
            outcome_ref_id=outcome_ref_id,
        )
        adapter = build_default_execution_adapter_registry().resolve("review", service.review_repository.db)
        result = adapter.submit(
            service=service,
            review=review,
            action_context=context,
        )
        row = result.review_row

        return ReviewResult(
            id=row.id,
            status=row.status,
            created_at=row.created_at.isoformat() if hasattr(row, "created_at") else utc_now().isoformat(),
            recommendation_id=row.recommendation_id,
            lessons_created=len(payload.get("lessons", [])),
            metadata={
                "action_context": asdict(context),
                "execution_request_id": result.execution_request_id,
                "execution_receipt_id": result.execution_receipt_id,
            },
        )

    def create_review(
        self,
        service: ReviewService,
        recommendation_id: str,
        action_context: ActionContext | None,
        review_type: str = "recommendation_postmortem",
        expected_outcome: str | None = None,
        outcome_ref_type: str | None = None,
        outcome_ref_id: str | None = None,
    ) -> ReviewResult:
        context = require_action_context("review creation", action_context)
        self._validate_outcome_ref(service.review_repository.db, outcome_ref_type, outcome_ref_id)
        review = Review(
            recommendation_id=recommendation_id,
            review_type=review_type,
            expected_outcome=expected_outcome or "",
            outcome_ref_type=outcome_ref_type,
            outcome_ref_id=outcome_ref_id,
        )
        row = service.create(review)
        return ReviewResult(
            id=row.id,
            status=row.status,
            created_at=row.created_at.isoformat() if hasattr(row, "created_at") else utc_now().isoformat(),
            recommendation_id=row.recommendation_id,
            lessons_created=0,
            metadata={"action_context": asdict(context)},
        )

    def complete_review(
        self,
        service: ReviewService,
        review_id: str,
        observed_outcome: str,
        verdict: Any,
        variance_summary: str | None,
        cause_tags: list[str],
        lessons: list[str],
        followup_actions: list[str],
        action_context: ActionContext | None,
        approval_id: str | None = None,
        require_approval: bool = False,
    ) -> ReviewResult:
        context = require_action_context("review completion", action_context)
        adapter = build_default_execution_adapter_registry().resolve("review", service.review_repository.db)
        result = adapter.complete(
            service=service,
            review_id=review_id,
            observed_outcome=observed_outcome,
            verdict=verdict,
            variance_summary=variance_summary,
            cause_tags=cause_tags,
            lessons=lessons,
            followup_actions=followup_actions,
            action_context=context,
            approval_id=approval_id,
            require_approval=require_approval,
        )
        review_row = result.review_row
        lesson_rows = result.lesson_rows
        knowledge_feedback = result.knowledge_feedback
        return ReviewResult(
            id=review_row.id,
            status=review_row.status.value if hasattr(review_row.status, "value") else review_row.status,
            created_at=review_row.created_at.isoformat() if hasattr(review_row, "created_at") else utc_now().isoformat(),
            recommendation_id=review_row.recommendation_id,
            lessons_created=len(lesson_rows),
            metadata={
                "action_context": asdict(context),
                "execution_request_id": result.execution_request_id,
                "execution_receipt_id": result.execution_receipt_id,
                "knowledge_feedback": {
                    "id": knowledge_feedback.id,
                    "recommendation_id": knowledge_feedback.recommendation_id,
                    "review_id": knowledge_feedback.review_id,
                    "knowledge_entry_ids": list(knowledge_feedback.knowledge_entry_ids),
                    "governance_hints": [
                        {
                            "target": hint.target,
                            "hint_type": hint.hint_type,
                            "summary": hint.summary,
                            "evidence_object_ids": list(hint.evidence_object_ids),
                        }
                        for hint in knowledge_feedback.governance_hints
                    ],
                    "intelligence_hints": [
                        {
                            "target": hint.target,
                            "hint_type": hint.hint_type,
                            "summary": hint.summary,
                            "evidence_object_ids": list(hint.evidence_object_ids),
                        }
                        for hint in knowledge_feedback.intelligence_hints
                    ],
                }
                if knowledge_feedback is not None
                else None,
            },
        )

    @staticmethod
    def _validate_outcome_ref(db: Any, outcome_ref_type: str | None, outcome_ref_id: str | None) -> None:
        """Validate outcome reference pair and that referenced outcome exists.

        Rules:
        - Both None: OK (no outcome reference).
        - Only one provided: reject (must be a pair).
        - Unsupported type: reject.
        - ``finance_manual_outcome``: must reference an existing FinanceManualOutcome.
        """
        # pylint: disable=import-outside-toplevel
        if outcome_ref_type is None and outcome_ref_id is None:
            return

        if outcome_ref_type is None and outcome_ref_id is not None:
            raise ValueError("outcome_ref_id provided without outcome_ref_type")
        if outcome_ref_type is not None and outcome_ref_id is None:
            raise ValueError("outcome_ref_type provided without outcome_ref_id")

        SUPPORTED = frozenset({"finance_manual_outcome"})
        if outcome_ref_type not in SUPPORTED:
            raise ValueError(
                f"Unsupported outcome_ref_type: {outcome_ref_type!r}. "
                f"Supported: {sorted(SUPPORTED)}"
            )

        if outcome_ref_type == "finance_manual_outcome":
            repo = FinanceManualOutcomeRepository(db)
            existing = repo.get(outcome_ref_id)
            if existing is None:
                raise ValueError(
                    f"FinanceManualOutcome not found: {outcome_ref_id}"
                )

    @staticmethod
    def _split_tags(raw_tags: str | None) -> list[str]:
        if not raw_tags:
            return []
        return [tag.strip() for tag in raw_tags.split(",") if tag.strip()]

    def _analysis_metadata(
        self,
        service: "ReviewService",
        analysis_repository: AnalysisRepository,
        recommendation_id: str | None,
    ) -> dict[str, Any]:
        if not recommendation_id or service.recommendation_service is None:
            return {}
        try:
            recommendation = service.recommendation_service.get_model(recommendation_id)
            if not recommendation.analysis_id:
                return {}
            row = analysis_repository.get(recommendation.analysis_id)
            if row is None:
                return {}
            return analysis_repository.to_model(row).metadata
        except Exception:
            return {}

    def _latest_outcome_status(self, outcome_repository: OutcomeRepository, recommendation_id: str | None) -> str | None:
        if not recommendation_id:
            return None
        try:
            rows = outcome_repository.list_for_recommendation(recommendation_id)
            if not rows:
                return None
            return outcome_repository.to_model(rows[0]).outcome_state.value
        except Exception:
            return None

    def _latest_outcome_reason(self, outcome_repository: OutcomeRepository, recommendation_id: str | None) -> str | None:
        if not recommendation_id:
            return None
        try:
            rows = outcome_repository.list_for_recommendation(recommendation_id)
            if not rows:
                return None
            return outcome_repository.to_model(rows[0]).trigger_reason or None
        except Exception:
            return None

    def _knowledge_hint_count(self, extraction_service: LessonExtractionService, recommendation_id: str | None) -> int:
        if not recommendation_id:
            return 0
        try:
            return len(extraction_service.extract_for_recommendation(recommendation_id))
        except Exception:
            return 0
