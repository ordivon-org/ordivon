from dataclasses import dataclass, field
from typing import Any

from shared.utils.ids import new_id
from shared.time.clock import utc_now


@dataclass
class AnalysisRequest:
    query: str
    symbol: str | None = None
    timeframe: str | None = None


@dataclass
class AnalysisResult:
    id: str = field(default_factory=lambda: new_id("analysis"))
    query: str = ""
    symbol: str | None = None
    timeframe: str | None = None
    summary: str = ""
    thesis: str = ""
    risks: list[str] = field(default_factory=list)
    suggested_actions: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: utc_now().isoformat())
