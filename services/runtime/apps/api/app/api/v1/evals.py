from fastapi import APIRouter, HTTPException

from apps.api.app.schemas.eval import EvalRunResponse
from capabilities.evals import EvalCapability

router = APIRouter()
eval_capability = EvalCapability()


@router.get("/latest", response_model=EvalRunResponse)
async def get_latest_eval():
    try:
        return EvalRunResponse(**eval_capability.get_latest())
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
