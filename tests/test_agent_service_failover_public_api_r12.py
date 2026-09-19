from __future__ import annotations

import unittest

import agent_service
from agent_service.failover import (
    AgentServiceR12,
    ExecutionClaimTransferCoordinator,
    ExecutionQuiescenceCoordinator,
    ExecutionQuiescenceRequestStore,
    FailoverCoordinator,
    ReplaySafetyCoordinator,
    TransferAwareDeliveryCoordinator,
)


class AgentServiceFailoverPublicApiR12Tests(unittest.TestCase):
    def test_package_exports_r12_failover_bricks(self) -> None:
        self.assertIs(agent_service.AgentServiceR12, AgentServiceR12)
        self.assertFalse(hasattr(agent_service, "ExecutionQuiescenceAdapter"))
        self.assertIs(agent_service.ExecutionQuiescenceRequestStore, ExecutionQuiescenceRequestStore)
        self.assertFalse(hasattr(agent_service, "ExecutionQuiescenceProofStore"))
        self.assertIs(agent_service.ExecutionQuiescenceCoordinator, ExecutionQuiescenceCoordinator)
        self.assertFalse(hasattr(agent_service, "ReplaySafetyAdapter"))
        self.assertFalse(hasattr(agent_service, "ReplaySafetyDecisionStore"))
        self.assertIs(agent_service.ReplaySafetyCoordinator, ReplaySafetyCoordinator)
        self.assertFalse(hasattr(agent_service, "ExecutionClaimTransferStore"))
        self.assertIs(agent_service.ExecutionClaimTransferCoordinator, ExecutionClaimTransferCoordinator)
        self.assertIs(agent_service.TransferAwareDeliveryCoordinator, TransferAwareDeliveryCoordinator)
        self.assertIs(agent_service.FailoverCoordinator, FailoverCoordinator)


if __name__ == "__main__":
    unittest.main()
