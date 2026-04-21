from domains.research.models import AnalysisResult
from intelligence.models.router import ReasoningProviderRouter
from intelligence.tasks.contracts import IntelligenceTaskRequest
from orchestrator.context.context_builder import AnalysisContext


class ReasoningEngine:
    def __init__(self) -> None:
        self.router = ReasoningProviderRouter()

    def analyze(self, ctx: AnalysisContext, request: IntelligenceTaskRequest | None = None) -> AnalysisResult:
        provider = self.router.get_provider()
        return provider.analyze(ctx, request=request)
