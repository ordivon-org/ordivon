from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class Lesson(BaseModel):
    lesson_type: str  # timing|risk|discipline|context|thesis
    lesson_text: str


class ReviewCreate(BaseModel):
    linked_report_id: str
    linked_recommendation_id: Optional[str] = None
    symbol: str
    expected_outcome: str
    actual_outcome: Optional[str] = None
    deviation: Optional[str] = None
    mistake_tags: Optional[str] = None
    lessons: List[Lesson]
    new_rule_candidate: Optional[str] = None


class ReviewResponse(BaseModel):
    review_id: str
    linked_report_id: str
    linked_recommendation_id: Optional[str]
    symbol: str
    expected_outcome: str
    actual_outcome: Optional[str]
    deviation: Optional[str]
    mistake_tags: Optional[str]
    lessons: List[Lesson]
    new_rule_candidate: Optional[str]
    created_at: datetime


class ReviewListResponse(BaseModel):
    reviews: List[ReviewResponse]
