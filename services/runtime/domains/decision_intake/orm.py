from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from shared.time.clock import utc_now
from state.db.base import Base


class DecisionIntakeORM(Base):
    __tablename__ = "decision_intakes"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    pack_id: Mapped[str] = mapped_column(String(64), default="")
    intake_type: Mapped[str] = mapped_column(String(64), default="")
    status: Mapped[str] = mapped_column(String(32), default="draft")
    payload_json: Mapped[str] = mapped_column(Text, default="{}")
    validation_errors_json: Mapped[str] = mapped_column(Text, default="[]")
    governance_status: Mapped[str] = mapped_column(String(32), default="not_started")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=utc_now)
