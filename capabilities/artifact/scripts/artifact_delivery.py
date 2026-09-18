#!/usr/bin/env python3
"""Standard-native Artifact Build & Delivery R1 gates.

This module deliberately does not define a universal document model. It checks
build/delivery facts around native artifacts and delegates format conformance to
mature validators whenever available.
"""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import importlib.util
import importlib.metadata
import io
import json
import os
from pathlib import Path, PurePosixPath
import posixpath
import re
import shutil
import subprocess
import struct
import sys
import tempfile
import urllib.parse
import xml.etree.ElementTree as ET
import zipfile
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from artifact_core.admission import AdmissionHooks, admit_delivery_request
from artifact_core.build_bindings import BuildCapabilityBindingRegistry
from artifact_core.build_planning import compile_delivery_plan_from_validation
from artifact_core.contracts import file_fact, sha256_file
from artifact_core.profile_v1 import validate_profile_v1 as validate_profile
from artifact_trust.provenance import slsa_statement, verify_release_provenance
import artifact_trust.vsa as trust_vsa
from artifact_capabilities.dispatch import execute_build_adapter
from artifact_capabilities.presentation import (
    PresentationBuildHooks,
    admit_presentation_source as presentation_admit_source,
    admit_semantic_svg_source as presentation_admit_semantic_svg_source,
    build_presentation_source as presentation_build_source,
    build_semantic_svg_presentation_source as presentation_build_semantic_svg_source,
)
import artifact_capabilities.presentation.common as presentation_common
import artifact_capabilities.presentation.ppt_master as presentation_ppt_master
from artifact_verification import (
    VerificationStageHooks,
    execute_verify_stage as verification_execute_stage,
    write_gate_receipt,
)
from artifact_evidence.delivery import (
    verify_delivery_evidence,
    verify_file_fact,
    verify_readback,
    verify_render_evidence,
    verify_target_evidence,
    verify_visual_review,
)

BUILD_BINDING_REGISTRY = BuildCapabilityBindingRegistry(ROOT / "artifact-delivery")
GLOBAL_ARTIFACT_TOOLCHAIN_ROOT = Path(os.environ.get("ARTIFACT_TOOLCHAIN_ROOT", "/opt/ordivon/external/artifact-toolchain"))
GLOBAL_PANDOC = GLOBAL_ARTIFACT_TOOLCHAIN_ROOT / "pandoc/3.10.2/bin/pandoc"
GLOBAL_PANDOC_ARCHIVE = GLOBAL_ARTIFACT_TOOLCHAIN_ROOT / "pandoc/3.10.2/pandoc-3.10.2-linux-amd64.tar.gz"
GLOBAL_VERAPDF = GLOBAL_ARTIFACT_TOOLCHAIN_ROOT / "verapdf/1.30.2/verapdf"
GLOBAL_VNU = GLOBAL_ARTIFACT_TOOLCHAIN_ROOT / "vnu/26.9.7/vnu.jar"
GLOBAL_NODE_PACKAGE_ROOT = GLOBAL_ARTIFACT_TOOLCHAIN_ROOT / "node/1.63.0"


def _selected_external_file(env_name: str, global_candidate: Path, legacy_candidate: Path) -> Path:
    configured = os.environ.get(env_name)
    if configured:
        return Path(configured)
    if global_candidate.is_file():
        return global_candidate
    if legacy_candidate.is_file():
        return legacy_candidate
    return global_candidate


DEFAULT_SCHEMA = ROOT / "artifact-delivery/profile-v1.schema.json"
DEFAULT_REQUEST_SCHEMA = ROOT / "artifact-delivery/request-v1.schema.json"
DEFAULT_PRESENTATION_SOURCE_SCHEMA = ROOT / "artifact-delivery/presentation-source-v1.schema.json"
DEFAULT_PRESENTATION_SEMANTIC_SVG_SOURCE_SCHEMA = ROOT / "artifact-delivery/presentation-semantic-svg-source-v1.schema.json"
PPT_MASTER_PROVIDER_LOCK = ROOT / "artifact-delivery/ppt-master-provider-v1.lock.json"
DEFAULT_OPC_MEMBER_PROJECTION_SCHEMA = ROOT / "artifact-delivery/opc-member-projection-v1.schema.json"
DEFAULT_WINDOWS_FONTS = Path("/mnt/c/Windows/Fonts")
DEFAULT_VSA_TRUST_POLICY_SCHEMA = trust_vsa.DEFAULT_VSA_TRUST_POLICY_SCHEMA
IN_TOTO_STATEMENT_V1 = trust_vsa.IN_TOTO_STATEMENT_V1
SLSA_PROVENANCE_V1 = "https://slsa.dev/provenance/v1"
SLSA_VERIFICATION_SUMMARY_V1 = trust_vsa.SLSA_VERIFICATION_SUMMARY_V1
SLSA_VERSION = trust_vsa.SLSA_VERSION
LOCAL_VSA_VERIFIER_ID = trust_vsa.LOCAL_VSA_VERIFIER_ID
SIGSTORE_BUNDLE_V03 = trust_vsa.SIGSTORE_BUNDLE_V03
INTOTO_DSSE_PAYLOAD_TYPE = trust_vsa.INTOTO_DSSE_PAYLOAD_TYPE
COSIGN_STANDARD_BUNDLE_MIN_VERSION = trust_vsa.COSIGN_STANDARD_BUNDLE_MIN_VERSION
COSIGN_LOCK_PATH = trust_vsa.COSIGN_LOCK_PATH
COSIGN_SELECTED_BINARY = trust_vsa.COSIGN_SELECTED_BINARY
COSIGN_ARCH_PACKAGE = trust_vsa.COSIGN_ARCH_PACKAGE
COSIGN_ARCH_PACKAGE_SIGNATURE = trust_vsa.COSIGN_ARCH_PACKAGE_SIGNATURE
_COSIGN_PROVENANCE_CACHE = trust_vsa._COSIGN_PROVENANCE_CACHE
VSA_GATE_NAMES = trust_vsa.VSA_GATE_NAMES
ASSEMBLY_GATE_NAMES = trust_vsa.ASSEMBLY_GATE_NAMES
OOXML_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
PRESENTATION_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
DRAWING_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")






def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


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




def validate_json_document(document_path: Path, schema_path: Path, expected_kind: str | None = None) -> dict[str, Any]:
    value = load_json(document_path)
    schema = load_json(schema_path)
    failures: list[str] = []
    if not isinstance(value, dict):
        failures.append("document must be a JSON object")
    elif expected_kind is not None and value.get("kind") != expected_kind:
        failures.append(f"document kind must equal {expected_kind}")
    validator = "jsonschema"
    schema_status = "NOT_RUN"
    schema_error: str | None = None
    if importlib.util.find_spec("jsonschema") is None:
        validator = "unavailable"
        schema_error = "Python jsonschema package is not installed"
    else:
        try:
            import jsonschema  # type: ignore

            jsonschema.Draft202012Validator.check_schema(schema)
            instance = dict(value) if isinstance(value, dict) else value
            if isinstance(instance, dict):
                instance.pop("$schema", None)
            jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker()).validate(instance)
            schema_status = "PASS"
        except Exception as error:
            schema_status = "FAIL"
            schema_error = str(error)
            failures.append(f"JSON Schema validation failed: {error}")
    return {
        "status": "PASS" if not failures and schema_status == "PASS" else "FAIL",
        "document": value,
        "failures": failures,
        "jsonSchema": {
            "dialect": "https://json-schema.org/draft/2020-12/schema",
            "validator": validator,
            "status": schema_status,
            "error": schema_error,
            "schemaPath": str(schema_path.resolve()),
        },
    }


def _presentation_build_hooks() -> PresentationBuildHooks:
    return PresentationBuildHooks(
        validate_json_document=validate_json_document,
        inspect_pptx=inspect_pptx,
        verify_semantics=verify_presentation_semantics,
        normalize_python_pptx=normalize_zip_member_timestamps,
        canonicalize_ppt_master=canonicalize_generated_ooxml_metadata,
    )


# Compatibility-only private projections for historical tests/callers.
_resolve_semantic_svg_source_path = presentation_common._resolve_semantic_svg_source_path
_safe_project_relative_path = presentation_common._safe_project_relative_path
_semantic_svg_source_material_facts = presentation_common._semantic_svg_source_material_facts
_ppt_master_provider_facts = presentation_ppt_master._ppt_master_provider_facts
_resolve_presentation_template = presentation_common._resolve_presentation_template
_resolve_presentation_image = presentation_common._resolve_presentation_image
_presentation_source_material_facts = presentation_common._presentation_source_material_facts
_presentation_template_package_fact = presentation_common._presentation_template_package_fact
_presentation_layout_by_id = presentation_common._presentation_layout_by_id
_presentation_layout_fact = presentation_common._presentation_layout_fact
_apply_text_to_shape = presentation_common._apply_text_to_shape
_hex_color = presentation_common._hex_color


def _resolve_request_path(request_path: Path, relative: str) -> Path:
    candidate = Path(relative)
    if candidate.is_absolute():
        return candidate.resolve()
    return (request_path.resolve().parent / candidate).resolve()










def build_semantic_svg_presentation_source(
    source_path: Path,
    profile_path: Path,
    output_path: Path,
    source_schema_path: Path = DEFAULT_PRESENTATION_SEMANTIC_SVG_SOURCE_SCHEMA,
) -> dict[str, Any]:
    return presentation_build_semantic_svg_source(
        source_path, profile_path, output_path, source_schema_path, hooks=_presentation_build_hooks()
    )



def _admit_presentation_source(source_path: Path) -> tuple[dict[str, Any] | None, list[dict[str, Any]], list[str]]:
    return presentation_admit_source(
        source_path, validate_json_document=validate_json_document, source_schema_path=DEFAULT_PRESENTATION_SOURCE_SCHEMA
    )



def _admit_semantic_svg_source(source_path: Path) -> tuple[dict[str, Any] | None, list[dict[str, Any]], list[str]]:
    return presentation_admit_semantic_svg_source(
        source_path, validate_json_document=validate_json_document, source_schema_path=DEFAULT_PRESENTATION_SEMANTIC_SVG_SOURCE_SCHEMA
    )



def validate_delivery_request(
    request_path: Path,
    request_schema_path: Path = DEFAULT_REQUEST_SCHEMA,
    profile_schema_path: Path = DEFAULT_SCHEMA,
) -> dict[str, Any]:
    hooks = AdmissionHooks(
        validate_json_document=validate_json_document,
        validate_profile=validate_profile,
        source_validators={
            "presentation-source-v1": _admit_presentation_source,
            "presentation-semantic-svg-source-v1": _admit_semantic_svg_source,
        },
        file_fact=file_fact,
        sha256_file=sha256_file,
    )
    return admit_delivery_request(
        request_path,
        request_schema_path=request_schema_path,
        profile_schema_path=profile_schema_path,
        hooks=hooks,
    )



def compile_delivery_plan(request_path: Path) -> dict[str, Any]:
    validation = validate_delivery_request(request_path)
    return compile_delivery_plan_from_validation(
        request_path,
        validation,
        registry=BUILD_BINDING_REGISTRY,
        sha256_file=sha256_file,
    )



def _primary_suffix(profile: dict[str, Any]) -> str:
    suffixes = {
        "pptx": ".pptx",
        "docx": ".docx",
        "xlsx": ".xlsx",
        "html": ".html",
        "pdf": ".pdf",
        "pdf-a-4": ".pdf",
        "pdf-ua-2": ".pdf",
    }
    fmt = str(profile.get("primaryOutput", {}).get("format", ""))
    suffix = suffixes.get(fmt)
    if suffix is None:
        raise RuntimeError(f"unsupported primary output format: {fmt}")
    return suffix


def _request_output_name(request_id: str, suffix: str) -> str:
    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", request_id).strip("-._") or "artifact"
    return stem + suffix


def execute_build_stage(request_path: Path, output_directory: Path | None = None) -> dict[str, Any]:
    plan = compile_delivery_plan(request_path)
    if plan.get("status") != "PASS":
        return {
            "schemaVersion": 1,
            "kind": "artifact-delivery-build-stage",
            "status": "FAIL",
            "plan": plan,
            "failures": ["derived delivery plan did not PASS"],
        }
    validation = validate_delivery_request(request_path)
    request = validation["request"]
    profile = validation["profileValidation"]["profile"]
    source_path = Path(validation["resolved"]["source"]["path"])
    profile_path = Path(validation["resolved"]["profile"]["path"])
    if output_directory is None:
        output_directory = _resolve_request_path(request_path, str(request["outputDirectory"]))
    output_directory.mkdir(parents=True, exist_ok=True)
    suffix = _primary_suffix(profile)
    output_path = output_directory / _request_output_name(str(request["requestId"]), suffix)
    adapter = plan["buildAdapter"]
    pandoc = _selected_external_file("ARTIFACT_PANDOC", GLOBAL_PANDOC, ROOT / ".cache/artifact-toolchain/pandoc/current/bin/pandoc")
    adapter_result = execute_build_adapter(
        adapter,
        source_path=source_path,
        profile_path=profile_path,
        output_path=output_path,
        presentation_builders={
            "python-pptx-presentation-source-v1": build_presentation_source,
            "ppt-master-semantic-svg-v1": build_semantic_svg_presentation_source,
        },
        pandoc=pandoc,
    )
    failures: list[str] = []
    if adapter_result.get("status") != "PASS":
        failures.append(f"build adapter did not PASS: {adapter}")
    if not output_path.is_file():
        failures.append("primary output file is absent")
    return {
        "schemaVersion": 1,
        "kind": "artifact-delivery-build-stage",
        "status": "PASS" if not failures else "FAIL",
        "request": file_fact(request_path),
        "plan": plan,
        "adapterResult": adapter_result,
        "artifact": file_fact(output_path) if output_path.is_file() else None,
        "failures": failures,
        "boundary": "Build-stage PASS means exact request/profile/source bytes produced the primary artifact through the selected adapter. Independent verification, target rendering, packaging, provenance and release gates are not implied.",
    }


def _pandoc_inline_text(values: Any) -> str:
    if not isinstance(values, list):
        return ""
    parts: list[str] = []
    for node in values:
        if not isinstance(node, dict):
            continue
        kind = node.get("t")
        content = node.get("c")
        if kind == "Str" and isinstance(content, str):
            parts.append(content)
        elif kind in {"Space", "SoftBreak", "LineBreak"}:
            parts.append(" ")
        elif kind in {"Emph", "Strong", "Strikeout", "Superscript", "Subscript", "SmallCaps", "Underline"}:
            parts.append(_pandoc_inline_text(content))
        elif kind in {"Code", "Math"} and isinstance(content, list) and len(content) >= 2:
            parts.append(str(content[1]))
        elif kind in {"Link", "Image"} and isinstance(content, list) and len(content) >= 2:
            parts.append(_pandoc_inline_text(content[1]))
        elif kind in {"Span", "Cite"} and isinstance(content, list) and len(content) >= 2:
            parts.append(_pandoc_inline_text(content[1]))
    return re.sub(r"\s+", " ", "".join(parts)).strip()


def _pandoc_semantic_projection(blocks: Any) -> list[dict[str, Any]]:
    if not isinstance(blocks, list):
        return []
    projection: list[dict[str, Any]] = []
    for block in blocks:
        if not isinstance(block, dict):
            continue
        kind = block.get("t")
        content = block.get("c")
        if kind == "Header" and isinstance(content, list) and len(content) >= 3:
            projection.append({"kind": "heading", "level": int(content[0]), "text": _pandoc_inline_text(content[2])})
        elif kind in {"Para", "Plain"}:
            projection.append({"kind": "paragraph", "text": _pandoc_inline_text(content)})
        elif kind == "OrderedList" and isinstance(content, list) and len(content) >= 2 and isinstance(content[1], list):
            for item in content[1]:
                text = " | ".join(entry["text"] for entry in _pandoc_semantic_projection(item) if entry.get("text"))
                projection.append({"kind": "ordered-item", "text": text})
        elif kind == "BulletList" and isinstance(content, list):
            for item in content:
                text = " | ".join(entry["text"] for entry in _pandoc_semantic_projection(item) if entry.get("text"))
                projection.append({"kind": "bullet-item", "text": text})
        elif kind == "BlockQuote":
            projection.extend(_pandoc_semantic_projection(content))
        elif kind == "Div" and isinstance(content, list) and len(content) >= 2:
            projection.extend(_pandoc_semantic_projection(content[1]))
        elif kind == "CodeBlock" and isinstance(content, list) and len(content) >= 2:
            projection.append({"kind": "code-block", "text": str(content[1])})
        elif kind == "HorizontalRule":
            projection.append({"kind": "horizontal-rule", "text": ""})
    return projection


def _pandoc_meta_text(value: Any) -> str | list[str] | None:
    if not isinstance(value, dict):
        return None
    kind = value.get("t")
    content = value.get("c")
    if kind == "MetaString" and isinstance(content, str):
        return content
    if kind == "MetaInlines":
        return _pandoc_inline_text(content)
    if kind == "MetaList" and isinstance(content, list):
        return [str(item) for item in (_pandoc_meta_text(entry) for entry in content) if item is not None]
    return None


def _run_pandoc_ast(pandoc: Path, source: Path, from_format: str) -> dict[str, Any]:
    proc = subprocess.run(
        [str(pandoc), "--from", from_format, "--to", "json", str(source)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=60,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"Pandoc semantic parse failed for {from_format}: {proc.stderr[-2000:]}")
    value = json.loads(proc.stdout)
    if not isinstance(value, dict) or not isinstance(value.get("blocks"), list):
        raise RuntimeError(f"Pandoc semantic parse did not return a document AST for {from_format}")
    return value


def verify_document_semantic_correspondence(source: Path, document: Path, pandoc: Path | None = None) -> dict[str, Any]:
    executable = pandoc or _selected_external_file("ARTIFACT_PANDOC", GLOBAL_PANDOC, ROOT / ".cache/artifact-toolchain/pandoc/current/bin/pandoc")
    failures: list[str] = []
    if not executable.is_file() or not os.access(executable, os.X_OK):
        return {"status": "FAIL", "source": file_fact(source), "artifact": file_fact(document), "pandoc": {"path": str(executable), "status": "NOT_AVAILABLE"}, "failures": ["Pandoc semantic verifier is unavailable"]}
    version_proc = subprocess.run([str(executable), "--version"], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=20)
    version = version_proc.stdout.splitlines()[0] if version_proc.returncode == 0 and version_proc.stdout else "unknown"
    try:
        source_ast = _run_pandoc_ast(executable, source, "markdown")
        document_ast = _run_pandoc_ast(executable, document, "docx")
    except Exception as error:
        return {"status": "FAIL", "source": file_fact(source), "artifact": file_fact(document), "pandoc": {"path": str(executable.resolve()), "sha256": sha256_file(executable), "version": version}, "failures": [str(error)]}
    source_projection = _pandoc_semantic_projection(source_ast.get("blocks"))
    document_projection = _pandoc_semantic_projection(document_ast.get("blocks"))
    if not source_projection:
        failures.append("source semantic projection is empty")
    if source_projection != document_projection:
        failures.append("normalized Pandoc source/document semantic projections differ")
    source_meta = source_ast.get("meta", {}) if isinstance(source_ast.get("meta"), dict) else {}
    document_meta = document_ast.get("meta", {}) if isinstance(document_ast.get("meta"), dict) else {}
    compared_meta: dict[str, Any] = {}
    for key in ("title", "subtitle", "author"):
        if key not in source_meta:
            continue
        expected = _pandoc_meta_text(source_meta.get(key))
        observed = _pandoc_meta_text(document_meta.get(key))
        compared_meta[key] = {"source": expected, "document": observed, "matched": expected == observed}
        if expected != observed:
            failures.append(f"document metadata did not preserve source {key}")
    return {"status": "PASS" if not failures else "FAIL", "source": file_fact(source), "artifact": file_fact(document), "pandoc": {"path": str(executable.resolve()), "sha256": sha256_file(executable), "version": version}, "sourceProjection": source_projection, "documentProjection": document_projection, "metadata": compared_meta, "failures": failures, "boundary": "PASS establishes normalized Markdown->DOCX semantic correspondence through the locked Pandoc parser on both sides. The builder and semantic parser share Pandoc and therefore this is not independent IV&V; Word target behavior, visual review and accessibility remain separate gates."}


def verify_document_dependencies(request_path: Path, document: Path, pandoc: Path | None = None, pandoc_archive: Path | None = None, toolchain_lock: Path | None = None, openxml_validator: Path | None = None) -> dict[str, Any]:
    validation = validate_delivery_request(request_path)
    plan = compile_delivery_plan(request_path)
    lock_path = toolchain_lock or ROOT / "artifact-delivery/toolchain-v1.lock.json"
    executable = pandoc or _selected_external_file("ARTIFACT_PANDOC", GLOBAL_PANDOC, ROOT / ".cache/artifact-toolchain/pandoc/current/bin/pandoc")
    archive = pandoc_archive or _selected_external_file("ARTIFACT_PANDOC_ARCHIVE", GLOBAL_PANDOC_ARCHIVE, ROOT / ".cache/artifact-toolchain/pandoc/pandoc-3.10.2-linux-amd64.tar.gz")
    validator = openxml_validator or Path(os.environ.get("ARTIFACT_OPENXML_VALIDATOR", "/root/.local/share/ordivon-workstation/artifact-openxml-v1/current/bin/validate-openxml"))
    failures: list[str] = []
    if validation.get("status") != "PASS":
        failures.append("delivery request did not PASS exact input validation")
    if plan.get("status") != "PASS" or plan.get("artifactClass") != "document" or plan.get("buildAdapter") != "pandoc-docx":
        failures.append("delivery plan did not select the mature pandoc-docx document adapter")
    try:
        lock = load_json(lock_path)
        pandoc_lock = lock.get("pandoc", {}) if isinstance(lock, dict) else {}
    except Exception as error:
        pandoc_lock = {}
        failures.append(f"toolchain lock could not be read: {error}")
    pandoc_fact: dict[str, Any] = {"path": str(executable)}
    if not executable.is_file() or not os.access(executable, os.X_OK):
        failures.append("locked Pandoc executable is unavailable")
    else:
        proc = subprocess.run([str(executable), "--version"], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=20)
        version_line = proc.stdout.splitlines()[0] if proc.returncode == 0 and proc.stdout else ""
        digest = sha256_file(executable)
        expected_version = str(pandoc_lock.get("version", ""))
        expected_digest = pandoc_lock.get("binarySha256")
        pandoc_fact = {**file_fact(executable), "version": version_line, "expectedVersion": f"pandoc {expected_version}", "versionMatched": version_line == f"pandoc {expected_version}", "expectedSha256": expected_digest, "digestMatched": digest == expected_digest}
        if not pandoc_fact["versionMatched"]:
            failures.append("Pandoc version does not match the toolchain lock")
        if not pandoc_fact["digestMatched"]:
            failures.append("Pandoc binary digest does not match the toolchain lock")
    archive_fact: dict[str, Any] = {"path": str(archive)}
    if not archive.is_file():
        failures.append("locked Pandoc release archive is unavailable")
    else:
        expected_archive = pandoc_lock.get("linuxAmd64ArchiveSha256")
        archive_fact = {**file_fact(archive), "expectedSha256": expected_archive, "digestMatched": sha256_file(archive) == expected_archive}
        if not archive_fact["digestMatched"]:
            failures.append("Pandoc release archive digest does not match the toolchain lock")
    validator_fact: dict[str, Any] = {"path": str(validator)}
    if not validator.is_file() or not os.access(validator, os.X_OK):
        failures.append("locked Open XML validator runtime is unavailable")
    else:
        validator_fact = file_fact(validator)
    resolved = validation.get("resolved", {}) if isinstance(validation.get("resolved"), dict) else {}
    return {"status": "PASS" if not failures else "FAIL", "artifact": file_fact(document), "request": file_fact(request_path), "profile": resolved.get("profile"), "source": resolved.get("source"), "declaredMaterials": resolved.get("materials", []), "pandoc": pandoc_fact, "pandocReleaseArchive": archive_fact, "openXmlValidator": validator_fact, "toolchainLock": file_fact(lock_path) if lock_path.is_file() else {"path": str(lock_path)}, "failures": failures, "boundary": "Dependency PASS binds the exact request/source/profile plus locked Pandoc builder bytes, official release archive digest, and Open XML validator availability. It does not establish Microsoft Word target behavior, PDF companion correctness, accessibility, visual acceptance, or release-signature authenticity."}



















def build_presentation_source(
    source_path: Path,
    profile_path: Path,
    output_path: Path,
    source_schema_path: Path = DEFAULT_PRESENTATION_SOURCE_SCHEMA,
) -> dict[str, Any]:
    return presentation_build_source(
        source_path, profile_path, output_path, source_schema_path, hooks=_presentation_build_hooks()
    )





def _normalized_posix_relative(value: str, field: str) -> PurePosixPath:
    if not isinstance(value, str) or not value or "\\" in value:
        raise RuntimeError(f"{field} must be one normalized POSIX relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or str(path) != value or value in {".", ""}:
        raise RuntimeError(f"{field} must be one normalized POSIX relative path")
    return path


def _normalized_sha256(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise RuntimeError(f"{field} must be sha256:<64-hex>")
    lowered = value.lower()
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", lowered):
        raise RuntimeError(f"{field} must be sha256:<64-hex>")
    return lowered


def project_opc_members(package_path: Path, manifest_path: Path, output_root: Path) -> dict[str, Any]:
    validation = validate_json_document(
        manifest_path,
        DEFAULT_OPC_MEMBER_PROJECTION_SCHEMA,
        "artifact-delivery-opc-member-projection",
    )
    if validation.get("status") != "PASS":
        return {
            "status": "FAIL",
            "package": file_fact(package_path) if package_path.is_file() else {"path": str(package_path)},
            "manifest": file_fact(manifest_path),
            "failures": ["OPC member projection manifest schema did not PASS"],
            "validation": validation,
        }
    manifest = validation["document"]
    if package_path.is_symlink():
        raise RuntimeError("OPC parent package must be one regular non-symlink file")
    package = package_path.resolve()
    if not package.is_file():
        raise RuntimeError("OPC parent package must be one regular non-symlink file")
    parent_digest = "sha256:" + sha256_file(package)
    expected_parent = _normalized_sha256(manifest["parentPackage"]["sha256"], "parentPackage.sha256")
    if parent_digest != expected_parent:
        raise RuntimeError(f"OPC parent package digest mismatch: expected {expected_parent}, observed {parent_digest}")
    expected_parent_size = int(manifest["parentPackage"]["expectedSizeBytes"])
    if package.stat().st_size != expected_parent_size:
        raise RuntimeError(
            f"OPC parent package size mismatch: expected {expected_parent_size}, observed {package.stat().st_size}"
        )
    if not zipfile.is_zipfile(package):
        raise RuntimeError("OPC parent package is not a ZIP/OPC package")

    if output_root.exists() and output_root.is_symlink():
        raise RuntimeError("OPC projection output root must be a real directory")
    root = output_root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    if not root.is_dir():
        raise RuntimeError("OPC projection output root must be a real directory")

    projected: list[dict[str, Any]] = []
    replayed = 0
    declared_parts: set[str] = set()
    declared_outputs: set[str] = set()
    with zipfile.ZipFile(package) as archive:
        all_infos = archive.infolist()
        unsafe = _safe_zip_names(info.filename for info in all_infos)
        if unsafe:
            raise RuntimeError(f"OPC package contains unsafe member paths: {unsafe[:5]}")
        by_name: dict[str, list[zipfile.ZipInfo]] = {}
        for info in all_infos:
            by_name.setdefault(info.filename, []).append(info)

        for index, raw in enumerate(manifest["members"]):
            part = str(_normalized_posix_relative(raw["part"], f"members[{index}].part"))
            output_relative = _normalized_posix_relative(
                raw["outputRelativePath"], f"members[{index}].outputRelativePath"
            )
            expected_digest = _normalized_sha256(raw["sha256"], f"members[{index}].sha256")
            expected_size = int(raw["expectedSizeBytes"])
            if part in declared_parts:
                raise RuntimeError(f"OPC projection manifest duplicates part: {part}")
            if str(output_relative) in declared_outputs:
                raise RuntimeError(f"OPC projection manifest duplicates outputRelativePath: {output_relative}")
            declared_parts.add(part)
            declared_outputs.add(str(output_relative))
            matches = by_name.get(part, [])
            if len(matches) != 1:
                raise RuntimeError(f"OPC projected part must occur exactly once: {part} count={len(matches)}")
            info = matches[0]
            if info.is_dir():
                raise RuntimeError(f"OPC projected part is a directory: {part}")
            if info.flag_bits & 0x1:
                raise RuntimeError(f"OPC projected part is encrypted and not admitted: {part}")
            if info.file_size != expected_size:
                raise RuntimeError(
                    f"OPC projected part size mismatch for {part}: expected {expected_size}, observed {info.file_size}"
                )
            data = archive.read(info)
            observed_digest = "sha256:" + hashlib.sha256(data).hexdigest()
            if observed_digest != expected_digest:
                raise RuntimeError(
                    f"OPC projected part digest mismatch for {part}: expected {expected_digest}, observed {observed_digest}"
                )

            target = root.joinpath(*output_relative.parts)
            target_parent = target.parent
            target_parent.mkdir(parents=True, exist_ok=True)
            cursor = root
            for component in output_relative.parts[:-1]:
                cursor = cursor / component
                if cursor.is_symlink():
                    raise RuntimeError(f"OPC projection output parent is a symlink: {cursor}")
            if target.exists() or target.is_symlink():
                if target.is_symlink() or not target.is_file():
                    raise RuntimeError(f"OPC projection target is not a regular file: {target}")
                existing_digest = "sha256:" + sha256_file(target)
                if target.stat().st_size != expected_size or existing_digest != expected_digest:
                    raise RuntimeError(f"OPC projection refuses to overwrite conflicting target: {target}")
                replayed += 1
            else:
                temporary = target.with_name(f".{target.name}.{os.getpid()}.part")
                if temporary.exists() or temporary.is_symlink():
                    temporary.unlink()
                try:
                    with temporary.open("xb") as handle:
                        handle.write(data)
                        handle.flush()
                        os.fsync(handle.fileno())
                    if temporary.stat().st_size != expected_size or "sha256:" + sha256_file(temporary) != expected_digest:
                        raise RuntimeError(f"OPC projected temporary bytes changed before commit: {part}")
                    os.replace(temporary, target)
                finally:
                    if temporary.exists():
                        temporary.unlink()
            projected.append({
                "part": part,
                "outputRelativePath": str(output_relative),
                "expectedSizeBytes": expected_size,
                "sha256": expected_digest,
                "output": file_fact(target),
            })
    return {
        "status": "PASS",
        "kind": "artifact-delivery-opc-member-projection-receipt",
        "truthRole": "exact-package-part-byte-projection-only-not-domain-or-visual-acceptance",
        "package": file_fact(package),
        "manifest": file_fact(manifest_path),
        "projectionId": manifest["projectionId"],
        "outputRoot": str(root),
        "members": projected,
        "replayedMemberCount": replayed,
        "nonClaims": [
            "no provider/source identity beyond the parent package binding",
            "no visual parity claim",
            "no accessibility claim",
            "no business-content validation claim",
        ],
    }


def compose_reference_hybrid_source(
    semantic_source_path: Path,
    reference_map_path: Path,
    visual_root: Path,
    output_path: Path,
) -> dict[str, Any]:
    semantic_validation = validate_json_document(
        semantic_source_path,
        DEFAULT_PRESENTATION_SOURCE_SCHEMA,
        "presentation-source",
    )
    reference_validation = validate_json_document(
        reference_map_path,
        DEFAULT_PRESENTATION_SOURCE_SCHEMA,
        "presentation-source",
    )
    if semantic_validation.get("status") != "PASS" or reference_validation.get("status") != "PASS":
        return {
            "status": "FAIL",
            "failures": ["semantic source and reference map must both pass the presentation-source schema"],
            "semanticValidation": semantic_validation,
            "referenceValidation": reference_validation,
        }
    semantic = json.loads(json.dumps(semantic_validation["document"]))
    reference = reference_validation["document"]
    failures: list[str] = []
    for field in ("profileId", "aspectRatio", "slideSizeInches"):
        if semantic.get(field) != reference.get(field):
            failures.append(f"semantic/reference {field} mismatch")
    semantic_slides = semantic.get("slides", [])
    reference_slides = reference.get("slides", [])
    if len(semantic_slides) != len(reference_slides):
        failures.append("semantic/reference slide count mismatch")
    root = visual_root.resolve()
    width = float(semantic.get("slideSizeInches", {}).get("width", 0))
    height = float(semantic.get("slideSizeInches", {}).get("height", 0))
    for index, (slide, ref_slide) in enumerate(zip(semantic_slides, reference_slides), 1):
        if slide.get("id") != ref_slide.get("id"):
            failures.append(f"slide identity mismatch at index {index}")
            continue
        legacy = ref_slide.get("legacySource")
        if not isinstance(legacy, dict) or int(legacy.get("slideIndex", -1)) != index:
            failures.append(f"reference map lacks exact legacySource binding for slide {index}")
            continue
        digest = _normalized_sha256("sha256:" + str(legacy.get("sha256", "")), f"slides[{index-1}].legacySource.sha256")
        visual = root / f"slide-{index:02d}.jpeg"
        if not visual.is_file() or visual.is_symlink():
            failures.append(f"projected visual is absent/non-regular for slide {index}: {visual}")
            continue
        observed = "sha256:" + sha256_file(visual)
        if observed != digest:
            failures.append(f"projected visual digest mismatch for slide {index}: expected {digest}, observed {observed}")
            continue
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_parent = output_path.resolve().parent
        relative_visual = os.path.relpath(visual, output_parent).replace(os.sep, "/")
        image = {
            "kind": "image",
            "id": "frozen-visual-authority",
            "path": relative_visual,
            "sha256": digest.removeprefix("sha256:"),
            "box": {"x": 0.0, "y": 0.0, "w": width, "h": height},
            "decorative": False,
            "altText": (
                f"Frozen visual authority for slide {index}; native semantic overlays remain independently editable, "
                "and accessibility/use review is still required."
            ),
        }
        elements = slide.get("elements")
        if not isinstance(elements, list):
            failures.append(f"semantic slide elements are invalid for slide {index}")
            continue
        if any(element.get("id") == image["id"] for element in elements if isinstance(element, dict)):
            failures.append(f"semantic slide already contains reserved hybrid element id on slide {index}")
            continue
        slide["elements"] = [image, *elements]
    if failures:
        return {
            "status": "FAIL",
            "semanticSource": file_fact(semantic_source_path),
            "referenceMap": file_fact(reference_map_path),
            "failures": failures,
        }
    semantic["presentationId"] = str(semantic.get("presentationId", "presentation")) + "-hybrid"
    note = str(semantic.get("notes") or "").strip()
    boundary = (
        "Hybrid source mechanically composes frozen raster visual authority beneath native semantic overlays. "
        "Decorative raster standing is composition-only; accessibility, visual parity, target-render and business-content acceptance remain independent gates."
    )
    semantic["notes"] = (note + " " + boundary).strip()
    write_json(output_path, semantic)
    validation = validate_json_document(output_path, DEFAULT_PRESENTATION_SOURCE_SCHEMA, "presentation-source")
    if validation.get("status") != "PASS":
        return {
            "status": "FAIL",
            "semanticSource": file_fact(semantic_source_path),
            "referenceMap": file_fact(reference_map_path),
            "hybridSource": file_fact(output_path),
            "failures": ["composed hybrid source failed presentation-source schema"],
            "validation": validation,
        }
    return {
        "status": "PASS",
        "kind": "artifact-delivery-reference-hybrid-source-receipt",
        "truthRole": "frozen-raster-plus-native-semantic-composition-only-not-acceptance",
        "semanticSource": file_fact(semantic_source_path),
        "referenceMap": file_fact(reference_map_path),
        "hybridSource": file_fact(output_path),
        "visualRoot": str(root),
        "slideCount": len(semantic_slides),
        "nonClaims": [
            "no accessibility claim",
            "no visual parity claim",
            "no Microsoft PowerPoint target claim",
            "no business-content validation claim",
        ],
    }


def _safe_zip_names(names: Iterable[str]) -> list[str]:
    bad: list[str] = []
    for name in names:
        p = PurePosixPath(name)
        if p.is_absolute() or ".." in p.parts:
            bad.append(name)
    return bad


def _relationship_base(rels_name: str) -> str:
    if rels_name == "_rels/.rels":
        return ""
    marker = "/_rels/"
    if marker not in rels_name or not rels_name.endswith(".rels"):
        return ""
    left, right = rels_name.split(marker, 1)
    owner = posixpath.join(left, right[:-5])
    return posixpath.dirname(owner)


def _resolve_relationship_target(base: str, target: str) -> str | None:
    target = target.split("#", 1)[0]
    parsed = urllib.parse.urlparse(target)
    if parsed.scheme:
        return None
    if target.startswith("/"):
        resolved = posixpath.normpath(target.lstrip("/"))
    else:
        resolved = posixpath.normpath(posixpath.join(base, target))
    if resolved.startswith("../") or resolved == "..":
        return None
    return resolved


def inspect_pptx(path: Path, placeholder_patterns: Iterable[str] = ()) -> dict[str, Any]:
    artifact = file_fact(path)
    failures: list[str] = []
    warnings: list[str] = []
    unresolved_relationships: list[dict[str, str]] = []
    font_names: set[str] = set()
    render_explicit_font_names: set[str] = set()
    placeholder_hits: list[dict[str, str]] = []
    slide_count = 0
    hidden_slides = 0
    slide_size: dict[str, int] | None = None

    if not zipfile.is_zipfile(path):
        return {"status": "FAIL", "artifact": artifact, "failures": ["not a ZIP/OPC package"]}

    with zipfile.ZipFile(path) as package:
        names = set(package.namelist())
        unsafe = _safe_zip_names(names)
        if unsafe:
            failures.append(f"unsafe package paths: {unsafe[:5]}")
        required = {
            "[Content_Types].xml",
            "_rels/.rels",
            "ppt/presentation.xml",
            "ppt/_rels/presentation.xml.rels",
        }
        missing = sorted(required - names)
        if missing:
            failures.append("missing required OPC/PPTX parts: " + ", ".join(missing))

        for rels_name in sorted(n for n in names if n.endswith(".rels")):
            try:
                root = ET.fromstring(package.read(rels_name))
            except Exception as error:
                failures.append(f"invalid relationships XML {rels_name}: {error}")
                continue
            base = _relationship_base(rels_name)
            for rel in root.findall(f"{{{OOXML_REL_NS}}}Relationship"):
                if rel.attrib.get("TargetMode") == "External":
                    continue
                target = rel.attrib.get("Target", "")
                resolved = _resolve_relationship_target(base, target)
                if resolved is None:
                    warnings.append(f"unresolved non-file relationship target in {rels_name}: {target}")
                    continue
                if resolved not in names:
                    unresolved_relationships.append({"rels": rels_name, "target": target, "resolved": resolved})
        if unresolved_relationships:
            failures.append(f"{len(unresolved_relationships)} internal relationship target(s) are missing")

        if "ppt/presentation.xml" in names:
            try:
                root = ET.fromstring(package.read("ppt/presentation.xml"))
                ids = root.findall(f".//{{{PRESENTATION_NS}}}sldId")
                slide_count = len(ids)
                size_node = root.find(f".//{{{PRESENTATION_NS}}}sldSz")
                if size_node is not None:
                    try:
                        cx = int(size_node.attrib.get("cx", "0"))
                        cy = int(size_node.attrib.get("cy", "0"))
                        if cx > 0 and cy > 0:
                            slide_size = {"cx": cx, "cy": cy}
                    except (TypeError, ValueError):
                        pass
            except Exception as error:
                failures.append(f"invalid ppt/presentation.xml: {error}")

        patterns = [re.compile(p, re.IGNORECASE) for p in placeholder_patterns]
        render_xml_names = sorted(
            n
            for n in names
            if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)
            or re.fullmatch(r"ppt/slideLayouts/slideLayout\d+\.xml", n)
            or re.fullmatch(r"ppt/slideMasters/slideMaster\d+\.xml", n)
        )
        for xml_name in render_xml_names:
            try:
                root = ET.fromstring(package.read(xml_name))
            except Exception as error:
                failures.append(f"invalid render-relevant XML {xml_name}: {error}")
                continue
            is_slide = bool(re.fullmatch(r"ppt/slides/slide\d+\.xml", xml_name))
            if is_slide and root.attrib.get("show") in {"0", "false", "False"}:
                hidden_slides += 1
            if is_slide:
                texts = [node.text or "" for node in root.findall(f".//{{{DRAWING_NS}}}t")]
                joined = "\n".join(texts)
                for pattern in patterns:
                    match = pattern.search(joined)
                    if match:
                        placeholder_hits.append({"slide": xml_name, "pattern": pattern.pattern, "match": match.group(0)})
            for node in root.iter():
                typeface = node.attrib.get("typeface")
                if typeface and not typeface.startswith("+"):
                    font_names.add(typeface)
                    render_explicit_font_names.add(typeface)

        for xml_name in sorted(n for n in names if n.startswith("ppt/theme/") and n.endswith(".xml")):
            try:
                root = ET.fromstring(package.read(xml_name))
            except Exception:
                continue
            for node in root.iter():
                typeface = node.attrib.get("typeface")
                if typeface and not typeface.startswith("+"):
                    font_names.add(typeface)

    if slide_count <= 0:
        failures.append("presentation has no slides")
    if placeholder_hits:
        failures.append(f"placeholder text found in {len(placeholder_hits)} slide occurrence(s)")
    return {
        "status": "PASS" if not failures else "FAIL",
        "artifact": artifact,
        "package": {
            "kind": "OOXML/OPC PPTX",
            "slideCount": slide_count,
            "hiddenSlideCount": hidden_slides,
            "slideSizeEmu": slide_size,
            "aspectRatio": (round(slide_size["cx"] / slide_size["cy"], 8) if slide_size else None),
            "referencedTypefaceNames": sorted(font_names),
            "renderExplicitTypefaceNames": sorted(render_explicit_font_names),
            "unresolvedRelationships": unresolved_relationships,
            "placeholderHits": placeholder_hits,
        },
        "scope": {
            "packageChecks": "performed",
            "OOXMLSchemaValidation": "NOT_RUN",
            "note": "Package/relationship/XML checks do not replace an ISO/IEC 29500 schema validator such as Open XML SDK validation.",
        },
        "warnings": warnings,
        "failures": failures,
    }


def verify_openxml_evidence(evidence_path: Path, artifact: Path) -> dict[str, Any]:
    value = load_json(evidence_path)
    failures: list[str] = []
    expected_digest = sha256_file(artifact)
    if value.get("artifact", {}).get("sha256") != expected_digest:
        failures.append("Open XML validation evidence artifact digest mismatch")
    validator = value.get("validator", {})
    if validator.get("implementation") != "DocumentFormat.OpenXml":
        failures.append("Open XML validation evidence did not use DocumentFormat.OpenXml")
    if validator.get("api") != "OpenXmlValidator":
        failures.append("Open XML validation evidence did not use OpenXmlValidator")
    if not validator.get("packageVersion"):
        failures.append("Open XML validation evidence omitted package version")
    if value.get("status") != "PASS":
        failures.append("Open XML validator did not PASS")
    if int(value.get("validationErrorCount", -1)) != 0:
        failures.append("Open XML validator reported validation errors")
    return {
        "status": "PASS" if not failures else "FAIL",
        "evidencePath": str(evidence_path.resolve()),
        "validator": validator,
        "failures": failures,
    }


def verify_presentation_semantics(profile: dict[str, Any], pptx_result: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    package = pptx_result.get("package", {})
    slide_count = int(package.get("slideCount", 0))
    policy = profile.get("semanticPolicy", {})
    minimum = policy.get("minimumSlideCount")
    maximum = policy.get("maximumSlideCount")
    if isinstance(minimum, int) and slide_count < minimum:
        failures.append(f"slide count {slide_count} is below minimum {minimum}")
    if isinstance(maximum, int) and slide_count > maximum:
        failures.append(f"slide count {slide_count} exceeds maximum {maximum}")
    declared_aspect = profile.get("aspectRatio")
    observed = package.get("aspectRatio")
    target_ratios = {"16:9": 16 / 9, "4:3": 4 / 3}
    if declared_aspect in target_ratios:
        if not isinstance(observed, (int, float)):
            failures.append("presentation slide size/aspect ratio is unavailable")
        elif abs(float(observed) - target_ratios[declared_aspect]) > 0.002:
            failures.append(f"presentation aspect ratio {observed:.6f} does not satisfy profile {declared_aspect}")
    return {
        "status": "PASS" if not failures else "FAIL",
        "slideCount": slide_count,
        "minimumSlideCount": minimum,
        "maximumSlideCount": maximum,
        "declaredAspectRatio": declared_aspect,
        "observedAspectRatio": observed,
        "slideSizeEmu": package.get("slideSizeEmu"),
        "failures": failures,
    }


def verify_font_manifest(
    profile: dict[str, Any],
    font_dir: Path,
    observed_typefaces: Iterable[str] = (),
) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    failures: list[str] = []
    declared = {str(font.get("family", "")).casefold(): str(font.get("family", "")) for font in profile.get("fonts", [])}
    observed = sorted({str(name) for name in observed_typefaces if str(name)})
    undeclared = [name for name in observed if name.casefold() not in declared]
    for name in undeclared:
        failures.append(f"artifact render graph directly references undeclared typeface: {name}")
    for font in profile.get("fonts", []):
        family = str(font.get("family", ""))
        required = bool(font.get("required"))
        files: list[dict[str, Any]] = []
        for filename in font.get("targetFiles", []):
            path = font_dir / str(filename)
            present = path.is_file() and not path.is_symlink()
            fact = {
                "name": str(filename),
                "path": str(path),
                "present": present,
                "sha256": sha256_file(path) if present else None,
            }
            files.append(fact)
            if required and not present:
                failures.append(f"required font file missing for {family}: {filename}")
        if required and not font.get("targetFiles"):
            failures.append(f"required font {family} has no targetFiles binding")
        results.append(
            {
                "family": family,
                "required": required,
                "embeddingPermission": font.get("embeddingPermission"),
                "files": files,
            }
        )
    return {
        "status": "PASS" if not failures else "FAIL",
        "fontDirectory": str(font_dir),
        "observedRenderExplicitTypefaces": observed,
        "undeclaredObservedTypefaces": undeclared,
        "fonts": results,
        "failures": failures,
    }


def verify_pdf(path: Path) -> dict[str, Any]:
    artifact = file_fact(path)
    qpdf = shutil.which("qpdf")
    if not qpdf:
        return {
            "status": "FAIL",
            "artifact": artifact,
            "validator": "qpdf",
            "error": "qpdf is not installed",
            "profileValidation": "NOT_RUN",
        }
    proc = subprocess.run(
        [qpdf, "--check", str(path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=30,
    )
    return {
        "status": "PASS" if proc.returncode == 0 else "FAIL",
        "artifact": artifact,
        "validator": qpdf,
        "exitCode": proc.returncode,
        "stdout": proc.stdout.strip()[:4000],
        "stderr": proc.stderr.strip()[:4000],
        "profileValidation": "NOT_RUN",
        "note": "qpdf structural checking does not establish PDF/A or PDF/UA conformance; use veraPDF/PAC in those profiles.",
    }


def _verapdf_executable() -> Path | None:
    configured = os.environ.get("ARTIFACT_VERAPDF")
    if configured:
        path = Path(configured)
        return path if path.is_file() else None
    if GLOBAL_VERAPDF.is_file():
        return GLOBAL_VERAPDF
    local = ROOT / ".cache/artifact-toolchain/verapdf/current/verapdf"
    if local.is_file():
        return local
    system = shutil.which("verapdf")
    return Path(system) if system else None


def verify_pdf_conformance(path: Path, flavour: str) -> dict[str, Any]:
    artifact = file_fact(path)
    if flavour not in {"4", "4f", "4e", "ua1", "ua2", "wt1r", "wt1a"}:
        return {"status": "FAIL", "artifact": artifact, "flavour": flavour, "error": "unsupported veraPDF flavour"}
    executable = _verapdf_executable()
    if executable is None:
        return {"status": "NOT_RUN", "artifact": artifact, "flavour": flavour, "error": "veraPDF is not installed"}
    proc = subprocess.run(
        [str(executable), "--format", "json", "--flavour", flavour, str(path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=60,
    )
    compliant = False
    profile_name: str | None = None
    failed_rules: int | None = None
    failed_checks: int | None = None
    parse_error: str | None = None
    try:
        parsed = json.loads(proc.stdout)
        validation = parsed["report"]["jobs"][0]["validationResult"][0]
        compliant = validation.get("compliant") is True
        profile_name = validation.get("profileName")
        details = validation.get("details", {})
        failed_rules = details.get("failedRules")
        failed_checks = details.get("failedChecks")
    except Exception as error:
        parse_error = str(error)
    return {
        "status": "PASS" if compliant and proc.returncode == 0 else "FAIL",
        "artifact": artifact,
        "validator": {"implementation": "veraPDF", "executable": str(executable), "flavour": flavour},
        "profileName": profile_name,
        "compliant": compliant,
        "failedRules": failed_rules,
        "failedChecks": failed_checks,
        "exitCode": proc.returncode,
        "parseError": parse_error,
        "stderr": proc.stderr.strip()[:4000],
        "boundary": "veraPDF conformance is machine-checkable profile evidence only; human accessibility/use review and target-viewer acceptance remain separate gates.",
    }


def verify_openxml_artifact(path: Path) -> dict[str, Any]:
    artifact = file_fact(path)
    validator = Path(os.environ.get("ARTIFACT_OPENXML_VALIDATOR", "/root/.local/share/ordivon-workstation/artifact-openxml-v1/current/bin/validate-openxml"))
    if not validator.is_file():
        return {
            "status": "NOT_RUN",
            "artifact": artifact,
            "error": "DocumentFormat.OpenXml validator runtime is unavailable",
        }
    proc = subprocess.run(
        [str(validator), str(path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=60,
    )
    parsed: dict[str, Any] | None = None
    parse_error: str | None = None
    try:
        parsed = json.loads(proc.stdout)
    except Exception as error:
        parse_error = str(error)
    return {
        "status": "PASS" if proc.returncode == 0 and parsed and parsed.get("status") == "PASS" else "FAIL",
        "artifact": artifact,
        "validatorOutput": parsed,
        "exitCode": proc.returncode,
        "parseError": parse_error,
        "stderr": proc.stderr.strip()[:4000],
        "boundary": "DocumentFormat.OpenXml schema/semantic validation only; Office target rendering, visual acceptance and delivery remain independent.",
    }


def _vnu_jar() -> Path | None:
    configured = os.environ.get("ARTIFACT_VNU")
    if configured:
        path = Path(configured)
        return path if path.is_file() else None
    if GLOBAL_VNU.is_file():
        return GLOBAL_VNU
    local = ROOT / ".cache/artifact-toolchain/vnu/vnu.jar"
    return local if local.is_file() else None


def verify_html_conformance(path: Path) -> dict[str, Any]:
    artifact = file_fact(path)
    jar = _vnu_jar()
    java = shutil.which("java")
    if jar is None or java is None:
        return {
            "status": "NOT_RUN",
            "artifact": artifact,
            "error": "Nu Html Checker or Java is unavailable",
        }
    proc = subprocess.run(
        [java, "-jar", str(jar), "--format", "json", str(path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=60,
    )
    parsed: dict[str, Any] | None = None
    messages: list[Any] = []
    version: str | None = None
    parse_error: str | None = None
    try:
        payload = proc.stdout.strip() or proc.stderr.strip()
        parsed = json.loads(payload)
        messages = parsed.get("messages", []) if isinstance(parsed, dict) else []
        version = parsed.get("version") if isinstance(parsed, dict) else None
    except Exception as error:
        parse_error = str(error)
    return {
        "status": "PASS" if proc.returncode == 0 and parsed is not None and not messages else "FAIL",
        "artifact": artifact,
        "validator": {
            "implementation": "Nu Html Checker",
            "version": version,
            "jar": str(jar),
            "jarSha256": sha256_file(jar),
        },
        "messageCount": len(messages),
        "messages": messages[:100],
        "exitCode": proc.returncode,
        "parseError": parse_error,
        "stderr": proc.stderr.strip()[:4000],
        "boundary": "Nu Html Checker conformance evidence covers HTML/CSS/SVG syntax/content-model checks; browser behavior, accessibility and deployed-origin behavior remain independent.",
    }


def verify_web_local(path: Path) -> dict[str, Any]:
    artifact = file_fact(path)
    node = shutil.which("node")
    verifier = ROOT / "artifact-delivery/node/verify_html.mjs"
    if node is None or not verifier.is_file():
        return {"status": "NOT_RUN", "artifact": artifact, "error": "Node/Playwright HTML verifier is unavailable"}
    node_env = os.environ.copy()
    if "ARTIFACT_NODE_PACKAGE_ROOT" not in node_env and (GLOBAL_NODE_PACKAGE_ROOT / "package.json").is_file():
        node_env["ARTIFACT_NODE_PACKAGE_ROOT"] = str(GLOBAL_NODE_PACKAGE_ROOT)
    proc = subprocess.run(
        [node, str(verifier), str(path.resolve())],
        cwd=ROOT / "artifact-delivery/node",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=90,
        env=node_env,
    )
    parsed: dict[str, Any] | None = None
    parse_error: str | None = None
    try:
        parsed = json.loads(proc.stdout)
    except Exception as error:
        parse_error = str(error)
    digest_ok = parsed is not None and parsed.get("subject", {}).get("sha256") == artifact["digest"]["sha256"]
    return {
        "status": "PASS" if proc.returncode == 0 and parsed and parsed.get("status") == "PASS" and digest_ok else "FAIL",
        "artifact": artifact,
        "verifierOutput": parsed,
        "digestBound": digest_ok,
        "exitCode": proc.returncode,
        "parseError": parse_error,
        "stderr": proc.stderr.strip()[:4000],
        "boundary": "Local Playwright/axe evidence only; delivery profile policy decides which renderers are required and unsupported-host WebKit cannot be promoted to PASS.",
    }


ni_sha256_uri = trust_vsa.ni_sha256_uri
verification_summary_statement = trust_vsa.verification_summary_statement
verify_verification_summary = trust_vsa.verify_verification_summary
validate_vsa_trust_policy = trust_vsa.validate_vsa_trust_policy
verify_sigstore_vsa_bundle_shape = trust_vsa.verify_sigstore_vsa_bundle_shape
_version_at_least = trust_vsa._version_at_least


def _delivery_trust_toolchain_config() -> trust_vsa.TrustToolchainConfig:
    return trust_vsa.TrustToolchainConfig(
        lock_path=COSIGN_LOCK_PATH,
        selected_binary=COSIGN_SELECTED_BINARY,
        arch_package=COSIGN_ARCH_PACKAGE,
        arch_package_signature=COSIGN_ARCH_PACKAGE_SIGNATURE,
    )


def _cosign_executable() -> Path | None:
    return trust_vsa._cosign_executable(_delivery_trust_toolchain_config())


def _cosign_selection_provenance(
    executable: Path,
    executable_digest: str,
    cosign_lock: dict[str, Any],
) -> dict[str, Any]:
    return trust_vsa._cosign_selection_provenance(
        executable, executable_digest, cosign_lock, _delivery_trust_toolchain_config()
    )


def cosign_tool_fact() -> dict[str, Any]:
    return trust_vsa.cosign_tool_fact(_delivery_trust_toolchain_config())


def verify_signed_verification_summary(
    statement_path: Path,
    bundle_path: Path,
    subject: Path,
    profile_path: Path,
    trust_policy_path: Path,
    signer_id: str,
) -> dict[str, Any]:
    return trust_vsa.verify_signed_verification_summary(
        statement_path,
        bundle_path,
        subject,
        profile_path,
        trust_policy_path,
        signer_id,
        toolchain=_delivery_trust_toolchain_config(),
    )




# Compatibility alias for historical private callers; implementation is owned by artifact_verification.
_write_raw_and_vsa = write_gate_receipt


def _verification_stage_hooks() -> VerificationStageHooks:
    return VerificationStageHooks(
        validate_profile=validate_profile,
        primary_suffix=_primary_suffix,
        verify_openxml_artifact=verify_openxml_artifact,
        validate_delivery_request=validate_delivery_request,
        verify_document_semantic_correspondence=verify_document_semantic_correspondence,
        verify_document_dependencies=verify_document_dependencies,
        inspect_pptx=inspect_pptx,
        verify_presentation_semantics=verify_presentation_semantics,
        verify_pdf=verify_pdf,
        verify_pdf_conformance=verify_pdf_conformance,
        verify_html_conformance=verify_html_conformance,
        verify_web_local=verify_web_local,
    )


def execute_verify_stage(
    profile_path: Path,
    artifact: Path,
    output_dir: Path,
    request_path: Path | None = None,
) -> dict[str, Any]:
    return verification_execute_stage(
        profile_path,
        artifact,
        output_dir,
        request_path,
        hooks=_verification_stage_hooks(),
    )



def aggregate_vsa_gates(
    profile_path: Path,
    subject: Path,
    gate_paths: dict[str, Path],
    allow_local_unsigned: bool = False,
    bundles: dict[str, Path] | None = None,
    trust_policy_path: Path | None = None,
    signer_ids: dict[str, str] | None = None,
) -> dict[str, Any]:
    return trust_vsa.aggregate_vsa_gates(
        profile_path,
        subject,
        gate_paths,
        allow_local_unsigned=allow_local_unsigned,
        bundles=bundles,
        trust_policy_path=trust_policy_path,
        signer_ids=signer_ids,
        toolchain=_delivery_trust_toolchain_config(),
    )


def snapshot_materials(paths: Iterable[Path]) -> dict[str, Any]:
    materials = [file_fact(path) for path in paths]
    return {
        "capturedAt": utc_now(),
        "materials": materials,
        "note": "Operational immutable-input snapshot. Durable build provenance should be emitted as an in-toto Statement/SLSA Provenance predicate.",
    }


def _require_uri(value: str, field: str) -> str:
    parsed = urllib.parse.urlparse(value)
    if not parsed.scheme:
        raise RuntimeError(f"{field} must be a URI")
    return value




def presentation_gate(
    profile_path: Path,
    pptx: Path,
    pdf: Path | None,
    render_dir: Path | None,
    openxml_evidence: Path | None,
    target_evidence: Path | None,
    visual_evidence: Path | None,
    delivery_evidence: Iterable[Path],
    font_dir: Path,
) -> dict[str, Any]:
    profile_result = validate_profile(profile_path)
    profile = profile_result["profile"]
    gates = profile.get("gates", {})
    placeholders = profile.get("semanticPolicy", {}).get("placeholderPatterns", [])
    pptx_result = inspect_pptx(pptx, placeholders)
    slide_count = int(pptx_result.get("package", {}).get("slideCount", 0))
    if openxml_evidence is None:
        openxml_result = {"status": "NOT_RUN", "reason": "no DocumentFormat.OpenXml validation evidence supplied"}
    else:
        openxml_result = verify_openxml_evidence(openxml_evidence, pptx)
    if pptx_result.get("status") != "PASS":
        structural_status = "FAIL"
    elif openxml_result.get("status") != "PASS":
        structural_status = openxml_result.get("status", "FAIL")
    else:
        structural_status = "PASS"
    semantic_result = verify_presentation_semantics(profile, pptx_result)
    font_result = verify_font_manifest(
        profile,
        font_dir,
        pptx_result.get("package", {}).get("renderExplicitTypefaceNames", []),
    )
    pdf_result: dict[str, Any]
    if pdf is None:
        pdf_result = {"status": "NOT_RUN", "reason": "no companion PDF supplied"}
    else:
        pdf_result = verify_pdf(pdf)
    render_result: dict[str, Any]
    if render_dir is None:
        render_result = {"status": "NOT_RUN", "reason": "no rendered PNG directory supplied"}
    else:
        render_result = verify_render_evidence(render_dir, slide_count)
    target_result: dict[str, Any]
    if target_evidence is None:
        target_result = {"status": "NOT_RUN", "reason": "no target PowerPoint evidence supplied"}
    else:
        target_result = verify_target_evidence(target_evidence, pptx, pdf, slide_count, render_result)
    visual_result: dict[str, Any]
    if visual_evidence is None:
        visual_result = {"status": "NOT_RUN", "reason": "no digest-bound visual review evidence supplied"}
    elif render_result.get("status") != "PASS":
        visual_result = {"status": "FAIL", "reason": "render evidence integrity failed before visual review"}
    else:
        visual_result = verify_visual_review(visual_evidence, pptx, render_result)
    delivery_paths = list(delivery_evidence)
    if not delivery_paths:
        delivery_result = {"status": "NOT_RUN", "reason": "no destination read-back evidence supplied"}
    else:
        delivery_result = verify_delivery_evidence(delivery_paths, profile, pptx, pdf)

    component = {
        "profileSchema": profile_result["status"],
        "structural": structural_status,
        "dependency": font_result["status"],
        "semantic": semantic_result["status"],
        "companionPdf": pdf_result["status"],
        "visual": visual_result["status"],
        "target": target_result["status"],
        "deliveryReadback": delivery_result["status"],
    }
    required_failures = [
        name
        for name, required in gates.items()
        if required and (name not in component or component[name] != "PASS")
    ]
    return {
        "status": "PASS" if not required_failures else "FAIL",
        "profileId": profile.get("id"),
        "artifact": file_fact(pptx),
        "requiredGateFailures": required_failures,
        "components": {
            "profile": profile_result,
            "pptx": pptx_result,
            "openXmlValidation": openxml_result,
            "semantic": semantic_result,
            "fonts": font_result,
            "pdf": pdf_result,
            "renders": render_result,
            "visualReview": visual_result,
            "target": target_result,
            "deliveryReadback": delivery_result,
        },
        "truthBoundary": "PASS requires every profile-required gate represented here, including target PowerPoint evidence, visual review, and destination read-back. External delivery adapters still own the actual write/read effects.",
    }


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def emit(value: Any, output: Path | None) -> None:
    if output is not None:
        write_json(output, value)
    print(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False))


def _parse_named_values(items: Iterable[str], option_name: str, path_values: bool = False) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for item in items:
        if "=" not in item:
            raise RuntimeError(f"{option_name} requires name=value")
        name, value = item.split("=", 1)
        if not name or not value or name in result:
            raise RuntimeError(f"duplicate/invalid {option_name} name: {name!r}")
        result[name] = Path(value) if path_values else value
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("validate-profile")
    p.add_argument("profile", type=Path)
    p.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    p.add_argument("--output", type=Path)

    p = sub.add_parser("validate-request")
    p.add_argument("request", type=Path)
    p.add_argument("--schema", type=Path, default=DEFAULT_REQUEST_SCHEMA)
    p.add_argument("--output", type=Path)

    p = sub.add_parser("compile-request")
    p.add_argument("request", type=Path)
    p.add_argument("--output", type=Path)

    p = sub.add_parser("build-request")
    p.add_argument("request", type=Path)
    p.add_argument("--output-directory", type=Path)
    p.add_argument("--output", type=Path)

    p = sub.add_parser("validate-presentation-source")
    p.add_argument("source", type=Path)
    p.add_argument("--schema", type=Path, default=DEFAULT_PRESENTATION_SOURCE_SCHEMA)
    p.add_argument("--output", type=Path)

    p = sub.add_parser("build-presentation-source")
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--profile", type=Path, required=True)
    p.add_argument("--pptx", type=Path, required=True)
    p.add_argument("--source-schema", type=Path, default=DEFAULT_PRESENTATION_SOURCE_SCHEMA)
    p.add_argument("--output", type=Path)

    p = sub.add_parser("project-opc-members")
    p.add_argument("--package", type=Path, required=True)
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--output-root", type=Path, required=True)
    p.add_argument("--output", type=Path)

    p = sub.add_parser("compose-reference-hybrid-source")
    p.add_argument("--semantic-source", type=Path, required=True)
    p.add_argument("--reference-map", type=Path, required=True)
    p.add_argument("--visual-root", type=Path, required=True)
    p.add_argument("--hybrid-source", type=Path, required=True)
    p.add_argument("--output", type=Path)

    p = sub.add_parser("verify-stage")
    p.add_argument("--profile", type=Path, required=True)
    p.add_argument("--artifact", type=Path, required=True)
    p.add_argument("--output-directory", type=Path, required=True)
    p.add_argument("--request", type=Path)
    p.add_argument("--output", type=Path)

    p = sub.add_parser("verify-vsa")
    p.add_argument("--statement", type=Path, required=True)
    p.add_argument("--subject", type=Path, required=True)
    p.add_argument("--profile", type=Path, required=True)
    p.add_argument("--allowed-verifier", action="append", default=[])
    p.add_argument("--output", type=Path)

    p = sub.add_parser("validate-vsa-trust-policy")
    p.add_argument("policy", type=Path)
    p.add_argument("--schema", type=Path, default=DEFAULT_VSA_TRUST_POLICY_SCHEMA)
    p.add_argument("--output", type=Path)

    p = sub.add_parser("verify-signed-vsa")
    p.add_argument("--statement", type=Path, required=True)
    p.add_argument("--bundle", type=Path, required=True)
    p.add_argument("--subject", type=Path, required=True)
    p.add_argument("--profile", type=Path, required=True)
    p.add_argument("--trust-policy", type=Path, required=True)
    p.add_argument("--signer-id", required=True)
    p.add_argument("--output", type=Path)

    p = sub.add_parser("aggregate-vsa-gates")
    p.add_argument("--profile", type=Path, required=True)
    p.add_argument("--subject", type=Path, required=True)
    p.add_argument("--gate", action="append", default=[], help="gateName=path/to/vsa.json")
    p.add_argument("--bundle", action="append", default=[], help="gateName=path/to/sigstore-bundle.json")
    p.add_argument("--signer", action="append", default=[], help="gateName=trusted-signer-id")
    p.add_argument("--trust-policy", type=Path)
    p.add_argument("--allow-local-unsigned", action="store_true")
    p.add_argument("--output", type=Path)

    p = sub.add_parser("inspect-pptx")
    p.add_argument("pptx", type=Path)
    p.add_argument("--placeholder", action="append", default=[])
    p.add_argument("--output", type=Path)

    p = sub.add_parser("verify-pdf")
    p.add_argument("pdf", type=Path)
    p.add_argument("--output", type=Path)

    p = sub.add_parser("verify-pdf-conformance")
    p.add_argument("pdf", type=Path)
    p.add_argument("--flavour", required=True, choices=("4", "4f", "4e", "ua1", "ua2", "wt1r", "wt1a"))
    p.add_argument("--output", type=Path)

    p = sub.add_parser("snapshot")
    p.add_argument("material", type=Path, nargs="+")
    p.add_argument("--output", type=Path, required=True)

    p = sub.add_parser("verify-readback")
    p.add_argument("source", type=Path)
    p.add_argument("readback", type=Path)
    p.add_argument("--destination", required=True)
    p.add_argument("--destination-reference", required=True)
    p.add_argument("--artifact-role", choices=("primary", "companion"), required=True)
    p.add_argument("--output", type=Path)

    p = sub.add_parser("attest-slsa")
    p.add_argument("--profile", type=Path, required=True)
    p.add_argument("--subject", type=Path, action="append", required=True)
    p.add_argument("--material", type=Path, action="append", default=[])
    p.add_argument("--builder-id", required=True)
    p.add_argument("--build-type", required=True)
    p.add_argument("--output", type=Path, required=True)

    p = sub.add_parser("gate-presentation")
    p.add_argument("--profile", type=Path, required=True)
    p.add_argument("--pptx", type=Path, required=True)
    p.add_argument("--pdf", type=Path)
    p.add_argument("--render-dir", type=Path)
    p.add_argument("--openxml-evidence", type=Path)
    p.add_argument("--target-evidence", type=Path)
    p.add_argument("--visual-evidence", type=Path)
    p.add_argument("--delivery-evidence", type=Path, action="append", default=[])
    p.add_argument("--font-dir", type=Path, default=DEFAULT_WINDOWS_FONTS)
    p.add_argument("--output", type=Path)

    args = parser.parse_args()
    try:
        if args.command == "validate-profile":
            value = validate_profile(args.profile, args.schema)
        elif args.command == "validate-request":
            value = validate_delivery_request(args.request, args.schema)
        elif args.command == "compile-request":
            value = compile_delivery_plan(args.request)
        elif args.command == "build-request":
            value = execute_build_stage(args.request, args.output_directory)
        elif args.command == "validate-presentation-source":
            value = validate_json_document(args.source, args.schema, "presentation-source")
        elif args.command == "build-presentation-source":
            value = build_presentation_source(args.source, args.profile, args.pptx, args.source_schema)
        elif args.command == "project-opc-members":
            value = project_opc_members(args.package, args.manifest, args.output_root)
        elif args.command == "compose-reference-hybrid-source":
            value = compose_reference_hybrid_source(
                args.semantic_source, args.reference_map, args.visual_root, args.hybrid_source
            )
        elif args.command == "verify-stage":
            value = execute_verify_stage(args.profile, args.artifact, args.output_directory, args.request)
        elif args.command == "verify-vsa":
            value = verify_verification_summary(args.statement, args.subject, args.profile, args.allowed_verifier)
        elif args.command == "validate-vsa-trust-policy":
            value = validate_vsa_trust_policy(args.policy, args.schema)
        elif args.command == "verify-signed-vsa":
            value = verify_signed_verification_summary(
                args.statement, args.bundle, args.subject, args.profile, args.trust_policy, args.signer_id
            )
        elif args.command == "aggregate-vsa-gates":
            gate_paths = _parse_named_values(args.gate, "--gate", path_values=True)
            bundle_paths = _parse_named_values(args.bundle, "--bundle", path_values=True)
            signer_ids = _parse_named_values(args.signer, "--signer")
            value = aggregate_vsa_gates(
                args.profile,
                args.subject,
                gate_paths,
                args.allow_local_unsigned,
                bundle_paths,
                args.trust_policy,
                signer_ids,
            )
        elif args.command == "inspect-pptx":
            value = inspect_pptx(args.pptx, args.placeholder)
        elif args.command == "verify-pdf":
            value = verify_pdf(args.pdf)
        elif args.command == "verify-pdf-conformance":
            value = verify_pdf_conformance(args.pdf, args.flavour)
        elif args.command == "snapshot":
            value = snapshot_materials(args.material)
        elif args.command == "verify-readback":
            value = verify_readback(
                args.source,
                args.readback,
                args.destination,
                args.destination_reference,
                args.artifact_role,
            )
        elif args.command == "attest-slsa":
            value = slsa_statement(args.subject, args.material, args.profile, args.builder_id, args.build_type)
        elif args.command == "gate-presentation":
            value = presentation_gate(
                args.profile,
                args.pptx,
                args.pdf,
                args.render_dir,
                args.openxml_evidence,
                args.target_evidence,
                args.visual_evidence,
                args.delivery_evidence,
                args.font_dir,
            )
        else:  # pragma: no cover
            raise AssertionError(args.command)
        emit(value, getattr(args, "output", None))
        status = value.get("status") if isinstance(value, dict) else None
        if args.command == "attest-slsa" or args.command == "snapshot":
            return 0
        return 0 if status == "PASS" else 1
    except Exception as error:
        print(json.dumps({"status": "ERROR", "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
