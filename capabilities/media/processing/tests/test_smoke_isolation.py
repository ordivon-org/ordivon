"""Actual concurrent native smoke invocations must not delete each other's fixtures."""
from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class NativeSmokeIsolationTests(unittest.TestCase):
    def test_two_real_invocations_per_provider(self):
        with tempfile.TemporaryDirectory() as scratch:
            env = {**os.environ, "TMPDIR": scratch}
            sentinel = Path(scratch) / "unrelated"
            sentinel.write_text("preserve")
            for name in ("smoke", "audio-smoke", "timedtext-smoke", "otio-smoke"):
                with self.subTest(provider=name):
                    def invoke(_):
                        return subprocess.run(
                            ["bash", str(ROOT / "processing/tests" / f"{name}.sh")],
                            cwd=ROOT, env=env, capture_output=True, text=True, timeout=90,
                        )

                    with ThreadPoolExecutor(max_workers=2) as pool:
                        results = list(pool.map(invoke, range(2)))
                    for result in results:
                        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                        self.assertIn("PASS", result.stdout)
                    self.assertEqual(sentinel.read_text(), "preserve")
                    self.assertEqual(
                        list(Path(scratch).glob("ordivon-media-*")), [],
                        "test-owned directories must be removed on exit",
                    )
