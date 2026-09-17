from __future__ import annotations

import unittest

import agent_service
from agent_service.semantics import (
    A2AAgentCardProjector,
    AgentIdentityStore,
    AgentServiceR8,
    CapabilityAdvertisementStore,
    DelegationEnvelopeStore,
    SessionItemStore,
    SessionStore,
)


class AgentServiceSemanticsPublicApiR8Tests(unittest.TestCase):
    def test_package_exports_r8_semantic_bricks(self) -> None:
        self.assertIs(agent_service.AgentServiceR8, AgentServiceR8)
        self.assertIs(agent_service.AgentIdentityStore, AgentIdentityStore)
        self.assertIs(agent_service.CapabilityAdvertisementStore, CapabilityAdvertisementStore)
        self.assertIs(agent_service.SessionStore, SessionStore)
        self.assertIs(agent_service.SessionItemStore, SessionItemStore)
        self.assertIs(agent_service.DelegationEnvelopeStore, DelegationEnvelopeStore)
        self.assertIs(agent_service.A2AAgentCardProjector, A2AAgentCardProjector)


if __name__ == "__main__":
    unittest.main()
