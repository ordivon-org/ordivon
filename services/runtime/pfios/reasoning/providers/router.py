from pfios.core.config.settings import settings
from pfios.reasoning.providers.mock_provider import MockReasoningProvider


class ReasoningProviderRouter:
    def get_provider(self):
        if settings.reasoning_provider == "mock":
            return MockReasoningProvider()
        return MockReasoningProvider()
