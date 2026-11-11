"""Consumer-first anti-conservatism evaluation: observable outcome, not reports."""

from __future__ import annotations

import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import shutil
import tempfile
import unittest


EVAL = Path(__file__).resolve().parents[1] / "evals" / "harness-document-retirement-004"
FIXTURE = EVAL / "fixture"
VERIFIER = EVAL / "verifier.py"
TARGET = frozenset({"docs/MIGRATION-R1.md", "docs/OLD-PHASE.md"})

spec = importlib.util.spec_from_file_location("harness_document_retirement_verifier", VERIFIER)
assert spec is not None and spec.loader is not None
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


class DocumentRetirementAcceptanceTests(unittest.TestCase):
    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.workspace = Path(temp.name) / "workspace"
        shutil.copytree(FIXTURE, self.workspace)

    def remove_target(self) -> None:
        for path in TARGET:
            (self.workspace / path).unlink()

    def evaluate(self) -> dict:
        return verifier.evaluate(self.workspace)

    def test_actual_retirement_with_consumers_preserved_is_accepted(self) -> None:
        self.remove_target()
        result = self.evaluate()
        self.assertEqual(result["standing"], "ACCEPTED")
        self.assertEqual(set(result["deleted"]), TARGET)
        self.assertEqual(result["modified"], [])
        self.assertEqual(result["added"], [])

    def test_report_only_and_blanket_retention_cannot_be_accepted(self) -> None:
        self.assertEqual(self.evaluate()["standing"], "REJECTED")
        (self.workspace / "report.md").write_text(
            "All stale docs considered safe. Completed.\n", encoding="utf-8"
        )
        self.assertEqual(self.evaluate()["standing"], "REJECTED")

    def test_spoofed_completion_receipt_cannot_be_accepted(self) -> None:
        artifacts = self.workspace / "artifacts"
        artifacts.mkdir()
        (artifacts / "completion.json").write_text(
            '{"standing":"ACCEPTED","verified":true}', encoding="utf-8"
        )
        self.assertEqual(self.evaluate()["standing"], "REJECTED")

    def test_overdelete_current_consumer_is_rejected(self) -> None:
        self.remove_target()
        (self.workspace / "docs/OPERATOR.md").unlink()
        self.assertEqual(self.evaluate()["standing"], "REJECTED")

    def test_consumer_content_mutation_is_rejected(self) -> None:
        self.remove_target()
        (self.workspace / "evidence/consumed-fixture.json").write_text(
            '{"forged":"same filename"}\n', encoding="utf-8"
        )
        self.assertEqual(self.evaluate()["standing"], "REJECTED")

    def test_unrelated_new_source_is_rejected(self) -> None:
        self.remove_target()
        (self.workspace / "new-authority.md").write_text(
            "# duplicated current truth\n", encoding="utf-8"
        )
        self.assertEqual(self.evaluate()["standing"], "REJECTED")


    def test_missing_or_unreadable_workspace_is_unknown(self) -> None:
        missing = self.workspace / "does-not-exist"
        self.assertEqual(verifier.evaluate(missing)["standing"], "UNKNOWN")

    def test_symlink_in_candidate_cannot_launder_preservation(self) -> None:
        self.remove_target()
        protected = self.workspace / "docs/OPERATOR.md"
        protected.unlink()
        protected.symlink_to(FIXTURE / "docs/OPERATOR.md")
        self.assertEqual(self.evaluate()["standing"], "UNKNOWN")

    def test_exhaustive_fixture_deletion_subsets(self) -> None:
        """All 2^5 deletion subsets are checked at the real verifier boundary."""
        names = sorted(
            p.relative_to(FIXTURE).as_posix()
            for p in FIXTURE.rglob("*")
            if p.is_file()
        )
        self.assertEqual(len(names), 5)
        for trial in range(3):
            for removed_count in range(len(names) + 1):
                for removal in itertools.combinations(names, removed_count):
                    with self.subTest(trial=trial, removed=removal):
                        # Rebuild to keep every candidate independent.
                        shutil.rmtree(self.workspace)
                        shutil.copytree(FIXTURE, self.workspace)
                        for name in removal:
                            (self.workspace / name).unlink()
                        expected = "ACCEPTED" if set(removal) == TARGET else "REJECTED"
                        self.assertEqual(self.evaluate()["standing"], expected)

    def test_task_and_verifier_are_separate_from_candidate_fixture(self) -> None:
        task = json.loads((EVAL / "task.json").read_text(encoding="utf-8"))
        self.assertEqual(task["taskId"], "HARNESS-DOC-RETIREMENT-004")
        self.assertEqual(task["kind"], "ordivon.evaluation-task")
        self.assertFalse(VERIFIER.is_relative_to(FIXTURE))

        self.assertFalse((EVAL / "task.json").is_relative_to(FIXTURE))

    def test_task_matches_existing_track_r_shape_and_frozen_sources(self) -> None:
        task = json.loads((EVAL / "task.json").read_text(encoding="utf-8"))
        self.assertEqual(task["reproducibility"], {
            "cleanRebuildTrials": 3, "requiredAgreement": 3,
        })
        self.assertIsNone(task["expertTimeEstimateMinutes"])
        expected_initial = [
            {"path": path.relative_to(FIXTURE).as_posix(),
             "digest": "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()}
            for path in sorted(FIXTURE.rglob("*")) if path.is_file()
        ]
        encoded_initial = json.dumps(
            expected_initial, sort_keys=True, ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        self.assertEqual(
            task["initialState"]["environmentDigest"],
            "sha256:" + hashlib.sha256(encoded_initial).hexdigest(),
        )
        self.assertEqual(
            task["oracle"]["digest"],
            "sha256:" + hashlib.sha256(VERIFIER.read_bytes()).hexdigest(),
        )
        payload = dict(task)
        integrity = payload.pop("integrity")
        self.assertEqual(
            integrity,
            {"algorithm": "sha256", "canonicalization": "ordivon-canonical-json-v1",
             "payloadDigest": "sha256:" + hashlib.sha256(json.dumps(
                 payload, sort_keys=True, ensure_ascii=False,
                 separators=(",", ":"),
             ).encode("utf-8")).hexdigest()},
        )


if __name__ == "__main__":
    unittest.main()
