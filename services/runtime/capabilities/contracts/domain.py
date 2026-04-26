from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class RecommendationResult:
    id: str
    status: str
    created_at: str
    analysis_id: str | None
    symbol: str | None
    action_summary: str | None
    confidence: float | None
    decision: str | None
    decision_reason: str | None
    adopted: bool
    review_status: str | None
    outcome_status: str | None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ReviewResult:
    id: str
    status: str
    created_at: str
    recommendation_id: str | None
    lessons_created: int
    outcome_ref_type: str | None = None
    outcome_ref_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
