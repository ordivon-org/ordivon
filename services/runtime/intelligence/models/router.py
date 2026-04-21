from intelligence.providers.hermes_agent_provider import HermesAgentProvider
from intelligence.models.mock_provider import MockReasoningProvider
from shared.config.settings import settings


class ReasoningProviderRouter:
    def get_provider(self):
        if settings.reasoning_provider == "mock":
            return MockReasoningProvider()
        if settings.reasoning_provider == "hermes":
            return HermesAgentProvider()
        return MockReasoningProvider()
