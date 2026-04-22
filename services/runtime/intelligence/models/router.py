from adapters.runtimes.factory import resolve_runtime
from intelligence.models.mock_provider import MockReasoningProvider
from intelligence.runtime.base import AgentRuntime


class ReasoningProviderRouter:
    def get_provider(self) -> AgentRuntime:
        provider = resolve_runtime()
        if isinstance(provider, MockReasoningProvider):
            return provider
        return provider
