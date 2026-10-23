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
    "scripts/test_verify_source.py",
}


def _require(valid: bool, message: str) -> None:
    # Unlike assert, this acceptance gate also executes under python -O.
    if not valid:
        raise ValueError(message)


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
    path_parts = path.split("/")
    pattern_parts = pattern.split("/")
    return len(path_parts) == len(pattern_parts) and all(
        fnmatch.fnmatchcase(part, glob)
        for part, glob in zip(path_parts, pattern_parts, strict=True)
    )


def main() -> int:
    data = json.loads(BOUNDARY.read_text(encoding="utf-8"))
    _require(data["schemaVersion"] == 1, "unsupported source boundary schema")
    _require(data["kind"] == "ordivon.preservation-source-boundary", "invalid source boundary kind")
    authority = data["authorityBoundary"]
    _require(authority["runtimeFrameworkOwnedByOrdivon"] is False, "preservation framework is external")
    _require(authority["localProfileOnly"] is True, "preservation profile must remain local only")

    included = data.get("includedPaths")
    _require(isinstance(included, list) and bool(included), "includedPaths must be nonempty")
    _require(all(isinstance(pattern, str) and pattern for pattern in included), "invalid source path pattern")

    tracked = _tracked_owner_files()
    payload = tracked - CONTROL_FILES
    unmatched = sorted(
        path for path in payload if not any(_matches(path, pattern) for pattern in included)
    )
    _require(not unmatched, f"tracked Preservation payload escaped SOURCE_BOUNDARY: {unmatched}")

    empty_patterns = sorted(
        pattern for pattern in included if not any(_matches(path, pattern) for path in payload)
    )
    _require(not empty_patterns, f"SOURCE_BOUNDARY includes empty patterns: {empty_patterns}")

    creative_library = [
        path
        for path in tracked
        if "creative-library" in path.lower() or "creative_library" in path.lower()
    ]
    _require(not creative_library, (
        "Creative Library is Media-owned and must not enter Preservation source: "
        f"{creative_library}"
    ))

    compose_path = OWNER_ROOT / "config/archivematica-preservation-r10.compose.yml"
    compose = yaml.safe_load(compose_path.read_text(encoding="utf-8"))
    _require(isinstance(compose, dict), "compose profile must be an object")
    services = compose.get("services")
    _require(isinstance(services, dict) and bool(services), "compose services must be nonempty")
    _require(
        all(isinstance(name, str) and isinstance(config, dict) for name, config in services.items()),
        "compose services require names and object configs",
    )

    service = (
        OWNER_ROOT / "systemd/ordivon-preservation-fixity-r7.service"
    ).read_text(encoding="utf-8")
    timer = (
        OWNER_ROOT / "systemd/ordivon-preservation-fixity-r7.timer"
    ).read_text(encoding="utf-8")
    for section in ("[Unit]", "[Service]", "[Install]"):
        _require(section in service, f"missing service section {section}")
    for section in ("[Unit]", "[Timer]", "[Install]"):
        _require(section in timer, f"missing timer section {section}")

    print(
        "preservation source profile: valid "
        f"(tracked={len(tracked)}, payload={len(payload)}, services={len(services)})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
