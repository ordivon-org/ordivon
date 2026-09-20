from __future__ import annotations

import copy
import hashlib
import json
from typing import Any

OBSERVATION_KIND = "artifact-evidence-observation-set"
SCHEMA_VERSION = 1


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _fact_ref(value: object) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    digest = value.get("digest")
    sha = digest.get("sha256") if isinstance(digest, dict) else value.get("sha256")
    size = value.get("size")
    if size is None:
        size = value.get("sizeBytes")
    result: dict[str, Any] = {}
    if isinstance(value.get("name"), str):
        result["name"] = value["name"]
    if isinstance(value.get("path"), str):
        result["path"] = value["path"]
    if isinstance(sha, str):
        result["sha256"] = sha
    if isinstance(size, int):
        result["size"] = size
    return result or None


def adapt_verify_stage_result(
    result: dict[str, Any],
    *,
    profile_ref: dict[str, Any],
    profile_authority: str = "PRODUCTION",
) -> dict[str, Any]:
    if result.get("kind") != "artifact-delivery-verify-stage":
        raise ValueError("expected artifact-delivery-verify-stage result")
    receipts = result.get("receipts")
    if not isinstance(receipts, dict):
        raise ValueError("verify-stage receipts must be an object")

    summary = copy.deepcopy(result)
    del summary["receipts"]
    observations = []
    for gate, receipt in sorted(receipts.items()):
        if not isinstance(receipt, dict):
            raise ValueError(f"verify-stage receipt must be an object: {gate}")
        evidence_refs = []
        for key in ("rawEvidence", "vsa"):
            ref = _fact_ref(receipt.get(key))
            if ref is not None:
                evidence_refs.append({"role": key, **ref})
        observations.append(
            {
                "observationId": gate,
                "observationKind": gate,
                "status": str(receipt.get("status", "UNKNOWN")),
                "methodRef": {
                    "adapter": "legacy-verify-stage-gate-receipt",
                    "verificationResult": receipt.get("verificationResult"),
                },
                "evidenceRefs": evidence_refs,
                "nonClaims": [],
                "nativeEvidence": copy.deepcopy(receipt),
            }
        )

    complete = result.get("profileVerificationComplete") is True
    return {
        "schemaVersion": SCHEMA_VERSION,
        "kind": OBSERVATION_KIND,
        "adapterKind": "legacy-verify-stage",
        "sourceResultKind": result.get("kind"),
        "sourceResultSha256": canonical_sha256(result),
        "subjectRef": _fact_ref(result.get("artifact")),
        "profileRef": copy.deepcopy(profile_ref),
        "capabilityRef": {
            "mode": "COMPATIBILITY_ADAPTER",
            "adapter": "artifact_verification.stage.execute_verify_stage",
        },
        "observations": observations,
        "standingProjection": {
            "verificationStatus": result.get("status", "UNKNOWN"),
            "profileAuthority": profile_authority,
            "evidenceCompleteness": "COMPLETE" if complete else "PARTIAL",
            "trustStatus": "UNSIGNED_LOCAL",
            "releaseStatus": "NOT_EVALUATED",
        },
        "nativeSummary": summary,
        "nonClaims": [
            "observation normalization does not make unsigned local VSA evidence trusted",
            "verify-stage PASS does not imply COMPLETE unless profileVerificationComplete is true",
        ],
    }


def reconstruct_verify_stage_result(envelope: dict[str, Any]) -> dict[str, Any]:
    if envelope.get("adapterKind") != "legacy-verify-stage":
        raise ValueError("not a legacy verify-stage observation envelope")
    result = copy.deepcopy(envelope["nativeSummary"])
    result["receipts"] = {
        item["observationId"]: copy.deepcopy(item["nativeEvidence"])
        for item in envelope["observations"]
    }
    if canonical_sha256(result) != envelope.get("sourceResultSha256"):
        raise ValueError("verify-stage round-trip digest mismatch")
    return result


def adapt_family_service_result(result: dict[str, Any]) -> dict[str, Any]:
    if result.get("kind") != "artifact-verification-result":
        raise ValueError("expected artifact-verification-result")
    verification = result.get("verification")
    if not isinstance(verification, dict):
        raise ValueError("family service result requires verification object")

    summary = copy.deepcopy(result)
    del summary["verification"]
    verifier = result.get("verifier") if isinstance(result.get("verifier"), dict) else {}
    profile = result.get("profile") if isinstance(result.get("profile"), dict) else {}
    capability = (
        result.get("capabilityBinding")
        if isinstance(result.get("capabilityBinding"), dict)
        else {}
    )
    status = str(verification.get("status", result.get("status", "UNKNOWN")))
    profile_standing = str(profile.get("standing", "UNKNOWN"))
    profile_authority = (
        "SHADOW"
        if "SHADOW" in profile_standing.upper()
        else "PRODUCTION"
        if "PRODUCTION" in profile_standing.upper()
        else "UNKNOWN"
    )
    return {
        "schemaVersion": SCHEMA_VERSION,
        "kind": OBSERVATION_KIND,
        "adapterKind": "family-verification-service",
        "sourceResultKind": result.get("kind"),
        "sourceResultSha256": canonical_sha256(result),
        "subjectRef": _fact_ref(result.get("subject")),
        "profileRef": copy.deepcopy(profile),
        "capabilityRef": {
            "mode": "REGISTERED_BINDING",
            "standing": capability.get("standing"),
            "binding": copy.deepcopy(capability),
            "verifier": copy.deepcopy(verifier),
        },
        "observations": [
            {
                "observationId": "delegated-family-result",
                "observationKind": "familyVerifierResult",
                "status": status,
                "methodRef": {
                    "capabilityId": verifier.get("capabilityId"),
                    "module": verifier.get("path"),
                    "callable": verifier.get("function"),
                    "sha256": verifier.get("sha256"),
                },
                "evidenceRefs": [],
                "nonClaims": [result.get("boundary")] if result.get("boundary") else [],
                "nativeEvidence": copy.deepcopy(verification),
            }
        ],
        "standingProjection": {
            "verificationStatus": result.get("status", "UNKNOWN"),
            "profileAuthority": profile_authority,
            "evidenceCompleteness": (
                "COMPLETE_WITHIN_DELEGATED_PROFILE_BOUNDARY"
                if result.get("status") == "PASS"
                else "INCOMPLETE"
            ),
            "trustStatus": "NOT_EVALUATED",
            "releaseStatus": "NOT_EVALUATED",
        },
        "nativeSummary": summary,
        "nonClaims": [result.get("boundary")] if result.get("boundary") else [],
    }


def reconstruct_family_service_result(envelope: dict[str, Any]) -> dict[str, Any]:
    if envelope.get("adapterKind") != "family-verification-service":
        raise ValueError("not a family verification service observation envelope")
    observations = envelope.get("observations")
    if not isinstance(observations, list) or len(observations) != 1:
        raise ValueError("family service envelope must retain exactly one native result")
    result = copy.deepcopy(envelope["nativeSummary"])
    result["verification"] = copy.deepcopy(observations[0]["nativeEvidence"])
    if canonical_sha256(result) != envelope.get("sourceResultSha256"):
        raise ValueError("family service round-trip digest mismatch")
    return result


def validate_common_envelope(value: dict[str, Any]) -> None:
    if value.get("schemaVersion") != SCHEMA_VERSION:
        raise ValueError("unsupported observation schemaVersion")
    if value.get("kind") != OBSERVATION_KIND:
        raise ValueError("invalid observation kind")
    observations = value.get("observations")
    if not isinstance(observations, list) or not observations:
        raise ValueError("at least one observation is required")
    if not isinstance(value.get("standingProjection"), dict):
        raise ValueError("standingProjection is required")
    axes = {
        "verificationStatus",
        "profileAuthority",
        "evidenceCompleteness",
        "trustStatus",
        "releaseStatus",
    }
    if set(value["standingProjection"]) != axes:
        raise ValueError("standingProjection axes drifted")
    for item in observations:
        if not isinstance(item, dict):
            raise ValueError("observation must be an object")
        for key in (
            "observationId",
            "observationKind",
            "status",
            "methodRef",
            "evidenceRefs",
            "nonClaims",
            "nativeEvidence",
        ):
            if key not in item:
                raise ValueError(f"observation missing field: {key}")

    adapter = value.get("adapterKind")
    summary = value.get("nativeSummary")
    if not isinstance(summary, dict):
        raise ValueError("nativeSummary is required")

    if adapter == "legacy-verify-stage":
        if summary.get("kind") != "artifact-delivery-verify-stage":
            raise ValueError("legacy summary kind drifted")
        if value.get("subjectRef") != _fact_ref(summary.get("artifact")):
            raise ValueError("legacy subject projection drifted")
        profile_ref = value.get("profileRef")
        if not isinstance(profile_ref, dict) or profile_ref.get("id") != summary.get("profileId"):
            raise ValueError("legacy profile projection drifted")
        expected_complete = (
            "COMPLETE"
            if summary.get("profileVerificationComplete") is True
            else "PARTIAL"
        )
        if value["standingProjection"].get("verificationStatus") != summary.get("status"):
            raise ValueError("legacy verificationStatus projection drifted")
        if value["standingProjection"].get("evidenceCompleteness") != expected_complete:
            raise ValueError("legacy evidenceCompleteness projection drifted")
        for item in observations:
            native = item.get("nativeEvidence")
            if not isinstance(native, dict):
                raise ValueError("legacy native receipt must be an object")
            if item.get("status") != str(native.get("status", "UNKNOWN")):
                raise ValueError(
                    f"legacy observation status projection drifted: {item.get('observationId')}"
                )
            if item.get("observationId") != item.get("observationKind"):
                raise ValueError("legacy gate identity projection drifted")
        reconstructed = reconstruct_verify_stage_result(value)
    elif adapter == "family-verification-service":
        if summary.get("kind") != "artifact-verification-result":
            raise ValueError("family summary kind drifted")
        if value.get("subjectRef") != _fact_ref(summary.get("subject")):
            raise ValueError("family subject projection drifted")
        if value.get("profileRef") != summary.get("profile"):
            raise ValueError("family profile projection drifted")
        if len(observations) != 1:
            raise ValueError("family service envelope must contain one native result")
        native = observations[0].get("nativeEvidence")
        if not isinstance(native, dict):
            raise ValueError("family native result must be an object")
        expected_native_status = str(native.get("status", summary.get("status", "UNKNOWN")))
        if observations[0].get("status") != expected_native_status:
            raise ValueError("family observation status projection drifted")
        if value["standingProjection"].get("verificationStatus") != summary.get("status"):
            raise ValueError("family verificationStatus projection drifted")
        reconstructed = reconstruct_family_service_result(value)
    else:
        raise ValueError(f"unsupported observation adapterKind: {adapter!r}")

    if canonical_sha256(reconstructed) != value.get("sourceResultSha256"):
        raise ValueError("source result digest projection drifted")
