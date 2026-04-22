from __future__ import annotations

from domains.knowledge_feedback.feedback_record_models import FeedbackRecord
from domains.knowledge_feedback.feedback_record_repository import FeedbackRecordRepository
from domains.knowledge_feedback.models import KnowledgeFeedbackPacketRecord


class FeedbackRecordService:
    def __init__(self, repository: FeedbackRecordRepository) -> None:
        self.repository = repository

    def record_consumption(
        self,
        packet: KnowledgeFeedbackPacketRecord,
        *,
        consumer_type: str,
        subject_key: str,
        consumed_hint_count: int,
    ):
        existing = self.repository.latest_for_packet_consumer_subject(
            packet.id,
            consumer_type=consumer_type,
            subject_key=subject_key,
        )
        if existing is not None:
            return existing
        return self.repository.create(
            FeedbackRecord(
                packet_id=packet.id,
                recommendation_id=packet.recommendation_id,
                review_id=packet.review_id,
                consumer_type=consumer_type,
                subject_key=subject_key,
                knowledge_entry_ids=packet.knowledge_entry_ids,
                consumed_hint_count=consumed_hint_count,
            )
        )
