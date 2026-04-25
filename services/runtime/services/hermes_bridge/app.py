"""PFIOS Hermes Bridge — FastAPI application.

Exposes the contract that Ordivon's HermesClient expects:
  GET  /pfios/v1/health
  POST /pfios/v1/tasks
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException, Request

from services.hermes_bridge.config import BRIDGE_API_TOKEN, BRIDGE_NAME, BRIDGE_VERSION, MODEL_NAME, MODEL_PROVIDER
from services.hermes_bridge.hermes_runner import run_analysis
from services.hermes_bridge.schemas import HealthResponse, TaskRequest, TaskResponse

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title=BRIDGE_NAME, version=BRIDGE_VERSION)


def _check_auth(request: Request) -> None:
    if not BRIDGE_API_TOKEN:
        return  # auth disabled
    auth = request.headers.get("Authorization", "")
    expected = f"Bearer {BRIDGE_API_TOKEN}"
    if auth != expected:
        raise HTTPException(status_code=401, detail="unauthorized")


@app.get("/pfios/v1/health", response_model=HealthResponse)
async def health(request: Request) -> HealthResponse:
    _check_auth(request)
    return HealthResponse(provider=MODEL_PROVIDER, model=MODEL_NAME)


@app.post("/pfios/v1/tasks", response_model=TaskResponse)
async def tasks(payload: TaskRequest, request: Request) -> TaskResponse:
    _check_auth(request)

    if payload.task_type != "analysis.generate":
        raise HTTPException(status_code=400, detail=f"unsupported task_type: {payload.task_type}")

    logger.info("Running task %s for symbol %s", payload.task_id, payload.input.symbol)
    result = run_analysis(payload)
    logger.info(
        "Task %s status=%s provider=%s model=%s",
        payload.task_id,
        result.status,
        result.provider,
        result.model,
    )
    return result
