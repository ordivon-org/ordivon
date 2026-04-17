from pydantic import BaseModel
from typing import List, Optional

from pfios.domain.common.enums import ReviewVerdict


class ReviewCreateRequest(BaseModel):
    recommendation_id: str
    review_type: str = "recommendation_postmortem"
    expected_outcome: Optional[str] = None


class ReviewCompleteRequest(BaseModel):
    observed_outcome: str
    verdict: ReviewVerdict
    variance_summary: Optional[str] = None
    cause_tags: List[str] = []
    lessons: List[str] = []
    followup_actions: List[str] = []
