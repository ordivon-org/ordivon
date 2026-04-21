from __future__ import annotations

from domains.research.models import AnalysisResult
from intelligence.runtime.hermes_client import HermesClient, HermesRuntimeError
from intelligence.tasks import build_analysis_task, normalize_analysis_output
from intelligence.tasks.contracts import IntelligenceTaskRequest
from orchestrator.context.context_builder import AnalysisContext


class HermesAgentProvider:
    def __init__(self, client: HermesClient | None = None) -> None:
        self.client = client or HermesClient()

    def analyze(self, ctx: AnalysisContext, request: IntelligenceTaskRequest | None = None) -> AnalysisResult:
        request = request or build_analysis_task(ctx)
        try:
            response = self.client.run_task("analysis.generate", request.to_payload())
        except HermesRuntimeError as exc:
            exc.task_id = request.task_id
            exc.trace_id = request.trace_id
            exc.request_payload = request.to_payload()
            raise
        normalized = normalize_analysis_output(request, response)
        return AnalysisResult(
            summary=normalized.summary,
            thesis=normalized.thesis,
            risks=normalized.risks,
            suggested_actions=normalized.suggested_actions,
            metadata=normalized.metadata.__dict__ | {"agent_action": normalized.agent_action.__dict__},
        )
