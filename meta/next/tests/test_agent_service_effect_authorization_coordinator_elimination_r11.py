from __future__ import annotations

import unittest

import agent_service
import agent_service.effect_authority as effect_authority


class EffectAuthorizationCoordinatorEliminationR11Tests(unittest.TestCase):
    def test_effect_authorization_coordinator_and_service_surface_are_deleted(self) -> None:
        self.assertFalse(hasattr(effect_authority, "EffectAuthorizationCoordinator"))
        self.assertFalse(hasattr(agent_service, "EffectAuthorizationCoordinator"))

    def test_delivery_guard_owns_current_policy_boundary(self) -> None:
        init_fields = effect_authority.EffectAuthorizedDeliveryCoordinator.__init__.__code__.co_varnames
        self.assertIn("policy_adapter", init_fields)
        self.assertIn("events", init_fields)
        self.assertIn("bindings", init_fields)
        self.assertIn("delegations", init_fields)


if __name__ == "__main__":
    unittest.main()
