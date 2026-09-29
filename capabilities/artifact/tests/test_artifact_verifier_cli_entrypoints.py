from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ArtifactVerifierCliEntrypointTests(unittest.TestCase):
    def test_claim_projection_verifiers_start_from_unrelated_cwd(self) -> None:
        scripts = [
            path
            for path in sorted((ROOT / "scripts").glob("artifact_*.py"))
            if "artifact_verification.claim_results" in path.read_text(encoding="utf-8")
        ]
        self.assertGreaterEqual(len(scripts), 1)
        with tempfile.TemporaryDirectory() as directory:
            cwd = Path(directory)
            failures: list[str] = []
            for script in scripts:
                result = subprocess.run(
                    [sys.executable, str(script), "--help"],
                    cwd=cwd,
                    text=True,
                    capture_output=True,
                    check=False,
                    timeout=30,
                )
                if result.returncode != 0:
                    failures.append(
                        f"{script.name}: rc={result.returncode} stderr={result.stderr[:500]!r}"
                    )
            self.assertEqual(failures, [], "\n".join(failures))


if __name__ == "__main__":
    unittest.main()
