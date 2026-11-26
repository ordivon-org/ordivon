"""Explicit Linux-only native Nix/PG qualification, not a production installer.

Uses the existing disposable PG release fixture, native Nix private store and
the existing operator lock. No shared Nix store, real unit or VPN is changed.
Run directly; the ordinary portable unittest lane does not collect this probe.
The PG release row here is only a dispatch/replay witness; it does not claim
that the existing Runtime release ABI supports Nix consumer activation.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import signal
import subprocess
import unittest

from test_pg_operator_release import NativePgReleaseOperator, op


class NativeNixGenerationProbe(NativePgReleaseOperator):
    def setUp(self) -> None:
        super().setUp()
        self.nix_root = self.work / "nix-probe"
        self.nix_root.mkdir()
        self.private = self.nix_root / "private"
        self.store = f"local?root={self.private}"
        self.profile = self.nix_root / "profile"
        self.home = self.nix_root / "home"
        self.home.mkdir()
        self.nix_env = {
            **os.environ,
            "HOME": str(self.home),
            "NIX_CONFIG": "experimental-features = nix-command\nsubstitute = false\n",
        }
        self.a = self.add_generation("A")
        self.b = self.add_generation("B")
        self.switch(self.a)

    def nix(self, binary: str, *args: str) -> str:
        return subprocess.run(
            [f"/usr/bin/{binary}", "--store", self.store, *args],
            env=self.nix_env, capture_output=True, text=True, check=True, timeout=30,
        ).stdout.strip()

    def add_generation(self, generation: str) -> str:
        root = self.nix_root / generation
        root.mkdir()
        for name in ("config", "helper"):
            (root / name).write_text(f"{generation}-{name}", encoding="utf-8")
        return self.nix("nix-store", "--add", str(root))

    def switch(self, path: str) -> None:
        self.nix("nix-env", "--profile", str(self.profile), "--set", path)

    def selected(self) -> tuple[str, str]:
        link = os.readlink(self.profile)
        return link, os.readlink(self.profile.parent / link)

    def physical(self, store_path: str) -> Path:
        return self.private / store_path.lstrip("/")

    def assert_complete(self, expected: str, generation: str) -> None:
        self.assertEqual(self.selected()[1], expected)
        for name in ("config", "helper"):
            self.assertEqual(
                (self.physical(expected) / name).read_text(), f"{generation}-{name}"
            )

    def test_native_pin_and_gc_lifecycle(self) -> None:
        root = self.nix_root / "reader-root"
        self.nix("nix-store", "--add-root", str(root), "--indirect", "--realise", self.a)
        pinned = self.physical(self.a)
        self.switch(self.b)
        self.nix("nix-env", "--profile", str(self.profile), "--delete-generations", "1")
        self.nix("nix-store", "--gc")
        self.assertEqual((pinned / "helper").read_text(), "A-helper")
        self.assert_complete(self.b, "B")
        root.unlink()
        self.nix("nix-store", "--gc")
        self.assertFalse(pinned.exists())
        self.assert_complete(self.b, "B")

    def test_native_pointer_is_not_a_monotonic_pg_revision(self) -> None:
        before = self.selected()
        self.switch(self.b)
        self.assertNotEqual(self.selected(), before)
        self.nix("nix-env", "--profile", str(self.profile), "--rollback")
        self.assertEqual(self.selected(), before)
        self.assert_complete(self.a, "A")
        print("ABA_WITNESS: native profile pointer returned to exact original link")

    def crash_cut(self, *, switched: bool) -> None:
        # The fixture's admitted PG effect is real, but the Nix action remains
        # an isolated consumer witness, not a released runtime service.
        pid = os.fork()
        if pid == 0:
            try:
                with op.DEPLOY["exclusive_lock"](self.args.lock_file):
                    with op.pg_connection(self.dsn, "fresh") as conn:
                        op.dispatch_claim(conn, self.args)
                    if switched:
                        self.switch(self.b)
                    os.kill(os.getpid(), signal.SIGKILL)
            except BaseException:
                os._exit(99)
            os._exit(98)
        _, status = os.waitpid(pid, 0)
        self.assertTrue(os.WIFSIGNALED(status))
        self.assertEqual(os.WTERMSIG(status), signal.SIGKILL)
        self.assert_complete(self.b if switched else self.a, "B" if switched else "A")
        self.assertFalse((self.args.receipt_root / f"effect-{self.args.effect_id}").exists())
        self.assertIsNone(self.db.execute(
            "SELECT resolution FROM jobs WHERE job_id=%s", (self.job_id,),
        ).fetchone()["resolution"])
        with op.pg_connection(self.dsn, "fresh") as conn:
            with self.assertRaisesRegex(RuntimeError, "dispatch was already committed"):
                op.dispatch_claim(conn, self.args)
        count = self.db.execute(
            "SELECT count(*) AS n FROM job_events WHERE job_id=%s AND event_type=%s",
            (self.job_id, op.DISPATCH_EVENT),
        ).fetchone()["n"]
        self.assertEqual(count, 1)
        print(json.dumps({
            "cut": "after_switch" if switched else "before_switch",
            "whole_generation": "B" if switched else "A",
            "terminal_receipt": False, "pg_resolution": None,
            "dispatch_count": count, "redispatch_blocked": True,
        }, sort_keys=True))

    def test_crash_before_profile_switch(self) -> None:
        self.crash_cut(switched=False)

    def test_crash_after_profile_switch(self) -> None:
        self.crash_cut(switched=True)


if __name__ == "__main__":
    names = (
        "test_native_pin_and_gc_lifecycle",
        "test_native_pointer_is_not_a_monotonic_pg_revision",
        "test_crash_before_profile_switch",
        "test_crash_after_profile_switch",
    )
    suite = unittest.TestSuite(NativeNixGenerationProbe(name) for name in names)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() and result.testsRun == len(names)
                     and not result.skipped else 1)
