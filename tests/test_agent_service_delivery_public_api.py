from __future__ import annotations

import unittest

import agent_service
from agent_service.delivery import (
    DelegationRoutePlanner,
    TransportBindingStore,
)


class AgentServiceDeliveryPublicApiTests(unittest.TestCase):
    def test_package_exports_governed_delivery_bricks(self) -> None:
        self.assertFalse(hasattr(agent_service, "AgentServiceR9"))
        self.assertFalse(hasattr(agent_service, "AgentInterfaceAdvertisementStore"))
        self.assertFalse(hasattr(agent_service, "PolicyAdapter"))
        self.assertFalse(hasattr(agent_service, "PolicyDecisionStore"))
        self.assertFalse(hasattr(agent_service, "PolicyEvaluationCoordinator"))
        self.assertIs(agent_service.DelegationRoutePlanner, DelegationRoutePlanner)
        self.assertIs(agent_service.TransportBindingStore, TransportBindingStore)
        self.assertFalse(hasattr(agent_service, "DeliveryAdapter"))
        self.assertFalse(hasattr(agent_service, "DeliveryCoordinator"))
        self.assertFalse(hasattr(agent_service, "DeliveryReceiptStore"))


if __name__ == "__main__":
    unittest.main()
