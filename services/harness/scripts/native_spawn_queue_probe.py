"""Opt-in native systemd no-block queue counterexample, not a Runtime product test.

This intentionally proves only that target ExecStart can occur after an
independent simulated revocation marker. It does NOT bind a real Harness
PostgreSQL issuer epoch or authenticate the production Runtime launcher.

Run ONLY on an isolated operator-authorized systemd host:
  ORDIVON_NATIVE_SPAWN_QUEUE_PROBE=yes python -m scripts.native_spawn_queue_probe

Creates uniquely named transient units; stops them and deletes its private
temporary output. No production service or PostgreSQL schema is modified.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
import uuid


def command(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args, text=True, capture_output=True, check=check, timeout=12
    )


def main() -> None:
    if os.environ.get("ORDIVON_NATIVE_SPAWN_QUEUE_PROBE") != "yes":
        raise SystemExit("Refuse native transient units without explicit opt-in")
    if os.geteuid() != 0 or not Path("/run/systemd/system").is_dir():
        raise SystemExit("Requires operator-authorized root and native systemd")
    suffix = uuid.uuid4().hex[:12]
    hold = f"ordivon-harness-probe-hold-{suffix}.service"
    target = f"ordivon-harness-probe-target-{suffix}.service"
    with tempfile.TemporaryDirectory(prefix="harness-systemd-queue-") as directory:
        root = Path(directory)
        marker = root / "target-exec-ns"
        try:
            command(
                "systemd-run", "--no-block", f"--unit={hold.removesuffix('.service')}",
                "--property=Type=oneshot", "--property=RemainAfterExit=yes",
                "--property=CollectMode=inactive", "/usr/bin/sleep", "7",
            )
            command(
                "systemd-run", "--no-block",
                f"--unit={target.removesuffix('.service')}",
                "--property=Type=exec",
                "--property=KillMode=control-group",
                "--property=CollectMode=inactive",
                f"--property=After={hold}",
                f"--property=Requires={hold}",
                "/usr/bin/python3", "-c",
                "from pathlib import Path; import time; "
                f"Path({str(marker)!r}).write_text(str(time.time_ns()))",
            )
            revoke_ns = time.time_ns()
            time.sleep(1)
            pending = command(
                "systemctl", "show", target,
                "-p", "ActiveState", "-p", "SubState", "-p", "Job",
                "-p", "ExecMainStartTimestampMonotonic", "--no-pager",
            ).stdout
            if marker.exists():
                raise AssertionError("target started before simulated revocation check")
            if "ExecMainStartTimestampMonotonic=0" not in pending:
                raise AssertionError("native queued target had already started")
            for _ in range(15):
                if marker.exists():
                    break
                time.sleep(1)
            if not marker.exists():
                raise AssertionError("target never physically started")
            start_ns = int(marker.read_text())
            if start_ns <= revoke_ns:
                raise AssertionError("physical target ExecStart preceded revocation marker")
            observed = command(
                "systemctl", "show", target,
                "-p", "ActiveState", "-p", "SubState", "-p", "Result",
                "-p", "Job", "--no-pager",
            ).stdout
            print(
                json.dumps(
                    {
                        "kind": "ordivon.native-systemd-no-block-queue-counterexample",
                        "evidenceScope": "isolated-native-os-only",
                        "originalHarnessPgIssuerBound": False,
                        "productionRuntimeConnected": False,
                        "unit": target,
                        "pendingBeforeExec": pending.strip(),
                        "revokeNs": revoke_ns,
                        "physicalExecNs": start_ns,
                        "lateExecAfterRevokeMs": round(
                            (start_ns - revoke_ns) / 1_000_000, 3
                        ),
                        "nativeUnitReadback": observed.strip(),
                        "noFutureSpawnQualified": False,
                    },
                    sort_keys=True,
                ),
                flush=True,
            )
        finally:
            subprocess.run(
                ["systemctl", "stop", target, hold],
                text=True, capture_output=True, check=False, timeout=12,
            )
            subprocess.run(
                ["systemctl", "reset-failed", target, hold],
                text=True, capture_output=True, check=False, timeout=12,
            )


if __name__ == "__main__":
    main()
