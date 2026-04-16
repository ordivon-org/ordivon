from fastapi import APIRouter
from app.schemas.common import StatusResponse

router = APIRouter()

@router.get("/health", response_model=StatusResponse)
async def health_check():
    return StatusResponse(status="ok")

@router.get("/version", response_model=StatusResponse)
async def get_version():
    return StatusResponse(status="ok", version="0.1.0")
