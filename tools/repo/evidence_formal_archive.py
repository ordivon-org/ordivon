"""Read one exact original GitHub Artifact archive without filesystem extraction."""

from __future__ import annotations

import hashlib
import io
import json
import re
import stat
import subprocess
import zipfile
import zlib
from typing import Any

MAX_BYTES = 1048576
REPORT_NAME = "ordivon-core-formal-report.json"
ARCHIVE_PROVENANCE = "GITHUB_ARTIFACT_ID_DIGEST_VERIFIED_NOT_PROOF_EQUIVALENCE"


def decode_report_json(raw: bytes) -> dict[str, Any]:
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate report JSON field")
            result[key] = value
        return result

    def nonfinite(value):
        raise ValueError("nonfinite report JSON number: " + value)

    if not isinstance(raw, bytes) or not 0 < len(raw) <= MAX_BYTES:
        raise ValueError("historical Formal report exceeds bounded JSON size")
    try:
        report = json.loads(raw.decode("utf-8"), object_pairs_hook=unique, parse_constant=nonfinite)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise ValueError("historical Formal report must contain valid unique JSON") from exc
    if not isinstance(report, dict):
        raise ValueError("historical Formal report must be a JSON object")  # noqa: TRY004
    return report


def read_formal_archive(raw: bytes, *, expected_size: int, expected_digest: str) -> dict[str, Any]:
    if (
        type(expected_size) is not int or not 0 < expected_size <= MAX_BYTES
        or not isinstance(expected_digest, str)
        or re.fullmatch(r"sha256:[0-9a-f]{64}", expected_digest) is None
        or len(raw) != expected_size
        or "sha256:" + hashlib.sha256(raw).hexdigest() != expected_digest
    ):
        raise ValueError("historical Formal Artifact archive identity/digest/size mismatch")
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            members = archive.infolist()
            if len(members) != 1:
                raise ValueError("historical Formal Artifact requires one report member")
            info = members[0]
            mode = stat.S_IFMT(info.external_attr >> 16)
            if (
                info.filename != REPORT_NAME or info.is_dir()
                or (info.create_system == 3 and mode not in (0, stat.S_IFREG))
                or info.flag_bits & 1
                or not 0 < info.file_size <= MAX_BYTES
            ):
                raise ValueError("historical Formal Artifact report member is unqualified")
            with archive.open(info) as stream:
                content = stream.read(MAX_BYTES + 1)
            if len(content) != info.file_size:
                raise ValueError("historical Formal Artifact report member size mismatch")
    except (zipfile.BadZipFile, NotImplementedError, RuntimeError, OSError, zlib.error) as exc:
        raise ValueError("historical Formal Artifact is not a qualified ZIP") from exc
    return decode_report_json(content)


def download_formal_archive(repo: str, artifact: dict[str, Any]) -> dict[str, Any]:
    identifier = artifact.get("id")
    size = artifact.get("size_in_bytes")
    digest = artifact.get("digest")
    if (
        repo != "ordivon-org/ordivon"
        or type(identifier) is not int or identifier <= 0
        or type(size) is not int or not 0 < size <= MAX_BYTES
        or not isinstance(digest, str)
        or re.fullmatch(r"sha256:[0-9a-f]{64}", digest) is None
    ):
        raise ValueError("historical Formal Artifact download identity is unqualified")
    # Use the official CLI transport and immutable Artifact ID. The metadata
    # and parsed bytes are bounded; this is not a physical transfer quota.
    completed = subprocess.run(
        ["gh", "api", f"repos/{repo}/actions/artifacts/{identifier}/zip"],
        capture_output=True, check=True, timeout=75,
    )
    return read_formal_archive(completed.stdout, expected_size=size, expected_digest=digest)
