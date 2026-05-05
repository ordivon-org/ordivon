from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from capabilities.contracts import AnalyzeResult
from domains.research.models import AnalysisRequest
from governance_engine.decision import build_governance_decision
from orchestrator.runtime.engine import PFIOSOrchestrator
from packs.finance.analyze_profile import build_finance_analyze_profile
from shared.observability import increment_counter, span
from sqlalchemy.orm import Session


@dataclass(slots=True)
class AnalyzeCapabilityInput:
    query: str
    symbols: list[str]
    timeframe: str | None = None


class AnalyzeCapability:
    """Workflow capability for analyze-and-suggest orchestration."""

    abstraction_type = "workflow"

    def __init__(self, orchestrator: PFIOSOrchestrator | None = None) -> None:
        self.orchestrator = orchestrator or PFIOSOrchestrator()

    async def analyze_and_suggest(self, request: AnalyzeCapabilityInput, db: Session | None = None) -> dict[str, Any]:
        profile = build_finance_analyze_profile(
            symbol=request.symbols[0] if request.symbols else None,
            timeframe=request.timeframe,
        )
        symbol = profile.symbol
        with span(
            "workflow.analyze_and_suggest",
            attributes={
                "workflow.symbol": symbol,
                "workflow.timeframe": profile.timeframe,
            },
        ):
            report = self.orchestrator.execute_analyze(
                AnalysisRequest(
                    query=request.query,
                    symbol=symbol,
                    timeframe=profile.timeframe,
                ),
                db=db,
            )

        governance = build_governance_decision(
            decision=report.get("governance", {}).get("decision", "reject"),
            reasons=report.get("governance", {}).get("reasons", []),
            source=report.get("governance", {}).get("source", "workflow.missing_decision"),
            advisory_hints=tuple(),
            policy_set_id=report.get("governance", {}).get("policy_set_id", "governance.unknown"),
            active_policy_ids=report.get("governance", {}).get("active_policy_ids", []),
            default_decision_rule_ids=report.get("governance", {}).get("default_decision_rule_ids", []),
        )
        governance_payload = report.get("governance", {})
        report_metadata = report.get("metadata", {}) if isinstance(report.get("metadata", {}), dict) else {}

        result = AnalyzeResult(
            status="success",
            decision=governance.decision,
            summary=report.get("summary", "No summary available"),
            risk_flags=governance.reasons or report.get("risks", []),
            recommendations=report.get("suggested_actions", ["Wait and see"]),
            analysis_id=report.get("analysis_id"),
            recommendation_id=report.get("recommendation_id"),
            metadata={
                "symbol": symbol,
                "timeframe": profile.timeframe,
                "contract_type": "workflow",
                "governance_decision": governance.decision,
                "governance_source": governance.source,
                "governance": governance_payload,
                "governance_advisory_hints": list(governance_payload.get("advisory_hints", [])),
                "governance_advisory_hint_status": report_metadata.get(
                    "governance_advisory_hint_status", "not_linked_yet"
                ),
                "governance_policy_set_id": governance_payload.get("policy_set_id", "governance.unknown"),
                "governance_active_policy_ids": list(governance_payload.get("active_policy_ids", [])),
                "governance_default_decision_rule_ids": list(governance_payload.get("default_decision_rule_ids", [])),
                "intelligence_feedback_hint_status": report_metadata.get(
                    "intelligence_feedback_hint_status", "not_linked_yet"
                ),
                "intelligence_memory_lesson_count": report_metadata.get("intelligence_memory_lesson_count", 0),
                "intelligence_related_review_count": report_metadata.get("intelligence_related_review_count", 0),
                "agent_action_id": report.get("agent_action_id"),
                "intelligence_run_id": report.get("intelligence_run_id"),
                "workflow_run_id": report.get("workflow_run_id"),
                "recommendation_id": report.get("recommendation_id"),
                "execution_request_id": report.get("execution_request_id"),
                "execution_receipt_id": report.get("execution_receipt_id"),
                "recommendation_generate_request_id": report.get("recommendation_generate_request_id"),
                "recommendation_generate_receipt_id": report.get("recommendation_generate_receipt_id"),
            },
        )

        increment_counter(
            "analyze_workflow_runs_total",
            attributes={
                "decision": governance.decision,
                "symbol": symbol,
            },
        )

        return asdict(result)
