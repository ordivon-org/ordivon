from __future__ import annotations

from sqlalchemy.orm import Session

from domains.knowledge_feedback.models import KnowledgeFeedbackPacketRecord
from domains.knowledge_feedback.orm import KnowledgeFeedbackPacketORM
from knowledge.feedback import KnowledgeHint
from shared.utils.serialization import from_json_text, to_json_text


class KnowledgeFeedbackPacketRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, packet: KnowledgeFeedbackPacketRecord) -> KnowledgeFeedbackPacketORM:
        row = KnowledgeFeedbackPacketORM(
            id=packet.id,
            recommendation_id=packet.recommendation_id,
            review_id=packet.review_id,
            knowledge_entry_ids_json=to_json_text(list(packet.knowledge_entry_ids)),
            governance_hints_json=to_json_text([self._hint_to_payload(hint) for hint in packet.governance_hints]),
            intelligence_hints_json=to_json_text([self._hint_to_payload(hint) for hint in packet.intelligence_hints]),
        )
        self.db.add(row)
        self.db.flush()
        return row

    def get(self, packet_id: str) -> KnowledgeFeedbackPacketORM | None:
        return self.db.get(KnowledgeFeedbackPacketORM, packet_id)

    def list_for_recommendations(
        self, recommendation_ids: list[str], limit: int = 10
    ) -> list[KnowledgeFeedbackPacketORM]:
        if not recommendation_ids:
            return []
        return (
            self.db.query(KnowledgeFeedbackPacketORM)
            .filter(KnowledgeFeedbackPacketORM.recommendation_id.in_(recommendation_ids))
            .order_by(KnowledgeFeedbackPacketORM.created_at.desc())
            .limit(limit)
            .all()
        )

    def latest_for_recommendation(self, recommendation_id: str) -> KnowledgeFeedbackPacketORM | None:
        return (
            self.db.query(KnowledgeFeedbackPacketORM)
            .filter(KnowledgeFeedbackPacketORM.recommendation_id == recommendation_id)
            .order_by(KnowledgeFeedbackPacketORM.created_at.desc())
            .first()
        )

    def latest_for_review(self, review_id: str) -> KnowledgeFeedbackPacketORM | None:
        return (
            self.db.query(KnowledgeFeedbackPacketORM)
            .filter(KnowledgeFeedbackPacketORM.review_id == review_id)
            .order_by(KnowledgeFeedbackPacketORM.created_at.desc())
            .first()
        )

    def to_model(self, row: KnowledgeFeedbackPacketORM) -> KnowledgeFeedbackPacketRecord:
        return KnowledgeFeedbackPacketRecord(
            id=row.id,
            recommendation_id=row.recommendation_id,
            review_id=row.review_id,
            knowledge_entry_ids=tuple(from_json_text(row.knowledge_entry_ids_json, [])),
            governance_hints=tuple(
                self._payload_to_hint(payload) for payload in from_json_text(row.governance_hints_json, [])
            ),
            intelligence_hints=tuple(
                self._payload_to_hint(payload) for payload in from_json_text(row.intelligence_hints_json, [])
            ),
            created_at=row.created_at.isoformat(),
        )

    @staticmethod
    def _hint_to_payload(hint: KnowledgeHint) -> dict[str, object]:
        return {
            "target": hint.target,
            "hint_type": hint.hint_type,
            "summary": hint.summary,
            "evidence_object_ids": list(hint.evidence_object_ids),
        }

    @staticmethod
    def _payload_to_hint(payload: dict[str, object]) -> KnowledgeHint:
        return KnowledgeHint(
            target=str(payload.get("target") or ""),
            hint_type=str(payload.get("hint_type") or ""),
            summary=str(payload.get("summary") or ""),
            evidence_object_ids=tuple(
                str(item) for item in payload.get("evidence_object_ids", []) if isinstance(item, str)
            ),
        )
