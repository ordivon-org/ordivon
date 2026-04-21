from __future__ import annotations

from domains.knowledge_feedback.models import KnowledgeFeedbackPacketRecord
from domains.knowledge_feedback.repository import KnowledgeFeedbackPacketRepository
from knowledge.feedback import KnowledgeFeedbackPacket


class KnowledgeFeedbackPacketService:
    def __init__(self, repository: KnowledgeFeedbackPacketRepository) -> None:
        self.repository = repository

    def persist_packet(self, packet: KnowledgeFeedbackPacket) -> KnowledgeFeedbackPacketRecord:
        record = KnowledgeFeedbackPacketRecord(
            id=packet.id,
            recommendation_id=packet.recommendation_id,
            review_id=packet.review_id,
            knowledge_entry_ids=packet.knowledge_entry_ids,
            governance_hints=packet.governance_hints,
            intelligence_hints=packet.intelligence_hints,
            created_at=packet.created_at,
        )
        row = self.repository.create(record)
        return self.repository.to_model(row)

    def latest_for_recommendation(self, recommendation_id: str) -> KnowledgeFeedbackPacketRecord | None:
        row = self.repository.latest_for_recommendation(recommendation_id)
        if row is None:
            return None
        return self.repository.to_model(row)

    def latest_for_review(self, review_id: str) -> KnowledgeFeedbackPacketRecord | None:
        row = self.repository.latest_for_review(review_id)
        if row is None:
            return None
        return self.repository.to_model(row)
