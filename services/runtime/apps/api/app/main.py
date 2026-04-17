from fastapi import FastAPI

from apps.api.app.routers.health import router as health_router
from apps.api.app.routers.recommendations import router as recommendations_router
from apps.api.app.routers.reviews import router as reviews_router

app = FastAPI(
    title="PFIOS API",
    version="0.1.0",
)

app.include_router(health_router)
app.include_router(recommendations_router)
app.include_router(reviews_router)
