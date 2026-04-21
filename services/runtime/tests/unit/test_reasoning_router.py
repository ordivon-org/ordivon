from intelligence.models.mock_provider import MockReasoningProvider
from intelligence.models.router import ReasoningProviderRouter
from intelligence.providers.hermes_agent_provider import HermesAgentProvider
from shared.config.settings import settings


def test_reasoning_router_returns_mock_provider():
    original = settings.reasoning_provider
    settings.reasoning_provider = "mock"
    try:
        provider = ReasoningProviderRouter().get_provider()
        assert isinstance(provider, MockReasoningProvider)
    finally:
        settings.reasoning_provider = original


def test_reasoning_router_returns_hermes_provider():
    original = settings.reasoning_provider
    settings.reasoning_provider = "hermes"
    try:
        provider = ReasoningProviderRouter().get_provider()
        assert isinstance(provider, HermesAgentProvider)
    finally:
        settings.reasoning_provider = original
