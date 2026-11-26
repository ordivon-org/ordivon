"""Opt-in native systemd Manager job protocol evidence for OriginalRun revoke.

A deferred systemd manager Job outlives its submitting process; cancelling
that *exact queued Job* before the dependency clears prevents its target
start. This is NOT proof that a crashed caller cannot submit a different
future Job or that HarnessPG has authenticated a full NoFutureSpawn ACK.
Never run against production Units or without the explicit test switch.

Optional exact JobRemoved witness uses installed Gio/GLib and a private
system-bus connection. From services/runtime:
    ORDIVON_RUN_NATIVE_ISSUER_HANDOFF_TEST=1 ORDIVON_RUN_NATIVE_DBUS_WITNESS_TEST=1 /usr/bin/python3 -m unittest -v scripts.tests.test_issuer_native_handoff
The observer-loss counterexample has an independent witness for the lost
event and a positive new event after reconnect. Signals are not durable
replay receipts; absence never proves original native or Domain closure.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import time
import unittest
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


def systemctl(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["/usr/bin/systemctl", *args],
        check=False,
        text=True,
        capture_output=True,
        timeout=10,
    )


@unittest.skipUnless(
    os.environ.get("ORDIVON_RUN_NATIVE_ISSUER_HANDOFF_TEST") == "1",
    "requires explicit opt-in for disposable native systemd Manager Units",
)
class OriginalNativeManagerHandoffTests(unittest.TestCase):
    @contextmanager
    def deferred_native_launch(self) -> Iterator[tuple[Path, Path, str, str]]:
        identity = uuid.uuid4().hex[:12]
        barrier = f"ordivon-issuer-handoff-barrier-{identity}.service"
        target = f"ordivon-issuer-handoff-target-{identity}.service"
        with tempfile.TemporaryDirectory(prefix=f"ordivon-issuer-handoff-{identity}-", dir="/var/tmp") as scratch:
            release = Path(scratch, "release")
            marker = Path(scratch, "started")
            try:
                # Both systemd-run submitting processes return while the
                # manager owns a pending start that cannot pass the barrier.
                started = subprocess.run(
                    [
                        "/usr/bin/systemd-run",
                        "--no-block",
                        f"--unit={barrier}",
                        "--property=Type=oneshot",
                        "--property=RemainAfterExit=yes",
                        "--property=TimeoutStartSec=20s",
                        "/usr/bin/bash",
                        "-c",
                        'while test ! -f "$1"; do /usr/bin/sleep 0.05; done',
                        "issuer-handoff-barrier",
                        str(release),
                    ],
                    check=False,
                    text=True,
                    capture_output=True,
                    timeout=10,
                )
                self.assertEqual(started.returncode, 0, started.stderr)
                submitted = subprocess.run(
                    [
                        "/usr/bin/systemd-run",
                        "--no-block",
                        f"--unit={target}",
                        f"--property=After={barrier}",
                        f"--property=Requires={barrier}",
                        "/usr/bin/touch",
                        str(marker),
                    ],
                    check=False,
                    text=True,
                    capture_output=True,
                    timeout=10,
                )
                self.assertEqual(submitted.returncode, 0, submitted.stderr)

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
                self.assertTrue(
                    manager_job.isdecimal(),
                    f"native Job must have a concrete Manager identity: {manager_job}",
                )
                self.assertFalse(marker.exists(), "target started before its barrier")
                yield release, marker, manager_job, target
            finally:
                # Never use --no-block stop here. A queued multi-unit stop
                # previously left an actual test-owned RemainAfterExit barrier.
                still_live: list[str] = []
                for unit in (target, barrier):
                    systemctl("stop", unit)
                    deadline = time.monotonic() + 5
                    state = "unknown"
                    while time.monotonic() < deadline:
                        settled = systemctl("show", unit, "--property=ActiveState", "--value")
                        state = settled.stdout.strip()
                        if state not in {"active", "activating"}:
                            break
                        time.sleep(0.05)
                    if state in {"active", "activating"}:
                        still_live.append(unit)
                systemctl("reset-failed", target, barrier)
                self.assertFalse(still_live, f"test-owned transient Units still running: {still_live}")

    def test_submitted_native_target_may_start_after_caller_exits(self) -> None:
        if os.geteuid() != 0:
            self.skipTest("requires root to start private systemd transient Units")
        with self.deferred_native_launch() as (release, marker, manager_job, _):
            time.sleep(0.25)
            self.assertFalse(marker.exists(), "manager ignored dependency barrier")
            release.touch()
            deadline = time.monotonic() + 10
            while not marker.exists() and time.monotonic() < deadline:
                time.sleep(0.05)
            self.assertTrue(marker.exists(), "manager did not start target after caller exit")
            print(f"ISSUER_NATIVE_SYSTEMD_DEFERRED_TARGET_AFTER_CALLER_EXIT_PASS queued_manager_job={manager_job}")

    def test_cancel_exact_pending_manager_job_prevents_its_late_target(self) -> None:
        if os.geteuid() != 0:
            self.skipTest("requires root to cancel private systemd transient Job")
        with self.deferred_native_launch() as (release, marker, manager_job, target):
            cancelled = systemctl("cancel", manager_job)
            self.assertEqual(
                cancelled.returncode,
                0,
                f"exact queued Manager Job cancellation failed: {cancelled.stderr}",
            )
            # Cancellation request returned; verify the exact OS manager
            # Job is now gone BEFORE releasing the start dependency.
            deadline = time.monotonic() + 5
            queued = manager_job
            while time.monotonic() < deadline:
                projection = systemctl("show", target, "--property=Job", "--value")
                self.assertEqual(projection.returncode, 0, projection.stderr)
                queued = projection.stdout.strip()
                if not queued:
                    break
                time.sleep(0.05)
            self.assertFalse(queued, "native manager still holds a queued target start after cancel")
            self.assertFalse(marker.exists(), "target started before cancelling Job")

            release.touch()
            # Negative physical effect: an old queued Manager Job must not
            # start the target after its dependency completes. This does not
            # guard against new/foreign StartUnit calls after this observation.
            time.sleep(0.8)
            self.assertFalse(marker.exists(), "cancelled exact systemd Job started a late target")
            projection = systemctl(
                "show",
                target,
                "--property=ActiveState,Job,MainPID,ControlGroup",
            )
            self.assertEqual(projection.returncode, 0, projection.stderr)
            props = dict(line.split("=", 1) for line in projection.stdout.splitlines() if "=" in line)
            self.assertEqual(props.get("Job"), "", props)
            self.assertEqual(props.get("MainPID"), "0", props)
            self.assertNotIn(props.get("ActiveState"), {"active", "activating"})
            print(
                f"ISSUER_NATIVE_SYSTEMD_EXACT_QUEUED_JOB_CANCEL_NO_LATE_START_PASS cancelled_manager_job={manager_job}"
            )

    def test_cancel_one_exact_job_does_not_cancel_another_owned_start(self) -> None:
        if os.geteuid() != 0:
            self.skipTest("requires root to control private systemd transient Jobs")
        # Different native Manager identities must not become a wildcard stop
        # or a fabricated all-Attempt ACK. Both test owners are UUID-scoped.
        with self.deferred_native_launch() as first:
            with self.deferred_native_launch() as second:
                first_release, first_marker, first_job, _ = first
                second_release, second_marker, second_job, _ = second
                self.assertNotEqual(first_job, second_job)
                cancelled = systemctl("cancel", first_job)
                self.assertEqual(cancelled.returncode, 0, cancelled.stderr)
                first_release.touch()
                second_release.touch()
                deadline = time.monotonic() + 7
                while not second_marker.exists() and time.monotonic() < deadline:
                    time.sleep(0.05)
                self.assertTrue(
                    second_marker.exists(),
                    "cancelling first native Job wrongly stopped unrelated queued start",
                )
                # A successful independent target is not enough: leave a
                # bounded late-start window for the cancelled original
                # Manager Job, then read its exact identity and PID again.
                time.sleep(0.6)
                self.assertFalse(first_marker.exists(), "cancelled original native Job still executed")
                first_status = systemctl("show", first[3], "--property=ActiveState,Job,MainPID")
                self.assertEqual(first_status.returncode, 0, first_status.stderr)
                properties = dict(line.split("=", 1) for line in first_status.stdout.splitlines() if "=" in line)
                self.assertEqual(properties.get("Job"), "", properties)
                self.assertEqual(properties.get("MainPID"), "0", properties)
                self.assertNotIn(properties.get("ActiveState"), {"active", "activating"})
                print(
                    "ISSUER_NATIVE_MANAGER_CANCEL_EXACT_JOB_DOES_NOT_STOP_OTHER_PASS "
                    f"cancelled={first_job} other={second_job}"
                )


    def test_cancel_manager_job_is_not_a_running_unit_drain_witness(self) -> None:
        """Scope: native counterexample qualification, not a product cancel API.

        The Manager permits cancelling a start Job without undoing its
        already-executing operation. A future provider that actually stops
        this Unit must be requalified; no missing witness is a safety proof.
        """
        if os.geteuid() != 0:
            self.skipTest("requires root to control private systemd transient Units")
        identity = uuid.uuid4().hex[:12]
        unit = f"ordivon-issuer-handoff-active-{identity}.service"
        with tempfile.TemporaryDirectory(
            prefix=f"ordivon-issuer-active-{identity}-", dir="/var/tmp"
        ) as scratch:
            started = Path(scratch, "started")
            release = Path(scratch, "release")
            completed = Path(scratch, "completed")

            def properties() -> dict[str, str]:
                result = systemctl(
                    "show", unit, "--property=Job,ActiveState,SubState,MainPID,InvocationID,ControlGroup"
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                return dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)

            try:
                submitted = subprocess.run(
                    [
                        "/usr/bin/systemd-run", "--no-block", f"--unit={unit}",
                        "--property=Type=oneshot", "--property=RemainAfterExit=yes",
                        "--property=TimeoutStartSec=20s", "--property=KillMode=control-group",
                        "/usr/bin/bash", "-c",
                        'printf started > "$1/started"; '
                        'while test ! -f "$1/release"; do /usr/bin/sleep 0.05; done; '
                        'printf completed > "$1/completed"',
                        "issuer-handoff-active", scratch,
                    ],
                    check=False, text=True, capture_output=True, timeout=10,
                )
                self.assertEqual(submitted.returncode, 0, submitted.stderr)
                deadline = time.monotonic() + 5
                while not started.exists() and time.monotonic() < deadline:
                    time.sleep(0.05)
                self.assertTrue(started.exists(), "actual operation must have started")
                self.assertFalse(completed.exists())
                before = properties()
                manager_job = before.get("Job", "")
                self.assertTrue(manager_job.isdecimal(), before)
                self.assertEqual(before.get("ActiveState"), "activating", before)
                self.assertGreater(int(before.get("MainPID", "0")), 0, before)
                self.assertTrue(before.get("InvocationID"), before)
                self.assertTrue(before.get("ControlGroup"), before)

                cancelled = systemctl("cancel", manager_job)
                self.assertEqual(cancelled.returncode, 0, cancelled.stderr)
                deadline = time.monotonic() + 5
                after = properties()
                while after.get("Job") and time.monotonic() < deadline:
                    time.sleep(0.05)
                    after = properties()
                self.assertEqual(after.get("Job"), "", after)
                # The native Job identity is gone, but this exact original
                # invocation and process still own the executing operation.
                self.assertEqual(after.get("ActiveState"), "activating", after)
                for key in ("InvocationID", "MainPID", "ControlGroup"):
                    self.assertEqual(after.get(key), before.get(key), after)
                self.assertFalse(completed.exists())
                release.touch()
                deadline = time.monotonic() + 5
                while not completed.exists() and time.monotonic() < deadline:
                    time.sleep(0.05)
                self.assertEqual(completed.read_text(), "completed")
                print(
                    "ISSUER_NATIVE_MANAGER_CANCEL_NOT_DRAIN_COUNTEREXAMPLE_PASS "
                    f"cancelled_manager_job={manager_job} original_pid={before['MainPID']}"
                )
            finally:
                # This is a separate real StopUnit effect, not CancelJob.
                systemctl("stop", unit)
                deadline = time.monotonic() + 5
                after_stop = properties()
                while after_stop.get("ActiveState") not in {"inactive", "failed"} and time.monotonic() < deadline:
                    time.sleep(0.05)
                    after_stop = properties()
                systemctl("reset-failed", unit)
                self.assertIn(after_stop.get("ActiveState"), {"inactive", "failed"}, after_stop)
                self.assertEqual(after_stop.get("MainPID"), "0", after_stop)
                self.assertEqual(after_stop.get("Job"), "", after_stop)


    @contextmanager
    def manager_job_removed_subscription(self, previously_owned_units=()):
        """Use the existing mature GLib D-Bus client; one private connection.

        A new connection is deliberately used rather than a cached shared
        bus connection so observer loss and reconnect are actual OS effects.
        Only test-owned UUID-scoped target signal identities are retained.
        """
        import gi
        gi.require_version("Gio", "2.0")
        from gi.repository import Gio, GLib

        address = Gio.dbus_address_get_for_bus_sync(Gio.BusType.SYSTEM, None)
        connection = Gio.DBusConnection.new_for_address_sync(
            address,
            Gio.DBusConnectionFlags.AUTHENTICATION_CLIENT
            | Gio.DBusConnectionFlags.MESSAGE_BUS_CONNECTION,
            None,
            None,
        )
        connection.set_exit_on_close(False)
        manager = "org.freedesktop.systemd1"
        manager_path = "/org/freedesktop/systemd1"
        interface = f"{manager}.Manager"
        events = []
        owned_units = set(previously_owned_units)

        def signal(_connection, _sender, _path, _interface, _signal, parameters):
            job_id, job_path, unit, result = parameters.unpack()
            # Never retain another caller's native manager records.
            if unit in owned_units:
                events.append((job_id, job_path, unit, result))

        handler = connection.signal_subscribe(
            manager, interface, "JobRemoved", manager_path, None,
            Gio.DBusSignalFlags.NONE, signal,
        )

        def call(method, args=None):
            return connection.call_sync(
                manager, manager_path, interface, method, args, None,
                Gio.DBusCallFlags.NONE, 5000, None,
            )

        def job_path(job_id, unit):
            # The deferred fixture still holds its dependency, so register
            # this exact UUID-scoped target before cancellation or release.
            result = call("GetJob", GLib.Variant("(u)", (int(job_id),))).unpack()[0]
            owned_units.add(unit)
            return result

        def drain():
            context = GLib.MainContext.default()
            while context.pending():
                context.iteration(False)

        try:
            # Subscribe BEFORE any target submission. GetJob returns the
            # exact existing native object, not a guessed path.
            call("Subscribe")
            yield connection, events, job_path, drain
        finally:
            if not connection.is_closed():
                connection.signal_unsubscribe(handler)
                call("Unsubscribe")
                connection.close_sync(None)

    def wait_manager_job_removed(self, events, drain, expected):
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            drain()
            matching = [event for event in events if event[:3] == expected[:3]]
            if matching:
                self.assertEqual(matching, [expected])
                return
            time.sleep(0.02)
        self.fail(f"did not observe exact test-owned Manager JobRemoved: {expected}")

    @unittest.skipUnless(
        os.environ.get("ORDIVON_RUN_NATIVE_DBUS_WITNESS_TEST") == "1",
        "explicit Gio/GLib system D-Bus witness opt-in",
    )
    def test_job_removed_correlates_exact_cancelled_and_completed_manager_jobs(self):
        if os.geteuid() != 0:
            self.skipTest("requires root to control private systemd transient Jobs")
        with self.manager_job_removed_subscription() as (_, events, path, drain):
            with self.deferred_native_launch() as first:
                with self.deferred_native_launch() as second:
                    first_release, first_marker, first_job, first_unit = first
                    second_release, second_marker, second_job, second_unit = second
                    first_identity = (int(first_job), path(first_job, first_unit), first_unit)
                    second_identity = (int(second_job), path(second_job, second_unit), second_unit)
                    self.assertNotEqual(first_identity, second_identity)
                    cancelled = systemctl("cancel", first_job)
                    self.assertEqual(cancelled.returncode, 0, cancelled.stderr)
                    self.wait_manager_job_removed(events, drain, (*first_identity, "canceled"))
                    self.assertFalse(first_marker.exists())
                    first_release.touch()
                    second_release.touch()
                    self.wait_manager_job_removed(events, drain, (*second_identity, "done"))
                    deadline = time.monotonic() + 5
                    while not second_marker.exists() and time.monotonic() < deadline:
                        time.sleep(0.02)
                    self.assertTrue(second_marker.exists(), "completed native target must run")
                    self.assertFalse(first_marker.exists(), "cancelled original target must not run")
                    print(
                        "ISSUER_NATIVE_DBUS_EXACT_JOB_REMOVED_PASS "
                        f"cancelled={first_identity} completed={second_identity}"
                    )

    @unittest.skipUnless(
        os.environ.get("ORDIVON_RUN_NATIVE_DBUS_WITNESS_TEST") == "1",
        "explicit Gio/GLib system D-Bus witness opt-in",
    )
    def test_job_removed_is_not_a_replayable_receipt_after_observer_disconnect(self):
        if os.geteuid() != 0:
            self.skipTest("requires root to control private systemd transient Jobs")
        # Independent witness stays subscribed so the original signal is
        # known to exist even though the recovering subscriber missed it.
        with self.manager_job_removed_subscription() as (_, witnessed, path, drain):
            with self.manager_job_removed_subscription() as (original, missed, original_path, drain_original):
                with self.deferred_native_launch() as first:
                    release, marker, job, unit = first
                    identity = (int(job), path(job, unit), unit)
                    self.assertEqual(original_path(job, unit), identity[1])
                    drain_original()
                    self.assertFalse(any(event[:3] == identity for event in missed))
                    original.close_sync(None)
                    self.assertTrue(original.is_closed())
                    cancelled = systemctl("cancel", job)
                    self.assertEqual(cancelled.returncode, 0, cancelled.stderr)
                    self.wait_manager_job_removed(witnessed, drain, (*identity, "canceled"))
                    release.touch()
                    self.assertFalse(marker.exists())
                    with self.manager_job_removed_subscription((unit,)) as (_, recovered, new_path, new_drain):
                        with self.deferred_native_launch() as second:
                            other_release, other_marker, other_job, other_unit = second
                            other = (int(other_job), new_path(other_job, other_unit), other_unit)
                            other_release.touch()
                            self.wait_manager_job_removed(recovered, new_drain, (*other, "done"))
                            deadline = time.monotonic() + 5
                            while not other_marker.exists() and time.monotonic() < deadline:
                                time.sleep(0.02)
                            self.assertTrue(other_marker.exists())
                            # Positive new signal proves the fresh subscription
                            # was live. No historical replay was observed in
                            # this bounded window; absence is not an ACK.
                            new_drain()
                            self.assertFalse(any(event[:3] == identity for event in recovered))
                            self.assertFalse(marker.exists())
                            print(
                                "ISSUER_NATIVE_DBUS_OBSERVER_LOSS_COUNTEREXAMPLE_PASS "
                                f"missed_original={identity} received_new={other}"
                            )


if __name__ == "__main__":
    unittest.main()
