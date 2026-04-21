from dataclasses import dataclass, field
from typing import Any

from shared.utils.ids import new_id
from shared.time.clock import utc_now


@dataclass
class UsageSnapshot:
    id: str = field(default_factory=lambda: new_id("usage"))
    snapshot_date: str = field(default_factory=lambda: utc_now().isoformat())
    analyses_count: int = 0
    recommendations_generated_count: int = 0
    recommendations_adopted_count: int = 0
    recommendations_tracking_count: int = 0
    reviews_generated_count: int = 0
    reviews_completed_count: int = 0
    issues_opened_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: utc_now().isoformat())
