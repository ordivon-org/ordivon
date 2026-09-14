from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest

REPO = Path(__file__).resolve().parents[1]
QA_PATH = REPO / "evals/harness-edit-multiregion-003/qa.py"
EVIDENCE_PATH = QA_PATH.parent / "evidence/r2-task-qa.json"
spec = importlib.util.spec_from_file_location("harness_edit_multiregion_qa", QA_PATH)
assert spec and spec.loader
qa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qa)


class HarnessEditMultiregion003Tests(unittest.TestCase):
    def test_task_definition_and_digests_validate(self) -> None:
        task = qa.validate_task()
        self.assertEqual(task["taskId"], "HARNESS-EDIT-MULTIREGION-003")
        self.assertEqual(task["family"], "edit_multiregion")
        self.assertEqual(task["integrity"]["payloadDigest"], qa.payload_digest(task))

    def test_qa_requires_both_regions_and_preserves_middle(self) -> None:
        result = qa.run_qa()
        self.assertTrue(result["passed"])
        self.assertEqual(result["agreement"], 3)
        self.assertEqual(result["outcomes"]["baseline"], (False, False))
        self.assertEqual(result["outcomes"]["oracle"], (True, True))
        self.assertEqual(result["outcomes"]["timeout-only"], (False, False))
        self.assertEqual(result["outcomes"]["retry-only"], (False, False))
        self.assertEqual(result["outcomes"]["collateral"], (True, False))

    def test_committed_qa_evidence_matches_current_gate(self) -> None:
        evidence = json.loads(EVIDENCE_PATH.read_text())
        current = json.loads(json.dumps(qa.run_qa()))
        self.assertEqual(evidence, current)
        self.assertEqual(evidence["integrity"]["payloadDigest"], qa.payload_digest(evidence))


if __name__ == "__main__":
    unittest.main()
