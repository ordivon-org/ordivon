from __future__ import annotations

import unittest

from tests.agent_service_control_stability_support import run_experiments


class AgentServiceControlStabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = run_experiments()

    def scenario(self, scenario_id: str) -> dict:
        return self.report["scenarios"][scenario_id]

    def test_placement_flap_is_measured_as_undamped_oscillation(self) -> None:
        s = self.scenario("S1_PLACEMENT_FLAP")
        self.assertEqual(s["classification"], "OSCILLATION_EXPOSED")
        self.assertEqual(
            s["instanceStates"],
            ["READY", "PROVISIONING", "READY", "PROVISIONING", "READY"],
        )
        self.assertEqual(s["ensureCalls"], 5)
        self.assertFalse(s["hysteresisPresent"])

    def test_stale_placement_observation_can_re_elevate_readiness(self) -> None:
        s = self.scenario("S2_STALE_PLACEMENT_OBSERVATION")
        self.assertEqual(s["classification"], "STALE_OBSERVATION_EXPOSED")
        self.assertEqual(s["stateAfterFreshUnknown"], "PROVISIONING")
        self.assertEqual(s["stateAfterLateStaleReady"], "READY")
        self.assertFalse(s["observationCarriesFreshness"])

    def test_runtime_response_loss_converges_when_provider_honors_exact_replay(
        self,
    ) -> None:
        s = self.scenario("S3_RUNTIME_RESPONSE_LOSS_IDEMPOTENT")
        self.assertEqual(s["classification"], "CONVERGES")
        self.assertEqual(s["submitCalls"], 2)
        self.assertEqual(s["externalJobCount"], 1)
        self.assertTrue(s["sameClientRequestIdentity"])
        self.assertEqual(s["taskState"], "RUNNING")

    def test_runtime_response_loss_exposes_lower_contract_dependency_if_provider_is_not_idempotent(
        self,
    ) -> None:
        s = self.scenario("S4_RUNTIME_RESPONSE_LOSS_NONIDEMPOTENT")
        self.assertEqual(s["classification"], "CONTRACT_DEPENDENCY_EXPOSED")
        self.assertEqual(s["submitCalls"], 2)
        self.assertEqual(s["externalJobCount"], 2)
        self.assertTrue(s["orphanExternalJobPresent"])
        self.assertFalse(s["boundMatchesFirstExternalJob"])

    def test_expired_identity_proof_fails_closed_before_secret_re_resolution(
        self,
    ) -> None:
        s = self.scenario("S5_CREDENTIAL_EXPIRES_BETWEEN_CALLS")
        self.assertEqual(s["classification"], "FAIL_CLOSED")
        self.assertTrue(s["firstHeaderResolved"])
        self.assertTrue(s["secondCallBlocked"])
        self.assertEqual(s["materialProviderCalls"], 1)

    def test_local_execution_claim_blocks_remote_overlap_before_send(self) -> None:
        s = self.scenario("S6_SINGLE_OWNER_BLOCKS_REMOTE_OVERLAP")
        self.assertEqual(s["classification"], "FAIL_CLOSED")
        self.assertEqual(s["claimMode"], "LOCAL_ASSIGNMENT")
        self.assertTrue(s["claimOwnerMatchesAssignment"])
        self.assertTrue(s["remoteDeliveryBlocked"])
        self.assertEqual(s["deliveryCalls"], 0)

    def test_exact_failover_replay_converges_without_duplicate_quiescence_or_replay_effect(
        self,
    ) -> None:
        s = self.scenario("S7_FAILOVER_EXACT_REPLAY")
        self.assertEqual(s["classification"], "CONVERGES")
        self.assertTrue(s["sameTransferId"])
        self.assertEqual(s["quiescenceCalls"], 1)
        self.assertEqual(s["replaySafetyCalls"], 1)
        self.assertTrue(s["claimTransferredToFallback"])

    def test_same_failure_domain_fallback_is_currently_admitted(self) -> None:
        s = self.scenario("S8_SHARED_FAILURE_DOMAIN_FALLBACK")
        self.assertEqual(s["classification"], "FAILURE_DOMAIN_UNMODELED_EXPOSED")
        self.assertTrue(s["sameHostname"])
        self.assertTrue(s["transferAdmitted"])
        self.assertFalse(s["failureDomainModeled"])

    def test_historical_remote_success_blocks_later_failover_after_status_regression(
        self,
    ) -> None:
        s = self.scenario("S9_REMOTE_SUCCESS_THEN_FAILURE")
        self.assertEqual(s["classification"], "FAIL_CLOSED")
        self.assertTrue(s["historicalSuccessPresent"])
        self.assertTrue(s["failoverBlocked"])
        self.assertEqual(s["quiescenceCalls"], 0)
        self.assertEqual(s["replaySafetyCalls"], 0)


if __name__ == "__main__":
    unittest.main()
