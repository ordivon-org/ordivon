from sqlalchemy import String, Text, Float, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from pfios.core.db.base import Base
from pfios.core.utils.time import utc_now


class RecommendationORM(Base):
    __tablename__ = "recommendations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    analysis_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    title: Mapped[str] = mapped_column(Text, default="")
    summary: Mapped[str] = mapped_column(Text, default="")
    rationale: Mapped[str] = mapped_column(Text, default="")
    expected_outcome: Mapped[str] = mapped_column(Text, default="")

    outcome_metric_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    outcome_metric_config_json: Mapped[str] = mapped_column(Text, default="{}")

    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    priority: Mapped[str] = mapped_column(String(32), default="normal")
    owner: Mapped[str | None] = mapped_column(String(128), nullable=True)

    status: Mapped[str] = mapped_column(String(32), default="generated")
    decision: Mapped[str | None] = mapped_column(String(32), nullable=True)
    decision_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    review_required: Mapped[bool] = mapped_column(Boolean, default=True)
    review_due_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    due_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    adopted_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    latest_outcome_snapshot_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
