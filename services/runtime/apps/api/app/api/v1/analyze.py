from fastapi import APIRouter, HTTPException

from apps.api.app.schemas.requests import AnalyzeRequest
from apps.api.app.schemas.responses import AnalyzeResponse
from capabilities.analyze import AnalyzeCapability, AnalyzeCapabilityInput
from intelligence.runtime.hermes_client import HermesRuntimeError
from sqlalchemy.orm import Session
from fastapi import Depends
from apps.api.app.deps import get_db

router = APIRouter()
analyze_capability = AnalyzeCapability()


@router.post("/analyze-and-suggest", response_model=AnalyzeResponse)
async def analyze_and_suggest(payload: AnalyzeRequest, db: Session = Depends(get_db)):
    try:
        result = await analyze_capability.analyze_and_suggest(
            AnalyzeCapabilityInput(
                query=payload.query,
                symbols=payload.symbols,
                timeframe=payload.timeframe,
            ),
            db=db
        )
        return AnalyzeResponse(**result)
    except HermesRuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
