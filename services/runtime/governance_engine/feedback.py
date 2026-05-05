from __future__ import annotations

from sqlalchemy.orm import Session

from domains.knowledge_feedback.feedback_record_repository import FeedbackRecordRepository
from domains.knowledge_feedback.feedback_record_service import FeedbackRecordService
from domains.knowledge_feedback.repository import KnowledgeFeedbackPacketRepository
from domains.research.orm import AnalysisORM
from domains.strategy.orm import RecommendationORM
from governance_engine.decision import GovernanceAdvisoryHint
from knowledge.extraction import LessonExtractionService
from knowledge.feedback import KnowledgeFeedbackService


class GovernanceFeedbackHintConsumer:
    """Consumes evidence-backed governance hints under advisory-only semantics."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.feedback_record_service = FeedbackRecordService(FeedbackRecordRepository(db))

    def list_hints_for_symbol(self, symbol: str | None, limit: int = 3) -> list[GovernanceAdvisoryHint]:
        if not symbol:
            return []

        recommendation_ids = [
            row.id
            for row in (
                self.db.query(RecommendationORM)
                .join(AnalysisORM, AnalysisORM.id == RecommendationORM.analysis_id)
                .filter(AnalysisORM.symbol == symbol)
                .order_by(RecommendationORM.created_at.desc())
                .limit(limit)
                .all()
            )
        ]
        if not recommendation_ids:
            return []

        hints: list[GovernanceAdvisoryHint] = []
        seen_keys: set[tuple[str, tuple[str, ...]]] = set()
        packet_repository = KnowledgeFeedbackPacketRepository(self.db)
        extraction_service = LessonExtractionService(self.db)
        feedback_service = KnowledgeFeedbackService()

        for recommendation_id in recommendation_ids:
            packet_row = packet_repository.latest_for_recommendation(recommendation_id)
            if packet_row is not None:
                packet = packet_repository.to_model(packet_row)
                if packet.governance_hints:
                    self.feedback_record_service.record_consumption(
                        packet,
                        consumer_type="governance",
                        subject_key=symbol,
                        consumed_hint_count=len(packet.governance_hints),
                    )
            else:
                entries = extraction_service.extract_for_recommendation(recommendation_id)
                if not entries:
                    continue
                packet = feedback_service.build_packet(recommendation_id, entries)
            for hint in packet.governance_hints:
                key = (hint.summary, tuple(hint.evidence_object_ids))
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                hints.append(
                    GovernanceAdvisoryHint(
                        target=hint.target,
                        hint_type=hint.hint_type,
                        summary=hint.summary,
                        evidence_object_ids=hint.evidence_object_ids,
                    )
                )

        return hints[:limit]


class GovernanceFeedbackReader(GovernanceFeedbackHintConsumer):
    """Backward-compatible name for governance advisory hint consumption."""
