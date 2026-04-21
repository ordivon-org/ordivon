from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from shared.time.clock import utc_now
from state.db.base import Base


class WorkflowRunORM(Base):
    __tablename__ = "workflow_runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    workflow_name: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    request_summary: Mapped[str] = mapped_column(Text, default="")
    trigger: Mapped[str] = mapped_column(String(32), default="api")
    analysis_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    recommendation_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    intelligence_run_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    agent_action_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    execution_request_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    execution_receipt_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    failed_step: Mapped[str | None] = mapped_column(String(128), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    step_statuses_json: Mapped[str] = mapped_column(Text, default="[]")
    lineage_refs_json: Mapped[str] = mapped_column(Text, default="{}")
    started_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=utc_now)
    completed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
