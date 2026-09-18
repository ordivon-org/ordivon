from __future__ import annotations

import copy
import hashlib
import io
import os
from pathlib import Path, PurePosixPath
import re
import struct
from typing import Any
import zipfile

from artifact_core.contracts import sha256_file

DETERMINISTIC_ZIP_DATETIME = (1980, 1, 1, 0, 0, 0)
DETERMINISTIC_OPC_CORE_TIMESTAMP = "1980-01-01T00:00:00Z"


def _dos_datetime_fields(value: tuple[int, int, int, int, int, int]) -> tuple[int, int]:
    year, month, day, hour, minute, second = value
    if year < 1980 or year > 2107 or not (1 <= month <= 12) or not (1 <= day <= 31):
        raise RuntimeError(f"ZIP canonical timestamp is outside DOS range: {value}")
    if not (0 <= hour <= 23) or not (0 <= minute <= 59) or not (0 <= second <= 59):
        raise RuntimeError(f"ZIP canonical timestamp has invalid time fields: {value}")
    dos_time = (hour << 11) | (minute << 5) | (second // 2)
    dos_date = ((year - 1980) << 9) | (month << 5) | day
    return dos_time, dos_date

def normalize_zip_member_timestamps(path: Path, value: tuple[int, int, int, int, int, int] = DETERMINISTIC_ZIP_DATETIME) -> dict[str, Any]:
    """Canonicalize ZIP local/central DOS timestamps without touching member payload bytes.

    Native ZIP writers commonly stamp the current wall clock into every member header.
    For generated OOXML this changes the whole-file digest even when every package part
    and compressed payload is identical. Patch only those header fields in place so the
    artifact becomes replay-stable without recompression or OOXML mutation.
    """
    if not path.is_file() or not zipfile.is_zipfile(path):
        raise RuntimeError(f"ZIP timestamp normalization requires a valid ZIP file: {path}")
    raw = bytearray(path.read_bytes())
    dos_time, dos_date = _dos_datetime_fields(value)
    with zipfile.ZipFile(path) as package:
        infos = package.infolist()
        before = [(info.filename, hashlib.sha256(package.read(info.filename)).hexdigest()) for info in infos]
    local_offsets = {info.header_offset: info.filename for info in infos}
    if len(local_offsets) != len(infos):
        raise RuntimeError("ZIP contains duplicate local-header offsets")
    for info in infos:
        off = info.header_offset
        if raw[off:off + 4] != b"PK\x03\x04":
            raise RuntimeError(f"ZIP local header signature mismatch for {info.filename}")
        raw[off + 10:off + 12] = struct.pack("<H", dos_time)
        raw[off + 12:off + 14] = struct.pack("<H", dos_date)

    search_start = max(0, len(raw) - (65535 + 22))
    eocd = raw.rfind(b"PK\x05\x06", search_start)
    if eocd < 0 or eocd + 22 > len(raw):
        raise RuntimeError("ZIP EOCD record is absent or truncated")
    disk_number, central_disk, entries_disk, entries_total, central_size, central_offset, comment_len = struct.unpack_from("<HHHHIIH", raw, eocd + 4)
    if disk_number != 0 or central_disk != 0 or entries_disk != entries_total:
        raise RuntimeError("multi-disk ZIP normalization is unsupported")
    if entries_total != len(infos):
        raise RuntimeError("ZIP central-directory entry count does not match local package census")
    if central_offset == 0xFFFFFFFF or central_size == 0xFFFFFFFF or entries_total == 0xFFFF:
        raise RuntimeError("ZIP64 timestamp normalization is not implemented")
    if eocd + 22 + comment_len != len(raw):
        raise RuntimeError("ZIP EOCD comment/length boundary mismatch")

    cursor = central_offset
    observed_offsets: set[int] = set()
    for _ in range(entries_total):
        if raw[cursor:cursor + 4] != b"PK\x01\x02":
            raise RuntimeError("ZIP central-directory signature mismatch")
        name_len, extra_len, entry_comment_len = struct.unpack_from("<HHH", raw, cursor + 28)
        local_offset = struct.unpack_from("<I", raw, cursor + 42)[0]
        if local_offset not in local_offsets:
            raise RuntimeError("ZIP central directory references an unknown local header")
        observed_offsets.add(local_offset)
        raw[cursor + 12:cursor + 14] = struct.pack("<H", dos_time)
        raw[cursor + 14:cursor + 16] = struct.pack("<H", dos_date)
        cursor += 46 + name_len + extra_len + entry_comment_len
    if cursor != central_offset + central_size:
        raise RuntimeError("ZIP central-directory size boundary mismatch")
    if observed_offsets != set(local_offsets):
        raise RuntimeError("ZIP local/central member identity mismatch")

    temp = path.with_name(path.name + ".timestamp-normalize.tmp")
    temp.unlink(missing_ok=True)
    try:
        temp.write_bytes(raw)
        with zipfile.ZipFile(temp) as package:
            after_infos = package.infolist()
            after = [(info.filename, hashlib.sha256(package.read(info.filename)).hexdigest()) for info in after_infos]
            observed_dates = {tuple(info.date_time) for info in after_infos}
        if after != before:
            raise RuntimeError("ZIP timestamp normalization changed member identity or payload bytes")
        if observed_dates != {value}:
            raise RuntimeError(f"ZIP canonical timestamp verification failed: {sorted(observed_dates)}")
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)
    return {
        "status": "PASS",
        "method": "in-place-local-and-central-dos-timestamp-normalization",
        "memberCount": len(infos),
        "canonicalDateTime": list(value),
        "memberPayloadBytesChanged": False,
        "recompressionPerformed": False,
        "zip64Supported": False,
    }

def _canonicalize_opc_core_xml(payload: bytes, timestamp: str = DETERMINISTIC_OPC_CORE_TIMESTAMP) -> tuple[bytes, int]:
    """Normalize only volatile W3CDTF created/modified values in OPC core properties."""
    replacement = timestamp.encode("ascii")
    total = 0
    result = payload
    for tag in (b"created", b"modified"):
        pattern = re.compile(
            rb"(<dcterms:" + tag + rb"\b[^>]*>)([^<]*)(</dcterms:" + tag + rb">)"
        )
        result, count = pattern.subn(lambda match: match.group(1) + replacement + match.group(3), result)
        total += count
    return result, total

def _canonicalize_ppt_creation_ids(
    payload: bytes,
    member_name: str,
    used_values: set[int] | None = None,
) -> tuple[bytes, int]:
    """Replace volatile PPT p14:creationId values with deterministic unique UInt32 values.

    PowerPoint treats creation IDs as package identities, and PPT Master's own template
    validation rejects duplicates across cloned parts. The allocator therefore shares a
    package-level used-value set and deterministically probes on a rare 32-bit hash
    collision instead of assuming truncated SHA-256 values are collision-free.
    """
    pattern = re.compile(rb'(<p14:creationId\b[^>]*\bval=")([0-9]+)("[^>]*/>)')
    matches = list(pattern.finditer(payload))
    if not matches:
        return payload, 0
    basis = pattern.sub(lambda match: match.group(1) + b"0" + match.group(3), payload)
    used = used_values if used_values is not None else set()
    index = 0

    def replace(match: re.Match[bytes]) -> bytes:
        nonlocal index
        digest = hashlib.sha256(member_name.encode("utf-8") + b"\0" + str(index).encode("ascii") + b"\0" + basis).digest()
        value = int.from_bytes(digest[:4], "big") or 1
        while value in used:
            value = (value + 1) & 0xFFFFFFFF
            if value == 0:
                value = 1
        used.add(value)
        index += 1
        return match.group(1) + str(value).encode("ascii") + match.group(3)

    return pattern.sub(replace, payload), len(matches)

def _canonicalize_generated_zip_bytes(raw: bytes, *, recurse_embedded_office: bool) -> tuple[bytes, dict[str, Any]]:
    """Repack one generated ZIP deterministically while normalizing bounded OPC metadata.

    This deliberately targets generated artifacts, not arbitrary donor/native files. Member
    order, compression method, attributes, comments and payloads are preserved except for
    explicit OPC core-property timestamps and recursively embedded generated Office ZIPs.
    """
    source_buffer = io.BytesIO(raw)
    if not zipfile.is_zipfile(source_buffer):
        raise RuntimeError("generated OOXML canonicalization requires a valid ZIP package")
    source_buffer.seek(0)
    with zipfile.ZipFile(source_buffer, "r") as source:
        infos = source.infolist()
        package_comment = source.comment
        rows: list[tuple[zipfile.ZipInfo, bytes]] = []
        changed_members: list[str] = []
        core_field_count = 0
        creation_id_count = 0
        creation_id_members: list[str] = []
        used_creation_ids: set[int] = set()
        nested_receipts: list[dict[str, Any]] = []
        for info in infos:
            data = source.read(info.filename)
            if info.filename == "docProps/core.xml":
                normalized, changed = _canonicalize_opc_core_xml(data)
                if changed:
                    data = normalized
                    changed_members.append(info.filename)
                    core_field_count += changed
            elif recurse_embedded_office and info.filename.startswith("ppt/embeddings/") and PurePosixPath(info.filename).suffix.lower() in {".xlsx", ".xlsm"}:
                normalized, receipt = _canonicalize_generated_zip_bytes(data, recurse_embedded_office=False)
                if normalized != data:
                    data = normalized
                    changed_members.append(info.filename)
                nested_receipts.append({"member": info.filename, **receipt})
            if info.filename.startswith("ppt/") and info.filename.endswith(".xml"):
                normalized, changed = _canonicalize_ppt_creation_ids(data, info.filename, used_creation_ids)
                if changed:
                    data = normalized
                    creation_id_count += changed
                    creation_id_members.append(info.filename)
                    if info.filename not in changed_members:
                        changed_members.append(info.filename)
            rows.append((info, data))

    target_buffer = io.BytesIO()
    with zipfile.ZipFile(target_buffer, "w") as target:
        target.comment = package_comment
        for info, data in rows:
            cloned = copy.copy(info)
            cloned.date_time = DETERMINISTIC_ZIP_DATETIME
            target.writestr(cloned, data, compress_type=info.compress_type)
    normalized_raw = target_buffer.getvalue()
    with zipfile.ZipFile(io.BytesIO(normalized_raw), "r") as check:
        if [item.filename for item in check.infolist()] != [item.filename for item, _ in rows]:
            raise RuntimeError("generated OOXML canonicalization changed member ordering or identity")
        observed_dates = {tuple(item.date_time) for item in check.infolist()}
        if observed_dates != {DETERMINISTIC_ZIP_DATETIME}:
            raise RuntimeError(f"generated OOXML canonical ZIP timestamp verification failed: {sorted(observed_dates)}")
    return normalized_raw, {
        "memberCount": len(rows),
        "changedMembers": changed_members,
        "coreTimestampFieldCount": core_field_count,
        "creationIdFieldCount": creation_id_count,
        "creationIdMembers": creation_id_members,
        "nestedPackages": nested_receipts,
    }

def canonicalize_generated_ooxml_metadata(path: Path) -> dict[str, Any]:
    """Canonicalize bounded volatile metadata on a newly generated OOXML artifact."""
    if not path.is_file():
        raise RuntimeError(f"generated OOXML artifact is absent: {path}")
    before_digest = sha256_file(path)
    normalized, details = _canonicalize_generated_zip_bytes(path.read_bytes(), recurse_embedded_office=True)
    temp = path.with_name(path.name + ".generated-ooxml-canonicalize.tmp")
    temp.unlink(missing_ok=True)
    try:
        temp.write_bytes(normalized)
        if not zipfile.is_zipfile(temp):
            raise RuntimeError("generated OOXML canonicalization produced an invalid ZIP package")
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)
    return {
        "status": "PASS",
        "method": "deterministic-generated-ooxml-repack-v1",
        "canonicalZipDateTime": list(DETERMINISTIC_ZIP_DATETIME),
        "canonicalCoreTimestamp": DETERMINISTIC_OPC_CORE_TIMESTAMP,
        "beforeSha256": before_digest,
        "afterSha256": sha256_file(path),
        **details,
        "boundary": "Only newly generated provider output is canonicalized. Donor/native input artifacts are never rewritten by this helper.",
    }
