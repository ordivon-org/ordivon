"""Real subprocess negative controls for the owner test result consumer."""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RUNNER = Path(__file__).resolve().parents[1] / "scripts/run-unittest.py"


class VerificationQualificationTests(unittest.TestCase):
    def test_actual_discovery_result_standing(self):
        for name, source, bounded, strict in (
            ("empty", "", 1, 1),
            ("pass", "    def test_one(self): self.assertTrue(True)\n", 0, 0),
            ("failure", "    def test_one(self): self.assertTrue(False)\n", 1, 1),
            ("error", "    def test_one(self): raise RuntimeError('fixture error')\n", 1, 1),
            ("skip", "    @unittest.skip('provider absent')\n    def test_one(self): pass\n", 0, 1),
            ("xfail", "    @unittest.expectedFailure\n    def test_one(self): self.fail()\n", 0, 1),
            ("unexpected_success", "    @unittest.expectedFailure\n    def test_one(self): pass\n", 1, 1),
        ):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                if source:
                    (root / "test_sample.py").write_text(
                        "import unittest\nclass Sample(unittest.TestCase):\n" + source, encoding="utf-8"
                    )
                env = dict(os.environ)
                env.pop("ORDIVON_MEDIA_STRICT_TESTS", None)
                for mode, flag, expected in (
                    ("bounded", [], bounded), ("strict", ["--strict"], strict),
                ):
                    run = subprocess.run(
                        [sys.executable, str(RUNNER), str(root), *flag],
                        env=env, capture_output=True, text=True, timeout=15,
                    )
                    self.assertEqual(run.returncode, expected, run.stdout + run.stderr)
                    self.assertIn(f"qualification={mode}", run.stdout)
                env["ORDIVON_MEDIA_STRICT_TESTS"] = "1"
                run = subprocess.run(
                    [sys.executable, str(RUNNER), str(root)],
                    env=env, capture_output=True, text=True, timeout=15,
                )
                self.assertEqual(run.returncode, strict, run.stdout + run.stderr)
                self.assertIn("qualification=strict", run.stdout)
