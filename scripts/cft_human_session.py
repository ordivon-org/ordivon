#!/usr/bin/env python3
"""Thin standards adapter for durable human-assisted Chromium sessions.

The adapter does not implement browser, remote-display, workflow, or credential semantics.
The doctor action is projection-only: it resolves Workstation-owned browser/equipment bindings
and verifies the mature systemd/X11/noVNC dependencies required by the session carrier.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
from typing import Any

EQUIPMENT_BINDING = Path("/root/tools/bin/equipment-binding")
SYSTEMD_RUN = Path("/usr/bin/systemd-run")
XVFB = Path("/usr/bin/Xvfb")
X11VNC = Path("/usr/bin/x11vnc")
NOVNC_ROOT = Path("/opt/ordivon/external/novnc/1.7.0")
WEBSOCKIFY_EQUIPMENT_ID = "browserless-websockify-0-13-0"
DIGEST_PREFIX = "sha256:"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return DIGEST_PREFIX + h.hexdigest()


def _binding(*args: str) -> dict[str, Any]:
    proc = subprocess.run(
        [str(EQUIPMENT_BINDING), *args],
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=15,
        check=False,
    )
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout).strip()[:500]
        raise RuntimeError(f"equipment binding failed: {detail or f'rc={proc.returncode}'}")
    try:
        value = json.loads(proc.stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError("equipment binding returned non-JSON") from error
    if not isinstance(value, dict):
        raise RuntimeError("equipment binding returned non-object")
    return value


def _verify_executable_binding(
    value: dict[str, Any], *, equipment_id: str, execution_target: str = "local_linux"
) -> dict[str, Any]:
    if value.get("state") != "AVAILABLE":
        raise RuntimeError(f"{equipment_id} is not AVAILABLE")
    if value.get("equipmentId") != equipment_id:
        raise RuntimeError(f"{equipment_id} binding identity mismatch")
    if value.get("executionTarget") != execution_target:
        raise RuntimeError(f"{equipment_id} execution target mismatch")
    executable = Path(str(value.get("executable") or ""))
    expected = value.get("executableDigest")
    binding_digest = value.get("bindingDigest")
    if (
        not executable.is_absolute()
        or not executable.is_file()
        or not os.access(executable, os.X_OK)
        or not isinstance(expected, str)
        or not expected.startswith(DIGEST_PREFIX)
        or len(expected) != 71
        or not isinstance(binding_digest, str)
        or not binding_digest.startswith(DIGEST_PREFIX)
        or len(binding_digest) != 71
    ):
        raise RuntimeError(f"{equipment_id} binding shape is invalid")
    actual = _sha256(executable)
    if actual != expected:
        raise RuntimeError(f"{equipment_id} executable digest mismatch")
    return {
        "equipmentId": equipment_id,
        "state": "AVAILABLE",
        "executionTarget": execution_target,
        "executable": str(executable),
        "executableDigest": expected,
        "bindingDigest": binding_digest,
        "provider": value.get("provider"),
        "providerIdentity": (
            value.get("providerIdentity") if isinstance(value.get("providerIdentity"), dict) else {}
        ),
    }


def doctor() -> dict[str, Any]:
    failures: list[str] = []
    browser: dict[str, Any] | None = None
    websockify: dict[str, Any] | None = None
    try:
        browser = _verify_executable_binding(
            _binding("browser", "--family", "chromium"),
            equipment_id="browser:playwright-chromium",
        )
    except Exception as error:
        failures.append(f"browser-equipment:{type(error).__name__}:{error}")
    try:
        websockify = _verify_executable_binding(
            _binding("managed", "--equipment-id", WEBSOCKIFY_EQUIPMENT_ID),
            equipment_id=WEBSOCKIFY_EQUIPMENT_ID,
        )
    except Exception as error:
        failures.append(f"websockify-equipment:{type(error).__name__}:{error}")

    local = {
        "systemdRun": SYSTEMD_RUN.is_file() and os.access(SYSTEMD_RUN, os.X_OK),
        "xvfb": XVFB.is_file() and os.access(XVFB, os.X_OK),
        "x11vnc": X11VNC.is_file() and os.access(X11VNC, os.X_OK),
        "noVnc": NOVNC_ROOT.is_dir() and (NOVNC_ROOT / "vnc.html").is_file(),
    }
    failures.extend(f"missing:{name}" for name, ready in local.items() if not ready)
    healthy = browser is not None and websockify is not None and all(local.values())
    return {
        "schemaVersion": 1,
        "kind": "ordivon.cft-human-session-doctor",
        "healthy": healthy,
        "standing": "READY" if healthy else "DEPENDENCY_UNAVAILABLE",
        "sessionOwner": "systemd",
        "cdpAuthority": "loopback",
        "humanSurface": "xvfb-x11vnc-novnc",
        "browserEquipment": browser,
        "websockifyEquipment": websockify,
        "localDependencies": local,
        "failures": failures,
        "sideEffectsAttempted": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("doctor",))
    args = parser.parse_args()
    if args.action == "doctor":
        value = doctor()
        print(json.dumps(value, sort_keys=True))
        return 0 if value["healthy"] else 2
    raise AssertionError(args.action)


if __name__ == "__main__":
    raise SystemExit(main())
