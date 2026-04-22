from intelligence.tasks.contracts import IntelligenceTaskRequest
from intelligence.runtime.base import AgentRuntime, RuntimeDescriptor
from orchestrator.context.context_builder import AnalysisContext
from domains.research.models import AnalysisResult


class MockReasoningProvider(AgentRuntime):
    @property
    def descriptor(self) -> RuntimeDescriptor:
        return RuntimeDescriptor(
            runtime_name="mock",
            provider_name="mock",
            model_name="mock-analysis",
            adapter_name="intelligence.models.mock_provider.MockReasoningProvider",
        )

    def analyze(self, ctx: AnalysisContext, request: IntelligenceTaskRequest | None = None) -> AnalysisResult:
        symbol = ctx.market.symbol or "UNKNOWN"
        return AnalysisResult(
            summary=f"Mock analysis for {symbol}",
            thesis=f"The current thesis for {symbol} is neutral-to-constructive.",
            risks=[
                "Market volatility may invalidate the short-term thesis.",
                "Lack of fresh event/news context in Step 1 mock mode.",
            ],
            suggested_actions=[
                "Observe price structure before acting.",
                "Avoid oversizing in uncertain conditions.",
            ],
            metadata={
                "provider": self.descriptor.provider_name,
                "runtime_name": self.descriptor.runtime_name,
                "runtime_adapter": self.descriptor.adapter_name,
                "query": ctx.query.query,
            },
        )
