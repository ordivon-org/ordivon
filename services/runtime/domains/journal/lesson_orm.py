from sqlalchemy import DateTime, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from shared.time.clock import utc_now
from state.db.base import Base


class LessonORM(Base):
    __tablename__ = "lessons"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    review_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    recommendation_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    title: Mapped[str] = mapped_column(Text, default="")
    body: Mapped[str] = mapped_column(Text, default="")
    lesson_type: Mapped[str] = mapped_column(String(64), default="review_learning")
    tags_json: Mapped[str] = mapped_column(Text, default="[]")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    source_refs_json: Mapped[str] = mapped_column(Text, default="[]")
    wiki_path: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=utc_now)
