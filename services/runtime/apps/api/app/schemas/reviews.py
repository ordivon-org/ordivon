from pydantic import BaseModel
from typing import List, Optional

from apps.api.app.schemas.common import ActionContextInput
from shared.enums.domain import ReviewVerdict


class ReviewLessonInput(BaseModel):
    lesson_text: str


class ReviewCreateRequest(BaseModel):
    recommendation_id: Optional[str] = None
    linked_recommendation_id: Optional[str] = None
    review_type: str = "recommendation_postmortem"
    expected_outcome: Optional[str] = None
    actual_outcome: Optional[str] = None
    deviation: Optional[str] = None
    mistake_tags: Optional[str] = None
    lessons: List[ReviewLessonInput] = []
    new_rule_candidate: Optional[str] = None
    outcome_ref_type: Optional[str] = None
    outcome_ref_id: Optional[str] = None
    action_context: Optional[ActionContextInput] = None


class ReviewCompleteRequest(BaseModel):
    observed_outcome: str
    verdict: ReviewVerdict
    variance_summary: Optional[str] = None
    cause_tags: List[str] = []
    lessons: List[str] = []
    followup_actions: List[str] = []
    approval_id: Optional[str] = None
    require_approval: bool = False
    action_context: Optional[ActionContextInput] = None


class PendingReviewResponse(BaseModel):
    id: str
    recommendation_id: Optional[str] = None
    review_type: str
    status: str
    expected_outcome: Optional[str] = None
    created_at: str
    workflow_run_id: Optional[str] = None
    intelligence_run_id: Optional[str] = None
    recommendation_generate_receipt_id: Optional[str] = None
    latest_outcome_status: Optional[str] = None
    latest_outcome_reason: Optional[str] = None
    knowledge_hint_count: int = 0


class PendingReviewListResponse(BaseModel):
    reviews: List[PendingReviewResponse]


class ReviewDetailResponse(BaseModel):
    id: str
    recommendation_id: Optional[str] = None
    review_type: str
    status: str
    expected_outcome: Optional[str] = None
    observed_outcome: Optional[str] = None
    verdict: Optional[str] = None
    variance_summary: Optional[str] = None
    cause_tags: List[str] = []
    lessons: List[str] = []
    followup_actions: List[str] = []
    created_at: str
    completed_at: Optional[str] = None
    submit_execution_request_id: Optional[str] = None
    submit_execution_receipt_id: Optional[str] = None
    complete_execution_request_id: Optional[str] = None
    complete_execution_receipt_id: Optional[str] = None
    latest_outcome_status: Optional[str] = None
    latest_outcome_reason: Optional[str] = None
    knowledge_feedback_packet_id: Optional[str] = None
    governance_hint_count: int = 0
    intelligence_hint_count: int = 0
    outcome_ref_type: Optional[str] = None
    outcome_ref_id: Optional[str] = None
    metadata: dict = {}
