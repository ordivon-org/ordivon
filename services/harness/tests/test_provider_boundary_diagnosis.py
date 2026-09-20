import unittest

from scripts.provider_boundary_diagnosis import (
    CARRIER_FAILOVER_STANDINGS,
    diagnose_provider_preflight,
    provider_boundary_policy,
)


class ProviderBoundaryDiagnosisTests(unittest.TestCase):
    def test_challenge_on_healthy_substrate_is_provider_boundary_not_carrier_failure(self) -> None:
        value = diagnose_provider_preflight(
            {
                "standing": "CHALLENGE_GATED",
                "substrateHealth": {"healthy": True},
            }
        )
        self.assertEqual(value["state"], "SUBSTRATE_HEALTHY_PROVIDER_NOT_ADMISSIBLE")
        self.assertEqual(value["substrateStanding"], "HEALTHY")
        self.assertEqual(value["providerAdmission"], "NOT_ADMISSIBLE")
        self.assertEqual(value["carrierRouting"], "PRESERVE_SELECTED_CARRIER")
        self.assertTrue(value["humanVerificationEligible"])
        self.assertFalse(value["automaticInfrastructureMutationAllowed"])
        self.assertIn("human-verification", value["allowedAutomaticActions"])
        for action in (
            "rotate-carrier",
            "restart-carrier",
            "clear-profile",
            "mutate-launcher-flags",
            "mutate-network-authority",
        ):
            self.assertIn(action, value["forbiddenAutomaticInfrastructureRepairs"])

    def test_transport_standing_allows_only_carrier_failover_not_infrastructure_mutation(self) -> None:
        for standing in sorted(CARRIER_FAILOVER_STANDINGS):
            with self.subTest(standing=standing):
                value = diagnose_provider_preflight({"standing": standing})
                self.assertEqual(value["state"], "CARRIER_PRE_EFFECT_UNAVAILABLE")
                self.assertEqual(value["carrierRouting"], "FAILOVER_ALLOWED")
                self.assertEqual(value["reentry"], "TRY_NEXT_CARRIER")
                self.assertFalse(value["automaticInfrastructureMutationAllowed"])

    def test_ready_is_admissible_without_infrastructure_repair(self) -> None:
        value = diagnose_provider_preflight(
            {"standing": "READY", "substrateHealth": {"healthy": True}}
        )
        self.assertEqual(value["state"], "PROVIDER_ADMISSIBLE")
        self.assertEqual(value["providerAdmission"], "ADMISSIBLE")
        self.assertEqual(value["carrierRouting"], "PRESERVE_SELECTED_CARRIER")
        self.assertEqual(value["reentry"], "CONTINUE_MATERIALIZATION")
        self.assertFalse(value["automaticInfrastructureMutationAllowed"])

    def test_rate_limit_waits_on_provider_condition_and_does_not_rotate(self) -> None:
        value = diagnose_provider_preflight(
            {"standing": "PROVIDER_RATE_LIMITED", "substrateHealth": {"healthy": True}}
        )
        self.assertEqual(value["state"], "SUBSTRATE_HEALTHY_PROVIDER_NOT_ADMISSIBLE")
        self.assertFalse(value["humanVerificationEligible"])
        self.assertEqual(value["reentry"], "WAIT_FOR_PROVIDER_CONDITION_CHANGE")
        self.assertEqual(value["carrierRouting"], "PRESERVE_SELECTED_CARRIER")

    def test_ui_unresolved_fails_closed_without_carrier_rotation(self) -> None:
        value = diagnose_provider_preflight(
            {"standing": "COMPOSER_UNAVAILABLE", "substrateHealth": {"healthy": True}}
        )
        self.assertEqual(value["state"], "PROVIDER_UI_OR_CONTROL_UNRESOLVED")
        self.assertEqual(value["providerAdmission"], "UNRESOLVED")
        self.assertEqual(value["carrierRouting"], "PRESERVE_SELECTED_CARRIER")
        self.assertFalse(value["humanVerificationEligible"])

    def test_policy_marks_r9_as_reference_not_live_assertion(self) -> None:
        value = provider_boundary_policy()
        self.assertEqual(value["policyVersion"], "provider-boundary-r1")
        self.assertEqual(
            value["neutralAttributionReference"],
            {
                "reference": "browser-security-r9",
                "standing": "REFERENCE_ONLY_NOT_LIVE_ASSERTION",
            },
        )
        self.assertFalse(value["automaticInfrastructureMutationFromProviderBoundary"])


if __name__ == "__main__":
    unittest.main()
