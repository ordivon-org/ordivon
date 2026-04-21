from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from shared.time.clock import utc_now
from state.db.base import Base


class IntelligenceRunORM(Base):
    __tablename__ = "intelligence_runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    task_type: Mapped[str] = mapped_column(String(128), default="")
    actor_runtime: Mapped[str] = mapped_column(String(64), default="hermes")
    provider: Mapped[str | None] = mapped_column(String(128), nullable=True)
    model: Mapped[str | None] = mapped_column(String(256), nullable=True)
    task_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    trace_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    idempotency_key: Mapped[str] = mapped_column(String(128), default="", index=True)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    reason: Mapped[str] = mapped_column(Text, default="")
    actor: Mapped[str] = mapped_column(String(128), default="")
    context: Mapped[str] = mapped_column(String(128), default="")
    input_summary: Mapped[str] = mapped_column(Text, default="")
    request_payload_json: Mapped[str] = mapped_column(Text, default="{}")
    lineage_refs_json: Mapped[str] = mapped_column(Text, default="{}")
    output_summary: Mapped[str] = mapped_column(Text, default="")
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=utc_now)
