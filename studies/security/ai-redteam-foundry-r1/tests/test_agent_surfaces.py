from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from foundry.agent_surfaces import (  # noqa: E402
    HardenedPersistentMemoryAgent,
    HardenedToolTrustAgent,
    LexicalSyntheticMonitor,
    MonitorCase,
    StructuralSyntheticMonitor,
    VulnerablePersistentMemoryAgent,
    VulnerableToolTrustAgent,
    find_monitor_blind_spots,
    run_memory_poisoning_campaign,
    run_tool_poisoning_campaign,
)


class AgentSurfaceTests(unittest.TestCase):
    def test_memory_poisoning_persists_across_synthetic_session_reset(self) -> None:
        finding = run_memory_poisoning_campaign(VulnerablePersistentMemoryAgent())
        self.assertIsNotNone(finding)
        assert finding is not None
        self.assertEqual(finding.family, "memory_poisoning")
        self.assertEqual(finding.detail["crossSession"], True)
        self.assertEqual(
            finding.root_cause_hypothesis,
            "persistence_collapsed_into_instruction_authority",
        )

    def test_memory_provenance_prevents_privilege_promotion(self) -> None:
        self.assertIsNone(run_memory_poisoning_campaign(HardenedPersistentMemoryAgent()))

    def test_connect_time_tool_trust_does_not_cover_runtime_drift(self) -> None:
        finding = run_tool_poisoning_campaign(VulnerableToolTrustAgent)
        self.assertIsNotNone(finding)
        assert finding is not None
        self.assertEqual(finding.family, "tool_poisoning")
        self.assertEqual(
            finding.root_cause_hypothesis,
            "connect_time_trust_was_reused_for_runtime_tool_content",
        )

    def test_tool_descriptor_binding_and_data_control_separation_blocks_drift(self) -> None:
        self.assertIsNone(run_tool_poisoning_campaign(HardenedToolTrustAgent))

    def test_monitor_is_a_target_not_a_trusted_oracle(self) -> None:
        cases = [
            MonitorCase("overt", overt_risk_marker=True, world_state_violation=True, representation="overt"),
            MonitorCase("covert", overt_risk_marker=False, world_state_violation=True, representation="structural"),
            MonitorCase("benign", overt_risk_marker=False, world_state_violation=False, representation="benign"),
        ]
        lexical = find_monitor_blind_spots(LexicalSyntheticMonitor(), cases)
        structural = find_monitor_blind_spots(StructuralSyntheticMonitor(), cases)
        self.assertEqual(len(lexical), 1)
        self.assertEqual(lexical[0].detail["caseId"], "covert")
        self.assertEqual(structural, [])


if __name__ == "__main__":
    unittest.main()
