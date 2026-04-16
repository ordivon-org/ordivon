from fastapi import APIRouter
from . import health, audits, reports, analyze, evals, recommendations, reviews, validation

router = APIRouter()

router.include_router(health.router, tags=["Health"])
router.include_router(audits.router, prefix="/audits", tags=["Audits"])
router.include_router(reports.router, prefix="/reports", tags=["Reports"])
router.include_router(evals.router, prefix="/evals", tags=["Evals"])
router.include_router(analyze.router, tags=["Analyze"])
router.include_router(recommendations.router, prefix="/recommendations", tags=["Recommendations"])
router.include_router(reviews.router, prefix="/reviews", tags=["Reviews"])
router.include_router(validation.router, prefix="/validation", tags=["Validation"])
