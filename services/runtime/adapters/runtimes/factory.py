from __future__ import annotations

from intelligence.runtime.base import AgentRuntime
from shared.config.settings import settings


def resolve_runtime() -> AgentRuntime:
    if settings.reasoning_provider == "hermes":
        from adapters.runtimes.hermes import HermesRuntime

        return HermesRuntime()

    from intelligence.models.mock_provider import MockReasoningProvider

    return MockReasoningProvider()
