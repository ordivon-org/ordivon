from __future__ import annotations

import unittest

import agent_service
from agent_service.delivery import (
    AgentServiceR9,
    DelegationRoutePlanner,
    DeliveryAdapter,
    DeliveryCoordinator,
    DeliveryReceiptStore,
    PolicyAdapter,
    PolicyDecisionStore,
    PolicyEvaluationCoordinator,
    TransportBindingStore,
)


class AgentServiceDeliveryPublicApiR9Tests(unittest.TestCase):
    def test_package_exports_governed_delivery_bricks(self) -> None:
        self.assertIs(agent_service.AgentServiceR9, AgentServiceR9)
        self.assertFalse(hasattr(agent_service, "AgentInterfaceAdvertisementStore"))
        self.assertIs(agent_service.PolicyAdapter, PolicyAdapter)
        self.assertIs(agent_service.PolicyDecisionStore, PolicyDecisionStore)
        self.assertIs(agent_service.PolicyEvaluationCoordinator, PolicyEvaluationCoordinator)
        self.assertIs(agent_service.DelegationRoutePlanner, DelegationRoutePlanner)
        self.assertIs(agent_service.TransportBindingStore, TransportBindingStore)
        self.assertIs(agent_service.DeliveryAdapter, DeliveryAdapter)
        self.assertIs(agent_service.DeliveryCoordinator, DeliveryCoordinator)
        self.assertIs(agent_service.DeliveryReceiptStore, DeliveryReceiptStore)


if __name__ == "__main__":
    unittest.main()
