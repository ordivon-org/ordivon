from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from shared.time.clock import utc_now
from state.db.base import Base


class KnowledgeFeedbackPacketORM(Base):
    __tablename__ = "knowledge_feedback_packets"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    recommendation_id: Mapped[str] = mapped_column(String(64), index=True)
    review_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    knowledge_entry_ids_json: Mapped[str] = mapped_column(Text, default="[]")
    governance_hints_json: Mapped[str] = mapped_column(Text, default="[]")
    intelligence_hints_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
