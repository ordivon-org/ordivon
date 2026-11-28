"""Live, caller-scoped PATH observation, not installation or domain capability truth.

Run inside the *actual* Runtime target/Windows identity. Never persist this
as an authoritative global registry or infer provider authorization.
"""

from __future__ import annotations

import argparse
import getpass
import hashlib
import json
import os
import platform
import re
import shutil
import socket
import subprocess
from datetime import UTC, datetime

_SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]{0,127}$")


def _mise_lookup(name: str, mise: str | None, path: str) -> dict:
    result = {"resolution": "unknown", "executablePath": None}
    if not mise:
        return {**result, "reason": "mise_not_on_path"}
    try:
        completed = subprocess.run(
            [os.path.abspath(mise), "which", name],
            env={**os.environ, "PATH": path},
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired, UnicodeError):
        return {**result, "reason": "mise_observation_failed"}
    if completed.returncode:
        return {**result, "reason": "mise_lookup_unsuccessful"}
    lines = completed.stdout.strip().splitlines()
    if len(lines) != 1:
        return {**result, "reason": "mise_output_ambiguous"}
    candidate = lines[0]
    if not os.path.isabs(candidate) or not os.path.isfile(candidate):
        return {**result, "reason": "mise_path_not_materialized"}
    return {"resolution": "resolved", "executablePath": candidate}


def observe(
    names: list[str], *, path: str | None = None, include_mise: bool = False
) -> dict:
    """Return a bounded current-process command lookup observation."""
    if not names or len(names) > 128:
        raise ValueError("provide 1..128 executable names")
    for name in names:
        if not _SAFE_NAME.fullmatch(name):
            raise ValueError(f"invalid executable name: {name!r}")

    effective_path = os.environ.get("PATH", "") if path is None else path
    observations = []
    mise = shutil.which("mise", path=effective_path) if include_mise else None
    remaining_mise_lookups = 16
    for name in names:
        found = shutil.which(name, path=effective_path)
        row = {
            "name": name,
            "resolution": "on_path" if found else "not_on_path",
            "executablePath": os.path.abspath(found) if found else None,
        }
        if include_mise and not found:
            if remaining_mise_lookups:
                row["mise"] = _mise_lookup(name, mise, effective_path)
                remaining_mise_lookups -= 1
            else:
                row["mise"] = {
                    "resolution": "unknown",
                    "executablePath": None,
                    "reason": "lookup_budget_exhausted",
                }
        observations.append(row)
    report = {
        "kind": "ordivon.workstation.executable-path-observation",
        "schemaVersion": 1,
        "observedAt": datetime.now(UTC).isoformat(),
        "node": socket.gethostname(),
        "platform": platform.system(),
        "userHint": getpass.getuser(),
        "pathSha256": hashlib.sha256(effective_path.encode("utf-8")).hexdigest(),
        "verificationBoundary": "PATH_resolution_only_not_installed_or_authorized_or_executable_success",
        "commands": observations,
    }
    if include_mise:
        report["miseContext"] = {
            "cwd": os.getcwd(),
            "verificationBoundary": "mise_which_resolution_only_not_runtime_admission_or_execution",
        }
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mise", action="store_true", help="also query mise for PATH misses in the current directory (no tool execution)")
    parser.add_argument("names", nargs="+", help="simple executable names; no shell expressions")
    args = parser.parse_args()
    try:
        result = observe(args.names, include_mise=args.mise)
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(result, sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    main()
