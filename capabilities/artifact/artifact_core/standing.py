from __future__ import annotations

import copy
from typing import Any

CLAIM_STATUSES = frozenset({"PASS", "FAIL", "NOT_EVALUATED"})
NATIVE_EVALUATION_STATUSES = frozenset({"PASS", "FAIL"})


def required_claim_keys(profile: dict[str, Any]) -> set[str]:
    required = profile.get("requiredEvidence")
    if not isinstance(required, dict):
        raise ValueError("profile requiredEvidence must be an object")
    keys: set[str] = set()
    for key, value in required.items():
        if not isinstance(key, str) or not key:
            raise ValueError("requiredEvidence keys must be non-empty strings")
        if not isinstance(value, dict):
            raise ValueError(f"requiredEvidence.{key} must be an object")
        if value.get("required") is True:
            keys.add(key)
    return keys


def derive_standing_decision(
    profile: dict[str, Any],
    claim_results: dict[str, dict[str, Any]],
    *,
    profile_authority: str,
    native_evaluation_status: str,
    trust_status: str = "NOT_EVALUATED",
    release_status: str = "NOT_EVALUATED",
) -> dict[str, Any]:
    """Derive bounded standing from explicit claim-local evidence.

    Claim results must cover the complete profile requiredEvidence key set, including
    optional claims. Only claims whose profile entry has required=true determine
    verification/completeness. Native aggregate PASS never upgrades missing or
    NOT_EVALUATED required claims; native FAIL remains fail-closed.
    """
    evidence = profile.get("requiredEvidence")
    if not isinstance(evidence, dict):
        raise ValueError("profile requiredEvidence must be an object")
    expected = set(evidence)
    actual = set(claim_results)
    if actual != expected:
        raise ValueError(
            "claimResults keys must exactly equal profile requiredEvidence; "
            f"missing={sorted(expected - actual)} extra={sorted(actual - expected)}"
        )
    if native_evaluation_status not in NATIVE_EVALUATION_STATUSES:
        raise ValueError(
            f"unsupported native evaluation status: {native_evaluation_status!r}"
        )

    normalized: dict[str, dict[str, Any]] = {}
    for claim in sorted(expected):
        value = claim_results[claim]
        if not isinstance(value, dict):
            raise ValueError(f"claim result must be an object: {claim}")
        status = value.get("status")
        if status not in CLAIM_STATUSES:
            raise ValueError(f"unsupported claim status for {claim}: {status!r}")
        normalized[claim] = copy.deepcopy(value)

    required = required_claim_keys(profile)
    failures = sorted(
        claim for claim in required if normalized[claim]["status"] == "FAIL"
    )
    pending = sorted(
        claim for claim in required if normalized[claim]["status"] == "NOT_EVALUATED"
    )
    if native_evaluation_status == "FAIL" or failures:
        verification = "FAIL"
    elif pending:
        verification = "PENDING"
    else:
        verification = "PASS"
    completeness = "COMPLETE" if not pending else "PARTIAL"

    return {
        "schemaVersion": 1,
        "kind": "artifact-standing-decision",
        "profileId": profile.get("id"),
        "requiredClaims": sorted(required),
        "claimResults": normalized,
        "requiredFailures": failures,
        "requiredNotEvaluated": pending,
        "standingVector": {
            "verificationStatus": verification,
            "profileAuthority": profile_authority,
            "evidenceCompleteness": completeness,
            "trustStatus": trust_status,
            "releaseStatus": release_status,
        },
        "nativeEvaluationStatus": native_evaluation_status,
        "boundary": (
            "Standing is profile/policy-derived from explicit claimResults. Native "
            "aggregate PASS never upgrades missing required evidence; native FAIL "
            "remains fail-closed. Trust, release and consumer acceptance are separate axes."
        ),
    }
