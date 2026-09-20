from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from .build_bindings import BuildCapabilityBindingRegistry


def compile_delivery_plan_from_validation(
    request_path: Path,
    validation: dict[str, Any],
    *,
    registry: BuildCapabilityBindingRegistry,
    sha256_file: Callable[[Path], str],
) -> dict[str, Any]:
    request = validation.get("request", {})
    profile = (validation.get("profileValidation") or {}).get("profile", {})
    source = request.get("source", {}) if isinstance(request, dict) else {}
    artifact_class = profile.get("artifactClass")
    source_kind = source.get("kind")
    failures = list(validation.get("failures", []))
    binding = None
    try:
        binding = registry.resolve(str(artifact_class), str(source_kind))
    except KeyError:
        failures.append(f"no v1 build adapter for artifactClass={artifact_class!r}, source.kind={source_kind!r}")

    if binding is not None:
        builder = request.get("builder", {}) if isinstance(request, dict) else {}
        if builder.get("id") != binding.builder_id:
            failures.append("request builder.id does not match the selected mature adapter")
        if builder.get("buildType") != binding.build_type:
            failures.append("request builder.buildType does not match the selected mature adapter")

    gates = profile.get("gates", {}) if isinstance(profile, dict) else {}
    required_gates = sorted(name for name, required in gates.items() if required is True)
    expected_outputs = [profile.get("primaryOutput")] + list(profile.get("companions", [])) if profile else []
    return {
        "schemaVersion": 1,
        "kind": "artifact-delivery-derived-plan",
        "status": "PASS" if not failures else "FAIL",
        "requestId": request.get("requestId") if isinstance(request, dict) else None,
        "requestSha256": sha256_file(request_path),
        "profileId": profile.get("id") if isinstance(profile, dict) else None,
        "artifactClass": artifact_class,
        "sourceKind": source_kind,
        "buildAdapter": binding.adapter_id if binding else None,
        "buildCapabilityId": binding.capability_id if binding else None,
        "builder": {"id": binding.builder_id, "buildType": binding.build_type} if binding else None,
        "resolvedInputs": validation.get("resolved", {}),
        "expectedOutputs": expected_outputs,
        "requiredGates": required_gates,
        "deliveryTargets": list(profile.get("deliveryTargets", [])) if isinstance(profile, dict) else [],
        "stages": ["build", "verify", "package", "release"],
        "failures": failures,
        "boundary": "This is a derived execution projection from exact request/profile bytes and a data-owned build capability binding, not durable workflow state. Runtime/Temporal own physical execution and durability.",
    }
