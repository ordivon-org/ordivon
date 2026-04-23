from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.api.app.api.v1.router import router as api_v1_router
from state.db.bootstrap import init_db
from shared.observability import increment_counter, init_observability, span


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_observability()
    init_db()
    yield


app = FastAPI(
    title="PFIOS API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1):30\d{2}$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(api_v1_router, prefix="/api/v1")


@app.middleware("http")
async def observability_middleware(request, call_next):
    route = request.url.path
    with span("http.request", attributes={"http.route": route, "http.method": request.method}):
        response = await call_next(request)
        increment_counter(
            "http_requests_total",
            attributes={
                "http.route": route,
                "http.method": request.method,
                "http.status_code": response.status_code,
            },
        )
        return response
