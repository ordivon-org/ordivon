from typing import Any

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from apps.api.app.deps import get_db
from capabilities.dashboard import DashboardCapability
from domains.ai_actions.repository import AgentActionRepository
from domains.dashboard.service import DashboardService
from domains.strategy.repository import RecommendationRepository
from domains.journal.repository import ReviewRepository
from dataclasses import asdict

router = APIRouter()
dashboard_capability = DashboardCapability()


@router.get("/summary")
async def get_dashboard_summary(db: Session = Depends(get_db)) -> dict[str, Any]:
    try:
        dashboard_service = DashboardService(
            recommendation_repo=RecommendationRepository(db),
            review_repo=ReviewRepository(db),
            agent_action_repo=AgentActionRepository(db),
        )

        result_contract = dashboard_capability.get_summary(dashboard_service)
        return asdict(result_contract)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
