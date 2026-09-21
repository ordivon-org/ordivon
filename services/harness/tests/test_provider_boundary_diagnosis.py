import unittest

from scripts.provider_boundary_diagnosis import (
    CARRIER_FAILOVER_STANDINGS,
    diagnose_provider_preflight,
    provider_boundary_policy,
)


class ProviderBoundaryDiagnosisTests(unittest.TestCase):
    def test_auth_required_allows_authorized_human_control_transfer(self) -> None:
        value = diagnose_provider_preflight(
            {"standing": "AUTH_REQUIRED", "substrateHealth": {"healthy": True}}
        )
        self.assertEqual(value["providerAction"], "HUMAN_CONTROL_TRANSFER")
        self.assertTrue(value["humanVerificationEligible"])
        self.assertEqual(value["carrierRouting"], "PRESERVE_SELECTED_CARRIER")
        self.assertFalse(value["automaticInfrastructureMutationAllowed"])

    def test_challenge_gated_is_pre_effect_hold_not_human_verification(self) -> None:
        value = diagnose_provider_preflight(
            {"standing": "CHALLENGE_GATED", "substrateHealth": {"healthy": True}}
        )
        self.assertEqual(value["state"], "SUBSTRATE_HEALTHY_PROVIDER_NOT_ADMISSIBLE")
        self.assertEqual(value["substrateStanding"], "HEALTHY")
        self.assertEqual(value["providerAdmission"], "NOT_ADMISSIBLE")
        self.assertEqual(value["carrierRouting"], "PRESERVE_SELECTED_CARRIER")
        self.assertEqual(value["providerAction"], "PRE_EFFECT_HOLD")
        self.assertFalse(value["humanVerificationEligible"])
        self.assertFalse(value["automaticInfrastructureMutationAllowed"])
        self.assertNotIn("human-verification", value["allowedAutomaticActions"])
        for action in (
            "rotate-carrier",
            "restart-carrier",
            "clear-profile",
            "mutate-launcher-flags",
            "mutate-network-authority",
        ):
            self.assertIn(action, value["forbiddenAutomaticInfrastructureRepairs"])

    def test_transport_standing_projects_explicit_failover_action(self) -> None:
        for standing in sorted(CARRIER_FAILOVER_STANDINGS):
            with self.subTest(standing=standing):
                value = diagnose_provider_preflight({"standing": standing})
                self.assertEqual(value["state"], "CARRIER_PRE_EFFECT_UNAVAILABLE")
                self.assertEqual(value["carrierRouting"], "FAILOVER_ALLOWED")
                self.assertEqual(value["providerAction"], "TRY_NEXT_CARRIER")
                self.assertEqual(value["reentry"], "TRY_NEXT_CARRIER")
                self.assertFalse(value["automaticInfrastructureMutationAllowed"])

    def test_ready_projects_continue_materialization_action(self) -> None:
        value = diagnose_provider_preflight(
            {"standing": "READY", "substrateHealth": {"healthy": True}}
        )
        self.assertEqual(value["state"], "PROVIDER_ADMISSIBLE")
        self.assertEqual(value["providerAdmission"], "ADMISSIBLE")
        self.assertEqual(value["carrierRouting"], "PRESERVE_SELECTED_CARRIER")
        self.assertEqual(value["providerAction"], "CONTINUE_MATERIALIZATION")
        self.assertEqual(value["reentry"], "CONTINUE_MATERIALIZATION")
        self.assertFalse(value["automaticInfrastructureMutationAllowed"])

    def test_rate_limit_projects_wait_action_and_does_not_rotate(self) -> None:
        value = diagnose_provider_preflight(
            {"standing": "PROVIDER_RATE_LIMITED", "substrateHealth": {"healthy": True}}
        )
        self.assertEqual(value["state"], "SUBSTRATE_HEALTHY_PROVIDER_NOT_ADMISSIBLE")
        self.assertFalse(value["humanVerificationEligible"])
        self.assertEqual(value["providerAction"], "WAIT_FOR_PROVIDER_CONDITION_CHANGE")
        self.assertEqual(value["reentry"], "WAIT_FOR_PROVIDER_CONDITION_CHANGE")
        self.assertEqual(value["carrierRouting"], "PRESERVE_SELECTED_CARRIER")

    def test_ui_unresolved_projects_pre_effect_hold(self) -> None:
        value = diagnose_provider_preflight(
            {"standing": "COMPOSER_UNAVAILABLE", "substrateHealth": {"healthy": True}}
        )
        self.assertEqual(value["state"], "PROVIDER_UI_OR_CONTROL_UNRESOLVED")
        self.assertEqual(value["providerAdmission"], "UNRESOLVED")
        self.assertEqual(value["carrierRouting"], "PRESERVE_SELECTED_CARRIER")
        self.assertEqual(value["providerAction"], "PRE_EFFECT_HOLD")
        self.assertFalse(value["humanVerificationEligible"])

    def test_unknown_standing_fails_closed_with_explicit_hold_action(self) -> None:
        value = diagnose_provider_preflight(
            {"standing": "SOMETHING_NEW", "substrateHealth": {"healthy": True}}
        )
        self.assertEqual(value["providerAction"], "PRE_EFFECT_HOLD")
        self.assertEqual(value["providerAdmission"], "UNRESOLVED")
        self.assertFalse(value["humanVerificationEligible"])

    def test_policy_projects_single_action_table_and_r9_reference(self) -> None:
        value = provider_boundary_policy()
        self.assertEqual(value["policyVersion"], "provider-boundary-r2")
        self.assertEqual(
            value["neutralAttributionReference"],
            {
                "reference": "browser-security-r9",
                "standing": "REFERENCE_ONLY_NOT_LIVE_ASSERTION",
            },
        )
        self.assertFalse(value["automaticInfrastructureMutationFromProviderBoundary"])
        self.assertEqual(value["providerActions"]["AUTH_REQUIRED"], "HUMAN_CONTROL_TRANSFER")
        self.assertEqual(value["providerActions"]["CHALLENGE_GATED"], "PRE_EFFECT_HOLD")
        self.assertEqual(value["providerActions"]["READY"], "CONTINUE_MATERIALIZATION")


if __name__ == "__main__":
    unittest.main()
