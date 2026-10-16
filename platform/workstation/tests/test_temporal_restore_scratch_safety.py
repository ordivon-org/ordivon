from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/temporal_pgbackrest_restore_smoke.sh"


class RestoreSmokeScratchSafetyTests(unittest.TestCase):
    """All negative controls fail before touching a real backup or PGDATA."""

    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="ordivon-restore-guard-test-", dir="/tmp"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.canary = self.root / "KEEP-ME"
        self.canary.write_text("unrelated pre-existing bytes", encoding="utf-8")
        self.shim = self.root / "bin"
        self.shim.mkdir()
        self.rm_called = self.root / "rm-invoked"
        fake_rm = self.shim / "rm"
        fake_rm.write_text('#!/bin/sh\nprintf "called\\n" > "$RC_TEST_RM_MARKER"\nexit 86\n')
        fake_rm.chmod(0o755)
        self.socket = Path("/tmp/" + self.root.name + "-socket")
        self.log = Path("/tmp/" + self.root.name + ".log")

    def run_smoke(self, *, data: str | None = None, socket: str | None = None,
                  log: str | None = None, workflow: str = "fixture-workflow") -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env.update(
            RESTORE_ROOT=data if data is not None else str(self.root),
            SOCKET_ROOT=socket if socket is not None else str(self.socket),
            LOG=log if log is not None else str(self.log),
            RC_TEST_RM_MARKER=str(self.rm_called),
            PATH=f"{self.shim}:/usr/bin:/bin",
        )
        return subprocess.run(
            ["/bin/bash", str(SCRIPT), "nonexistent-fixture-backup", workflow, "55439"],
            text=True, capture_output=True, env=env, timeout=8, check=False,
        )

    def assert_preflight_refused(self, result: subprocess.CompletedProcess[str], reason: str) -> None:
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(reason, result.stdout + result.stderr)
        self.assertFalse(self.rm_called.exists(), "preflight must never enter destructive cleanup")
        self.assertEqual(self.canary.read_text(encoding="utf-8"), "unrelated pre-existing bytes")
        self.assertFalse(self.socket.exists())
        self.assertFalse(self.log.exists())

    def test_preexisting_restore_path_is_not_removed(self) -> None:
        self.assert_preflight_refused(self.run_smoke(), "already exists")

    def test_preexisting_log_path_is_not_overwritten(self) -> None:
        self.log.write_text("other log", encoding="utf-8")
        self.addCleanup(self.log.unlink, missing_ok=True)
        result = self.run_smoke(data="/tmp/" + self.root.name + "-not-created")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("already exists", result.stdout + result.stderr)
        self.assertFalse(self.rm_called.exists())
        self.assertEqual(self.log.read_text(), "other log")

    def test_unowned_path_outside_is_rejected(self) -> None:
        result = self.run_smoke(data="/var/lib/ordivon/production")
        self.assert_preflight_refused(result, "must be a direct /tmp scratch path")

    def test_untrusted_workflow_identifier_is_rejected_before_shell_sql(self) -> None:
        result = self.run_smoke(data="/tmp/" + self.root.name + "-not-created",
                                workflow="candidate' OR 1=1 --")
        self.assert_preflight_refused(result, "unsafe workflow id")


if __name__ == "__main__":
    unittest.main()
