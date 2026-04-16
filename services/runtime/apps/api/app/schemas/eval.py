from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class EvalSummary(BaseModel):
    total_cases: int
    passed_cases: int
    failed_cases: int
    avg_total_score: float
    parse_failure_rate: float
    aggressive_action_rate: float

class EvalCaseResult(BaseModel):
    case_id: str
    status: str
    risk_decision: str
    scores: Dict[str, float]
    notes: List[str]

class EvalRunResponse(BaseModel):
    run_id: str
    timestamp: str
    provider: str
    dataset: str
    summary: EvalSummary
    cases: List[EvalCaseResult]
    gate_decision: str = "PASS" # 默认为 PASS，由逻辑判断
