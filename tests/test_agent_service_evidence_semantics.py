from __future__ import annotations

import unittest

import agent_service.evidence as evidence
from agent_service.evidence import EvidenceBundle


class EvidenceSemanticsTests(unittest.TestCase):
    def _bundle(self, text):
        return EvidenceBundle(
            resolver="test",
            facts={"text": text},
            provenance={"runtimeJobId": "job-evidence"},
        )

    def test_resolution_and_semantic_verification_are_module_functions(self) -> None:
        self.assertTrue(callable(evidence._resolve_evidence))
        self.assertTrue(callable(evidence._verify_evidence_semantics))

    def test_text_acceptance_rules_are_preserved(self) -> None:
        contains = evidence._verify_evidence_semantics(
            {"kind": "stdout_contains", "value": "needle"},
            self._bundle("hay needle stack"),
        )
        self.assertTrue(contains.accepted)
        self.assertIsNone(contains.reason)

        equals = evidence._verify_evidence_semantics(
            {"kind": "stdout_equals", "value": "exact"},
            self._bundle("not exact"),
        )
        self.assertFalse(equals.accepted)
        self.assertEqual(equals.reason, "acceptance:stdout_equals:not_satisfied")

        artifact = evidence._verify_evidence_semantics(
            {"kind": "runtime_artifact_text_contains", "value": "artifact"},
            self._bundle("artifact text"),
        )
        self.assertTrue(artifact.accepted)

        with self.assertRaisesRegex(
            RuntimeError,
            "text acceptance requires normalized text evidence",
        ):
            evidence._verify_evidence_semantics(
                {"kind": "stdout_equals", "value": "x"},
                self._bundle(None),
            )

        with self.assertRaisesRegex(ValueError, "unsupported acceptance kind"):
            evidence._verify_evidence_semantics(
                {"kind": "unsupported", "value": "x"},
                self._bundle("x"),
            )


if __name__ == "__main__":
    unittest.main()
