from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from shared.time.clock import utc_now
from state.db.base import Base


class CandidateRuleORM(Base):
    __tablename__ = "candidate_rules"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    issue_key: Mapped[str] = mapped_column(String(255), index=True)
    summary: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="draft", index=True)
    recommendation_ids_json: Mapped[str] = mapped_column(Text, default="[]")
    review_ids_json: Mapped[str] = mapped_column(Text, default="[]")
    lesson_ids_json: Mapped[str] = mapped_column(Text, default="[]")
    knowledge_entry_ids_json: Mapped[str] = mapped_column(Text, default="[]")
    source_refs_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
