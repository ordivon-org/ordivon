"""The current-tree scan covers tracked bytes, not mutable build artifacts."""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).with_name("check_tracked_secrets.sh")


class TrackedSecretsTests(unittest.TestCase):
    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.trace = self.root / "trace"
        (self.bin / "gitleaks").write_text(
            '#!/usr/bin/env bash\n'
            'printf "%s|%s\\n" "$PWD" "$*" >> "$GITLEAKS_TRACE"\n'
            'test -f tracked.txt || exit 7\n'
            'test ! -f untracked.txt || exit 8\n'
            'if [[ "${FAIL_SCAN:-}" == yes ]]; then exit 1; fi\n'
        )
        (self.bin / "gitleaks").chmod(0o755)
        (self.repo / "tools/repo").mkdir(parents=True)
        shutil.copyfile(SCRIPT, self.repo / "tools/repo/check_tracked_secrets.sh")
        (self.repo / "tracked.txt").write_text("tracked material\n")
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        subprocess.run(["git", "-C", str(self.repo), "add", "."], check=True)
        subprocess.run(
            ["git", "-C", str(self.repo), "-c", "user.name=Test",
             "-c", "user.email=test@local.invalid", "commit", "-qm", "base"], check=True
        )
        (self.repo / "untracked.txt").write_text("local-only environment\n")
        self.head = subprocess.check_output(
            ["git", "-C", str(self.repo), "rev-parse", "HEAD"], text=True
        ).strip()

    def run_check(self, *, sha: str | None = None, fail: bool = False) -> subprocess.CompletedProcess[str]:
        env = dict(os.environ)
        env.update({
            "PATH": str(self.bin) + os.pathsep + env.get("PATH", ""),
            "GITHUB_SHA": self.head if sha is None else sha,
            "GITLEAKS_TRACE": str(self.trace),
            "RUNNER_TEMP": str(self.root),
            "FAIL_SCAN": "yes" if fail else "no",
        })
        return subprocess.run(
            ["bash", str(self.repo / "tools/repo/check_tracked_secrets.sh")],
            cwd=self.repo, env=env, capture_output=True, text=True, check=False, timeout=15,
        )

    def test_scans_all_tracked_source_without_untracked_artifacts(self) -> None:
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(self.trace.read_text().splitlines()), 1)
        self.assertIn("dir --no-banner --redact=100 --timeout 120 .", self.trace.read_text())

    def test_mismatched_sha_refuses_evidence_before_scanning(self) -> None:
        result = self.run_check(sha="0" * 40)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SHA mismatch", result.stderr)
        self.assertFalse(self.trace.exists())

    def test_detected_secret_fails_closed(self) -> None:
        result = self.run_check(fail=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(len(self.trace.read_text().splitlines()), 1)


if __name__ == "__main__":
    unittest.main()
