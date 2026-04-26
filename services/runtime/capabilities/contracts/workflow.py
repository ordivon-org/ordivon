from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class AnalyzeResult:
    """Composite workflow contract, not a stable domain object."""

    status: str
    decision: str
    summary: str
    risk_flags: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    analysis_id: str | None = None
    recommendation_id: str | None = None
    report_path: str | None = None
    audit_event_id: str | None = None
    workflow: str = "analyze_and_suggest"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ReviewSkeletonResult:
    id: str | None
    status: str
    created_at: str
    recommendation_id: str | None
    review_type: str
    sections: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class PendingReviewItemResult:
    id: str
    recommendation_id: str | None
    review_type: str
    status: str
    expected_outcome: str | None
    created_at: str
    workflow_run_id: str | None = None
    intelligence_run_id: str | None = None
    recommendation_generate_receipt_id: str | None = None
    latest_outcome_status: str | None = None
    latest_outcome_reason: str | None = None
    knowledge_hint_count: int = 0


@dataclass(slots=True)
class PendingReviewListResult:
    reviews: list[PendingReviewItemResult] = field(default_factory=list)


@dataclass(slots=True)
class ReviewDetailResult:
    id: str
    recommendation_id: str | None
    review_type: str
    status: str
    expected_outcome: str | None
    observed_outcome: str | None
    verdict: str | None
    variance_summary: str | None
    cause_tags: list[str] = field(default_factory=list)
    lessons: list[str] = field(default_factory=list)
    followup_actions: list[str] = field(default_factory=list)
    created_at: str = ""
    completed_at: str | None = None
    submit_execution_request_id: str | None = None
    submit_execution_receipt_id: str | None = None
    complete_execution_request_id: str | None = None
    complete_execution_receipt_id: str | None = None
    latest_outcome_status: str | None = None
    latest_outcome_reason: str | None = None
    knowledge_feedback_packet_id: str | None = None
    governance_hint_count: int = 0
    intelligence_hint_count: int = 0
    outcome_ref_type: str | None = None
    outcome_ref_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class UsageSyncResult:
    snapshot_id: str
    created_at: str
