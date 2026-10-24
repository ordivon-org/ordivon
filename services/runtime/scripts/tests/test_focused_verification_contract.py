from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import unittest

RUNTIME_ROOT = Path(__file__).resolve().parents[2]
TAXONOMY = RUNTIME_ROOT / "planning" / "test-taxonomy-r1.json"
POSITIVE_TEST = "public_requests_reject_unknown_fields_and_path_escape"
ZERO_MATCH_TEST = "ordivon_zero_match_probe_must_not_exist"


class FocusedVerificationContractTests(unittest.TestCase):
    def test_taxonomy_declares_fail_closed_focused_verifier(self) -> None:
        data = json.loads(TAXONOMY.read_text(encoding="utf-8"))
        contract = data["focusedVerification"]
        self.assertEqual(contract["id"], "R01-V1")
        self.assertEqual(contract["provider"], "cargo-nextest")
        self.assertEqual(contract["entrypoint"], "mise run test:focused")
        self.assertEqual(contract["selectorEnv"], "RUNTIME_TEST_EXPR")
        self.assertEqual(contract["zeroMatchStanding"], "FAIL_CLOSED")
        self.assertIn("matched(selector) >= 1", contract["formalObligation"])

    @staticmethod
    def run_focused(selector: str) -> subprocess.CompletedProcess[str]:
        env = {**os.environ, "RUNTIME_TEST_EXPR": f"test({selector})"}
        return subprocess.run(
            ["mise", "run", "test:focused"],
            cwd=RUNTIME_ROOT,
            env=env,
            text=True,
            capture_output=True,
            timeout=120,
            close_fds=False,
        )

    def test_real_focused_entrypoint_rejects_zero_matches(self) -> None:
        result = self.run_focused(ZERO_MATCH_TEST)
        combined = result.stdout + result.stderr
        self.assertNotEqual(result.returncode, 0, combined)
        self.assertIn("0 tests run", combined)
        self.assertIn("no tests to run", combined)

    def test_real_focused_entrypoint_runs_named_consumer(self) -> None:
        result = self.run_focused(POSITIVE_TEST)
        combined = result.stdout + result.stderr
        self.assertEqual(result.returncode, 0, combined)
        self.assertIn("1 test run", combined)
        self.assertIn(POSITIVE_TEST, combined)


if __name__ == "__main__":
    unittest.main()
