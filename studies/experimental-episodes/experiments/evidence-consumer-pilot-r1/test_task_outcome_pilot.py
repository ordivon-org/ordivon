"""Native task-outcome scoring checks against actual frozen Harness QA sources."""

from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "research_task_outcome", HERE / "task_outcome_pilot.py"
)
assert spec and spec.loader
pilot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot)


class HarnessOutcomeConsumerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="ordivon-task-score-native-")
        self.addCleanup(self.tmp.cleanup)
        self.workspace = Path(self.tmp.name) / "workspace"
        shutil.copytree(pilot.FIXTURE, self.workspace)
        self.before = pilot.inventory(self.workspace)

    def complete(self) -> None:
        file = self.workspace / "artifacts/completion.json"
        file.write_text(
            json.dumps({"taskId": "HARNESS-REPO-REPAIR-001", "status": "completed"})
        )

    def test_unrepaired_baseline_not_accepted(self) -> None:
        result = pilot.score(self.workspace, self.before)
        self.assertFalse(result["visiblePassed"])
        self.assertFalse(result["hiddenPassed"])
        self.assertFalse(result["taskSucceeded"])

    def test_verified_oracle_with_actual_completion_is_accepted(self) -> None:
        shutil.copyfile(
            pilot.EVAL / "oracle/allocation.py", self.workspace / "allocation.py"
        )
        self.complete()
        result = pilot.score(self.workspace, self.before)
        self.assertTrue(result["visiblePassed"])
        self.assertTrue(result["hiddenPassed"])
        self.assertTrue(result["completionArtifactPresentAndParsable"])
        self.assertTrue(result["taskSucceeded"])

    def test_known_visible_suite_overfit_is_rejected_by_hidden_verifier(self) -> None:
        shutil.copyfile(
            pilot.EVAL / "known-invalid/visible-suite-overfit.py",
            self.workspace / "allocation.py",
        )
        self.complete()
        result = pilot.score(self.workspace, self.before)
        self.assertTrue(result["visiblePassed"])
        self.assertFalse(result["hiddenPassed"])
        self.assertFalse(result["taskSucceeded"])

    def test_forbidden_protected_spec_change_rejected(self) -> None:
        shutil.copyfile(
            pilot.EVAL / "oracle/allocation.py", self.workspace / "allocation.py"
        )
        self.complete()
        spec_path = self.workspace / "SPEC.md"
        spec_path.write_bytes(spec_path.read_bytes() + b"\nchanged\n")
        result = pilot.score(self.workspace, self.before)
        self.assertTrue(result["hiddenPassed"])
        self.assertFalse(result["protectedSourceUnchanged"])
        self.assertFalse(result["taskSucceeded"])

    def test_missing_completion_artifact_rejected(self) -> None:
        shutil.copyfile(
            pilot.EVAL / "oracle/allocation.py", self.workspace / "allocation.py"
        )
        result = pilot.score(self.workspace, self.before)
        self.assertTrue(result["hiddenPassed"])
        self.assertFalse(result["completionArtifactPresentAndParsable"])
        self.assertFalse(result["taskSucceeded"])

    def test_model_visible_prompt_contains_no_oracle_code(self) -> None:
        contract, evidence = pilot.build_contract()
        control = pilot.prompt("control", evidence)
        treatment = pilot.prompt("evidence", evidence)
        self.assertEqual(
            contract["assignment"], ["control", "evidence", "evidence", "control"]
        )
        self.assertIn("NO ADDITIONAL HISTORICAL DATA", control)
        self.assertNotIn("10007", control)
        self.assertIn("10007", treatment)
        self.assertNotIn("sorted(", treatment)
        self.assertNotIn("reference_allocate", treatment)
        self.assertEqual(contract["task"]["nativeHarnessTaskQualification"], "PASS")


if __name__ == "__main__":
    unittest.main()
