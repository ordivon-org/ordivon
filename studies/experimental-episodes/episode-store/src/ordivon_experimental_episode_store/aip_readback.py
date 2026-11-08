"""Bounded Archivematica AIP -> Episode committed source read-back.

This composes the existing Episode PostgreSQL readback with the OS descriptor
snapshot and upstream 7-Zip implementation. It neither produces nor catalogs
AIPs; the caller must obtain the exact package from the Storage Service.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any
from uuid import UUID

from .ingest import (
    EpisodeStoreError,
    _frozen_source,
    _require_sha256,
    read_committed_ingest_source,
)

_MAX_PACKAGE_BYTES = 512 * 1024 * 1024
_MAX_SOURCE_BYTES = 64 * 1024 * 1024


def _exact_object_entry(aip_uuid: str, entry: str) -> str:
    try:
        uuid = str(UUID(aip_uuid))
    except (TypeError, ValueError) as exc:
        raise EpisodeStoreError("AIP UUID must be canonical") from exc
    if uuid != aip_uuid:
        raise EpisodeStoreError("AIP UUID must be canonical")
    if not isinstance(entry, str) or len(entry) > 1024:
        raise EpisodeStoreError("explicit bounded AIP object entry is required")
    path = PurePosixPath(entry)
    if (
        not entry
        or path.is_absolute()
        or str(path) != entry
        or len(path.parts) < 4
        or not path.parts[0].endswith("-" + uuid)
        or path.parts[1:3] != ("data", "objects")
        or any(part in (".", "..") for part in entry.split("/"))
        or any(char in entry for char in "\\*?[]\r\n\x00")
    ):
        raise EpisodeStoreError("AIP object entry is not an exact original-file path")
    return entry


def _list_exact_entry(archive_fd: int, entry: str, *, max_bytes: int) -> int:
    listed = subprocess.run(
        ["7z", "l", "-t7z", "-slt", f"/proc/self/fd/{archive_fd}"],
        capture_output=True,
        text=True,
        pass_fds=(archive_fd,),
        timeout=45,
        check=False,
    )
    if listed.returncode != 0:
        raise EpisodeStoreError("native 7z archive directory read failed")
    matches: list[dict[str, str]] = []
    for stanza in listed.stdout.split("\n\n"):
        fields = {}
        for line in stanza.splitlines():
            if " = " in line:
                k, value = line.split(" = ", 1)
                fields[k] = value
        if fields.get("Path") == entry:
            matches.append(fields)
    if len(matches) != 1:
        raise EpisodeStoreError("expected exactly one original AIP entry")
    item = matches[0]
    if item.get("Folder") == "+" or item.get("Attributes", "").startswith("D"):
        raise EpisodeStoreError("AIP entry is not a regular stored file")
    try:
        size = int(item["Size"])
    except (KeyError, ValueError) as exc:
        raise EpisodeStoreError("AIP original entry has no valid size") from exc
    if size < 0 or size > max_bytes:
        raise EpisodeStoreError("AIP entry exceeds bounded source size")
    return size


def read_archived_episode_source(
    *,
    archive: Path,
    aip_uuid: str,
    package_digest: str,
    source_entry: str,
    ingest_id: str,
    dsn: str,
    db_role: str | None = None,
) -> dict[str, Any]:
    """Observe an exact 7z AIP file against committed PG source+projection rows.

    Provider AIP identity must be separately observed: a caller-supplied
    package and UUID are not evidence that an AIP is still stored or leased.
    """
    exact_entry = _exact_object_entry(aip_uuid, source_entry)
    package_digest = _require_sha256(package_digest, "package digest")
    if archive.stat().st_size > _MAX_PACKAGE_BYTES:
        raise EpisodeStoreError("AIP archive exceeds bounded package size")
    if shutil.which("7z") is None:
        raise EpisodeStoreError("upstream 7z executable is required")
    with _frozen_source(archive) as (frozen, frozen_digest, size):
        if size > _MAX_PACKAGE_BYTES or frozen_digest != package_digest:
            raise EpisodeStoreError("AIP package bytes differ from declared SHA-256")
        fd = frozen.fileno()
        expected_size = _list_exact_entry(fd, exact_entry, max_bytes=_MAX_SOURCE_BYTES)
        with tempfile.TemporaryDirectory(
            prefix="ordivon-episode-aip-readback-"
        ) as temp:
            original = Path(temp) / "episode-source.jsonl"
            with original.open("xb") as output:
                extracted = subprocess.run(
                    [
                        "7z",
                        "e",
                        "-t7z",
                        "-so",
                        "-bso0",
                        "-bsp0",
                        f"/proc/self/fd/{fd}",
                        exact_entry,
                    ],
                    stdout=output,
                    stderr=subprocess.DEVNULL,
                    pass_fds=(fd,),
                    timeout=60,
                    check=False,
                )
            if extracted.returncode != 0 or original.stat().st_size != expected_size:
                raise EpisodeStoreError("native 7z failed to restore exact AIP source")
            consumer = read_committed_ingest_source(
                dsn=dsn, db_role=db_role, ingest_id=ingest_id, path=original
            )
            # This is a consumer observation, not a provider AIP or retention
            # attestation. Return the exact externally supplied AIP identity.
            return {
                "kind": "ordivon.episode-aip-source-consumer-readback",
                "aipUuid": aip_uuid,
                "archiveSha256": frozen_digest,
                "sourceEntry": exact_entry,
                "sourceFileDigest": consumer["sourceFileDigest"],
                "sourceByteLength": consumer["sourceByteLength"],
                "ingestId": consumer["ingestId"],
                "episodeCount": consumer["episodeCount"],
                "standing": "PASS_EXPLICIT_ARCHIVE_AND_COMMITTED_PG_READBACK",
                "providerStorageStanding": "UNKNOWN_NOT_OBSERVED",
                "retentionOrGcAuthorized": False,
            }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--aip-uuid", required=True)
    parser.add_argument("--package-sha256", required=True)
    parser.add_argument("--entry", required=True)
    parser.add_argument("--ingest-id", required=True)
    parser.add_argument("--dsn", default=os.environ.get("ORDIVON_EXPERIMENTAL_DSN"))
    parser.add_argument(
        "--db-role", default=os.environ.get("ORDIVON_EXPERIMENTAL_DB_ROLE")
    )
    args = parser.parse_args()
    if not args.dsn:
        parser.error("explicit Episode PostgreSQL DSN is required")
    try:
        result = read_archived_episode_source(
            archive=args.archive,
            aip_uuid=args.aip_uuid,
            package_digest=args.package_sha256,
            source_entry=args.entry,
            ingest_id=args.ingest_id,
            dsn=args.dsn,
            db_role=args.db_role,
        )
    except (EpisodeStoreError, OSError, subprocess.SubprocessError) as exc:
        parser.exit(1, f"archived Episode source readback: {exc}\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
