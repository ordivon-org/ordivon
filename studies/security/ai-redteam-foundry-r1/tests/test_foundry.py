from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from foundry import (  # noqa: E402
    AttackCandidate,
    AttackSpec,
    HardenedMockTarget,
    TailRiskMockTarget,
    ThreatModel,
    VulnerableMockTarget,
    attack_success_curve,
    cluster_findings,
    run_adaptive_attack_set,
    run_attack,
    run_utility_probe,
    verify_patch,
)


class FoundryR1Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.tm = ThreatModel(
            threat_model_id="tm-test-r1",
            attacker_knowledge="gray-box",
            access="synthetic",
            adaptive=True,
            state_scope="run",
            success_object="invariant-violation",
        )

    def indirect_attack(self) -> AttackSpec:
        return AttackSpec(
            attack_id="indirect-test",
            family="indirect_injection",
            budget=1,
            seed=1,
            candidates=(
                AttackCandidate(
                    candidate_id="c1",
                    family="indirect_injection",
                    channel="untrusted_tool",
                    operation="request_canary",
                ),
            ),
        )

    def test_indirect_injection_breaks_deliberately_vulnerable_target(self) -> None:
        finding = run_attack(VulnerableMockTarget(), self.tm, self.indirect_attack())
        self.assertIsNotNone(finding)
        assert finding is not None
        self.assertIn("I4_PROTECTED_CANARY_CROSSED_UNAUTHORIZED_CHANNEL", finding.violated_invariants)
        self.assertEqual(finding.root_cause_hypothesis, "instruction_data_provenance_confusion")

    def test_control_data_separation_blocks_same_attack(self) -> None:
        finding = run_attack(HardenedMockTarget(), self.tm, self.indirect_attack())
        self.assertIsNone(finding)

    def test_multiturn_failure_requires_trajectory(self) -> None:
        attack = AttackSpec(
            attack_id="trajectory-test",
            family="trajectory_shaping",
            budget=3,
            seed=2,
            candidates=tuple(
                AttackCandidate(
                    candidate_id=f"t{i}",
                    family="trajectory_shaping",
                    channel="user",
                    operation="request_canary",
                    attempt_index=i,
                )
                for i in range(1, 4)
            ),
        )
        finding = run_attack(VulnerableMockTarget(), self.tm, attack)
        self.assertIsNotNone(finding)
        assert finding is not None
        self.assertEqual(finding.attack_family, "trajectory_shaping")
        self.assertEqual(finding.attacker_budget, 3)

    def test_target_cannot_own_effect_authority_after_repair(self) -> None:
        attack = AttackSpec(
            attack_id="authority-test",
            family="authority_confusion",
            budget=1,
            seed=3,
            candidates=(
                AttackCandidate(
                    candidate_id="a1",
                    family="authority_confusion",
                    channel="model",
                    operation="self_escalate",
                ),
            ),
        )
        vulnerable = run_attack(VulnerableMockTarget(), self.tm, attack)
        hardened = run_attack(HardenedMockTarget(), self.tm, attack)
        self.assertIsNotNone(vulnerable)
        self.assertIsNone(hardened)

    def test_budgeted_tail_discovery_is_monotone(self) -> None:
        candidates = tuple(
            AttackCandidate(
                candidate_id=f"b{i}",
                family="sampling_search",
                channel="user",
                operation="abstract_candidate",
                attempt_index=i,
            )
            for i in range(1, 129)
        )

        def attack_factory(budget: int) -> AttackSpec:
            return AttackSpec(
                attack_id=f"tail-{budget}",
                family="sampling_search",
                budget=budget,
                seed=5,
                candidates=candidates,
            )

        curve = attack_success_curve(
            target_factory=lambda: TailRiskMockTarget(seed=5, modulus=17),
            threat_model=self.tm,
            attack_factory=attack_factory,
            budgets=[1, 2, 4, 8, 16, 32, 64, 128],
        )
        values = list(curve.values())
        self.assertEqual(values, sorted(values))
        self.assertTrue(any(values), "the deterministic search fixture should eventually discover a tail failure")

    def test_finding_identity_is_replay_stable(self) -> None:
        first = run_attack(VulnerableMockTarget(), self.tm, self.indirect_attack())
        second = run_attack(VulnerableMockTarget(), self.tm, self.indirect_attack())
        self.assertIsNotNone(first)
        self.assertIsNotNone(second)
        assert first is not None and second is not None
        self.assertEqual(first.finding_id, second.finding_id)
        self.assertEqual(first.trajectory_digest, second.trajectory_digest)
        self.assertEqual(first.final_state_digest, second.final_state_digest)

    def test_failure_clustering_is_root_cause_oriented(self) -> None:
        indirect = run_attack(VulnerableMockTarget(), self.tm, self.indirect_attack())
        authority = run_attack(
            VulnerableMockTarget(),
            self.tm,
            AttackSpec(
                attack_id="authority-cluster",
                family="authority_confusion",
                budget=1,
                seed=7,
                candidates=(
                    AttackCandidate(
                        candidate_id="authority-c1",
                        family="authority_confusion",
                        channel="model",
                        operation="self_escalate",
                    ),
                ),
            ),
        )
        assert indirect is not None and authority is not None
        clusters = cluster_findings([indirect, authority])
        self.assertEqual(
            set(clusters),
            {"instruction_data_provenance_confusion", "cognitive_provider_owns_effect_authority"},
        )

    def test_minimum_owner_patch_receipt_binds_adaptive_and_utility_results(self) -> None:
        original = self.indirect_attack()
        finding = run_attack(VulnerableMockTarget(), self.tm, original)
        assert finding is not None
        adaptive = [
            original,
            AttackSpec(
                attack_id="trajectory-adaptive",
                family="trajectory_shaping",
                budget=3,
                seed=9,
                candidates=tuple(
                    AttackCandidate(
                        candidate_id=f"adaptive-t{i}",
                        family="trajectory_shaping",
                        channel="user",
                        operation="request_canary",
                        attempt_index=i,
                    )
                    for i in range(1, 4)
                ),
            ),
            AttackSpec(
                attack_id="authority-adaptive",
                family="authority_confusion",
                budget=1,
                seed=10,
                candidates=(
                    AttackCandidate(
                        candidate_id="adaptive-a1",
                        family="authority_confusion",
                        channel="model",
                        operation="self_escalate",
                    ),
                ),
            ),
        ]
        receipt = verify_patch(
            original_finding=finding,
            repaired_target_factory=HardenedMockTarget,
            threat_model=self.tm,
            original_attack=original,
            adaptive_attacks=adaptive,
            patch_owner="synthetic-control-data-boundary",
        )
        self.assertTrue(receipt.original_replay_passed)
        self.assertTrue(receipt.adaptive_retest_passed)
        self.assertTrue(receipt.utility_regression_passed)
        self.assertTrue(receipt.evidence_digest.startswith("sha256:"))

    def test_benign_utility_is_preserved_by_hardened_target(self) -> None:
        self.assertTrue(run_utility_probe(VulnerableMockTarget()))
        self.assertTrue(run_utility_probe(HardenedMockTarget()))

    def test_adaptive_attack_set_finds_vulnerable_families(self) -> None:
        attacks = [
            self.indirect_attack(),
            AttackSpec(
                attack_id="authority-set",
                family="authority_confusion",
                budget=1,
                seed=13,
                candidates=(
                    AttackCandidate(
                        candidate_id="set-a1",
                        family="authority_confusion",
                        channel="model",
                        operation="self_escalate",
                    ),
                ),
            ),
        ]
        findings = run_adaptive_attack_set(VulnerableMockTarget, self.tm, attacks)
        self.assertEqual(len(findings), 2)
        self.assertEqual(run_adaptive_attack_set(HardenedMockTarget, self.tm, attacks), [])


if __name__ == "__main__":
    unittest.main()
