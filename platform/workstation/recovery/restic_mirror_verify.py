#!/usr/bin/env python3
"""Verify a restic cross-repository copy by content-bearing snapshot identity.

Restic snapshot IDs are repository-local because copied snapshots can acquire a
new parent identity.  Mirror correctness therefore binds the source snapshot to
its tree and stable snapshot metadata rather than requiring equal IDs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any

RESTIC = "/usr/bin/restic"


class MirrorVerificationError(RuntimeError):
    pass


def extract_backup_snapshot_id(text: str) -> str:
    snapshot_id = None
    for raw in text.splitlines():
        raw = raw.strip()
        if not raw:
            continue
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and value.get("message_type") == "summary":
            candidate = value.get("snapshot_id")
            if isinstance(candidate, str) and candidate:
                snapshot_id = candidate
    if snapshot_id is None:
        raise MirrorVerificationError("restic backup JSON did not contain a summary snapshot_id")
    return snapshot_id


def snapshot_projection(value: dict[str, Any]) -> dict[str, Any]:
    return {
        "tree": value.get("tree"),
        "time": value.get("time"),
        "hostname": value.get("hostname"),
        "username": value.get("username"),
        "paths": list(value.get("paths") or []),
        "tags": list(value.get("tags") or []),
        "excludes": list(value.get("excludes") or []),
    }


def projection_digest(value: dict[str, Any]) -> str:
    encoded = (json.dumps(snapshot_projection(value), sort_keys=True, separators=(",", ":")) + "\n").encode()
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def matching_mirror_rows(source: dict[str, Any], mirror_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    expected = snapshot_projection(source)
    return [row for row in mirror_rows if snapshot_projection(row) == expected]


def _restic_env(repository: Path, password_file: Path) -> dict[str, str]:
    return {
        **os.environ,
        "RESTIC_REPOSITORY": str(repository),
        "RESTIC_PASSWORD_FILE": str(password_file),
    }


def _checked_json(args: list[str], *, repository: Path, password_file: Path, timeout: int = 120) -> Any:
    proc = subprocess.run(
        [RESTIC, "--no-cache", *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=_restic_env(repository, password_file),
        timeout=timeout,
        check=False,
    )
    if proc.returncode != 0:
        raise MirrorVerificationError(
            f"restic command failed ({proc.returncode}): {' '.join(args)}\n{proc.stdout}{proc.stderr}"
        )
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as error:
        raise MirrorVerificationError(f"restic returned invalid JSON for {' '.join(args)}") from error


def latest_snapshot_id(repository: Path, password_file: Path, *, tag: str | None = None) -> str:
    args = ["snapshots", "--json"]
    if tag:
        args.extend(["--tag", tag])
    rows = _checked_json(args, repository=repository, password_file=password_file)
    if not isinstance(rows, list) or not rows:
        raise MirrorVerificationError(f"no source restic snapshots found in {repository}")
    latest = max(rows, key=lambda row: str(row.get("time", "")))
    snapshot_id = latest.get("id")
    if not isinstance(snapshot_id, str) or not snapshot_id:
        raise MirrorVerificationError("latest source snapshot has no id")
    return snapshot_id


def verify_copy(
    primary_repository: Path,
    mirror_repository: Path,
    password_file: Path,
    source_snapshot_id: str,
    *,
    tag: str | None = None,
) -> dict[str, Any]:
    source = _checked_json(
        ["cat", "snapshot", source_snapshot_id],
        repository=primary_repository,
        password_file=password_file,
    )
    if not isinstance(source, dict):
        raise MirrorVerificationError("source snapshot metadata is not an object")
    args = ["snapshots", "--json"]
    if tag:
        args.extend(["--tag", tag])
    mirror_rows = _checked_json(args, repository=mirror_repository, password_file=password_file)
    if not isinstance(mirror_rows, list):
        raise MirrorVerificationError("mirror snapshot listing is not an array")
    matches = matching_mirror_rows(source, [row for row in mirror_rows if isinstance(row, dict)])
    if len(matches) != 1:
        raise MirrorVerificationError(
            f"expected exactly one mirror snapshot with source tree/metadata identity, found {len(matches)}"
        )
    mirror = matches[0]
    return {
        "schemaVersion": 0,
        "kind": "ordivon.workstation.restic-mirror-verification.v0",
        "status": "pass",
        "sourceSnapshotId": source_snapshot_id,
        "mirrorSnapshotId": mirror.get("id"),
        "sameRepositoryLocalId": mirror.get("id") == source_snapshot_id,
        "tree": source.get("tree"),
        "projectionDigest": projection_digest(source),
        "projection": snapshot_projection(source),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract or verify one Workstation restic mirror snapshot.")
    sub = parser.add_subparsers(dest="command", required=True)
    extract = sub.add_parser("extract-id")
    extract.add_argument("backup_json", type=Path)
    verify = sub.add_parser("verify")
    verify.add_argument("--primary-repository", required=True, type=Path)
    verify.add_argument("--mirror-repository", required=True, type=Path)
    verify.add_argument("--password-file", required=True, type=Path)
    verify.add_argument("--source-snapshot-id")
    verify.add_argument("--tag")
    args = parser.parse_args()

    if args.command == "extract-id":
        print(extract_backup_snapshot_id(args.backup_json.read_text()))
        return 0

    source_id = args.source_snapshot_id or latest_snapshot_id(
        args.primary_repository, args.password_file, tag=args.tag,
    )
    result = verify_copy(
        args.primary_repository,
        args.mirror_repository,
        args.password_file,
        source_id,
        tag=args.tag,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
