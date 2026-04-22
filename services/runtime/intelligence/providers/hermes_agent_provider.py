"""Legacy compatibility export for adapter-owned Hermes runtime.

This path remains only to avoid import breakage while runtime ownership lives
under ``adapters.runtimes.hermes``.
"""

from adapters.runtimes.hermes import HermesRuntime

HermesAgentProvider = HermesRuntime

__all__ = ["HermesAgentProvider"]
