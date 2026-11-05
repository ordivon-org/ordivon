"""Validate and read exact operation-bound native Resolve Runner receipts.

The receipt consumer may read results without loading optional OpenTimelineIO;
a syntactically valid receipt is not proof of a real Resolve host edit.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .resolve_contracts import (
    _DIGEST,
    _OPERATION_ID,
    ASSEMBLY_CONFORM_PROJECT_PREFIX,
    ASSEMBLY_CONFORM_TIMELINE_NAME,
    COMPATIBILITY_PRODUCT_NAME,
    COMPATIBILITY_VERSION_STRING,
    OPERATION_FILENAME,
    RESULT_FILENAME,
    canonical_operation_digest,
)
from .resolve_host import discover_resolve_paths


def validate_result(result: dict[str, Any], *, expected_operation_id: str | None = None) -> list[str]:
    errors: list[str] = []
    if result.get("schemaVersion") != 1:
        errors.append("schemaVersion must be 1")
    if result.get("adapter") != "resolve":
        errors.append("adapter must be resolve")
    action = result.get("action")
    if action not in {
        "probe",
        "create-smoke-project",
        "probe-compatibility",
        "probe-assembly-conform",
    }:
        errors.append("action is unsupported")
    if result.get("status") not in {"succeeded", "failed"}:
        errors.append("status must be succeeded or failed")
    operation_id = result.get("operationId")
    if operation_id is not None and (not isinstance(operation_id, str) or not _OPERATION_ID.fullmatch(operation_id)):
        errors.append("operationId has an invalid format")
    if expected_operation_id is not None and operation_id != expected_operation_id:
        errors.append(f"operationId does not match expected {expected_operation_id}")
    digest = result.get("operationDigest")
    if digest is not None and (not isinstance(digest, str) or not _DIGEST.fullmatch(digest)):
        errors.append("operationDigest is invalid")
    if result.get("status") == "succeeded":
        if action == "probe":
            probe = result.get("probe")
            if not isinstance(probe, dict):
                errors.append("successful probe result must contain probe")
            elif not isinstance(probe.get("capabilities"), dict):
                errors.append("probe must contain capabilities")
        elif action == "create-smoke-project":
            smoke = result.get("smoke")
            if not isinstance(smoke, dict):
                errors.append("successful smoke result must contain smoke")
            else:
                project = smoke.get("project")
                timeline = smoke.get("timeline")
                media = smoke.get("media")
                if not isinstance(project, dict) or not str(project.get("name", "")).startswith("Ordivon Resolve Smoke "):
                    errors.append("smoke result has an invalid project")
                if not isinstance(timeline, dict) or not timeline.get("videoTrackItems"):
                    errors.append("smoke result has no video timeline item")
                if not isinstance(media, dict) or not _DIGEST.fullmatch(str(media.get("digest", ""))):
                    errors.append("smoke result has an invalid media digest")
                if smoke.get("restoredPreviousProject") is not True:
                    errors.append("smoke result did not restore the previous project")
        elif action == "probe-compatibility":
            compatibility = result.get("compatibility")
            if not isinstance(compatibility, dict):
                errors.append("successful compatibility result must contain compatibility")
            else:
                resolve = compatibility.get("resolve")
                cases = compatibility.get("cases")
                summary = compatibility.get("caseSummary")
                if not isinstance(resolve, dict):
                    errors.append("compatibility result has no Resolve identity")
                else:
                    if resolve.get("productName") != COMPATIBILITY_PRODUCT_NAME:
                        errors.append("compatibility result product does not match")
                    if resolve.get("versionString") != COMPATIBILITY_VERSION_STRING:
                        errors.append("compatibility result version does not match")
                    if resolve.get("edition") != "free":
                        errors.append("compatibility result edition does not match")
                if not isinstance(cases, list) or len(cases) != 6:
                    errors.append("compatibility result must contain six cases")
                if not isinstance(summary, dict) or summary.get("total") != 6:
                    errors.append("compatibility case summary is invalid")
                if compatibility.get("restoredPreviousProject") is not True:
                    errors.append("compatibility result did not restore the previous project")
        elif action == "probe-assembly-conform":
            conform = result.get("assemblyConform")
            if not isinstance(conform, dict):
                errors.append("successful assembly conform result must contain assemblyConform")
            else:
                project = conform.get("project")
                timeline = conform.get("timeline")
                segments = conform.get("segments")
                cleanup = conform.get("cleanup")
                resolve = conform.get("resolve")
                if not isinstance(project, dict) or not str(project.get("name", "")).startswith(
                    ASSEMBLY_CONFORM_PROJECT_PREFIX
                ):
                    errors.append("assembly conform result has an invalid project")
                if not isinstance(timeline, dict) or timeline.get("name") != ASSEMBLY_CONFORM_TIMELINE_NAME:
                    errors.append("assembly conform result has an invalid timeline")
                elif timeline.get("totalFrames") != 2340 or timeline.get("videoItemCount") != 11:
                    errors.append("assembly conform timeline structure is incomplete")
                if not isinstance(segments, list) or len(segments) != 11:
                    errors.append("assembly conform result must contain 11 segments")
                if conform.get("placeholderCount") != 8:
                    errors.append("assembly conform placeholder count differs")
                if conform.get("restoredPreviousProject") is not True:
                    errors.append("assembly conform did not restore the previous project")
                if not isinstance(cleanup, dict) or cleanup.get("deleted") is not True:
                    errors.append("assembly conform disposable project was not deleted")
                if not isinstance(resolve, dict) or resolve.get("versionString") != COMPATIBILITY_VERSION_STRING:
                    errors.append("assembly conform Resolve profile differs")
    if result.get("status") == "failed" and not isinstance(result.get("error"), dict):
        errors.append("failed result must contain error")
    encoded = json.dumps(result, ensure_ascii=False, sort_keys=True)
    for forbidden in ("Authorization", "Bearer ", "ORDIVON_BEARER_TOKEN", "\\Users\\", "/root/"):
        if forbidden in encoded:
            errors.append(f"result contains forbidden private material: {forbidden!r}")
    return errors


def validate_probe_result(result: dict[str, Any], *, expected_operation_id: str | None = None) -> list[str]:
    return validate_result(result, expected_operation_id=expected_operation_id)


def read_result(
    *, control_directory: Path | None = None, expected_operation_id: str | None = None
) -> dict[str, Any]:
    control = control_directory or discover_resolve_paths().control_directory
    path = control / RESULT_FILENAME
    if not path.is_file():
        raise FileNotFoundError(path)
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError("Resolve result root must be an object")
    errors = validate_result(value, expected_operation_id=expected_operation_id)
    # The Runner itself keys idempotent success by operationId + exact source
    # digest. A successful readback must not outlive a different staged
    # operation in the same control directory.
    staged_path = control / OPERATION_FILENAME
    if value.get("status") == "succeeded" and staged_path.is_file():
        staged = json.loads(staged_path.read_text(encoding="utf-8-sig"))
        if not isinstance(staged, dict):
            raise ValueError("staged Resolve operation root must be an object")
        if value.get("operationId") != staged.get("operationId"):
            errors.append("result operationId does not match staged operation")
        if value.get("operationDigest") != canonical_operation_digest(staged):
            errors.append("result operationDigest does not match staged operation")
    if errors:
        raise ValueError("; ".join(errors))
    return value
