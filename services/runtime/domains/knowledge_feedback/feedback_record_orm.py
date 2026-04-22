from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from shared.time.clock import utc_now
from state.db.base import Base


class FeedbackRecordORM(Base):
    __tablename__ = "knowledge_feedback_records"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    packet_id: Mapped[str] = mapped_column(String(64), index=True)
    recommendation_id: Mapped[str] = mapped_column(String(64), index=True)
    review_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    consumer_type: Mapped[str] = mapped_column(String(32), index=True)
    subject_key: Mapped[str] = mapped_column(String(255), index=True)
    knowledge_entry_ids_json: Mapped[str] = mapped_column(Text, default="[]")
    consumed_hint_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
