from __future__ import annotations

import unittest

import agent_service
from agent_service.provider_adapters import (
    A2AQuiescenceAdapter,
    EffectLedgerEffect,
    EffectLedgerReplaySafetyAdapter,
    EffectLedgerSnapshot,
    MCPTaskQuiescenceAdapter,
    ProviderProtocolError,
    ProviderRemoteError,
    QuiescencePending,
    RemoteExecutionCompleted,
)


class AgentServiceProviderAdaptersPublicApiTests(unittest.TestCase):
    def test_package_exports_r13_provider_bricks(self) -> None:
        self.assertFalse(hasattr(agent_service, "AgentServiceR13"))
        self.assertFalse(hasattr(agent_service, "A2AJsonRpcHttpClient"))
        self.assertIs(agent_service.A2AQuiescenceAdapter, A2AQuiescenceAdapter)
        self.assertFalse(hasattr(agent_service, "MCPTasksHttpClient"))
        self.assertIs(agent_service.MCPTaskQuiescenceAdapter, MCPTaskQuiescenceAdapter)
        self.assertFalse(hasattr(agent_service, "EffectLedgerReader"))
        self.assertIs(agent_service.EffectLedgerEffect, EffectLedgerEffect)
        self.assertIs(agent_service.EffectLedgerSnapshot, EffectLedgerSnapshot)
        self.assertIs(agent_service.EffectLedgerReplaySafetyAdapter, EffectLedgerReplaySafetyAdapter)
        self.assertIs(agent_service.ProviderProtocolError, ProviderProtocolError)
        self.assertIs(agent_service.ProviderRemoteError, ProviderRemoteError)
        self.assertIs(agent_service.QuiescencePending, QuiescencePending)
        self.assertIs(agent_service.RemoteExecutionCompleted, RemoteExecutionCompleted)


if __name__ == "__main__":
    unittest.main()
