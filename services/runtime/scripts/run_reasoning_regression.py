import asyncio
import json
import logging
import os
import time
import statistics
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from apps.api.app.core.config import settings
from services.orchestrator.engine import PFIOSOrchestrator
from services.reasoning.models import ReasoningResult, MarketThesis, ExecutionAction
from scripts.eval_reasoning_quality import ReasoningEvaluator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RegressionRunner:
    """回归执行器 (Regression Runner Substrate) - 负责自动化跑完评测集全链路 (Step 8.4.2)"""

    def __init__(self):
        self.orchestrator = PFIOSOrchestrator()
        self.evaluator = ReasoningEvaluator()
        self.runs_dir = Path(settings.get_abs_path("data/evals/runs"))
        self.datasets_dir = Path(settings.get_abs_path("data/evals/datasets"))

    async def run_dataset(self, category: str = "core") -> str:
        dataset_path = self.datasets_dir / category
        if not dataset_path.exists():
            raise FileNotFoundError(f"Dataset path {dataset_path} not found")

        case_files = list(dataset_path.glob("*.json"))
        logger.info(f"Found {len(case_files)} cases in {category}")

        run_id = f"{datetime.now().strftime('%Y-%m-%d_run_%H%M%S')}"
        results = []

        for case_file in case_files:
            with open(case_file, "r", encoding="utf-8") as f:
                case = json.load(f)
            
            logger.info(f"Running Case: {case['case_id']} - {case['description']}")
            
            try:
                # 注入 Case 中的输入作为 Context
                # 注意: 这里我们通过直接注入 Context 绕过了 ContextBuilder 的数据库查询，
                # 以实现“确定性输入”的回归测试。
                input_ctx = case["input"]
                
                # 执行推理全链路
                # NOTE: 我们需要一个能直接接受已构建 Context 的 orchestrator 方法
                # 为了不修改 engine.py 太多，我们直接调用推理服务
                reasoning_res = self.orchestrator.reasoning_service.analyze(input_ctx)
                
                # 2. 进行治理层模拟 (RiskEngine)
                # 适配：风险引擎目前期望扁平化的 dict 格式
                thesis_data = {
                    "summary": reasoning_res.thesis.summary,
                    "evidence_for": reasoning_res.thesis.evidence_for,
                    "evidence_against": reasoning_res.thesis.evidence_against,
                    "confidence": reasoning_res.thesis.confidence,
                    "symbol": input_ctx["query_context"]["symbols"][0],
                    "risk_flags": reasoning_res.risk_flags
                }
                action_data = {
                    "action": reasoning_res.action_plan.action.upper(),
                    "symbol": input_ctx["query_context"]["symbols"][0],
                    "suggested_size": reasoning_res.action_plan.position_size_pct,
                    "invalidation": reasoning_res.action_plan.invalidation_condition
                }
                
                risk_report = self.orchestrator.risk_engine.validate_thesis_and_action(thesis_data, action_data)
                
                # 进行评分
                scores = self.evaluator.evaluate_result(reasoning_res, "")
                
                results.append({
                    "case_id": case["case_id"],
                    "status": "ok",
                    "reasoning_result": reasoning_res.model_dump(),
                    "risk_decision": "block" if not risk_report.is_safe else "allow",
                    "scores": scores,
                    "notes": scores.get("notes", [])
                })
            except Exception as e:
                logger.error(f"Case {case['case_id']} failed: {str(e)}")
                results.append({
                    "case_id": case["case_id"],
                    "status": "failed",
                    "error": str(e)
                })

        # 生成摘要
        summary = self._generate_summary(results)
        
        run_data = {
            "run_id": run_id,
            "timestamp": datetime.now().isoformat(),
            "provider": settings.reasoning_provider,
            "dataset": category,
            "cases": results,
            "summary": summary
        }

        # 保存结果
        run_file = self.runs_dir / f"{run_id}.json"
        with open(run_file, "w", encoding="utf-8") as f:
            json.dump(run_data, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Run completed. Results saved to {run_file}")
        return run_id

    def _generate_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        valid_results = [r for r in results if r["status"] == "ok"]
        total = len(results)
        passed = len(valid_results)
        
        avg_score = statistics.mean([r["scores"]["total_score"] for r in valid_results]) if valid_results else 0
        
        # 计算过激动作比例 (非 observe/hold)
        aggressive_actions = [
            r for r in valid_results 
            if r["reasoning_result"]["action_plan"]["action"] not in ["observe", "hold", "avoid"]
        ]

        return {
            "total_cases": total,
            "passed_cases": passed,
            "failed_cases": total - passed,
            "avg_total_score": round(avg_score, 2),
            "parse_failure_rate": round((total - passed) / total if total > 0 else 0, 2),
            "aggressive_action_rate": round(len(aggressive_actions) / passed if passed > 0 else 0, 2)
        }

if __name__ == "__main__":
    runner = RegressionRunner()
    asyncio.run(runner.run_dataset("core"))
