from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ValidationSummaryResult:
    """Diagnostic summary contract, not a domain object."""

    period_id: str | None
    days_active: int
    total_analyses: int
    total_recommendations: int
    open_critical_issues: int
    system_go_no_go: str | None
    metrics: dict[str, Any] | None = field(default=None)
    metadata: dict[str, Any] = field(default_factory=dict)
