from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from apps.api.app.schemas.common import ActionContextInput


class RecommendationCreate(BaseModel):
    source_report_id: str
    source_audit_id: Optional[str] = None
    symbol: str
    action: str
    confidence: float
    decision: str


class RecommendationUpdate(BaseModel):
    lifecycle_status: Optional[str] = None  # generated|adopted|ignored|tracking|closed
    review_status: Optional[str] = None  # pending|reviewed
    adopted: Optional[bool] = None
    outcome_status: Optional[str] = None  # pending|tracking|closed
    user_note: Optional[str] = None
    action_context: Optional[ActionContextInput] = None


class RecommendationResponse(BaseModel):
    id: str
    status: str
    created_at: str
    analysis_id: Optional[str] = None
    symbol: Optional[str] = None
    action_summary: Optional[str] = None
    confidence: Optional[float] = None
    decision: Optional[str] = None
    decision_reason: Optional[str] = None
    adopted: bool
    review_status: Optional[str] = None
    outcome_status: Optional[str] = None
    metadata: Dict[str, Any]


class RecommendationListResponse(BaseModel):
    recommendations: List[RecommendationResponse]
