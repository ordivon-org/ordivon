"""Pure DaVinci Resolve operation identity and result contracts.

Shared identity patterns and result checks implement the declared Resolve profile,
without probing Windows, running commands, installing scripts, mutating projects,
or acquiring publication authority. Resolve still owns the original result.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from .resolve_editorial import COMPATIBILITY_VERSION_STRING

COMPATIBILITY_PRODUCT_NAME = "DaVinci Resolve"
ASSEMBLY_CONFORM_PROJECT_PREFIX = "Ordivon Runtime Introduction Conform Probe "
ASSEMBLY_CONFORM_TIMELINE_NAME = "Assembly v0 Conform Probe"
_OPERATION_ID = re.compile(r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$")
_DIGEST = re.compile(r"^sha256:[a-f0-9]{64}$")


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



def _canonical_digest(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"
