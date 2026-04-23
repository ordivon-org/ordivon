from fastapi import APIRouter

from . import agent_actions, health, audits, reports, analyze, evals, recommendations, reviews, validation, dashboard, traces, knowledge

router = APIRouter()

router.include_router(health.router, tags=["Health"])
router.include_router(audits.router, prefix="/audits", tags=["Audits"])
router.include_router(reports.router, prefix="/reports", tags=["Reports"])
router.include_router(evals.router, prefix="/evals", tags=["Evals"])
router.include_router(analyze.router, tags=["Analyze"])
router.include_router(recommendations.router, prefix="/recommendations", tags=["Recommendations"])
router.include_router(reviews.router, prefix="/reviews", tags=["Reviews"])
router.include_router(validation.router, prefix="/validation", tags=["Validation"])
router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
router.include_router(agent_actions.router, prefix="/agent-actions", tags=["AgentActions"])
router.include_router(traces.router, prefix="/traces", tags=["Traces"])
router.include_router(knowledge.router, prefix="/knowledge", tags=["Knowledge"])
