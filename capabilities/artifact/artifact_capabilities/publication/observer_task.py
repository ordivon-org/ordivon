from __future__ import annotations

import hashlib
import json
import re
from typing import Any

_SHA = re.compile(r"^sha256:[0-9a-f]{64}$")
_ROLES = {"BLIND_VISION", "VENUE_AWARE_VISION", "SEMANTIC_LAYOUT"}


def canonical_json_sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _observer_assignment_identity(
    *,
    task_envelope_sha256: str,
    expected_observer_id: str,
    independence_key: str,
) -> dict[str, Any]:
    if not _SHA.fullmatch(task_envelope_sha256):
        raise ValueError("task_envelope_sha256 must be sha256:<64 lowercase hex>")
    if not expected_observer_id:
        raise ValueError("expected_observer_id is required")
    if not independence_key:
        raise ValueError("independence_key is required")
    return {
        "schemaVersion": 1,
        "kind": "publication-perceptual-observer-assignment",
        "taskEnvelopeSha256": task_envelope_sha256,
        "expectedObserverId": expected_observer_id,
        "independenceKey": independence_key,
    }


def build_observer_assignment(
    *,
    assignment_id: str,
    task_envelope_sha256: str,
    expected_observer_id: str,
    independence_key: str,
) -> dict[str, Any]:
    """Freeze one expected observer identity before provider execution."""
    if not assignment_id:
        raise ValueError("assignment_id is required")

    identity = _observer_assignment_identity(
        task_envelope_sha256=task_envelope_sha256,
        expected_observer_id=expected_observer_id,
        independence_key=independence_key,
    )
    return {
        **identity,
        "assignmentId": assignment_id,
        "assignmentRef": canonical_json_sha256(identity),
        "truthBoundary": (
            "assignment freezes expected observer identity before execution; "
            "it does not prove provider execution, Runtime occurrence, "
            "model independence, or observer-report correctness"
        ),
    }


def validate_observer_assignment(value: dict[str, Any]) -> dict[str, Any]:
    """Reject post-build semantic tampering before a consumer uses an assignment."""
    if value.get("schemaVersion") != 1:
        raise ValueError("observer assignment schemaVersion must be 1")
    if value.get("kind") != "publication-perceptual-observer-assignment":
        raise ValueError("observer assignment kind is invalid")

    identity = _observer_assignment_identity(
        task_envelope_sha256=value.get("taskEnvelopeSha256", ""),
        expected_observer_id=value.get("expectedObserverId", ""),
        independence_key=value.get("independenceKey", ""),
    )
    expected_ref = canonical_json_sha256(identity)
    if value.get("assignmentRef") != expected_ref:
        raise ValueError("assignmentRef does not match observer assignment semantic identity")
    return value


def build_observer_task_envelope(
    *,
    task_id: str,
    role: str,
    carrier_sha256: str,
    allowed_read: list[str],
    forbidden_read: list[str],
    required_outputs: list[str],
    acceptance_predicates: list[str],
) -> dict[str, Any]:
    if not task_id:
        raise ValueError("task_id is required")
    if role not in _ROLES:
        raise ValueError(f"unsupported observer role: {role}")
    if not _SHA.fullmatch(carrier_sha256):
        raise ValueError("carrier_sha256 must be sha256:<64 lowercase hex>")
    if set(allowed_read) & set(forbidden_read):
        raise ValueError("allowed_read and forbidden_read must be disjoint")
    if not required_outputs:
        raise ValueError("required_outputs must not be empty")
    if not acceptance_predicates:
        raise ValueError("acceptance_predicates must not be empty")

    input_view = {
        "carrierSha256": carrier_sha256,
        "role": role,
        "allowedRead": sorted(allowed_read),
        "forbiddenRead": sorted(forbidden_read),
    }
    return {
        "schemaVersion": 1,
        "kind": "publication-perceptual-observer-task",
        "taskId": task_id,
        "role": role,
        "carrierSha256": carrier_sha256,
        "inputViewDigest": canonical_json_sha256(input_view),
        "allowedRead": allowed_read,
        "forbiddenRead": forbidden_read,
        "requiredOutputs": required_outputs,
        "acceptancePredicates": acceptance_predicates,
        "truthBoundary": (
            "task scope proves declared observer isolation inputs; "
            "it does not prove provider-internal model independence"
        ),
    }
