from domains.ai_actions.repository import AgentActionRepository
from domains.strategy.repository import RecommendationRepository
from domains.journal.repository import ReviewRepository
from shared.config.settings import settings


class DashboardService:
    """Read-only aggregation service for dashboard metrics across domains."""

    def __init__(
        self,
        recommendation_repo: RecommendationRepository,
        review_repo: ReviewRepository,
        agent_action_repo: AgentActionRepository | None = None,
    ):
        self.recommendation_repo = recommendation_repo
        self.review_repo = review_repo
        self.agent_action_repo = agent_action_repo

    def get_aggregated_metrics(self) -> dict:
        reco_stats = self.recommendation_repo.get_status_counts()
        recent_outcomes_rows = self.recommendation_repo.get_recent_outcomes(limit=5)

        # Aggregation logic
        def extract_symbol(title: str | None) -> str:
            if title and " for " in title:
                return title.split(" for ", 1)[1]
            return "UNKNOWN"

        recent_outcomes = [
            {
                "state": row[0],
                "reason": row[1],
                "symbol": extract_symbol(row[2]),
                "timestamp": str(row[3]),
            }
            for row in recent_outcomes_rows
        ]

        # Get pending reviews using the dedicated review repo logic
        pending_review_count = len(self.review_repo.list_pending())
        latest_agent_action = None
        if self.agent_action_repo is not None:
            rows = self.agent_action_repo.list_recent(limit=1)
            if rows:
                latest_agent_action = {
                    "id": rows[0].id,
                    "task_type": rows[0].task_type,
                    "status": rows[0].status,
                    "provider": rows[0].provider,
                    "model": rows[0].model,
                    "created_at": rows[0].created_at.isoformat(),
                }

        return {
            "recommendation_stats": {status: count for status, count in reco_stats},
            "recent_outcomes": recent_outcomes,
            "pending_review_count": pending_review_count,
            "system_health": "nominal",
            "reasoning_provider": settings.reasoning_provider,
            "runtime_status": "configured" if settings.reasoning_provider else None,
            "hermes_status": "configured" if settings.reasoning_provider == "hermes" else None,
            "last_agent_action": latest_agent_action,
            "total_balance_estimate": None,
        }
