"""Construct exact Resolve Runner on-wire operations from selected media sources.

The Resolve-private editorial conform composes OpenTimelineIO via the existing
source owner. Only these builders own operation shape, not host execution.
"""

from __future__ import annotations

import datetime as dt
import secrets
from pathlib import Path
from typing import Any

from .assets import hash_file
from .resolve_contracts import (
    _DIGEST,
    _OPERATION_ID,
    ASSEMBLY_CONFORM_PROJECT_PREFIX,
    ASSEMBLY_CONFORM_TIMELINE_NAME,
    COMPATIBILITY_PRODUCT_NAME,
    COMPATIBILITY_PROJECT_PREFIX,
    COMPATIBILITY_VERSION,
    COMPATIBILITY_VERSION_STRING,
    DEVELOPER_README_PATH,
)
from .resolve_editorial import _build_assembly_source_parameters, _write_resolve_assembly_otio


def _new_operation_id(kind: str) -> str:
    timestamp = dt.datetime.now(dt.UTC).strftime("%Y%m%dt%H%M%Sz").lower()
    return f"resolve-{kind}-{timestamp}-{secrets.token_hex(4)}"


def _requested_at() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _validate_operation_id(operation_id: str) -> str:
    if not _OPERATION_ID.fullmatch(operation_id):
        raise ValueError("operationId has an invalid format")
    return operation_id


def build_probe_operation(operation_id: str | None = None) -> dict[str, Any]:
    operation_id = _validate_operation_id(operation_id or _new_operation_id("probe"))
    return {
        "schemaVersion": 1,
        "operationId": operation_id,
        "action": "probe",
        "requestedAt": _requested_at(),
    }


def build_smoke_operation(
    *,
    media_path: str,
    media_digest: str,
    operation_id: str | None = None,
    project_name: str | None = None,
) -> dict[str, Any]:
    operation_id = _validate_operation_id(operation_id or _new_operation_id("smoke"))
    if not _DIGEST.fullmatch(media_digest):
        raise ValueError("mediaDigest must be a sha256 digest")
    suffix = operation_id.removeprefix("resolve-smoke-")
    project_name = project_name or f"Ordivon Resolve Smoke {suffix}"
    if not project_name.startswith("Ordivon Resolve Smoke "):
        raise ValueError("smoke project name must use the reserved prefix")
    return {
        "schemaVersion": 1,
        "operationId": operation_id,
        "action": "create-smoke-project",
        "requestedAt": _requested_at(),
        "parameters": {
            "projectName": project_name,
            "timelineName": "Assembly",
            "binName": "01_SMOKE",
            "mediaPath": media_path,
            "mediaDigest": media_digest,
            "settings": {"frameRate": 30, "width": 1920, "height": 1080},
            "restorePreviousProject": True,
        },
    }


def build_compatibility_operation(
    *,
    media_path: str,
    media_digest: str,
    media_file_name: str,
    media_expected_frames: int,
    otio_path: str,
    otio_digest: str,
    source_clips_path: str,
    developer_package_digest: str,
    operation_id: str | None = None,
) -> dict[str, Any]:
    operation_id = _validate_operation_id(operation_id or _new_operation_id("compatibility"))
    if not _DIGEST.fullmatch(media_digest):
        raise ValueError("mediaDigest must be a sha256 digest")
    if not _DIGEST.fullmatch(otio_digest):
        raise ValueError("otioDigest must be a sha256 digest")
    if not _DIGEST.fullmatch(developer_package_digest):
        raise ValueError("developerPackageDigest must be a sha256 digest")
    if media_expected_frames < 60:
        raise ValueError("compatibility media must contain at least 60 frames")
    suffix = operation_id.removeprefix("resolve-compatibility-")
    return {
        "schemaVersion": 1,
        "operationId": operation_id,
        "action": "probe-compatibility",
        "requestedAt": _requested_at(),
        "parameters": {
            "projectName": COMPATIBILITY_PROJECT_PREFIX + suffix,
            "expectedProductName": COMPATIBILITY_PRODUCT_NAME,
            "expectedVersionString": COMPATIBILITY_VERSION_STRING,
            "expectedVersion": COMPATIBILITY_VERSION,
            "developerPackageDigest": developer_package_digest,
            "mediaPath": media_path,
            "mediaDigest": media_digest,
            "mediaFileName": media_file_name,
            "mediaExpectedFrames": media_expected_frames,
            "otioPath": otio_path,
            "otioDigest": otio_digest,
            "sourceClipsPath": source_clips_path,
            "settings": {"frameRate": 30, "width": 1920, "height": 1080},
            "restorePreviousProject": True,
            "cleanupProject": True,
        },
    }


def build_assembly_conform_operation(
    *,
    production_root: Path,
    media_root: Path,
    windows_media_root: str,
    resolve_otio_path: Path,
    windows_resolve_otio_path: str,
    developer_readme_path: Path = DEVELOPER_README_PATH,
    operation_id: str | None = None,
) -> dict[str, Any]:
    operation_id = _validate_operation_id(operation_id or _new_operation_id("assembly-conform"))
    parameters = _build_assembly_source_parameters(
        production_root=production_root,
        media_root=media_root,
        windows_media_root=windows_media_root,
    )
    suffix = operation_id.removeprefix("resolve-assembly-conform-")
    _write_resolve_assembly_otio(
        resolve_otio_path,
        production_id=parameters["productionId"],
        start_timecode=parameters["startTimecode"],
        segments=parameters["segments"],
    )
    parameters.update(
        {
            "projectName": ASSEMBLY_CONFORM_PROJECT_PREFIX + suffix,
            "timelineName": ASSEMBLY_CONFORM_TIMELINE_NAME,
            "expectedProductName": COMPATIBILITY_PRODUCT_NAME,
            "expectedVersionString": COMPATIBILITY_VERSION_STRING,
            "expectedVersion": COMPATIBILITY_VERSION,
            "developerPackageDigest": hash_file(developer_readme_path).digest,
            "resolveOtioPath": windows_resolve_otio_path,
            "resolveOtioDigest": hash_file(resolve_otio_path).digest,
            "cleanupProject": True,
        }
    )
    return {
        "schemaVersion": 1,
        "operationId": operation_id,
        "action": "probe-assembly-conform",
        "requestedAt": _requested_at(),
        "parameters": parameters,
    }
