"""Single-claim Agent readout over the original Harness evidence authority."""

import importlib.util
import json
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

CHECKER = Path(__file__).resolve().parents[1] / "scripts/check_evidence.py"
spec = importlib.util.spec_from_file_location("harness_evidence_query_test", CHECKER)
assert spec and spec.loader
subject = importlib.util.module_from_spec(spec)
spec.loader.exec_module(subject)

HISTORICAL = "harness.runtime-correlation.h2"


class HarnessClaimReadTests(unittest.TestCase):
    def test_current_archive_is_explicitly_historical_only(self):
        result = subject.query_claim_currentness(HISTORICAL)
        self.assertEqual(result["standing"], "HISTORICAL_NOT_CURRENT")
        self.assertFalse(result["evidenceCurrent"])
        self.assertRegex(result["sourceCut"], r"^[a-f0-9]{40}$")
        self.assertTrue(result["receiptFile"].endswith(".json"))

    def test_missing_claim_stays_unknown_not_false_verified(self):
        result = subject.query_claim_currentness("missing.new.agent.claim")
        self.assertEqual(result["standing"], "UNREGISTERED_UNKNOWN")
        self.assertFalse(result["evidenceCurrent"])

    def test_invalid_input_does_not_trigger_fallback_replay(self):
        with self.assertRaisesRegex(ValueError, "single token"):
            subject.query_claim_currentness("agent claim with whitespace")

    def test_modified_evidence_index_cannot_issue_currentness(self):
        original = subject.subprocess.check_output

        def forged_index(command, **kwargs):
            if len(command) > 3 and command[1:3] == ["--no-replace-objects", "show"]:
                return b'{"not":"the index"}'
            return original(command, **kwargs)

        with patch.object(subject.subprocess, "check_output", side_effect=forged_index):
            with self.assertRaisesRegex(ValueError, "not exact Git HEAD"):
                subject.query_claim_currentness(HISTORICAL)

    def test_verified_requires_original_checker_not_caller_string(self):
        original = json.loads((subject.EVIDENCE / "index.json").read_text())
        mutant = deepcopy(original)
        for entry in mutant["entries"]:
            if entry.get("claimId") == HISTORICAL:
                entry["status"] = "verified"
                break
        for native_result, standing, trusted in [
            (1, "UNKNOWN_FAILED_NATIVE_CHECKER", False),
            (0, "VERIFIED_CURRENT_NATIVE_CHECKER", True),
        ]:
            with self.subTest(native_result=native_result):
                with (
                    patch.object(subject.json, "loads", return_value=mutant),
                    patch.object(subject, "main", return_value=native_result) as native,
                ):
                    result = subject.query_claim_currentness(HISTORICAL)
                    self.assertEqual(result["standing"], standing)
                    self.assertEqual(result["evidenceCurrent"], trusted)
                    native.assert_called_once()


if __name__ == "__main__":
    unittest.main()
