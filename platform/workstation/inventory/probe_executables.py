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


def observe(names: list[str], *, path: str | None = None) -> dict:
    """Return a bounded current-process command lookup observation."""
    if not names or len(names) > 128:
        raise ValueError("provide 1..128 executable names")
    for name in names:
        if not _SAFE_NAME.fullmatch(name):
            raise ValueError(f"invalid executable name: {name!r}")

    effective_path = os.environ.get("PATH", "") if path is None else path
    observations = []
    for name in names:
        found = shutil.which(name, path=effective_path)
        observations.append(
            {
                "name": name,
                "resolution": "on_path" if found else "not_on_path",
                "executablePath": os.path.abspath(found) if found else None,
            }
        )
    return {
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


def observe_mise_installed(names: list[str]) -> dict:
    """Read mise's installed-version records, not executable or authority truth."""
    supplier = shutil.which("mise")
    if supplier is None:
        return {"state": "unknown", "reason": "mise_not_on_path"}
    try:
        result = subprocess.run(
            [supplier, "ls", "--installed", "--json"],
            capture_output=True,
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
    parser.add_argument("--mise-installed", action="store_true", help="also query mise installed-version records")
    args = parser.parse_args()
    try:
        result = observe(args.names)
        if args.mise_installed:
            result["miseInventory"] = observe_mise_installed(args.names)
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(result, sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    main()
