from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from shared.time.clock import utc_now
from state.db.base import Base


class FinanceManualOutcomeORM(Base):
    __tablename__ = "finance_manual_outcomes"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    decision_intake_id: Mapped[str] = mapped_column(String(64), index=True)
    execution_receipt_id: Mapped[str] = mapped_column(String(64), index=True)

    outcome_source: Mapped[str] = mapped_column(String(32), default="manual")
    observed_outcome: Mapped[str] = mapped_column(Text, default="")
    verdict: Mapped[str] = mapped_column(String(32), default="")
    variance_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    plan_followed: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=utc_now)
