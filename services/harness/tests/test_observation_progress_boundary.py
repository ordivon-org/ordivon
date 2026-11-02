from __future__ import annotations

import inspect
import unittest

from ordivon_harness.agent_run import HarnessToolBridgeFactory
from ordivon_harness.agent_tool_observation import HarnessToolObservation
from ordivon_harness.ordivon.loop import RunBudget
from ordivon_harness.ordivon.model import AgentToolCall
from ordivon_harness.ordivon.run_recovery import _evaluate_observation_progress
from ordivon_harness.ordivon.run_store_port import HarnessRunContinuityStore


class ObservationProgressBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.signatures: set[str] = set()
        self.search_evidence: dict[tuple[str, str], set[str]] = {}
        self.read_only = frozenset({"read_workspace", "search_workspace", "observe_job"})

    def advance(self, calls, observations):
        return _evaluate_observation_progress(
            tuple(calls),
            list(observations),
            observation_only_tool_names=self.read_only,
            evidence_signatures=self.signatures,
            search_evidence=self.search_evidence,
        )

    @staticmethod
    def observed(call_id: str, tool: str, content: dict, status: str = "observed"):
        return HarnessToolObservation(
            tool_call_id=call_id,
            tool_name=tool,
            status=status,
            structured_content=content,
        )

    def test_observation_replay_without_new_evidence_is_not_progress(self) -> None:
        read = self.observed("call:read", "read_workspace", {"digest": "one"})
        first = self.advance((), (read,))
        second = self.advance((), (read,))
        self.assertEqual(
            (first.observation_only, first.action_progress, first.new_evidence),
            (True, False, True),
        )
        self.assertEqual(
            (second.observation_only, second.action_progress, second.new_evidence),
            (True, False, False),
        )
        self.assertEqual(len(self.signatures), 1)

    def test_action_progress_is_separate_from_new_evidence(self) -> None:
        write = self.observed("call:write", "mutate_workspace", {"result": "ok"})
        first = self.advance((), (write,))
        second = self.advance((), (write,))
        self.assertEqual(
            (first.observation_only, first.action_progress, first.new_evidence),
            (False, True, True),
        )
        self.assertEqual(
            (second.observation_only, second.action_progress, second.new_evidence),
            (False, True, False),
        )

    def test_rejected_and_unknown_observations_do_not_create_progress(self) -> None:
        for status in ("rejected", "unknown", "cancelled"):
            outcome = self.advance(
                (), (self.observed("call:skip", "read_workspace", {}, status),)
            )
            self.assertFalse(outcome.observation_only)
            self.assertFalse(outcome.action_progress)
            self.assertFalse(outcome.new_evidence)
        self.assertEqual(self.signatures, set())

    def test_search_subsumption_and_changed_outcome_are_distinct(self) -> None:
        broad = AgentToolCall("call:broad", "search_workspace", {
            "query": "needle", "relativePath": "."
        })
        narrow = AgentToolCall("call:narrow", "search_workspace", {
            "query": "needle", "relativePath": "src"
        })
        payload = {"matches": [{"relativePath": "src/a.py", "line": 7}], "exitCode": 0}
        self.assertTrue(self.advance(
            (broad,), (self.observed("call:broad", "search_workspace", payload),)
        ).new_evidence)
        self.assertFalse(self.advance(
            (narrow,), (self.observed("call:narrow", "search_workspace", payload),)
        ).new_evidence)
        changed = dict(payload, exitCode=2)
        self.assertTrue(self.advance(
            (narrow,), (self.observed("call:narrow", "search_workspace", changed),)
        ).new_evidence)

    def test_invalid_search_shape_uses_existing_signature_fallback(self) -> None:
        call = AgentToolCall("call:bad", "search_workspace", {
            "query": "needle", "relativePath": 3
        })
        obs = self.observed("call:bad", "search_workspace", {"matches": []})
        self.assertTrue(self.advance((call,), (obs,)).new_evidence)
        self.assertFalse(self.advance((call,), (obs,)).new_evidence)

    def test_gate_disabled_thresholds_and_priority_are_preserved(self) -> None:
        budget = RunBudget(
            max_model_calls=5,
            max_tool_calls=5,
            max_observation_bytes=4096,
            max_wall_time_ms=30_000,
            max_no_progress_turns=2,
            max_observation_only_turns=3,
        )
        self.assertIsNone(budget.observation_gate_reason(
            no_progress_turns=1, observation_only_turns=2
        ))
        self.assertIn("2 consecutive turns", budget.observation_gate_reason(
            no_progress_turns=2, observation_only_turns=0
        ) or "")
        self.assertIn("3 consecutive observation-only turns", budget.observation_gate_reason(
            no_progress_turns=0, observation_only_turns=3
        ) or "")
        self.assertIn("turns without a mutation", budget.observation_gate_reason(
            no_progress_turns=2, observation_only_turns=3
        ) or "")
        disabled = RunBudget(
            max_model_calls=5, max_tool_calls=5, max_observation_bytes=4096,
            max_wall_time_ms=30_000, max_no_progress_turns=0,
            max_observation_only_turns=0,
        )
        self.assertIsNone(disabled.observation_gate_reason(
            no_progress_turns=999, observation_only_turns=999
        ))

    def test_supported_bridge_factory_type_depends_on_existing_port(self) -> None:
        annotation = inspect.signature(HarnessToolBridgeFactory.build).parameters[
            "continuity"
        ].annotation
        self.assertEqual(annotation, "HarnessRunContinuityStore")
        self.assertNotEqual(annotation, "SQLiteHarnessRunContinuityStore")
        self.assertTrue(getattr(HarnessRunContinuityStore, "_is_protocol", False))


if __name__ == "__main__":
    unittest.main()
