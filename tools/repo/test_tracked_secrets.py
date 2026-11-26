"""The current-tree scan covers tracked bytes, not mutable build artifacts."""
from __future__ import annotations

import os
import json
import random
import string
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tools.repo.triage_git_secret_scan import observe

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


class SecretTriageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        subprocess.run(["git", "-C", str(self.repo), "-c", "user.name=Test",
                        "-c", "user.email=test@local.invalid", "commit",
                        "--allow-empty", "-qm", "fixture"], check=True)
        self.head = subprocess.check_output(
            ["git", "-C", str(self.repo), "rev-parse", "HEAD"], text=True
        ).strip()
        self.row = {"RuleID": "fixture", "File": "fixture.txt",
                    "Commit": self.head, "StartLine": 1,
                    "Secret": "DO_NOT_EMIT", "Match": "DO_NOT_EMIT",
                    "Message": "DO_NOT_EMIT"}

    def scan(self, code, rows):
        def fake(args, **kwargs):
            self.assertEqual(args[:2], ["gitleaks", "git"])
            self.assertIn("--redact=100", args)
            self.assertIn("--exit-code", args)
            self.assertIn(f"--log-opts={self.head}", args)
            self.assertEqual(kwargs["stdout"], subprocess.DEVNULL)
            self.assertEqual(kwargs["stderr"], subprocess.DEVNULL)
            dest = Path(next(s.split("=", 1)[1] for s in args
                             if s.startswith("--report-path=")))
            if rows is not None:
                dest.write_text(json.dumps(rows), encoding="utf-8")
            return subprocess.CompletedProcess(args, code)
        with patch("tools.repo.triage_git_secret_scan.subprocess.run", side_effect=fake):
            # Resolve the actual Git cut outside the patched scanner path.
            def git_result(args, **kwargs):
                if "--show-toplevel" in args:
                    return str(self.repo) + "\n"
                if "--is-shallow-repository" in args:
                    return "false\n"
                if "status" in args:
                    return ""
                return self.head + "\n"
            with patch("tools.repo.triage_git_secret_scan.subprocess.check_output",
                       side_effect=git_result):
                return observe(self.repo, self.head)

    def test_findings_projection_does_not_emit_secret(self):
        code, result = self.scan(17, [self.row])
        self.assertEqual((code, result["status"]), (1, "findings"))
        self.assertEqual(result["findings"], [{"rule": "fixture",
            "file": "fixture.txt", "commit": self.head, "line": 1}])
        self.assertNotIn("DO_NOT_EMIT", json.dumps(result))

    def test_clean_requires_native_success_and_empty_report(self):
        self.assertEqual(self.scan(0, [])[0], 0)
        for code, rows in [(0, [self.row]), (17, []), (2, []),
                           (0, None), (17, [{}]), (0, {})]:
            self.assertEqual(self.scan(code, rows)[0], 2)

    def test_native_gitleaks_clean_and_synthetic_finding(self):
        code, result = observe(self.repo, self.head)
        self.assertEqual((code, result["status"]), (0, "clean"))
        # Deliberately synthetic, generated only in the disposable Git repository.
        rng = random.Random(72)
        value = "gh" + "p_" + "".join(
            rng.choices(string.ascii_letters + string.digits, k=36)
        )
        (self.repo / "synthetic.txt").write_text("fixture = " + value + "\n")
        subprocess.run(["git", "-C", str(self.repo), "add", "synthetic.txt"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "-c", "user.name=Test",
                        "-c", "user.email=test@local.invalid", "commit",
                        "-qm", "synthetic"], check=True)
        head = subprocess.check_output(
            ["git", "-C", str(self.repo), "rev-parse", "HEAD"], text=True
        ).strip()
        code, result = observe(self.repo, head)
        self.assertEqual((code, result["status"]), (1, "findings"))
        self.assertTrue(any(row["file"] == "synthetic.txt" and row["commit"] == head
                            for row in result["findings"]))
        self.assertNotIn(value, json.dumps(result))
        self.assertTrue(all(set(row) == {"rule", "file", "commit", "line"}
                            for row in result["findings"]))

    def test_checkout_policy_drift_is_unknown(self):
        (self.repo / ".gitleaksignore").write_text("local policy\n")
        self.assertEqual(observe(self.repo, self.head)[0], 2)
        (self.repo / ".gitleaksignore").unlink()
        subprocess.run(["git", "-C", str(self.repo), "-c", "user.name=Test",
                        "-c", "user.email=test@local.invalid", "commit",
                        "--allow-empty", "-qm", "later"], check=True)
        self.assertEqual(observe(self.repo, self.head)[0], 2)

    def test_unknown_commit_and_symbolic_ref_fail_before_scan(self):
        for rev in ("HEAD", "0" * 40):
            self.assertEqual(observe(self.repo, rev)[0], 2)


if __name__ == "__main__":
    unittest.main()
