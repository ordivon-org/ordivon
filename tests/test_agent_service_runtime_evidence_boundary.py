from __future__ import annotations

import unittest
from pathlib import Path

import agent_service.evidence as evidence
from agent_service.task_runtime import RuntimeJobObservation


class RuntimeEvidenceBoundaryTests(unittest.TestCase):
    def _observation(self, **overrides):
        values = dict(
            job_id="job-r26",
            status="succeeded",
            execution_terminal=True,
            delivery_disposition="committed",
            semantic_completion_evaluated=False,
            stdout_tail="",
            stderr_tail="",
            artifacts=(),
        )
        values.update(overrides)
        return RuntimeJobObservation(**values)

    def test_gate_class_and_facade_are_deleted(self) -> None:
        self.assertFalse(hasattr(evidence, "RuntimeEvidenceGate"))
        source = Path(evidence.__file__).read_text(encoding="utf-8")
        self.assertNotIn("self.mechanical_gate =", source)
        self.assertTrue(callable(evidence._evaluate_runtime_evidence_gate))

    def test_mechanical_boundary_semantics_are_preserved(self) -> None:
        self.assertIsNone(
            evidence._evaluate_runtime_evidence_gate(
                self._observation(execution_terminal=False)
            )
        )
        failed = evidence._evaluate_runtime_evidence_gate(
            self._observation(status="failed")
        )
        self.assertFalse(failed.accepted)
        self.assertEqual(failed.reason, "runtime:failed")

        uncommitted = evidence._evaluate_runtime_evidence_gate(
            self._observation(delivery_disposition="in_progress")
        )
        self.assertFalse(uncommitted.accepted)
        self.assertEqual(uncommitted.reason, "runtime:delivery:in_progress")

        accepted = evidence._evaluate_runtime_evidence_gate(self._observation())
        self.assertTrue(accepted.accepted)
        self.assertIsNone(accepted.reason)

        with self.assertRaisesRegex(
            RuntimeError,
            "Runtime crossed semantic-completion authority boundary",
        ):
            evidence._evaluate_runtime_evidence_gate(
                self._observation(semantic_completion_evaluated=True)
            )


if __name__ == "__main__":
    unittest.main()
