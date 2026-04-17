from sqlalchemy import String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from pfios.core.db.base import Base
from pfios.core.utils.time import utc_now


class OutcomeSnapshotORM(Base):
    __tablename__ = "outcome_snapshots"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    recommendation_id: Mapped[str] = mapped_column(String(64), index=True)

    outcome_state: Mapped[str] = mapped_column(String(32), default="unchanged")
    observed_metrics_json: Mapped[str] = mapped_column(Text, default="{}")
    evidence_refs_json: Mapped[str] = mapped_column(Text, default="[]")
    trigger_reason: Mapped[str] = mapped_column(Text, default="")
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    observed_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=utc_now)
