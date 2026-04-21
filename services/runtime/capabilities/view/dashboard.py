from __future__ import annotations

from capabilities.contracts import DashboardResult
from domains.dashboard.service import DashboardService


class DashboardCapability:
    """View aggregate for homepage dashboard data."""

    abstraction_type = "view"

    def get_summary(self, dashboard_service: DashboardService) -> DashboardResult:
        metrics = dashboard_service.get_aggregated_metrics()
        return DashboardResult(**metrics)
