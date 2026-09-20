from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()


def validate_plugin_result(
    value: dict[str, Any],
    profile: dict[str, Any],
) -> None:
    if value.get("schemaVersion") != 1:
        raise ValueError("plugin result schemaVersion must equal 1")
    if value.get("kind") != "artifact-verifier-plugin-result":
        raise ValueError("plugin result kind is invalid")
    profile_ref = value.get("profileRef")
    if not isinstance(profile_ref, dict) or profile_ref.get("id") != profile.get("id"):
        raise ValueError("plugin profileRef does not match profile")
    required_evidence = profile.get("requiredEvidence")
    if not isinstance(required_evidence, dict):
        raise ValueError("profile requiredEvidence must be an object")
    claim_results = value.get("claimResults")
    if not isinstance(claim_results, dict):
        raise ValueError("plugin claimResults must be an object")
    if set(claim_results) != set(required_evidence):
        missing = sorted(set(required_evidence) - set(claim_results))
        extra = sorted(set(claim_results) - set(required_evidence))
        raise ValueError(
            f"plugin claimResults keys must exactly equal profile requiredEvidence; "
            f"missing={missing} extra={extra}"
        )
    for key, item in claim_results.items():
        if not isinstance(item, dict):
            raise ValueError(f"claimResults.{key} must be an object")
        if item.get("status") not in {"PASS", "FAIL", "NOT_EVALUATED"}:
            raise ValueError(f"claimResults.{key}.status is invalid")
        for field in ("observationIds", "evidenceRefs", "nativePointers", "nonClaims"):
            if not isinstance(item.get(field), list):
                raise ValueError(f"claimResults.{key}.{field} must be an array")
    native = value.get("nativeResult")
    if not isinstance(native, dict):
        raise ValueError("nativeResult must be an object")
    if canonical_sha256(native) != value.get("nativeResultCanonicalSha256"):
        raise ValueError("nativeResult canonical digest mismatch")
    if not isinstance(value.get("subjectRef"), dict):
        raise ValueError("subjectRef must be an object")
    if not isinstance(value.get("capabilityRef"), dict):
        raise ValueError("capabilityRef must be an object")
    if not isinstance(value.get("pluginBoundary"), str) or not value["pluginBoundary"]:
        raise ValueError("pluginBoundary is required")
