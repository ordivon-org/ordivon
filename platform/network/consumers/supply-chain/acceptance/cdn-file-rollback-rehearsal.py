#!/usr/bin/env python3
"""Nonproduction-only scoped CDN file transaction/rollback rehearsal.

Never edits /etc, never invokes systemctl, never edits service units.
The fixture lifecycle is for real byte-level file restoration testing only.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile

MARKER = "NETWORK_V2_CDN_NONPRODUCTION_FIXTURE_ONLY"
FILENAMES = ("authority.json", "egress.json")
PREFLIGHT = Path(__file__).resolve().with_name("cdn-preflight.py")


def publish(result: str, fault: str, code: int) -> int:
    print(json.dumps({
        "schemaVersion": 1,
        "kind": "ordivon.network-v2.cdn-file-rollback-fixture",
        "standing": result,
        "faultInjected": fault,
        "productionServiceTouched": False,
        "providerIdentityUsed": False,
        "productionNetworkMutation": False,
    }, separators=(",", ":")))
    return code


def put_atomic(path: Path, data: bytes, mode: int) -> None:
    fd, temp_name = tempfile.mkstemp(prefix=".nv2-cdn-file.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temp_name, mode)
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture-root", type=Path, required=True)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--fault", required=True,
                        choices=("after-authority", "after-egress", "after-fake-restart"))
    args = parser.parse_args()

    root = args.fixture_root
    if root.is_symlink() or not root.is_dir() or root.name.startswith("."):
        return publish("HOLD_NOT_SANDBOX", args.fault, 2)
    resolved = root.resolve()
    sandbox_parent = Path(tempfile.gettempdir()).resolve()
    if sandbox_parent not in resolved.parents or not resolved.name.startswith("nv2-r5-sandbox-"):
        return publish("HOLD_NOT_SANDBOX", args.fault, 2)
    if not (resolved / MARKER).is_file() or (resolved / MARKER).is_symlink():
        return publish("HOLD_NOT_SANDBOX", args.fault, 2)
    for name in FILENAMES:
        f = resolved / name
        if f.is_symlink() or not f.is_file() or f.stat().st_nlink != 1:
            return publish("HOLD_NOT_SANDBOX", args.fault, 2)

    verdict = subprocess.run([
        "/usr/bin/python3", str(PREFLIGHT),
        "--source-dir", str(args.source_dir),
        "--installed-dir", str(resolved),
    ], text=True, capture_output=True, check=False, timeout=10)
    if verdict.returncode:
        return publish("HOLD_PREIMAGE_DRIFT", args.fault, 2)
    decision = json.loads(verdict.stdout)
    if decision["standing"] != "READY_TO_DEPLOY_NARROW_SCOPE":
        return publish("HOLD_PREIMAGE_DRIFT", args.fault, 2)

    original = {}
    for name in FILENAMES:
        target = resolved / name
        original[name] = (target.read_bytes(), stat.S_IMODE(target.stat().st_mode))
    faulted = False
    try:
        for step, name in enumerate(FILENAMES):
            put_atomic(resolved / name, (args.source_dir / name).read_bytes(),
                       original[name][1])
            # Negative fault injection after real bytes have changed.
            if args.fault == ("after-authority" if step == 0 else "after-egress"):
                raise RuntimeError("synthetic-fault")
        # No real service is started/stopped; represents a failure AFTER both
        # config-file writes and before the real service's health acceptance.
        raise RuntimeError("synthetic-fault-after-staging")
    except RuntimeError:
        faulted = True
    finally:
        for name in FILENAMES:
            content, mode = original[name]
            put_atomic(resolved / name, content, mode)
    if not faulted:
        return publish("HOLD_UNEXPECTED_NO_FAULT", args.fault, 2)
    if not all((resolved / name).read_bytes() == original[name][0]
               and stat.S_IMODE((resolved / name).stat().st_mode) == original[name][1]
               for name in FILENAMES):
        return publish("HOLD_RESTORE_VERIFICATION", args.fault, 2)
    return publish("SANDBOX_PREIMAGE_RESTORED", args.fault, 0)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError, subprocess.TimeoutExpired) as error:
        print(f"cdn sandbox rehearsal ERROR: {type(error).__name__}", file=sys.stderr)
        sys.exit(2)
