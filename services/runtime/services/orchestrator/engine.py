from __future__ import annotations
import json
from datetime import datetime
from typing import Any

from apps.api.app.core.config import settings
from apps.api.app.utils.crypto import make_id
from apps.api.app.services.object_service import ObjectService
from services.orchestrator.context_builder import ContextBuilder
from services.reasoning import ReasoningService, ReasoningParser, ReasoningResult
from services.reasoning.llm_client import HermesCLIClient, MockLLMClient
from services.risk_engine.rules import RiskEngine
from services.risk_engine.audit import RiskAuditor
from services.risk_engine.models import AuditEvent, RiskDecision
from apps.api.app.services.recommendation_service import RecommendationService

class PFIOSOrchestrator:
    """编排引擎核心 (Orchestration Layer) - 负责控制工作流生命周期"""

    def __init__(self):
        self.context_builder = ContextBuilder()
        
        # 初始化推理服务 (按约束实现)
        templates_dir = settings.get_abs_path("services/reasoning/prompt_templates")
        
        # 根据配置选择 LLM 客户端
        if settings.reasoning_provider == "hermes_cli":
            llm_client = HermesCLIClient(
                python_executable=settings.get_hermes_python_executable(),
                runtime_path=str(settings.hermes_runtime_abs_path),
                timeout_seconds=settings.hermes_timeout_seconds
            )
        else:
            # 默认或明确指定为 mock 时，注入 MockLLMClient 以支持回归测试
            llm_client = MockLLMClient() 

        self.reasoning_service = ReasoningService(
            llm_client=llm_client,
            parser=ReasoningParser(),
            templates_dir=str(templates_dir)
        )
        self.risk_engine = RiskEngine()
        self.risk_auditor = RiskAuditor()

    def _get_mock_reasoning(self, context: dict) -> ReasoningResult:
        """Mock 推理逻辑 (满足约束 6, 且对齐 8.1 嵌套模型)"""
        from services.reasoning import MarketThesis, ExecutionAction
        return ReasoningResult(
            thesis=MarketThesis(
                summary=f"Strategic Analysis: Market appears consolidating for {context.get('symbol')}.",
                evidence_for=["RSI divergence", "Technical support holding"],
                evidence_against=["Macro headwinds"],
                confidence=0.75
            ),
            action_plan=ExecutionAction(
                action="accumulate",
                position_size_pct=5.0,
                invalidation_condition="Close below 50MA"
            ),
            risk_flags=[],
            next_steps=["Observe volume on next breakout"]
        )

    async def execute_analyze_and_suggest(self, symbol: str, user_query: str) -> dict[str, Any]:
        """执行‘分析与建议’主工作流"""
        event_id = make_id("evt")
        
        # 1. Load Hierarchical Context (Step 8.3 升级)
        ctx = self.context_builder.build_layered_context(symbol, user_query)
        
        # 2. 推理阶段 (Step 8 改良: 接入真实推理引擎)
        if settings.reasoning_provider == "hermes_cli" and self.reasoning_service.llm_client:
            reasoning_result = self.reasoning_service.analyze(ctx)
        else:
            # 执行 Mock 推理逻辑 (满足约束 6，作为开发/离线模式回退)
            reasoning_result = self._get_mock_reasoning(ctx)
        
        thesis_obj = reasoning_result.thesis
        action_obj = reasoning_result.action_plan
        
        # 将结构化结果展平或适配给后续的 RiskEngine (目前风险引擎仍期望旧格式，需做简单适配)
        thesis_data = {
            "summary": thesis_obj.summary,
            "evidence_for": thesis_obj.evidence_for,
            "evidence_against": thesis_obj.evidence_against,
            "confidence": thesis_obj.confidence,
            "symbol": symbol,
            "risk_flags": reasoning_result.risk_flags
        }
        
        action_data = {
            "action": action_obj.action.upper(), # 适配旧版 BUY/SELL 枚举
            "symbol": symbol,
            "suggested_size": action_obj.position_size_pct,
            "invalidation": action_obj.invalidation_condition
        }
        
        # 3. Decision / Action Planning (Skill 挂点)
        action_data = {
            "action": "BUY",
            "symbol": symbol,
            "leverage": 3,
            "sl": 0.95,
            "reason": "Technical breakout confirmed"
        }
        
        # 4. Governance: Policy Check (Governance 挂点)
        risk_report = self.risk_engine.validate_thesis_and_action(thesis_data, action_data)
        
        # 5. Audit: Decision Tracing (Audit 挂点)
        audit_event = AuditEvent(
            event_id=event_id,
            workflow_name="analyze_and_suggest",
            stage="post_reasoning",
            decision=risk_report.decision,
            subject_id=symbol,
            status="blocked" if risk_report.decision == RiskDecision.BLOCK else "persisted",
            context_summary=f"Analysis of {symbol} for query: {user_query}",
            details={
                "risk_report": risk_report.model_dump(),
                "thesis_summary": thesis_data["summary"]
            }
        )
        self.risk_auditor.record_event(audit_event)
        
        # 6. Persistence & Output
        if risk_report.decision != RiskDecision.BLOCK:
            ObjectService.add_observation(symbol, f"PFIOS Decision [{risk_report.decision}]: {thesis_data['summary']}", 0.0, "risk_engine")
        
        return {
            "event_id": event_id,
            "workflow": "analyze_and_suggest",
            "status": "success" if risk_report.is_safe else "blocked",
            "decision": risk_report.decision,
            "thesis": thesis_data,
            "action": action_data if risk_report.is_safe else None,
            "risk_report": risk_report.model_dump(),
            "timestamp": datetime.now().isoformat()
        }

        # 7. Step 10: 业务工作流闭合 - 自动生成建议 (带白名单过滤)
        # 适配返回结构以符合 Service 预期
        if result["status"] == "success":
            # 构造符合 Service 处理的结构
            analysis_data = {
                "decision": result["decision"],
                "thesis": thesis_data,
                "action_plan": {"action": action_obj.action}, # 使用原始 action 评估
                "metadata": {"symbol": symbol}
            }
            RecommendationService.auto_generate_if_needed(analysis_data, report_id=event_id, audit_id=event_id)

        return result
