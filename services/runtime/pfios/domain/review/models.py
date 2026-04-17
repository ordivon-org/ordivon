from dataclasses import dataclass, field

from pfios.core.utils.ids import new_id
from pfios.core.utils.time import utc_now
from pfios.domain.common.enums import ReviewStatus, ReviewVerdict


@dataclass
class Review:
    id: str = field(default_factory=lambda: new_id("review"))
    recommendation_id: str | None = None
    analysis_id: str | None = None
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
