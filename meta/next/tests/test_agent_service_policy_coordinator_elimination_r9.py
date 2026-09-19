from __future__ import annotations

import inspect
import unittest

import agent_service
from agent_service import delivery


class PolicyCoordinatorEliminationR9Tests(unittest.TestCase):
    def test_policy_evaluation_coordinator_is_deleted(self) -> None:
        self.assertFalse(hasattr(delivery, "PolicyEvaluationCoordinator"))
        self.assertFalse(hasattr(agent_service, "PolicyEvaluationCoordinator"))

    def test_route_plan_owns_policy_admission_request_identity(self) -> None:
        signature = inspect.signature(delivery.DelegationRoutePlanner.plan)
        self.assertIn("client_policy_request_id", signature.parameters)
        self.assertNotIn("policy_receipt_id", signature.parameters)


if __name__ == "__main__":
    unittest.main()
