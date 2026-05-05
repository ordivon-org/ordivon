from dataclasses import dataclass, field
from typing import Any

from shared.utils.ids import new_id
from shared.time.clock import utc_now


@dataclass
class AuditEvent:
    id: str = field(default_factory=lambda: new_id("audit"))
    event_type: str = ""
    entity_type: str | None = None
    entity_id: str | None = None
    analysis_id: str | None = None
    recommendation_id: str | None = None
    outcome_snapshot_id: str | None = None
    review_id: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: utc_now().isoformat())
