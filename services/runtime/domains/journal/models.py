from dataclasses import dataclass, field

from shared.utils.ids import new_id
from shared.enums.domain import ReviewStatus, ReviewVerdict
from shared.time.clock import utc_now


@dataclass
class Review:
    id: str = field(default_factory=lambda: new_id("review"))
    recommendation_id: str | None = None
    analysis_id: str | None = None
    submit_execution_request_id: str | None = None
    submit_execution_receipt_id: str | None = None
    complete_execution_request_id: str | None = None
    complete_execution_receipt_id: str | None = None
    knowledge_feedback_packet_id: str | None = None
    outcome_ref_type: str | None = None
    outcome_ref_id: str | None = None
    review_type: str = "recommendation_postmortem"
    status: ReviewStatus = ReviewStatus.PENDING
    expected_outcome: str = ""
    observed_outcome: str | None = None
    verdict: ReviewVerdict | None = None
    variance_summary: str | None = None
    cause_tags: list[str] = field(default_factory=list)
    lessons: list[str] = field(default_factory=list)
    followup_actions: list[str] = field(default_factory=list)
    wiki_path: str | None = None
    scheduled_at: str = field(default_factory=lambda: utc_now().isoformat())
    started_at: str | None = None
    completed_at: str | None = None
    created_at: str = field(default_factory=lambda: utc_now().isoformat())
