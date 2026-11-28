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
from pathlib import Path

_SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]{0,127}$")


def _mise_observation(name: str, mise: str | None, cwd: Path, path: str) -> dict:
    """Ask the existing owner toolchain resolver; never install or trust config."""
    if mise is None:
        return {"resolution": "resolver_unavailable", "executablePath": None}
    try:
        result = subprocess.run(
            [mise, "which", name], cwd=cwd, capture_output=True,
            text=True, timeout=5, check=False, stdin=subprocess.DEVNULL,
            env=os.environ | {"PATH": path},
        )
    except (OSError, subprocess.TimeoutExpired, UnicodeError):
        return {"resolution": "resolver_error", "executablePath": None}
    if result.returncode:
        return {"resolution": "unresolved", "executablePath": None,
                "exitCode": result.returncode}
    lines = result.stdout.strip().splitlines()
    if len(lines) != 1:
        return {"resolution": "unverified_path", "executablePath": None}
    selected = Path(lines[0])
    if not selected.is_absolute() or not selected.is_file() or not os.access(selected, os.X_OK):
        return {"resolution": "unverified_path", "executablePath": None}
    return {"resolution": "resolved", "executablePath": str(selected)}


def observe(names: list[str], *, path: str | None = None,
            mise_scope: bool = False) -> dict:
    """Return a bounded current-process command lookup observation."""
    if not names or len(names) > 128:
        raise ValueError("provide 1..128 executable names")
    for name in names:
        if not _SAFE_NAME.fullmatch(name):
            raise ValueError(f"invalid executable name: {name!r}")

    effective_path = os.environ.get("PATH", "") if path is None else path
    cwd = Path.cwd()
    mise = shutil.which("mise", path=effective_path) if mise_scope else None
    observations = []
    remaining_mise_lookups = 16
    for name in names:
        found = shutil.which(name, path=effective_path)
        row = {
            "name": name,
            "resolution": "on_path" if found else "not_on_path",
            "executablePath": os.path.abspath(found) if found else None,
        }
        if mise_scope:
            if remaining_mise_lookups:
                row["mise"] = _mise_observation(name, mise, cwd, effective_path)
                remaining_mise_lookups -= 1
            else:
                row["mise"] = {"resolution": "lookup_budget_exhausted", "executablePath": None}
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
    if mise_scope:
        report["miseScope"] = {
            "cwd": str(cwd),
            "resolverPath": mise,
            "verificationBoundary": "mise_which_resolution_only_not_installation_or_execution_success",
        }
    return report


def observe_mise_installed(names: list[str]) -> dict:
    """Read mise's installed-version records, not executable or authority truth."""
    supplier = shutil.which("mise")
    if supplier is None:
        return {"state": "unknown", "reason": "mise_not_on_path"}
    try:
        result = subprocess.run(
            [supplier, "ls", "--installed", "--json"],
            capture_output=True,
            stdin=subprocess.DEVNULL,
            text=True,
            check=True,
            timeout=15,
        )
        records = json.loads(result.stdout)
        if not isinstance(records, dict):
            raise ValueError("unexpected mise inventory")
        versions = {}
        for name in names:
            rows = records.get(name, [])
            if not isinstance(rows, list) or any(
                not isinstance(row, dict)
                or not isinstance(row.get("version"), str)
                or row.get("installed") is not True
                for row in rows
            ):
                raise ValueError("unexpected mise tool records")
            versions[name] = [row["version"] for row in rows]
        return {"state": "observed", "installedVersions": versions}
    except (OSError, subprocess.SubprocessError, ValueError):
        return {"state": "unknown", "reason": "mise_inventory_failed"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("names", nargs="+", help="simple executable names; no shell expressions")
    parser.add_argument("--mise", action="store_true",
                        help="also resolve via mise which in the current project directory; no install")
    parser.add_argument("--mise-installed", action="store_true",
                        help="also observe mise installed-version records; no install")
    args = parser.parse_args()
    try:
        result = observe(args.names, mise_scope=args.mise)
        if args.mise_installed:
            result["miseInventory"] = observe_mise_installed(args.names)
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(result, sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    main()
