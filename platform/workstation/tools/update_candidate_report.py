#!/usr/bin/env python3
"""Read-only update candidate discovery using installed native package tools.

This is not an upgrader: never invoke pacman -Syu, mise upgrade, podman
auto-update without --dry-run, nix flake update, or winget upgrade --all.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any


def run_probe(command: list[str], *, cwd: str, timeout: int) -> dict[str, Any]:
    if shutil.which(command[0]) is None:
        return {"state": "missing", "items": [], "reason": "executable_not_found"}
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {"state": "unknown", "items": [], "reason": "probe_timeout"}
    except OSError:
        return {"state": "unknown", "items": [], "reason": "probe_os_error"}
    return {"returncode": result.returncode, "stdout": result.stdout}


def normalize_arch(result: dict[str, Any]) -> dict[str, Any]:
    if "state" in result:
        return result
    code = result["returncode"]
    if code == 2:
        return {"state": "current", "items": []}
    if code != 0:
        return {"state": "unknown", "items": [], "reason": "checkupdates_exit_nonzero"}
    rows = []
    for line in result["stdout"].splitlines():
        fields = line.split()
        if len(fields) >= 4 and fields[-2] == "->":
            rows.append({"package": fields[0], "current": fields[-3], "latest": fields[-1]})
    if result["stdout"].strip() and not rows:
        return {"state": "unknown", "items": [], "reason": "checkupdates_unrecognized_output"}
    return {"state": "updates_available" if rows else "current", "items": rows}


def normalize_mise(result: dict[str, Any]) -> dict[str, Any]:
    if "state" in result:
        return result
    if result["returncode"] != 0:
        return {"state": "unknown", "items": [], "reason": "mise_outdated_exit_nonzero"}
    try:
        parsed = json.loads(result["stdout"])
        if not isinstance(parsed, dict):
            raise ValueError("unexpected type")
        rows = []
        for name, info in parsed.items():
            if not isinstance(info, dict):
                raise ValueError("bad tool entry")
            rows.append(
                {
                    "tool": name,
                    "current": str(info.get("current") or ""),
                    "latest": str(info.get("latest") or ""),
                    "requested": str(info.get("requested") or ""),
                    "bump": str(info.get("bump") or ""),
                }
            )
    except json.JSONDecodeError, ValueError, TypeError:
        return {"state": "unknown", "items": [], "reason": "mise_unrecognized_json"}
    return {"state": "updates_available" if rows else "current", "items": rows}


def normalize_podman(result: dict[str, Any]) -> dict[str, Any]:
    if "state" in result:
        return result
    if result["returncode"] != 0:
        return {"state": "unknown", "items": [], "reason": "podman_dry_run_failed"}
    try:
        payload = json.loads(result["stdout"]) if result["stdout"].strip() else []
        if not isinstance(payload, list):
            raise ValueError("expected list")
        rows = []
        for item in payload:
            if not isinstance(item, dict):
                raise ValueError("expected object")
            rows.append(
                {
                    "image": str(item.get("image") or item.get("Image") or ""),
                    "unit": str(item.get("unit") or item.get("Unit") or ""),
                    "status": str(item.get("updated") or item.get("Updated") or ""),
                }
            )
    except ValueError, json.JSONDecodeError:
        return {"state": "unknown", "items": [], "reason": "podman_unrecognized_json"}
    # Empty means no eligible auto-update containers, not every image is current.
    if not rows:
        return {"state": "no_eligible_containers", "items": []}
    return {"state": "candidates_inspected", "items": rows}


def tracked_mise_scopes(cwd: str) -> list[str]:
    """Discover *tracked* mise config directories, without walking untracked trees."""
    try:
        result = subprocess.run(
            ["git", "-C", cwd, "ls-files", "-z"],
            capture_output=True,
            check=False,
            timeout=12,
        )
    except OSError, subprocess.TimeoutExpired:
        return []
    if result.returncode:
        return []
    paths = result.stdout.decode("utf-8", errors="replace").split("\0")
    return sorted(
        {
            str(Path(p).parent)
            for p in paths
            if p == "mise.toml"
            or p == ".mise.toml"
            or p.endswith("/mise.toml")
            or p.endswith("/.mise.toml")
        }
    )


def check_mise_scopes(
    cwd: str,
    scopes: list[str],
    probe=run_probe,
) -> dict[str, Any]:
    if not scopes:
        return {
            "state": "unknown",
            "items": [],
            "scopes": [],
            "reason": "no_tracked_mise_configs",
        }
    # A hard bound ensures systemd TimeoutStartSec stays effective.
    # Every excess or failed scope is visible as coverage debt, not "current".
    checked = scopes[:64]

    def inspect(scope: str) -> dict[str, Any]:
        path = Path(cwd, scope)
        # Only repository-relative, pre-existing directories can be probed.
        if not path.is_dir() or not path.resolve().is_relative_to(Path(cwd).resolve()):
            return {"scope": scope, "state": "unknown", "items": [], "reason": "invalid_scope"}
        result = normalize_mise(
            probe(
                ["mise", "outdated", "--bump", "--json", "--local"],
                cwd=str(path),
                timeout=12,
            )
        )
        return {"scope": scope, **result}

    with ThreadPoolExecutor(max_workers=4) as executor:
        details = list(executor.map(inspect, checked))

    items = [
        {"scope": detail["scope"], **item} for detail in details for item in detail.get("items", [])
    ]
    incomplete = len(scopes) > len(checked) or any(
        d["state"] not in ("current", "updates_available") for d in details
    )
    state = (
        "partial"
        if incomplete and any(d["state"] in ("current", "updates_available") for d in details)
        else "unknown"
        if incomplete
        else "updates_available"
        if items
        else "current"
    )
    return {
        "state": state,
        "items": items,
        "scopes": details,
        "scopesTotal": len(scopes),
        "scopesChecked": len(checked),
        "scopesUncovered": max(0, len(scopes) - len(checked)),
    }


def source_snapshot(cwd: str) -> dict[str, str | bool | None]:
    """Bind the current tracked worktree to an exact Git commit, fail closed."""
    try:
        revision = subprocess.run(
            ["git", "-C", cwd, "rev-parse", "--verify", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        status = subprocess.run(
            ["git", "-C", cwd, "status", "--porcelain", "--untracked-files=no"],
            capture_output=True,
            text=True,
            check=False,
            timeout=12,
        )
    except OSError, subprocess.TimeoutExpired:
        return {"revision": None, "dirty": None}
    sha = revision.stdout.strip()
    if revision.returncode or len(sha) != 40 or not all(c in "0123456789abcdef" for c in sha):
        return {"revision": None, "dirty": None}
    return {
        "revision": sha,
        "dirty": bool(status.stdout) if status.returncode == 0 else None,
    }


def collect(
    cwd: str,
    probe=run_probe,
    *,
    mise_scopes: list[str] | None = None,
) -> dict[str, Any]:
    source_before = source_snapshot(cwd)
    scopes = tracked_mise_scopes(cwd) if mise_scopes is None else mise_scopes
    checks = {
        "arch": normalize_arch(probe(["checkupdates", "--nocolor"], cwd=cwd, timeout=70)),
        "mise": check_mise_scopes(cwd, scopes, probe=probe),
        "podman": normalize_podman(
            probe(["podman", "auto-update", "--dry-run", "--format", "json"], cwd=cwd, timeout=55)
        ),
    }
    source_after = source_snapshot(cwd)
    if (
        source_before["revision"] is None
        or source_after["revision"] is None
        or source_before["dirty"] is None
        or source_after["dirty"] is None
    ):
        source_standing = "unknown"
    elif (
        source_before["revision"] == source_after["revision"]
        and source_before["dirty"] is False
        and source_after["dirty"] is False
    ):
        source_standing = "stable"
    else:
        source_standing = "changed_or_dirty"

    return {
        "schemaVersion": 1,
        "kind": "ordivon.workstation.update-candidates",
        "generatedAt": dt.datetime.now(dt.UTC).isoformat(),
        "source": "native-read-only-probes",
        "sourceRevision": source_after["revision"] if source_standing == "stable" else None,
        "sourceRevisionBefore": source_before["revision"],
        "sourceRevisionAfter": source_after["revision"],
        "sourceStanding": source_standing,
        "checks": checks,
        "effects": {"packagesUpgraded": 0, "containersRestarted": 0, "deploymentChanged": False},
    }


def store(report: dict[str, Any], output: Path) -> None:
    output.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".update-candidates-", dir=output.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(report, stream, ensure_ascii=False, sort_keys=True, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, output)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cwd", default="/root/projects/ordivon")
    parser.add_argument("--output", type=Path, help="Atomic local JSON evidence file")
    args = parser.parse_args(argv)
    report = collect(args.cwd)
    if args.output is None:
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    else:
        store(report, args.output)
        print("Update candidate report written:", args.output)
        print(
            "Probe states:",
            ", ".join(f"{key}={check['state']}" for key, check in report["checks"].items()),
        )
    # A failed probe is UNKNOWN, not "no updates"; the JSON always preserves it.
    return 0


if __name__ == "__main__":
    sys.exit(main())
