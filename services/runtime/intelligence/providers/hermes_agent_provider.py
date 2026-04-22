from __future__ import annotations

from adapters.runtimes.hermes import HermesRuntime
from domains.research.models import AnalysisResult
from intelligence.runtime.base import AgentRuntime, RuntimeDescriptor
from intelligence.tasks.contracts import IntelligenceTaskRequest
from orchestrator.context.context_builder import AnalysisContext


class HermesAgentProvider(AgentRuntime):
    """Legacy compatibility shim over the adapter-owned Hermes runtime."""

    def __init__(self, runtime: HermesRuntime | None = None) -> None:
        self.runtime = runtime or HermesRuntime()

    @property
    def descriptor(self) -> RuntimeDescriptor:
        base = self.runtime.descriptor
        return RuntimeDescriptor(
            runtime_name=base.runtime_name,
            provider_name=base.provider_name,
            model_name=base.model_name,
            adapter_name="intelligence.providers.hermes_agent_provider.HermesAgentProvider",
        )

    def analyze(self, ctx: AnalysisContext, request: IntelligenceTaskRequest | None = None) -> AnalysisResult:
        analysis = self.runtime.analyze(ctx, request=request)
        analysis.metadata["runtime_provider_shim"] = self.descriptor.adapter_name
        return analysis
