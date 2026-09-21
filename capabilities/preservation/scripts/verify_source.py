#!/usr/bin/env python3
from __future__ import annotations

import fnmatch
import json
import subprocess
from pathlib import Path, PurePosixPath

import yaml

OWNER_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(
    subprocess.check_output(
        ["git", "-C", str(OWNER_ROOT), "rev-parse", "--show-toplevel"],
        text=True,
    ).strip()
)
BOUNDARY = OWNER_ROOT / "SOURCE_BOUNDARY.json"
CONTROL_FILES = {
    "README.md",
    "SOURCE_BOUNDARY.json",
    "scripts/verify_source.py",
}


def _tracked_owner_files() -> set[str]:
    prefix = OWNER_ROOT.relative_to(REPO_ROOT).as_posix() + "/"
    output = subprocess.check_output(
        ["git", "-C", str(REPO_ROOT), "ls-files", prefix],
        text=True,
    )
    return {
        PurePosixPath(path.removeprefix(prefix)).as_posix()
        for path in output.splitlines()
        if path
    }


def _matches(path: str, pattern: str) -> bool:
    if pattern.endswith("/**"):
        prefix = pattern[:-3].rstrip("/")
        return path == prefix or path.startswith(prefix + "/")
    return fnmatch.fnmatchcase(path, pattern)


def main() -> int:
    data = json.loads(BOUNDARY.read_text(encoding="utf-8"))
    assert data["schemaVersion"] == 1
    assert data["kind"] == "ordivon.preservation-source-boundary"
    authority = data["authorityBoundary"]
    assert authority["runtimeFrameworkOwnedByOrdivon"] is False
    assert authority["localProfileOnly"] is True

    included = data.get("includedPaths")
    assert isinstance(included, list) and included
    assert all(isinstance(pattern, str) and pattern for pattern in included)

    tracked = _tracked_owner_files()
    payload = tracked - CONTROL_FILES
    unmatched = sorted(
        path for path in payload if not any(_matches(path, pattern) for pattern in included)
    )
    assert not unmatched, f"tracked Preservation payload escaped SOURCE_BOUNDARY: {unmatched}"

    empty_patterns = sorted(
        pattern for pattern in included if not any(_matches(path, pattern) for path in payload)
    )
    assert not empty_patterns, f"SOURCE_BOUNDARY includes empty patterns: {empty_patterns}"

    creative_library = [
        path
        for path in tracked
        if "creative-library" in path.lower() or "creative_library" in path.lower()
    ]
    assert not creative_library, (
        "Creative Library is Media-owned and must not enter Preservation source: "
        f"{creative_library}"
    )

    compose_path = OWNER_ROOT / "config/archivematica-preservation-r10.compose.yml"
    compose = yaml.safe_load(compose_path.read_text(encoding="utf-8"))
    assert isinstance(compose, dict)
    services = compose.get("services")
    assert isinstance(services, dict) and services
    assert "archivematica-storage-service" in services
    assert all(isinstance(name, str) and isinstance(config, dict) for name, config in services.items())

    current_mechanics = "\n".join(
        [
            compose_path.read_text(encoding="utf-8"),
            (OWNER_ROOT / "systemd/ordivon-preservation-fixity-r7.service").read_text(
                encoding="utf-8"
            ),
            (OWNER_ROOT / "systemd/ordivon-preservation-fixity-r7.timer").read_text(
                encoding="utf-8"
            ),
        ]
    )
    assert "/root/workstation-lab" not in current_mechanics

    service = (
        OWNER_ROOT / "systemd/ordivon-preservation-fixity-r7.service"
    ).read_text(encoding="utf-8")
    timer = (
        OWNER_ROOT / "systemd/ordivon-preservation-fixity-r7.timer"
    ).read_text(encoding="utf-8")
    for section in ("[Unit]", "[Service]", "[Install]"):
        assert section in service, f"missing service section {section}"
    for section in ("[Unit]", "[Timer]", "[Install]"):
        assert section in timer, f"missing timer section {section}"

    print(
        "preservation source profile: valid "
        f"(tracked={len(tracked)}, payload={len(payload)}, services={len(services)})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
