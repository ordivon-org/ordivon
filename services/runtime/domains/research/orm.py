from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from shared.time.clock import utc_now
from state.db.base import Base


class AnalysisORM(Base):
    __tablename__ = "analyses"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    query: Mapped[str] = mapped_column(Text, default="")
    symbol: Mapped[str | None] = mapped_column(String(64), nullable=True)
    timeframe: Mapped[str | None] = mapped_column(String(32), nullable=True)

    summary: Mapped[str] = mapped_column(Text, default="")
    thesis: Mapped[str] = mapped_column(Text, default="")
    risks_json: Mapped[str] = mapped_column(Text, default="[]")
    suggested_actions_json: Mapped[str] = mapped_column(Text, default="[]")
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=utc_now)
