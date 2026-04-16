import json
from pathlib import Path
from fastapi import APIRouter, HTTPException
from app.schemas.eval import EvalRunResponse
from apps.api.app.core.config import settings

router = APIRouter()

@router.get("/latest", response_model=EvalRunResponse)
async def get_latest_eval():
    """获取最新的回归评测结果 (Step 9.1 Support)"""
    try:
        runs_dir = Path(settings.get_abs_path("data/evals/runs"))
        if not runs_dir.exists():
            raise HTTPException(status_code=404, detail="Evals directory not found")
        
        # 获取最新的 run 文件
        run_files = list(runs_dir.glob("*.json"))
        if not run_files:
            raise HTTPException(status_code=404, detail="No evaluation runs found")
        
        latest_run_file = max(run_files, key=lambda p: p.stat().st_mtime)
        
        with open(latest_run_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # 简单判定 Gate Decision (TODO: 以后对焦 compare_eval_runs.py 的逻辑)
        gate_decision = "PASS"
        summary = data.get("summary", {})
        if summary.get("parse_failure_rate", 0) > 0.05 or summary.get("avg_total_score", 0) < 0.8:
            gate_decision = "FAIL"
            
        return EvalRunResponse(
            run_id=data["run_id"],
            timestamp=data["timestamp"],
            provider=data["provider"],
            dataset=data["dataset"],
            summary=summary,
            cases=data["cases"],
            gate_decision=gate_decision
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
