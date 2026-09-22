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
