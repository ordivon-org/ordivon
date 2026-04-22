from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from domains.knowledge_feedback.feedback_record_models import FeedbackRecord
from domains.knowledge_feedback.feedback_record_orm import FeedbackRecordORM
from shared.utils.serialization import from_json_text, to_json_text


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class FeedbackRecordRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, record: FeedbackRecord) -> FeedbackRecordORM:
        row = FeedbackRecordORM(
            id=record.id,
            packet_id=record.packet_id,
            recommendation_id=record.recommendation_id,
            review_id=record.review_id,
            consumer_type=record.consumer_type,
            subject_key=record.subject_key,
            knowledge_entry_ids_json=to_json_text(list(record.knowledge_entry_ids)),
            consumed_hint_count=record.consumed_hint_count,
            created_at=_parse_dt(record.created_at),
        )
        self.db.add(row)
        self.db.flush()
        return row

    def latest_for_packet_consumer_subject(
        self,
        packet_id: str,
        *,
        consumer_type: str,
        subject_key: str,
    ) -> FeedbackRecordORM | None:
        return (
            self.db.query(FeedbackRecordORM)
            .filter(
                FeedbackRecordORM.packet_id == packet_id,
                FeedbackRecordORM.consumer_type == consumer_type,
                FeedbackRecordORM.subject_key == subject_key,
            )
            .order_by(FeedbackRecordORM.created_at.desc())
            .first()
        )

    def list_for_recommendation(self, recommendation_id: str) -> list[FeedbackRecordORM]:
        return (
            self.db.query(FeedbackRecordORM)
            .filter(FeedbackRecordORM.recommendation_id == recommendation_id)
            .order_by(FeedbackRecordORM.created_at.desc())
            .all()
        )

    def to_model(self, row: FeedbackRecordORM) -> FeedbackRecord:
        return FeedbackRecord(
            id=row.id,
            packet_id=row.packet_id,
            recommendation_id=row.recommendation_id,
            review_id=row.review_id,
            consumer_type=row.consumer_type,
            subject_key=row.subject_key,
            knowledge_entry_ids=tuple(from_json_text(row.knowledge_entry_ids_json, [])),
            consumed_hint_count=row.consumed_hint_count,
            created_at=row.created_at.isoformat(),
        )
