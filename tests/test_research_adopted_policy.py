from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OPA = Path("/usr/bin/opa")
PROFILE = ROOT / "policies" / "research-adopted-r1"


class ResearchAdoptedPolicyTests(unittest.TestCase):
    def test_opa_reference_profile_is_machine_enforceable(self) -> None:
        self.assertTrue(OPA.is_file(), "mature OPA evaluator is required by the current reference profile")
        completed = subprocess.run(
            [str(OPA), "test", str(PROFILE)],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_profile_does_not_define_a_research_to_permission_api(self) -> None:
        policy = (PROFILE / "policy.rego").read_text()
        self.assertNotIn("research_standing", policy)
        self.assertNotIn("human_approval", policy)
        self.assertIn("decision.status == \"adopted\"", policy)
        self.assertIn("input.delegation.decision == \"ALLOW\"", policy)


if __name__ == "__main__":
    unittest.main()
