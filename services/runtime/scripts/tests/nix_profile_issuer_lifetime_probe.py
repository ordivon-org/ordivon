"""Explicit native challenger for issuer death and pending Nix activation.

The existing PG release fixture owns intent and the isolated Nix store owns
bytes. No live deployment or generic generation ABI is introduced.
"""
from __future__ import annotations

import json
import os
import select
import signal
import subprocess
import sys
import time
import unittest

from nix_profile_generation_probe import NativeNixGenerationProbe, op


# Gate the actual native Nix command at an observable pre-exec cut.
# This is a test-only child, not another deployment controller.
CHILD = """
import os, pathlib, subprocess, sys, time
ready, gate, done, store, profile, target = sys.argv[1:]
pathlib.Path(ready).write_text(str(os.getpid()))
deadline = time.monotonic() + 15
while not pathlib.Path(gate).exists():
    if time.monotonic() >= deadline:
        raise SystemExit(97)
    time.sleep(.02)
subprocess.run(['/usr/bin/nix-env', '--store', store, '--profile', profile,
                '--set', target], check=True, timeout=10)
pathlib.Path(done).write_text('native-switch-complete')
"""


class NativeNixIssuerLifetimeProbe(NativeNixGenerationProbe):
    def pending_activation(self, *, child_owns_lock: bool) -> None:
        ready = self.nix_root / "child-ready"
        gate = self.nix_root / "allow-native-switch"
        done = self.nix_root / "child-done"
        child_args = [
            sys.executable, "-B", "-c", CHILD, str(ready), str(gate), str(done),
            self.store, str(self.profile), self.b,
        ]
        issuer = os.fork()
        if issuer == 0:
            try:
                with op.pg_connection(self.dsn, "fresh") as conn:
                    op.dispatch_claim(conn, self.args)
                if child_owns_lock:
                    child = subprocess.Popen(
                        ["/usr/bin/flock", "--exclusive", "--nonblock", "--no-fork",
                         str(self.args.lock_file), *child_args],
                        env=self.nix_env,
                    )
                    child.wait()
                else:
                    with op.DEPLOY["exclusive_lock"](self.args.lock_file):
                        child = subprocess.Popen(child_args, env=self.nix_env)
                        child.wait()
            except BaseException:
                os._exit(99)
            os._exit(98)

        issuer_reaped = False
        child_pidfd = None
        try:
            deadline = time.monotonic() + 12
            while not ready.exists() or not ready.read_text():
                if time.monotonic() >= deadline:
                    self.fail("native child did not reach pre-exec cut")
                time.sleep(.02)
            child_pid = int(ready.read_text())
            child_pidfd = os.pidfd_open(child_pid)
            poll = select.poll()
            poll.register(child_pidfd, select.POLLIN)
            self.assertFalse(poll.poll(0))
            self.assert_complete(self.a, "A")
            os.kill(issuer, signal.SIGKILL)
            _, status = os.waitpid(issuer, 0)
            issuer_reaped = True
            self.assertEqual(os.WTERMSIG(status), signal.SIGKILL)
            self.assertFalse(poll.poll(0), "child must genuinely outlive issuer")

            if child_owns_lock:
                with self.assertRaisesRegex(RuntimeError, "deployment lock is already held"):
                    with op.DEPLOY["exclusive_lock"](self.args.lock_file):
                        self.fail("a competing writer acquired the in-flight child fence")
                self.assert_complete(self.a, "A")
                gate.touch()
                self.assertTrue(poll.poll(12000), "child did not terminate")
                with op.DEPLOY["exclusive_lock"](self.args.lock_file):
                    self.assert_complete(self.b, "B")
            else:
                # The issuer-only lock disappeared with the issuer, even
                # though the native effect is still capable of being issued.
                with op.DEPLOY["exclusive_lock"](self.args.lock_file):
                    self.assert_complete(self.a, "A")
                    gate.touch()
                    self.assertTrue(poll.poll(12000), "child did not terminate")
                    self.assert_complete(self.b, "B")

            self.assertEqual(done.read_text(), "native-switch-complete")
            self.assertIsNone(self.db.execute(
                "SELECT resolution FROM jobs WHERE job_id=%s", (self.job_id,),
            ).fetchone()["resolution"])
            with op.pg_connection(self.dsn, "fresh") as conn:
                with self.assertRaisesRegex(RuntimeError, "dispatch was already committed"):
                    op.dispatch_claim(conn, self.args)
            print(json.dumps({
                "child_owned_native_lock": child_owns_lock,
                "issuer_sigkill": True, "child_survived": True,
                "competing_lock_before_terminal": not child_owns_lock,
                "native_effect_completed": True,
                "pg_resolution": None, "redispatch_blocked": True,
            }, sort_keys=True), flush=True)
        finally:
            gate.touch(exist_ok=True)
            if not issuer_reaped:
                try:
                    os.kill(issuer, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                os.waitpid(issuer, 0)
            if child_pidfd is not None:
                poll = select.poll()
                poll.register(child_pidfd, select.POLLIN)
                if not poll.poll(12000):
                    signal.pidfd_send_signal(child_pidfd, signal.SIGKILL)
                    poll.poll(3000)
                os.close(child_pidfd)

    def test_resolved_path_is_not_a_gc_root(self) -> None:
        # Merely resolving the current profile is not an acquisition.
        pinned = self.selected()[1]
        self.assertEqual(pinned, self.a)
        self.switch(self.b)
        self.nix("nix-env", "--profile", str(self.profile), "--delete-generations", "1")
        self.nix("nix-store", "--gc")
        self.assertFalse(self.physical(pinned).exists())
        root = self.nix_root / "too-late-reader-root"
        with self.assertRaises(subprocess.CalledProcessError):
            self.nix("nix-store", "--add-root", str(root), "--indirect", "--realise", pinned)
        self.assertFalse(self.physical(pinned).exists())
        self.assert_complete(self.b, "B")
        print("STALE_PATH_NOT_ROOT: old bytes collected; late native acquisition rejected",
              flush=True)

    def test_fenced_reader_root_precedes_generation_retirement(self) -> None:
        # A cooperating profile writer cannot switch/delete while the
        # reader selects the current store path and registers its root.
        root = self.nix_root / "fenced-reader-root"
        with op.DEPLOY["exclusive_lock"](self.args.lock_file):
            pinned = self.selected()[1]
            competing = subprocess.run(
                ["/usr/bin/flock", "--exclusive", "--nonblock",
                 str(self.args.lock_file), "/usr/bin/true"],
                capture_output=True, timeout=5,
            )
            self.assertEqual(competing.returncode, 1)
            self.nix("nix-store", "--add-root", str(root), "--indirect", "--realise", pinned)
            self.assertIn(str(root), self.nix("nix-store", "--gc", "--print-roots"))
        with op.DEPLOY["exclusive_lock"](self.args.lock_file):
            self.switch(self.b)
            self.nix("nix-env", "--profile", str(self.profile), "--delete-generations", "1")
        self.nix("nix-store", "--gc")
        self.assertEqual((self.physical(pinned) / "helper").read_text(), "A-helper")
        self.assert_complete(self.b, "B")
        root.unlink()
        self.nix("nix-store", "--gc")
        self.assertFalse(self.physical(pinned).exists())
        print("FENCED_ROOT_BEFORE_RETIREMENT: exact old bytes survived until release",
              flush=True)

    def test_issuer_only_lock_is_not_native_no_future_effect(self) -> None:
        self.pending_activation(child_owns_lock=False)

    def test_native_child_lock_survives_issuer_crash(self) -> None:
        self.pending_activation(child_owns_lock=True)


if __name__ == "__main__":
    names = (
        "test_issuer_only_lock_is_not_native_no_future_effect",
        "test_native_child_lock_survives_issuer_crash",
        "test_resolved_path_is_not_a_gc_root",
        "test_fenced_reader_root_precedes_generation_retirement",
    )
    suite = unittest.TestSuite(NativeNixIssuerLifetimeProbe(name) for name in names)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() and result.testsRun == len(names)
                     and not result.skipped else 1)
