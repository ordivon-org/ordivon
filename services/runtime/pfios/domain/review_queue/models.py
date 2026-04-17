"""
pfios.domain.review_queue.models — 复盘队列模型
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class ReviewQueueStatus(str, Enum):
    """队列项状态"""
    PENDING = "pending"
    GENERATED = "generated"
    DISMISSED = "dismissed"
    COMPLETED = "completed"


class ReviewQueueItem(BaseModel):
    """复盘队列项"""
    item_id: str
    recommendation_id: str
    analysis_id: Optional[str] = None
    outcome_snapshot_id: str
    reason: str
    priority: str = "medium"
    status: ReviewQueueStatus = ReviewQueueStatus.PENDING
    scheduled_at: datetime
    created_at: Optional[datetime] = None
