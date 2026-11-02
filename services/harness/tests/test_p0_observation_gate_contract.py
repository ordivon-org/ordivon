from __future__ import annotations

import unittest
from typing import get_type_hints

from ordivon_harness.agent_run import HarnessToolBridgeFactory
from ordivon_harness.ordivon.loop import RunBudget, _soft_observation_gate_reason
from ordivon_harness.ordivon.run_store_port import HarnessRunContinuityStore


class ObservationGateContractTests(unittest.TestCase):
    def budget(self, *, no_progress: int = 3, observation_only: int = 4) -> RunBudget:
        return RunBudget(
            max_model_calls=5,
            max_tool_calls=5,
            max_observation_bytes=1000,
            max_wall_time_ms=10000,
            max_no_progress_turns=no_progress,
            max_observation_only_turns=observation_only,
        )

    def test_thresholds_are_inclusive_and_independent(self) -> None:
        budget = self.budget()
        self.assertIsNone(_soft_observation_gate_reason(budget, 2, 3))
        self.assertIn("3 consecutive turns", _soft_observation_gate_reason(budget, 3, 0))
        self.assertIn("4 consecutive observation-only", _soft_observation_gate_reason(budget, 0, 4))

    def test_no_progress_precedence_is_preserved(self) -> None:
        reason = _soft_observation_gate_reason(self.budget(), 3, 4)
        self.assertIn("without a mutation, check, materially new", reason)
        self.assertNotIn("observation-only", reason)

    def test_zero_disables_each_soft_gate(self) -> None:
        self.assertIsNone(
            _soft_observation_gate_reason(self.budget(no_progress=0, observation_only=0), 100, 100)
        )
        self.assertIn(
            "observation-only", _soft_observation_gate_reason(self.budget(no_progress=0), 100, 4)
        )
        self.assertIn(
            "without a mutation",
            _soft_observation_gate_reason(self.budget(observation_only=0), 3, 100),
        )

    def test_public_bridge_factory_uses_owner_neutral_store_port(self) -> None:
        annotations = get_type_hints(HarnessToolBridgeFactory.build)
        self.assertIs(annotations["continuity"], HarnessRunContinuityStore)


if __name__ == "__main__":
    unittest.main()
