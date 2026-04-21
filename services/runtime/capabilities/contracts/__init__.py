"""Capability contracts grouped by abstraction type."""

from capabilities.contracts.diagnostic import ValidationSummaryResult
from capabilities.contracts.domain import RecommendationResult, ReviewResult
from capabilities.contracts.view import AuditEventResult, DashboardResult, ReportResult
from capabilities.contracts.workflow import (
    AnalyzeResult,
    PendingReviewItemResult,
    PendingReviewListResult,
    ReviewDetailResult,
    ReviewSkeletonResult,
    UsageSyncResult,
)

__all__ = [
    "AnalyzeResult",
    "AuditEventResult",
    "DashboardResult",
    "PendingReviewItemResult",
    "PendingReviewListResult",
    "RecommendationResult",
    "ReportResult",
    "ReviewDetailResult",
    "ReviewResult",
    "ReviewSkeletonResult",
    "UsageSyncResult",
    "ValidationSummaryResult",
]
