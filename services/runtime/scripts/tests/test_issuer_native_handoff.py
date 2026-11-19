"""Opt-in real systemd proof: manager delivery outlives the launch caller.

This demonstrates an OS ordering counterexample, not a PostgreSQL/Harness
domain ACK or a crash-of-the-Rust-runtime reproduction. Never run against
production Units; this test uses only its own UUID-scoped transient names.
"""
from __future__ import annotations

import os
import subprocess
import tempfile
import time
import unittest
import uuid
from pathlib import Path


@unittest.skipUnless(
    os.environ.get("ORDIVON_RUN_NATIVE_ISSUER_HANDOFF_TEST") == "1",
    "requires explicit opt-in for disposable native systemd manager Units",
)
class OriginalNativeManagerHandoffTests(unittest.TestCase):
    def test_submitted_native_target_may_start_after_caller_exits(self) -> None:
        if os.geteuid() != 0:
            self.skipTest("requires root to start private systemd transient Units")
        identity = uuid.uuid4().hex[:12]
        barrier = f"ordivon-issuer-handoff-barrier-{identity}.service"
        target = f"ordivon-issuer-handoff-target-{identity}.service"
        with tempfile.TemporaryDirectory(
            prefix=f"ordivon-issuer-handoff-{identity}-", dir="/var/tmp"
        ) as scratch:
            release = Path(scratch, "release")
            marker = Path(scratch, "started")

            def systemctl(*args: str) -> subprocess.CompletedProcess[str]:
                return subprocess.run(
                    ["/usr/bin/systemctl", *args],
                    check=False, text=True, capture_output=True, timeout=10,
                )

            try:
                # One-shot barrier is *actively running* but not completed.
                # Consequently a second service After/Requires this barrier
                # has an authentic queued manager Job after systemd-run exits.
                started = subprocess.run(
                    [
                        "/usr/bin/systemd-run", "--no-block",
                        f"--unit={barrier}", "--property=Type=oneshot",
                        "--property=RemainAfterExit=yes",
                        "--property=TimeoutStartSec=20s",
                        "/usr/bin/bash", "-c",
                        'while test ! -f "$1"; do /usr/bin/sleep 0.05; done',
                        "issuer-handoff-barrier", str(release),
                    ],
                    check=False, text=True, capture_output=True, timeout=10,
                )
                self.assertEqual(started.returncode, 0, started.stderr)

                submitted = subprocess.run(
                    [
                        "/usr/bin/systemd-run", "--no-block",
                        f"--unit={target}", f"--property=After={barrier}",
                        f"--property=Requires={barrier}",
                        "/usr/bin/touch", str(marker),
                    ],
                    check=False, text=True, capture_output=True, timeout=10,
                )
                self.assertEqual(submitted.returncode, 0, submitted.stderr)

                # The process that submitted native launch has exited.
                # No target effect exists; systemd still owns a pending Job.
                deadline = time.monotonic() + 5
                manager_job = ""
                while time.monotonic() < deadline:
                    projection = systemctl("show", target, "--property=Job", "--value")
                    self.assertEqual(projection.returncode, 0, projection.stderr)
                    manager_job = projection.stdout.strip()
                    if manager_job:
                        break
                    time.sleep(0.05)
                self.assertTrue(manager_job, "native manager must own a queued Job")
                self.assertFalse(marker.exists(), "target started before its barrier")
                # Give the original submitter time to vanish while the OS
                # manager retains the accepted deferred launch. Never use
                # caller completion as evidence that the target was cancelled.
                time.sleep(0.25)
                self.assertFalse(marker.exists(), "manager ignored explicit barrier")

                release.touch()
                deadline = time.monotonic() + 10
                while not marker.exists() and time.monotonic() < deadline:
                    time.sleep(0.05)
                self.assertTrue(
                    marker.exists(),
                    "manager did not eventually start the target after the submitter exited",
                )
                print(
                    "ISSUER_NATIVE_SYSTEMD_DEFERRED_TARGET_AFTER_CALLER_EXIT_PASS "
                    f"queued_manager_job={manager_job}"
                )
            finally:
                # Exact test-owned UUID-scoped Units only, no wildcard stop
                # and no other Agent/Production service effects.
                # A single multi-Unit stop command can leave an active
                # dependency barrier behind. Stop each exact owned Unit, then
                # await native state readback; an accepted stop is not quiet.
                still_live: list[str] = []
                for unit in (target, barrier):
                    systemctl("stop", unit)
                    deadline = time.monotonic() + 5
                    state = "unknown"
                    while time.monotonic() < deadline:
                        settled = systemctl(
                            "show", unit, "--property=ActiveState", "--value",
                        )
                        state = settled.stdout.strip()
                        if state not in {"active", "activating"}:
                            break
                        time.sleep(0.05)
                    if state in {"active", "activating"}:
                        still_live.append(unit)
                systemctl("reset-failed", target, barrier)
                self.assertFalse(
                    still_live, f"test-owned transient Units still running: {still_live}",
                )


if __name__ == "__main__":
    unittest.main()
