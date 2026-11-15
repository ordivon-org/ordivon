"""Pure projection of native verifier results onto one exact canonical Profile.

This module never runs a verifier or promotes an aggregate PASS to missing claims.
The Profile and native result are provided by their existing owner; this projection
contains no additional profile registry, provider selection or transport semantics.
"""
from __future__ import annotations

from typing import Any

_STATUSES = frozenset({"PASS", "FAIL", "NOT_EVALUATED"})


def _at_pointer(value: dict[str, Any], pointer: str) -> object:
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        raise ValueError("native pointer must be an absolute JSON pointer")
    # A claim cannot be its own evidence. The native observation must sit
    # outside the claimResults projection, otherwise a self-referential PASS
    # would make the evidence check vacuous.
    if pointer.split("/")[1].replace("~1", "/").replace("~0", "~") == "claimResults":
        raise ValueError("claimResults cannot witness itself")
    result: object = value
    for raw in pointer[1:].split("/"):
        part = raw.replace("~1", "/").replace("~0", "~")
        if not isinstance(result, dict) or part not in result:
            raise KeyError(pointer)
        result = result[part]
    return result


def assess_required_evidence(
    profile: dict[str, Any],
    native_result: dict[str, Any],
) -> dict[str, Any]:
    """Return mandatory claim completeness; never infer from aggregate status.

    Only declarations with required=True are mandatory. Optional observations
    remain in raw native evidence. PASS/FAIL required claims need matching native
    pointers; NOT_EVALUATED is neither PASS nor FAIL.
    """
    required = profile.get("requiredEvidence")
    if not isinstance(required, dict) or not required:
        return {
            "status": "NOT_DECLARED",
            "complete": False,
            "expectedClaims": [],
            "claimStatuses": {},
            "issues": ["profile does not declare requiredEvidence"],
        }

    invalid = [
        str(name)
        for name, declaration in required.items()
        if not isinstance(declaration, dict)
        or type(declaration.get("required")) is not bool
    ]
    if invalid:
        return {
            "status": "INVALID_DECLARATION",
            "complete": False,
            "expectedClaims": [],
            "claimStatuses": {},
            "issues": [f"invalid requiredEvidence declaration: {name}" for name in invalid],
        }

    # A v2 Profile may declare optional observations alongside mandatory ones.
    # Optional failures remain available in raw evidence, but cannot silently
    # enlarge the mandatory gate. An all-optional gate is not a vacuous PASS.
    expected = sorted(name for name, declaration in required.items() if declaration["required"])
    if not expected:
        return {
            "status": "NOT_DECLARED",
            "complete": False,
            "expectedClaims": [],
            "claimStatuses": {},
            "issues": ["profile declares no mandatory requiredEvidence claims"],
        }
    raw = native_result.get("claimResults")
    if not isinstance(raw, dict):
        return {
            "status": "NOT_EVALUATED",
            "complete": False,
            "expectedClaims": expected,
            "claimStatuses": {name: "NOT_EVALUATED" for name in expected},
            "issues": ["native verifier does not emit claimResults"],
        }

    issues: list[str] = []
    statuses: dict[str, str] = {}
    for key in sorted(raw.keys() - required.keys()):
        issues.append(f"undeclared native claim: {key}")
    for name in expected:
        claim = raw.get(name)
        if not isinstance(claim, dict):
            statuses[name] = "NOT_EVALUATED"
            issues.append(f"required native claim absent: {name}")
            continue
        status = claim.get("status")
        if not isinstance(status, str) or status not in _STATUSES:
            statuses[name] = "NOT_EVALUATED"
            issues.append(f"invalid native claim status: {name}")
            continue
        statuses[name] = status
        if status != "PASS":
            issues.append(f"required claim not verified PASS: {name}={status}")
        pointers = claim.get("nativePointers")
        if status in {"PASS", "FAIL"}:
            if not isinstance(pointers, list) or not pointers:
                issues.append(f"native evidence pointer absent: {name}")
                continue
            matched = False
            for pointer in pointers:
                try:
                    observed = _at_pointer(native_result, pointer)
                except (ValueError, KeyError):
                    continue
                if isinstance(observed, dict) and observed.get("status") == status:
                    matched = True
                    break
            if not matched:
                issues.append(f"native evidence status/pointer mismatch: {name}")
    return {
        "status": "COMPLETE" if not issues else "INCOMPLETE",
        "complete": not issues,
        "expectedClaims": expected,
        "claimStatuses": statuses,
        "issues": issues,
    }
