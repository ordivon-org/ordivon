from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping


JsonValidator = Callable[[Path, Path, str | None], dict[str, Any]]
ProfileValidator = Callable[[Path, Path], dict[str, Any]]
SourceValidator = Callable[[Path], tuple[dict[str, Any] | None, list[dict[str, Any]], list[str]]]
FileFact = Callable[[Path], dict[str, Any]]
Sha256File = Callable[[Path], str]


@dataclass(frozen=True)
class AdmissionHooks:
    validate_json_document: JsonValidator
    validate_profile: ProfileValidator
    source_validators: Mapping[str, SourceValidator]
    file_fact: FileFact
    sha256_file: Sha256File


def resolve_request_path(request_path: Path, relative: str) -> Path:
    candidate = Path(relative)
    if candidate.is_absolute():
        return candidate.resolve()
    return (request_path.resolve().parent / candidate).resolve()


def admit_delivery_request(
    request_path: Path,
    *,
    request_schema_path: Path,
    profile_schema_path: Path,
    hooks: AdmissionHooks,
) -> dict[str, Any]:
    """Bind exact request/profile/source/material bytes without executing a build."""
    request_result = hooks.validate_json_document(request_path, request_schema_path, "artifact-delivery-request")
    request = request_result.get("document", {})
    failures = list(request_result.get("failures", []))
    profile_result: dict[str, Any] | None = None
    source_result: dict[str, Any] | None = None
    resolved: dict[str, Any] = {}
    source_material_results: list[dict[str, Any]] = []

    if isinstance(request, dict):
        profile_ref = request.get("profile", {})
        source_ref = request.get("source", {})
        try:
            profile_path = resolve_request_path(request_path, str(profile_ref.get("path", "")))
            if hooks.sha256_file(profile_path) != profile_ref.get("sha256"):
                failures.append("profile digest mismatch")
            profile_result = hooks.validate_profile(profile_path, profile_schema_path)
            if profile_result.get("status") != "PASS":
                failures.append("referenced delivery profile did not PASS validation")
            if profile_result.get("profile", {}).get("id") != profile_ref.get("id"):
                failures.append("profile id does not match referenced profile bytes")
            resolved["profile"] = hooks.file_fact(profile_path)
        except Exception as error:
            failures.append(f"profile reference error: {error}")

        try:
            source_path = resolve_request_path(request_path, str(source_ref.get("path", "")))
            if hooks.sha256_file(source_path) != source_ref.get("sha256"):
                failures.append("source digest mismatch")
            source_kind = str(source_ref.get("kind", ""))
            source_validator = hooks.source_validators.get(source_kind)
            if source_validator is not None:
                source_result, source_material_results, source_failures = source_validator(source_path)
                failures.extend(source_failures)
            resolved["source"] = hooks.file_fact(source_path)
        except Exception as error:
            failures.append(f"source reference error: {error}")

        material_results: list[dict[str, Any]] = list(source_material_results)
        for item in request.get("materials", []) if isinstance(request.get("materials"), list) else []:
            try:
                material_path = resolve_request_path(request_path, str(item.get("path", "")))
                actual = hooks.sha256_file(material_path)
                if actual != item.get("sha256"):
                    failures.append(f"material digest mismatch: {item.get('path')}")
                fact = hooks.file_fact(material_path)
                if not any(
                    existing.get("path") == fact.get("path") and existing.get("digest") == fact.get("digest")
                    for existing in material_results
                ):
                    material_results.append(fact)
            except Exception as error:
                failures.append(f"material reference error: {error}")
        resolved["materials"] = material_results

    if request_result.get("status") != "PASS":
        failures.append("request envelope did not PASS schema validation")
    return {
        "status": "PASS" if not failures else "FAIL",
        "request": request,
        "requestValidation": request_result,
        "profileValidation": profile_result,
        "sourceValidation": source_result,
        "resolved": resolved,
        "failures": failures,
        "boundary": "Request admission binds exact profile/source/material bytes plus schema/source contracts only. It does not establish build success, target rendering, visual acceptance, accessibility or delivery completion.",
    }
