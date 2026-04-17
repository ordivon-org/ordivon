from pfios.context.context_builder import AnalysisContext
from pfios.domain.analysis.models import AnalysisResult
from pfios.reasoning.providers.router import ReasoningProviderRouter


class ReasoningEngine:
    def __init__(self) -> None:
        self.router = ReasoningProviderRouter()

    def analyze(self, ctx: AnalysisContext) -> AnalysisResult:
        provider = self.router.get_provider()
        return provider.analyze(ctx)
