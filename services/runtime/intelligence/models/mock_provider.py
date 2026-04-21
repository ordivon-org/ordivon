from intelligence.tasks.contracts import IntelligenceTaskRequest
from orchestrator.context.context_builder import AnalysisContext
from domains.research.models import AnalysisResult


class MockReasoningProvider:
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
                "provider": "mock",
                "query": ctx.query.query,
            },
        )
