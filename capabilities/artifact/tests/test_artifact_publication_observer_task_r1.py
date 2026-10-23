from __future__ import annotations

import unittest

from artifact_capabilities.publication import observer_task


class PublicationObserverTaskR1Tests(unittest.TestCase):
    TASK_SHA = "sha256:" + "b" * 64

    def _assignment(self, **overrides: str) -> dict[str, object]:
        kwargs = {
            "assignment_id": "assignment-a",
            "task_envelope_sha256": self.TASK_SHA,
            "expected_observer_id": "observer-a",
            "independence_key": "attempt-a",
        }
        kwargs.update(overrides)
        return observer_task.build_observer_assignment(**kwargs)

    def test_task_envelope_binds_role_scope_and_carrier(self) -> None:
        carrier = "sha256:" + "a" * 64
        value = observer_task.build_observer_task_envelope(
            task_id="PC10-PAPER3-R1",
            role="BLIND_VISION",
            carrier_sha256=carrier,
            allowed_read=["page-raster/"],
            forbidden_read=["manuscript-source", "observer-results/"],
            required_outputs=["observer-a-r1.json"],
            acceptance_predicates=["PAGE_COVERAGE_100_PERCENT"],
        )
        self.assertEqual(value["carrierSha256"], carrier)
        self.assertEqual(value["role"], "BLIND_VISION")
        self.assertTrue(value["inputViewDigest"].startswith("sha256:"))

    def test_task_scope_rejects_overlap(self) -> None:
        with self.assertRaises(ValueError):
            observer_task.build_observer_task_envelope(
                task_id="PC10",
                role="BLIND_VISION",
                carrier_sha256="sha256:" + "a" * 64,
                allowed_read=["source"],
                forbidden_read=["source"],
                required_outputs=["report.json"],
                acceptance_predicates=["COVERAGE"],
            )

    def test_canonical_json_digest_is_order_stable(self) -> None:
        self.assertEqual(
            observer_task.canonical_json_sha256({"b": 2, "a": 1}),
            observer_task.canonical_json_sha256({"a": 1, "b": 2}),
        )

    def test_observer_assignment_binds_task_expected_observer_and_independence(self) -> None:
        value = self._assignment()
        self.assertEqual(value["kind"], "publication-perceptual-observer-assignment")
        self.assertEqual(value["taskEnvelopeSha256"], self.TASK_SHA)
        self.assertEqual(value["expectedObserverId"], "observer-a")
        self.assertEqual(value["independenceKey"], "attempt-a")
        self.assertRegex(str(value["assignmentRef"]), r"^sha256:[0-9a-f]{64}$")
        self.assertIs(observer_task.validate_observer_assignment(value), value)

    def test_assignment_ref_excludes_assignment_label_and_truth_boundary(self) -> None:
        first = self._assignment(assignment_id="display-label-a")
        second = self._assignment(assignment_id="display-label-b")
        self.assertNotEqual(first["assignmentId"], second["assignmentId"])
        self.assertEqual(first["assignmentRef"], second["assignmentRef"])

        first["assignmentId"] = "display-label-mutated"
        first["truthBoundary"] = "metadata text changed after construction"
        self.assertIs(observer_task.validate_observer_assignment(first), first)

    def test_assignment_ref_changes_when_semantic_identity_changes(self) -> None:
        base = self._assignment()
        different_task = self._assignment(task_envelope_sha256="sha256:" + "c" * 64)
        different_observer = self._assignment(expected_observer_id="observer-b")
        different_independence = self._assignment(independence_key="attempt-b")
        self.assertNotEqual(base["assignmentRef"], different_task["assignmentRef"])
        self.assertNotEqual(base["assignmentRef"], different_observer["assignmentRef"])
        self.assertNotEqual(base["assignmentRef"], different_independence["assignmentRef"])

    def test_observer_assignment_rejects_invalid_identity_inputs(self) -> None:
        cases = (
            {"assignment_id": ""},
            {"task_envelope_sha256": "not-a-sha"},
            {"expected_observer_id": ""},
            {"independence_key": ""},
        )
        for override in cases:
            with self.subTest(override=override):
                with self.assertRaises(ValueError):
                    self._assignment(**override)

    def test_postbuild_expected_observer_tamper_fails_closed(self) -> None:
        value = self._assignment()
        value["expectedObserverId"] = "observer-b"
        with self.assertRaisesRegex(ValueError, "assignmentRef"):
            observer_task.validate_observer_assignment(value)

    def test_postbuild_independence_key_tamper_fails_closed(self) -> None:
        value = self._assignment()
        value["independenceKey"] = "attempt-b"
        with self.assertRaisesRegex(ValueError, "assignmentRef"):
            observer_task.validate_observer_assignment(value)

    def test_postbuild_task_envelope_tamper_fails_closed(self) -> None:
        value = self._assignment()
        value["taskEnvelopeSha256"] = "sha256:" + "c" * 64
        with self.assertRaisesRegex(ValueError, "assignmentRef"):
            observer_task.validate_observer_assignment(value)

    def test_invalid_assignment_ref_fails_closed(self) -> None:
        value = self._assignment()
        value["assignmentRef"] = "sha256:" + "0" * 64
        with self.assertRaisesRegex(ValueError, "assignmentRef"):
            observer_task.validate_observer_assignment(value)


if __name__ == "__main__":
    unittest.main()
