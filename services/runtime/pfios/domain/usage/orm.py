from sqlalchemy import String, Text, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from pfios.core.db.base import Base
from pfios.core.utils.time import utc_now


class UsageSnapshotORM(Base):
    __tablename__ = "usage_snapshots"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    snapshot_date: Mapped[DateTime] = mapped_column(DateTime(timezone=True), index=True)

    analyses_count: Mapped[int] = mapped_column(Integer, default=0)
    recommendations_generated_count: Mapped[int] = mapped_column(Integer, default=0)
    recommendations_adopted_count: Mapped[int] = mapped_column(Integer, default=0)
    recommendations_tracking_count: Mapped[int] = mapped_column(Integer, default=0)
    reviews_generated_count: Mapped[int] = mapped_column(Integer, default=0)
    reviews_completed_count: Mapped[int] = mapped_column(Integer, default=0)
    issues_opened_count: Mapped[int] = mapped_column(Integer, default=0)

    metadata_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=utc_now)
