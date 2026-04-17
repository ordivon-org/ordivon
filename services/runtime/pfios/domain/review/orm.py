from sqlalchemy import String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from pfios.core.db.base import Base
from pfios.core.utils.time import utc_now


class ReviewORM(Base):
    __tablename__ = "reviews"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    recommendation_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    analysis_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    review_type: Mapped[str] = mapped_column(String(64), default="recommendation_postmortem")
    status: Mapped[str] = mapped_column(String(32), default="pending")

    expected_outcome: Mapped[str] = mapped_column(Text, default="")
    observed_outcome: Mapped[str | None] = mapped_column(Text, nullable=True)
    verdict: Mapped[str | None] = mapped_column(String(32), nullable=True)
    variance_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    cause_tags_json: Mapped[str] = mapped_column(Text, default="[]")
    lessons_json: Mapped[str] = mapped_column(Text, default="[]")
    followup_actions_json: Mapped[str] = mapped_column(Text, default="[]")
    wiki_path: Mapped[str | None] = mapped_column(Text, nullable=True)

    scheduled_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=utc_now)
    started_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=utc_now)
