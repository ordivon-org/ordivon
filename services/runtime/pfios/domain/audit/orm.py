from sqlalchemy import String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from pfios.core.db.base import Base
from pfios.core.utils.time import utc_now


class AuditEventORM(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(128), index=True)

    entity_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    entity_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    analysis_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    recommendation_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    outcome_snapshot_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    review_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    payload_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=utc_now)
