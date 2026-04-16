from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class RecommendationCreate(BaseModel):
    source_report_id: str
    source_audit_id: Optional[str] = None
    symbol: str
    action: str
    confidence: float
    decision: str

class RecommendationUpdate(BaseModel):
    lifecycle_status: Optional[str] = None # generated|adopted|ignored|tracking|closed
    review_status: Optional[str] = None # pending|reviewed
    adopted: Optional[bool] = None
    outcome_status: Optional[str] = None # pending|tracking|closed
    user_note: Optional[str] = None

class RecommendationResponse(BaseModel):
    recommendation_id: str
    source_report_id: str
    source_audit_id: Optional[str]
    symbol: str
    action: str
    confidence: float
    decision: str
    lifecycle_status: str
    review_status: str  # pending|reviewed
    adopted: Optional[bool]
    adopted_at: Optional[datetime]
    outcome_status: str
    user_note: Optional[str]
    created_at: datetime

class RecommendationListResponse(BaseModel):
    recommendations: List[RecommendationResponse]
