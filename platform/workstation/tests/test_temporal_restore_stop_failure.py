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


    def test_replaced_scratch_directory_is_not_reclaimed(self) -> None:
        """Path equality is not ownership of the current filesystem object."""
        with tempfile.TemporaryDirectory(prefix="ordivon-restore-swap-", dir="/tmp") as temp:
            base = Path(temp)
            shim = base / "sudo"
            shim.write_text(
                '#!/bin/sh\n'
                'case "$*" in\n'
                '  *pgbackrest*) mv "$RESTORE_ROOT" "$RESTORE_ROOT.original"; '
                'mkdir "$RESTORE_ROOT"; printf unrelated > "$RESTORE_ROOT/canary"; exit 71;;\n'
                'esac\nexit 73\n',
                encoding="utf-8",
            )
            shim.chmod(0o755)
            chown = base / "chown"
            chown.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            chown.chmod(0o755)
            identity = uuid.uuid4().hex
            data = Path(f"/tmp/ordivon-restore-swap-{identity}-data")
            original = Path(str(data) + ".original")
            socket = Path(f"/tmp/ordivon-restore-swap-{identity}-socket")
            log = Path(f"/tmp/ordivon-restore-swap-{identity}.log")
            env = {
                **os.environ, "PATH": f"{temp}:/usr/bin:/bin",
                "RESTORE_ROOT": str(data), "SOCKET_ROOT": str(socket), "LOG": str(log),
            }
            try:
                result = subprocess.run(
                    ["/bin/bash", str(SCRIPT), "fake-backup", "test-workflow", "55439"],
                    env=env, text=True, capture_output=True, timeout=10, check=False,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertTrue(original.is_dir())
                self.assertTrue((data / "canary").exists(), "must not reclaim a substituted object")
                self.assertEqual((data / "canary").read_text(), "unrelated")
                self.assertNotIn('"standing":"PASS"', result.stdout)
            finally:
                for path in (data, original, socket):
                    if path.exists() and not path.is_symlink():
                        shutil.rmtree(path)
                log.unlink(missing_ok=True)

    def test_start_attempt_without_pid_cannot_claim_release(self) -> None:
        """A missing PID file is not positive proof of stopped after start."""
        with tempfile.TemporaryDirectory(prefix="ordivon-stop-unknown-", dir="/tmp") as temp:
            base = Path(temp)
            shim = base / "sudo"
            shim.write_text(
                '#!/bin/sh\n'
                'case "$*" in\n'
                '  *pgbackrest*) touch "$RESTORE_ROOT/recovery.signal"; exit 0;;\n'
                '  *pg_ctl*start*) touch "$START_MARKER"; exit 0;;\n'
                '  *pg_ctl*stop*) exit 72;;\n'
                '  *psql*"select not pg_is_in_recovery"*) printf "t\\nt\\n"; exit 0;;\n'
                '  *psql*temporal_visibility*"schema_version"*) printf "t\\n1.14\\n"; exit 0;;\n'
                '  *psql*temporal_visibility*"executions_visibility"*) printf "t\\ntest-workflow|2\\n"; exit 0;;\n'
                '  *psql*temporal*"schema_version"*) printf "t\\n1.19\\n"; exit 0;;\n'
                'esac\nexit 73\n',
                encoding="utf-8",
            )
            shim.chmod(0o755)
            chown = base / "chown"
            chown.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            chown.chmod(0o755)
            identity = uuid.uuid4().hex
            data = Path(f"/tmp/ordivon-stop-unknown-{identity}-data")
            socket = Path(f"/tmp/ordivon-stop-unknown-{identity}-socket")
            log = Path(f"/tmp/ordivon-stop-unknown-{identity}.log")
            env = {
                **os.environ, "PATH": f"{temp}:/usr/bin:/bin",
                "RESTORE_ROOT": str(data), "SOCKET_ROOT": str(socket), "LOG": str(log),
                "START_MARKER": str(base / "started"),
            }
            try:
                result = subprocess.run(
                    ["/bin/bash", str(SCRIPT), "fake-backup", "test-workflow", "55439"],
                    env=env, text=True, capture_output=True, timeout=10, check=False,
                )
                self.assertTrue((base / "started").exists())
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertTrue(data.is_dir())
                self.assertTrue(socket.is_dir())
                self.assertTrue(log.is_file())
                self.assertNotIn('"standing":"PASS"', result.stdout)
            finally:
                for path in (data, socket):
                    if path.exists() and not path.is_symlink():
                        shutil.rmtree(path)
                log.unlink(missing_ok=True)

    def test_matching_payload_from_wrong_endpoint_cannot_verify_restore(self) -> None:
        """A matching result from a different connection is not restore evidence."""
        with tempfile.TemporaryDirectory(prefix="ordivon-restore-wrong-endpoint-", dir="/tmp") as temp:
            base = Path(temp)
            shim = base / "sudo"
            shim.write_text(
                '#!/bin/sh\n'
                'case "$*" in\n'
                '  *pgbackrest*) touch "$RESTORE_ROOT/recovery.signal"; exit 0;;\n'
                '  *pg_ctl*start*) printf "999999\\n%s\\n" "$RESTORE_ROOT" > "$RESTORE_ROOT/postmaster.pid"; exit 0;;\n'
                '  *pg_ctl*stop*) rm -f "$RESTORE_ROOT/postmaster.pid"; exit 0;;\n'
                '  *psql*)\n'
                '    case "$*" in *inet_server_addr*temporal_visibility*executions_visibility*|*temporal_visibility*inet_server_addr*executions_visibility*) printf "f\\n";; '
                '*inet_server_addr*) printf "t\\n";; esac\n'
                '    case "$*" in\n'
                '      *"select not pg_is_in_recovery"*) printf "t\\n";;\n'
                '      *temporal_visibility*"schema_version"*) printf "1.14\\n";;\n'
                '      *temporal_visibility*"executions_visibility"*) printf "test-workflow|2\\n";;\n'
                '      *temporal*"schema_version"*) printf "1.19\\n";;\n'
                '      *) exit 73;;\n'
                '    esac; exit 0;;\n'
                'esac\nexit 73\n',
                encoding="utf-8",
            )
            shim.chmod(0o755)
            chown = base / "chown"
            chown.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            chown.chmod(0o755)
            identity = uuid.uuid4().hex
            data = Path(f"/tmp/ordivon-restore-wrong-endpoint-{identity}-data")
            socket = Path(f"/tmp/ordivon-restore-wrong-endpoint-{identity}-socket")
            log = Path(f"/tmp/ordivon-restore-wrong-endpoint-{identity}.log")
            env = {
                **os.environ, "PATH": f"{temp}:/usr/bin:/bin",
                "RESTORE_ROOT": str(data), "SOCKET_ROOT": str(socket), "LOG": str(log),
            }
            try:
                result = subprocess.run(
                    ["/bin/bash", str(SCRIPT), "fake-backup", "test-workflow", "55439"],
                    env=env, text=True, capture_output=True, timeout=10, check=False,
                )
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertNotIn('"standing":"PASS"', result.stdout)
                self.assertFalse(data.exists(), "the qualified synthetic stop permits cleanup")
                self.assertFalse(socket.exists())
                self.assertFalse(log.exists())
            finally:
                for path in (data, socket):
                    if path.exists() and not path.is_symlink():
                        shutil.rmtree(path)
                log.unlink(missing_ok=True)

    def test_recovered_configuration_and_failed_stop_do_not_emit_pass(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ordivon-restore-fixture-", dir="/tmp") as temp:
            base = Path(temp)
            shim = base / "sudo"
            shim.write_text(
                '#!/bin/sh\n'
                'case "$*" in\n'
                '  *pgbackrest*)\n'
                '    printf "archive_command = bad\\n" > "$RESTORE_ROOT/postgresql.auto.conf"\n'
                '    touch "$RESTORE_ROOT/recovery.signal"; exit 0;;\n'
                '  *pg_ctl*start*)\n'
                '    printf "999999\\n%s\\n" "$RESTORE_ROOT" > "$RESTORE_ROOT/postmaster.pid"\n'
                '    touch "$FIXTURE_STARTED"; exit 0;;\n'
                '  *pg_ctl*stop*) touch "$FIXTURE_STOP"; exit 72;;\n'
                '  *psql*"select not pg_is_in_recovery"*) printf "t\\nt\\n"; exit 0;;\n'
                '  *psql*temporal_visibility*"schema_version"*) printf "t\\n1.14\\n"; exit 0;;\n'
                '  *psql*temporal_visibility*"executions_visibility"*) printf "t\\ntest-workflow|2\\n"; exit 0;;\n'
                '  *psql*temporal*"schema_version"*) printf "t\\n1.19\\n"; exit 0;;\n'
                'esac\nexit 73\n',
                encoding="utf-8",
            )
            shim.chmod(0o755)
            chown = base / "chown"
            chown.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            chown.chmod(0o755)
            identity = uuid.uuid4().hex
            data = Path(f"/var/tmp/ordivon-restore-fixture-{identity}-data")
            socket = Path(f"/var/tmp/ordivon-restore-fixture-{identity}-socket")
            log = Path(f"/var/tmp/ordivon-restore-fixture-{identity}.log")
            env = {
                **os.environ,
                "PATH": f"{temp}:/usr/bin:/bin",
                "RESTORE_ROOT": str(data),
                "SOCKET_ROOT": str(socket),
                "LOG": str(log),
                "FIXTURE_STARTED": str(base / "started"),
                "FIXTURE_STOP": str(base / "stop"),
            }
            try:
                result = subprocess.run(
                    ["/bin/bash", str(SCRIPT), "fake-backup", "test-workflow", "55439"],
                    env=env, text=True, capture_output=True, timeout=10, check=False,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertTrue((base / "started").exists(), result.stdout + result.stderr)
                self.assertTrue((base / "stop").exists(), result.stdout + result.stderr)
                self.assertNotIn('"standing":"PASS"', result.stdout)
                self.assertEqual((data / "postgresql.auto.conf").read_text(), "")
                config = (data / "ordivon-smoke.conf").read_text()
                self.assertIn("listen_addresses = ''", config)
                self.assertIn("archive_mode = off", config)
                self.assertIn("recovery_target_action = 'promote'", config)
                self.assertTrue((data / "postmaster.pid").exists())
            finally:
                for path in (data, socket):
                    if path.exists() and not path.is_symlink():
                        shutil.rmtree(path)
                log.unlink(missing_ok=True)



if __name__ == "__main__":
    unittest.main()
