from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from shared.time.clock import utc_now
from state.db.base import Base


class ScheduledTriggerORM(Base):
    __tablename__ = "scheduled_triggers"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    trigger_type: Mapped[str] = mapped_column(String(64), default="interval", index=True)
    cron_or_interval: Mapped[str] = mapped_column(String(128), default="")
    target_capability: Mapped[str] = mapped_column(String(128), default="", index=True)
    payload_json: Mapped[str] = mapped_column(Text, default="{}")
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    last_dispatched_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    dispatch_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
