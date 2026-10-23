from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
import uuid
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/temporal_pgbackrest_restore_smoke.sh"


class RestoreSmokeFailedStopTests(unittest.TestCase):
    def test_failed_pg_ctl_stop_preserves_restored_pgdata_for_reconciliation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ordivon-restore-stub-", dir="/tmp") as temp:
            shim = Path(temp) / "sudo"
            shim.write_text(
                '#!/bin/sh\n'
                'case "$*" in\n'
                '  *pgbackrest*) printf "synthetic pid\\n" > "$RESTORE_ROOT/postmaster.pid"; exit 71;;\n'
                '  *pg_ctl*) exit 72;;\n'
                'esac\n'
                'exit 73\n', encoding="utf-8"
            )
            shim.chmod(0o755)
            # CI is non-root: only the simulated scratch owns these paths.
            # Mock chown rather than requiring a real postgres account/privilege.
            fake_chown = Path(temp) / "chown"
            fake_chown.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            fake_chown.chmod(0o755)
            identity = uuid.uuid4().hex
            data = Path(f"/tmp/ordivon-restore-stop-failure-{identity}-data")
            socket = Path(f"/tmp/ordivon-restore-stop-failure-{identity}-socket")
            log = Path(f"/tmp/ordivon-restore-stop-failure-{identity}.log")
            self.assertFalse(any(path.exists() for path in (data, socket, log)))
            env = {
                **os.environ,
                "PATH": f"{temp}:/usr/bin:/bin",
                "RESTORE_ROOT": str(data),
                "SOCKET_ROOT": str(socket),
                "LOG": str(log),
            }
            try:
                result = subprocess.run(
                    ["/bin/bash", str(SCRIPT), "fake-backup", "test-workflow", "55439"],
                    env=env, text=True, capture_output=True, timeout=10, check=False,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertTrue(data.is_dir(), "unknown stop outcome must retain restored PGDATA")
                self.assertTrue((data / "postmaster.pid").exists())
                self.assertIn("could not confirm isolated PostgreSQL stopped", result.stderr)
            finally:
                # Only the synthetic, non-running test carrier is removed by the test.
                for path in (data, socket):
                    if path.exists() and not path.is_symlink():
                        shutil.rmtree(path)
                log.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
