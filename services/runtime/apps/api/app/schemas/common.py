from pydantic import BaseModel
from typing import Any

class BaseResponse(BaseModel):
    status: str = "success"
    message: str | None = None

class StatusResponse(BaseModel):
    status: str
    system: str = "PFIOS"
    version: str = "0.1.0"

class ErrorResponse(BaseModel):
    status: str = "error"
    detail: str
