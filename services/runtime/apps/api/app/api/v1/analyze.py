from fastapi import APIRouter, HTTPException
from app.schemas.requests import AnalyzeRequest
from app.schemas.responses import AnalyzeResponse
from services.orchestrator.engine import PFIOSOrchestrator
from services.risk_engine.models import RiskDecision

router = APIRouter()
orchestrator = PFIOSOrchestrator()

@router.post("/analyze-and-suggest", response_model=AnalyzeResponse)
async def analyze_and_suggest(payload: AnalyzeRequest):
    """
    执行核心‘分析与建议’工作流 (Intelligence -> Governance -> Audit -> Persistence)
    """
    try:
        # 1. 执行编排引擎 (内置风控校验与审计)
        # 注意：此处 symbols 为列表，当前引擎仅支持单 symbol，取第一个或遍历
        symbol = payload.symbols[0] if payload.symbols else "BTC/USDT"
        
        result = await orchestrator.execute_analyze_and_suggest(
            symbol=symbol,
            user_query=payload.query
        )
        
        # 2. 映射 18 级字段响应体
        # 哪怕是 BLOCK，我们也返回 200 并带上解析结果
        thesis = result.get("thesis", {})
        risk_report = result.get("risk_report", {})
        
        return AnalyzeResponse(
            status=result["status"],
            decision=result["decision"],
            summary=thesis.get("summary", "No summary available"),
            risk_flags=[r["name"] for r in risk_report.get("triggered_rules", []) if r["decision"] != "allow"],
            recommendations=[thesis.get("recommendations", "Wait and see")],
            report_path=result.get("report_path"),
            audit_event_id=result.get("event_id"),
            workflow=result["workflow"],
            metadata={
                "confidence": thesis.get("confidence"),
                "symbol": symbol
            }
        )
    except Exception as e:
        # 系统级异常才抛出 500
        raise HTTPException(status_code=500, detail=str(e))
