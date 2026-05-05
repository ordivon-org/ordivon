from domains.journal.models import Review
from domains.journal.repository import ReviewRepository
from domains.journal.lesson_models import Lesson
from domains.journal.lesson_service import LessonService
from domains.candidate_rules.draft_extraction import CandidateRuleDraftExtractionService
from domains.candidate_rules.repository import CandidateRuleRepository
from domains.knowledge_feedback.repository import KnowledgeFeedbackPacketRepository
from domains.knowledge_feedback.service import KnowledgeFeedbackPacketService
from domains.strategy.outcome_models import OutcomeSnapshot
from domains.strategy.outcome_service import OutcomeService
from domains.strategy.service import RecommendationService
from domains.journal.state_machine import ReviewStateMachine
from governance_engine.audit.auditor import RiskAuditor
from knowledge.extraction import LessonExtractionService
from knowledge.feedback import KnowledgeFeedbackService
from shared.enums.domain import OutcomeState, ReviewStatus, ReviewVerdict
from shared.errors.domain import DomainNotFound


class ReviewService:
    def __init__(
        self,
        review_repository: ReviewRepository,
        lesson_service: LessonService,
        auditor: RiskAuditor | None = None,
        outcome_service: OutcomeService | None = None,
        recommendation_service: RecommendationService | None = None,
    ) -> None:
        self.review_repository = review_repository
        self.lesson_service = lesson_service
        self.auditor = auditor
        self.outcome_service = outcome_service
        self.recommendation_service = recommendation_service
        self.state_machine = ReviewStateMachine()

    def create(self, review: Review):
        return self.create_with_options(review, emit_review_submitted_audit=True)

    def create_with_options(self, review: Review, *, emit_review_submitted_audit: bool):
        row = self.review_repository.create(review)

        if self.auditor is not None and emit_review_submitted_audit:
            self.auditor.record_event(
                event_type="review_submitted",
                payload={
                    "expected_outcome": review.expected_outcome,
                    "actual_outcome": review.observed_outcome,
                    "lessons_count": len(review.lessons) if hasattr(review, "lessons") else 0,
                },
                entity_type="review",
                entity_id=row.id,
                recommendation_id=row.recommendation_id,
                review_id=row.id,
                db=self.review_repository.db,
            )

        return row

    def list_pending(self, limit: int = 10):
        return self.review_repository.list_pending()[:limit]

    def get_model(self, review_id: str) -> Review:
        row = self.review_repository.get(review_id)
        if row is None:
            raise DomainNotFound(f"Review not found: {review_id}")
        return self.review_repository.to_model(row)

    def complete_review(
        self,
        review_id: str,
        observed_outcome: str,
        verdict: ReviewVerdict,
        variance_summary: str | None,
        cause_tags: list[str],
        lessons: list[str],
        followup_actions: list[str],
        emit_review_completed_audit: bool = True,
        lesson_types: list[str] | None = None,
    ):
        row = self.review_repository.get(review_id)
        if row is None:
            raise DomainNotFound(f"Review not found: {review_id}")

        self.state_machine.ensure_transition(ReviewStatus(row.status), ReviewStatus.COMPLETED)
        row.status = ReviewStatus.COMPLETED.value
        row.observed_outcome = observed_outcome
        row.verdict = verdict.value
        row.variance_summary = variance_summary
        row.cause_tags_json = self.review_repository.encode_list(cause_tags)
        row.lessons_json = self.review_repository.encode_list(lessons)
        row.followup_actions_json = self.review_repository.encode_list(followup_actions)

        self.review_repository.db.flush()

        if self.auditor is not None and emit_review_completed_audit:
            self.auditor.record_event(
                "review_completed",
                {
                    "verdict": verdict.value,
                    "observed_outcome": observed_outcome,
                    "lessons_count": len(lessons),
                    "followup_actions_count": len(followup_actions),
                },
                entity_type="review",
                entity_id=row.id,
                review_id=row.id,
                recommendation_id=row.recommendation_id,
                db=self.review_repository.db,
            )

        self._backfill_outcome_snapshot(
            recommendation_id=row.recommendation_id,
            review_id=row.id,
            observed_outcome=observed_outcome,
            verdict=verdict,
            variance_summary=variance_summary,
        )

        lesson_records: list[dict] = []
        lesson_rows = []
        outcome_ref_source = (
            f"finance_manual_outcome:{row.outcome_ref_id}"
            if row.outcome_ref_id and row.outcome_ref_type == "finance_manual_outcome"
            else None
        )
        types = lesson_types or []
        for idx, lesson_text in enumerate(lessons, start=1):
            source_refs: list[str] = []
            if row.recommendation_id:
                source_refs.append(f"recommendation:{row.recommendation_id}")
            if outcome_ref_source:
                source_refs.append(outcome_ref_source)
            lesson_type = types[idx - 1] if idx - 1 < len(types) else "review_learning"
            lesson_model = Lesson(
                review_id=row.id,
                recommendation_id=row.recommendation_id,
                title=f"Lesson {idx} from review {row.id}",
                body=lesson_text,
                lesson_type=lesson_type,
                tags=cause_tags,
                confidence=0.8,
                source_refs=source_refs,
            )
            lesson_row = self.lesson_service.create(lesson_model)
            lesson_rows.append(lesson_row)
            lesson_records.append(
                {
                    "id": lesson_row.id,
                    "lesson_type": lesson_type,
                    "body": lesson_text,
                    "tags": cause_tags,
                }
            )

            if self.auditor is not None:
                self.auditor.record_event(
                    "lesson_persisted",
                    {
                        "lesson_id": lesson_row.id,
                        "review_id": row.id,
                        "recommendation_id": row.recommendation_id,
                    },
                    entity_type="lesson",
                    entity_id=lesson_row.id,
                    review_id=row.id,
                    recommendation_id=row.recommendation_id,
                    db=self.review_repository.db,
                )

        # ── Draft extraction: rule_candidate lessons → CandidateRule drafts ──
        extraction = CandidateRuleDraftExtractionService(CandidateRuleRepository(self.review_repository.db))
        extraction.extract_from_review(
            review_id=row.id,
            recommendation_id=row.recommendation_id,
            lessons=lesson_records,
            outcome_ref_type=row.outcome_ref_type,
            outcome_ref_id=row.outcome_ref_id,
        )

        knowledge_feedback = self._build_knowledge_feedback(row.recommendation_id, row.id)

        return row, lesson_rows, knowledge_feedback

    def _backfill_outcome_snapshot(
        self,
        *,
        recommendation_id: str | None,
        review_id: str,
        observed_outcome: str,
        verdict: ReviewVerdict,
        variance_summary: str | None,
    ):
        if recommendation_id is None or self.outcome_service is None or self.recommendation_service is None:
            return None

        snapshot = OutcomeSnapshot(
            recommendation_id=recommendation_id,
            outcome_state=self._map_verdict_to_outcome_state(verdict),
            observed_metrics={"review_verdict": verdict.value},
            evidence_refs=[f"review:{review_id}", f"recommendation:{recommendation_id}"],
            trigger_reason="review_completion_backfill",
            note=variance_summary or observed_outcome,
        )
        outcome_row = self.outcome_service.create_snapshot(snapshot)
        self.recommendation_service.attach_latest_outcome_snapshot(
            recommendation_id=recommendation_id,
            outcome_snapshot_id=outcome_row.id,
        )

        if self.auditor is not None:
            self.auditor.record_event(
                "outcome_backfilled",
                {
                    "outcome_snapshot_id": outcome_row.id,
                    "outcome_state": snapshot.outcome_state.value,
                    "trigger_reason": snapshot.trigger_reason,
                    "review_id": review_id,
                },
                entity_type="outcome_snapshot",
                entity_id=outcome_row.id,
                review_id=review_id,
                recommendation_id=recommendation_id,
                db=self.review_repository.db,
            )
        return outcome_row

    def _build_knowledge_feedback(self, recommendation_id: str | None, review_id: str):
        extraction = LessonExtractionService(self.review_repository.db)
        if recommendation_id is not None:
            entries = extraction.extract_for_recommendation(recommendation_id)
        else:
            entries = extraction.extract_for_review_by_id(review_id)

        if not entries:
            return None

        packet = KnowledgeFeedbackService().build_packet(
            recommendation_id or review_id,
            entries,
            review_id=review_id,
        )
        persisted_packet = KnowledgeFeedbackPacketService(
            KnowledgeFeedbackPacketRepository(self.review_repository.db)
        ).persist_packet(packet)
        self.review_repository.attach_knowledge_feedback_packet(
            review_id,
            packet_id=persisted_packet.id,
        )
        if self.auditor is not None:
            self.auditor.record_event(
                "knowledge_feedback_prepared",
                {
                    "knowledge_feedback_packet_id": persisted_packet.id,
                    "recommendation_id": recommendation_id,
                    "review_id": review_id,
                    "knowledge_entry_ids": list(persisted_packet.knowledge_entry_ids),
                    "governance_hint_count": len(persisted_packet.governance_hints),
                    "intelligence_hint_count": len(persisted_packet.intelligence_hints),
                },
                entity_type="knowledge_feedback",
                entity_id=persisted_packet.id,
                review_id=review_id,
                recommendation_id=recommendation_id,
                db=self.review_repository.db,
            )
        return persisted_packet

    @staticmethod
    def _map_verdict_to_outcome_state(verdict: ReviewVerdict) -> OutcomeState:
        if verdict == ReviewVerdict.VALIDATED:
            return OutcomeState.SATISFIED
        if verdict == ReviewVerdict.INVALIDATED:
            return OutcomeState.FAILED
        if verdict == ReviewVerdict.PARTIALLY_VALIDATED:
            return OutcomeState.IMPROVING
        return OutcomeState.INCONCLUSIVE
