"""Exercise the actual isolated PG shell entrypoint without a database or build."""
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "crates/harness-pg/tests/run_isolated_pg18.sh"

STUB = """import os, sys
from pathlib import Path
name = Path(sys.argv[0]).name
root = Path(os.environ["FIXTURE_ROOT"])
trace = Path(os.environ["FIXTURE_TRACE"])
mode = os.environ["FIXTURE_MODE"]
args = sys.argv[1:]
if name == "id":
    print(0)
elif name == "mktemp":
    root.mkdir()
    print(root)
elif name == "runuser":
    cmd = args[args.index("--") + 1:]
    os.execvp(cmd[0], cmd)
elif name == "initdb":
    (root / "data").mkdir()
    if mode == "init_failure":
        sys.exit(19)
elif name == "pg_ctl":
    action = args[-1]
    with trace.open("a") as stream:
        print(action, file=stream)
    marker = root / "running"
    if action == "start":
        marker.touch()
        if mode == "start_signal":
            import time
            (root / "start_ready").touch()
            time.sleep(30)
        if mode == "start_failure":
            sys.exit(17)
    elif action == "status":
        if mode == "status_unknown":
            sys.exit(4)
        sys.exit(0 if marker.exists() else 3)
    elif action == "stop":
        if mode == "stop_failure":
            sys.exit(1)
        if mode != "stop_not_confirmed":
            marker.unlink()
    else:
        sys.exit(99)
elif name == "psql":
    sys.exit(23)
elif name == "chown":
    if mode == "setup_failure":
        sys.exit(29)
elif name in {"cargo", "uv"}:
    sys.exit(98)
else:
    sys.exit(97)
"""


@unittest.skipUnless(os.name == "posix" and shutil.which("bash"), "requires Bash")
class IsolatedPGFixtureCleanupTests(unittest.TestCase):
    def run_fixture(self, mode, interrupt=None):
        with tempfile.TemporaryDirectory() as scratch:
            scratch = Path(scratch)
            root = scratch / "owned-cluster"
            trace = scratch / "trace"
            bin_dir = scratch / "bin"
            bin_dir.mkdir()
            for name in ("id", "mktemp", "runuser", "initdb", "pg_ctl", "psql", "chown", "cargo", "uv"):
                command = bin_dir / name
                command.write_text(f"#!{sys.executable}\n{STUB}")
                command.chmod(0o700)
            env = dict(os.environ, PATH=f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
                       FIXTURE_ROOT=str(root), FIXTURE_TRACE=str(trace), FIXTURE_MODE=mode)
            if interrupt is None:
                result = subprocess.run(["bash", str(SCRIPT)], env=env, capture_output=True, text=True, timeout=15)
                code, stderr = result.returncode, result.stderr
            else:
                with subprocess.Popen(["bash", str(SCRIPT)], env=env, stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE, text=True, start_new_session=True) as proc:
                    try:
                        deadline = time.monotonic() + 5
                        while not (root / "start_ready").exists() and proc.poll() is None and time.monotonic() < deadline:
                            time.sleep(0.02)
                        self.assertTrue((root / "start_ready").exists(), "fixture did not start")
                        os.killpg(proc.pid, interrupt)
                        _, stderr = proc.communicate(timeout=8)
                        code = proc.returncode
                    finally:
                        if proc.poll() is None:
                            os.killpg(proc.pid, signal.SIGKILL)
                            proc.communicate(timeout=5)
            return code, root.exists(), trace.read_text().splitlines() if trace.exists() else [], stderr

    def test_confirmed_stop_reclaims_owned_fixture(self):
        code, retained, trace, _ = self.run_fixture("normal")
        self.assertEqual(code, 23)
        self.assertFalse(retained)
        self.assertIn("stop", trace)

    def test_stop_failure_retains_evidence(self):
        code, retained, trace, stderr = self.run_fixture("stop_failure")
        self.assertNotEqual(code, 0)
        self.assertTrue(retained)
        self.assertIn("stop", trace)
        self.assertIn("preserving", stderr)

    def test_failed_start_still_stops_owned_process(self):
        code, retained, trace, _ = self.run_fixture("start_failure")
        self.assertEqual(code, 17)
        self.assertFalse(retained)
        self.assertIn("stop", trace)

    def test_uncertain_status_or_stop_retains_fixture(self):
        for mode in ("status_unknown", "stop_not_confirmed"):
            with self.subTest(mode=mode):
                code, retained, _, stderr = self.run_fixture(mode)
                self.assertNotEqual(code, 0)
                self.assertTrue(retained)
                self.assertIn("preserving", stderr)

    def test_prestart_failure_reclaims_owned_fixture(self):
        for mode in ("init_failure", "setup_failure"):
            with self.subTest(mode=mode):
                code, retained, trace, _ = self.run_fixture(mode)
                self.assertNotEqual(code, 0)
                self.assertFalse(retained)
                self.assertEqual(trace, [])


    def test_interrupted_start_still_stops_owned_process(self):
        for interrupt in (signal.SIGTERM, signal.SIGINT):
            with self.subTest(interrupt=interrupt):
                code, retained, trace, _ = self.run_fixture("start_signal", interrupt)
                self.assertIn(code, (-interrupt, 128 + interrupt))
                self.assertFalse(retained)
                self.assertEqual(trace, ["start", "status", "stop", "status"])
