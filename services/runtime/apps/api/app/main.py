from contextlib import asynccontextmanager

from fastapi import FastAPI

from apps.api.app.api.v1.router import router as api_v1_router
from state.db.bootstrap import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="PFIOS API",
    version="0.1.0",
    lifespan=lifespan,
)


app.include_router(api_v1_router, prefix="/api/v1")
