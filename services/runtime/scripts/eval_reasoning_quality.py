import json
import statistics
from typing import Dict, Any, List
from services.reasoning.models import ReasoningResult

class ReasoningEvaluator:
    """推理质量评估框架 (Reasoning Quality Eval Substrate) - 负责量化模型输出质量"""

    def evaluate_result(self, result: ReasoningResult, raw_output: str) -> Dict[str, Any]:
        """对单次推理结果进行 6 维评分 (启发式算法)"""
        
        scores = {
            "structure_score": self._score_structure(result),
            "counter_evidence_score": self._score_counter_evidence(result),
            "action_conservatism_score": self._score_action_conservatism(result),
            "confidence_alignment_score": self._score_confidence_alignment(result),
            "timeframe_consistency_score": self._score_timeframe_consistency(result),
            "policy_alignment_score": self._score_policy_alignment(result)
        }
        
        scores["total_score"] = round(statistics.mean(scores.values()), 2)
        scores["notes"] = self._generate_notes(scores, result)
        
        return scores

    def _score_structure(self, result: ReasoningResult) -> float:
        """结构完整性评分"""
        required_fields = [
            result.thesis.summary, 
            result.thesis.evidence_for,
            result.action_plan.action,
            result.next_steps
        ]
        score = 1.0 if all(required_fields) else 0.5
        return score

    def _score_counter_evidence(self, result: ReasoningResult) -> float:
        """反证平衡度评分 (关键金融指标)"""
        evidence_for = len(result.thesis.evidence_for)
        evidence_against = len(result.thesis.evidence_against)
        
        if evidence_against == 0:
            return 0.2  # 严重警告：无反证
        
        # 理想比例在 1:1 到 2:1 之间
        ratio = evidence_for / evidence_against
        if 0.5 <= ratio <= 2.0:
            return 1.0
        return 0.7

    def _score_action_conservatism(self, result: ReasoningResult) -> float:
        """建议克制度评分 (Action vs. Confidence)"""
        action = result.action_plan.action.lower()
        conf = result.thesis.confidence
        
        # 激进动作 (accumulate/exit) 在低置信度下应减分
        if action in ["accumulate", "exit", "reduce"] and conf < 0.6:
            return 0.4
        # 多空证据平衡时若选择 observe/hold 则加分
        if action in ["observe", "hold"] and len(result.thesis.evidence_for) == len(result.thesis.evidence_against):
            return 1.0
        return 0.8

    def _score_confidence_alignment(self, result: ReasoningResult) -> float:
        """置信度一致性评分"""
        # 证据越少，置信度越高 -> 扣分
        evidence_count = len(result.thesis.evidence_for) + len(result.thesis.evidence_against)
        if evidence_count <= 2 and result.thesis.confidence > 0.8:
            return 0.3
        return 0.9

    def _score_timeframe_consistency(self, result: ReasoningResult) -> float:
        """时间框架一致性评分"""
        # 如果 timeframe 为空但给出了具体的入场建议 -> 扣分
        if not result.thesis.timeframe and result.action_plan.action != "observe":
            return 0.5
        return 1.0

    def _score_policy_alignment(self, result: ReasoningResult) -> float:
        """政策一致度评分 (保守原则验证)"""
        # 如果风险标志中包含 HIGH_VOLATILITY 但仍给高仓位 -> 扣分
        risk_flags = [f.upper() for f in result.risk_flags]
        if ("HIGH_VOLATILITY" in risk_flags or "UNCERTAINTY" in risk_flags) and result.action_plan.position_size_pct > 15:
            return 0.2
        return 1.0

    def _generate_notes(self, scores: Dict[str, float], result: ReasoningResult) -> List[str]:
        notes = []
        if scores["counter_evidence_score"] <= 0.2:
            notes.append("CRITICAL: Missing counter-evidence in thesis.")
        if scores["action_conservatism_score"] <= 0.5:
            notes.append("WARN: Action appears too aggressive for current confidence level.")
        if scores["policy_alignment_score"] <= 0.5:
            notes.append("WARN: Result may violate system-wide risk policy.")
        return notes

if __name__ == "__main__":
    import asyncio
    from apps.api.app.core.config import settings
    from services.orchestrator.engine import PFIOSOrchestrator
    
    async def demo_eval():
        print("=== Reasoning Quality Evaluation Demo ===")
        orchestrator = PFIOSOrchestrator()
        evaluator = ReasoningEvaluator()
        
        # 模拟一次分析
        symbol = "BTC/USDT"
        query = "BTC 突破了 65000，我该追涨吗？"
        
        # 强制使用真实推理源 (如果配置允许) 或 Mock
        res = await orchestrator.execute_analyze_and_suggest(symbol, query)
        
        # 此处需要将 dict 转换回 ReasoningResult 对象进行评分 (或者直接评分 dict)
        # 组装用于评分的 mock 数据 (基于 orchestrator 输出)
        # 兼容处理：若 action 被风控拦截为 None，则从元数据或默认值恢复以进行质量评估
        action_payload = res.get("action") or {
            "action": "observe", 
            "position_size_pct": 0.0,
            "invalidation_condition": "Risk blocked"
        }
        
        from services.reasoning.models import MarketThesis, ExecutionAction
        
        # 组装用于评分的 mock 数据 (基于 orchestrator 输出)
        mock_res = ReasoningResult(
            thesis=MarketThesis(**res["thesis"]),
            action_plan=ExecutionAction(**action_payload),
            risk_flags=[r.get("name", "unknown") for r in res["risk_report"].get("triggered_rules", [])],
            next_steps=["Observe volume"]
        )
        
        report = evaluator.evaluate_result(mock_res, "")
        print(json.dumps(report, indent=2))

    asyncio.run(demo_eval())
