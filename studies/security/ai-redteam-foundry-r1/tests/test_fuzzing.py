from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from foundry import HardenedMockTarget, ThreatModel, VulnerableMockTarget  # noqa: E402
from foundry.fuzzing import AbstractInvariantFuzzer, discovery_frontier_by_budget, run_fuzz_campaign  # noqa: E402


class AbstractFuzzingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tm = ThreatModel(
            threat_model_id="tm-fuzz-r1",
            attacker_knowledge="gray-box",
            access="synthetic-typed-operations",
            adaptive=True,
            state_scope="run",
            success_object="invariant-violation",
        )

    def test_mutation_generation_is_deterministic_and_payload_free(self) -> None:
        first = AbstractInvariantFuzzer(17).generate(24)
        second = AbstractInvariantFuzzer(17).generate(24)
        self.assertEqual(first, second)
        self.assertEqual(len(first), 24)
        # The fuzzer operates on typed labels; it does not contain free-form exploit prompt bodies.
        for mutation in first:
            self.assertIn(mutation.family, {template[0] for template in AbstractInvariantFuzzer.TEMPLATES})
            self.assertIn(mutation.channel, AbstractInvariantFuzzer.CHANNELS)

    def test_vulnerable_target_discovers_multiple_root_cause_families(self) -> None:
        result, findings = run_fuzz_campaign(
            target_factory=VulnerableMockTarget,
            threat_model=self.tm,
            seed=17,
            budget=8,
        )
        self.assertGreaterEqual(len(findings), 3)
        self.assertEqual(
            set(result.root_cause_families),
            {
                "instruction_data_provenance_confusion",
                "conversation_state_overrides_privileged_control",
                "cognitive_provider_owns_effect_authority",
            },
        )

    def test_hardened_target_has_no_synthetic_invariant_findings(self) -> None:
        result, findings = run_fuzz_campaign(
            target_factory=HardenedMockTarget,
            threat_model=self.tm,
            seed=17,
            budget=64,
        )
        self.assertEqual(findings, ())
        self.assertEqual(result.root_cause_families, ())

    def test_root_cause_discovery_frontier_is_monotone(self) -> None:
        frontier = discovery_frontier_by_budget(
            target_factory=VulnerableMockTarget,
            threat_model=self.tm,
            seed=17,
            budgets=(1, 2, 4, 8, 16),
        )
        previous: set[str] = set()
        for budget in sorted(frontier):
            current = set(frontier[budget])
            self.assertTrue(previous.issubset(current))
            previous = current
        self.assertGreaterEqual(len(previous), 3)


if __name__ == "__main__":
    unittest.main()
