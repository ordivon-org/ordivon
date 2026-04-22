from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from shared.time.clock import utc_now
from state.db.base import Base


class ApprovalRecordORM(Base):
    __tablename__ = "governance_approvals"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    action_key: Mapped[str] = mapped_column(String(128), index=True)
    entity_type: Mapped[str] = mapped_column(String(64), index=True)
    entity_id: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    requested_by: Mapped[str] = mapped_column(String(128))
    reason: Mapped[str] = mapped_column(Text)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    decided_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    decided_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=utc_now)
    decided_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
