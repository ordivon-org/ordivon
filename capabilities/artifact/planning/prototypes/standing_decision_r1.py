from __future__ import annotations

from typing import Any

CLAIM_STATUSES = frozenset({"PASS", "FAIL", "NOT_EVALUATED"})


def required_claim_keys(profile: dict[str, Any]) -> set[str]:
    required = profile.get("requiredEvidence")
    if not isinstance(required, dict):
        raise ValueError("canonical profile requiredEvidence must be an object")
    result = set()
    for key, value in required.items():
        if not isinstance(key, str) or not key:
            raise ValueError("requiredEvidence keys must be non-empty strings")
        if not isinstance(value, dict):
            raise ValueError(f"requiredEvidence.{key} must be an object")
        if value.get("required") is True:
            result.add(key)
    return result


def evaluate_standing(
    profile: dict[str, Any],
    claim_results: dict[str, dict[str, Any]],
    *,
    profile_authority: str,
    trust_status: str = "NOT_EVALUATED",
    release_status: str = "NOT_EVALUATED",
) -> dict[str, Any]:
    required = required_claim_keys(profile)
    normalized: dict[str, dict[str, Any]] = {}
    for claim, value in claim_results.items():
        if not isinstance(claim, str) or not claim:
            raise ValueError("claim result key must be a non-empty string")
        if not isinstance(value, dict):
            raise ValueError(f"claim result must be an object: {claim}")
        status = value.get("status")
        if status not in CLAIM_STATUSES:
            raise ValueError(f"unsupported claim status for {claim}: {status!r}")
        normalized[claim] = dict(value)

    missing = sorted(required - set(normalized))
    required_failures = sorted(
        claim
        for claim in required
        if claim in normalized and normalized[claim]["status"] == "FAIL"
    )
    required_not_evaluated = sorted(
        claim
        for claim in required
        if claim in normalized and normalized[claim]["status"] == "NOT_EVALUATED"
    )

    if required_failures:
        verification = "FAIL"
    elif missing or required_not_evaluated:
        verification = "PENDING"
    else:
        verification = "PASS"

    completeness = (
        "COMPLETE"
        if not missing and not required_not_evaluated
        else "PARTIAL"
    )
    return {
        "profileId": profile.get("id"),
        "requiredClaims": sorted(required),
        "claimResults": normalized,
        "missingRequiredClaims": missing,
        "requiredFailures": required_failures,
        "requiredNotEvaluated": required_not_evaluated,
        "standingVector": {
            "verificationStatus": verification,
            "profileAuthority": profile_authority,
            "evidenceCompleteness": completeness,
            "trustStatus": trust_status,
            "releaseStatus": release_status,
        },
        "boundary": (
            "Standing is derived only from explicit claimResults for profile-required "
            "evidence. Native verifier overall PASS is not promoted to profile PASS "
            "when any required claim lacks an explicit result."
        ),
    }


def legacy_stage_claim_results(result: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if result.get("kind") != "artifact-delivery-verify-stage":
        raise ValueError("expected artifact-delivery-verify-stage result")
    receipts = result.get("receipts")
    if not isinstance(receipts, dict):
        raise ValueError("verify-stage receipts must be an object")
    claims: dict[str, dict[str, Any]] = {}
    for gate, receipt in receipts.items():
        if not isinstance(receipt, dict):
            raise ValueError(f"gate receipt must be an object: {gate}")
        status = receipt.get("status")
        if status not in {"PASS", "FAIL"}:
            status = "NOT_EVALUATED"
        claims[str(gate)] = {
            "status": status,
            "source": "legacy-stage-gate-receipt",
            "observationId": str(gate),
        }
    return claims


def family_explicit_claim_results(
    service_result: dict[str, Any],
    profile: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """Extract only zero-inference same-name claim result objects.

    This intentionally refuses aliases, failure-text inference, or aggregate PASS
    laundering. A future VerifierPlugin contract should emit explicit claimResults
    when native result vocabulary differs from profile requiredEvidence keys.
    """
    if service_result.get("kind") != "artifact-verification-result":
        raise ValueError("expected artifact-verification-result")
    native = service_result.get("verification")
    if not isinstance(native, dict):
        raise ValueError("verification payload must be an object")

    claims: dict[str, dict[str, Any]] = {}
    for claim in sorted(required_claim_keys(profile)):
        value = native.get(claim)
        if not isinstance(value, dict):
            continue
        status = value.get("status")
        if status not in {"PASS", "FAIL"}:
            continue
        claims[claim] = {
            "status": status,
            "source": "family-native-same-name-explicit-status",
            "nativeKey": claim,
        }
    return claims
