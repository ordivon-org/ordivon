from __future__ import annotations

import inspect
import unittest

import agent_service.delivery as delivery
import agent_service.effect_authority as effect_authority


class PolicyEffectBoundaryTests(unittest.TestCase):
    def test_route_planning_owns_policy_admission_request_identity(self) -> None:
        signature = inspect.signature(delivery.DelegationRoutePlanner.plan)
        self.assertIn("client_policy_request_id", signature.parameters)
        self.assertNotIn("policy_receipt_id", signature.parameters)

    def test_transport_binding_keeps_only_policy_receipt_snapshot(self) -> None:
        fields = set(delivery.TransportBinding.__dataclass_fields__)
        self.assertNotIn("policy_decision_id", fields)
        self.assertTrue(
            {"policy_receipt_id", "policy_revision", "granted_permissions"}.issubset(
                fields
            )
        )

    def test_effect_delivery_guard_owns_current_policy_boundary(self) -> None:
        init_fields = effect_authority.EffectAuthorizedDeliveryCoordinator.__init__.__code__.co_varnames
        self.assertIn("policy_adapter", init_fields)
        self.assertIn("events", init_fields)
        self.assertIn("bindings", init_fields)
        self.assertIn("delegations", init_fields)


if __name__ == "__main__":
    unittest.main()
