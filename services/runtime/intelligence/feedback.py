from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from domains.knowledge_feedback.feedback_record_repository import FeedbackRecordRepository
from domains.knowledge_feedback.feedback_record_service import FeedbackRecordService
from domains.knowledge_feedback.repository import KnowledgeFeedbackPacketRepository
from domains.research.orm import AnalysisORM
from domains.strategy.orm import RecommendationORM
from knowledge.extraction import LessonExtractionService
from knowledge.feedback import KnowledgeFeedbackService


@dataclass(frozen=True, slots=True)
class IntelligenceFeedbackContext:
    memory_lessons: tuple[str, ...] = field(default_factory=tuple)
    related_reviews: tuple[str, ...] = field(default_factory=tuple)


class IntelligenceFeedbackReader:
    """Reads evidence-backed intelligence hints for future analysis context."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.feedback_record_service = FeedbackRecordService(FeedbackRecordRepository(db))

    def read_for_symbol(self, symbol: str | None, limit: int = 3) -> IntelligenceFeedbackContext:
        if not symbol:
            return IntelligenceFeedbackContext()

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
            return IntelligenceFeedbackContext()

        extraction_service = LessonExtractionService(self.db)
        feedback_service = KnowledgeFeedbackService()
        packet_repository = KnowledgeFeedbackPacketRepository(self.db)
        memory_lessons: list[str] = []
        related_reviews: list[str] = []
        seen_lesson_summaries: set[str] = set()
        seen_reviews: set[str] = set()

        for recommendation_id in recommendation_ids:
            entries = None
            packet_row = packet_repository.latest_for_recommendation(recommendation_id)
            if packet_row is not None:
                packet = packet_repository.to_model(packet_row)
                if packet.intelligence_hints:
                    self.feedback_record_service.record_consumption(
                        packet,
                        consumer_type="intelligence",
                        subject_key=symbol,
                        consumed_hint_count=len(packet.intelligence_hints),
                    )
            else:
                entries = extraction_service.extract_for_recommendation(recommendation_id)
                if not entries:
                    continue
                packet = feedback_service.build_packet(recommendation_id, entries)
            for hint in packet.intelligence_hints:
                if hint.summary in seen_lesson_summaries:
                    continue
                seen_lesson_summaries.add(hint.summary)
                memory_lessons.append(hint.summary)
            if packet.review_id and packet.review_id not in seen_reviews:
                seen_reviews.add(packet.review_id)
                related_reviews.append(packet.review_id)
            if entries is not None:
                for entry in entries:
                    for ref in entry.evidence_refs:
                        if ref.object_type == "review" and ref.object_id not in seen_reviews:
                            seen_reviews.add(ref.object_id)
                            related_reviews.append(ref.object_id)

        return IntelligenceFeedbackContext(
            memory_lessons=tuple(memory_lessons[:limit]),
            related_reviews=tuple(related_reviews[:limit]),
        )
