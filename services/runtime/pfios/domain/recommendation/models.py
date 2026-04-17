from dataclasses import dataclass, field
from typing import Any

from pfios.core.utils.ids import new_id
from pfios.core.utils.time import utc_now
from pfios.domain.common.enums import RecommendationStatus


@dataclass
class Recommendation:
    id: str = field(default_factory=lambda: new_id("reco"))
    analysis_id: str | None = None
    title: str = ""
    summary: str = ""
    rationale: str = ""
    expected_outcome: str = ""
    outcome_metric_type: str | None = None
    outcome_metric_config: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    priority: str = "normal"
    owner: str | None = None
    status: RecommendationStatus = RecommendationStatus.GENERATED
    decision: str | None = None
    decision_reason: str | None = None
    review_required: bool = True
    review_due_at: str | None = None
    due_at: str | None = None
    expires_at: str | None = None
    adopted_at: str | None = None
    completed_at: str | None = None
    latest_outcome_snapshot_id: str | None = None
    created_at: str = field(default_factory=lambda: utc_now().isoformat())
    updated_at: str = field(default_factory=lambda: utc_now().isoformat())
