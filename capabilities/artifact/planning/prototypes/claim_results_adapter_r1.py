from __future__ import annotations

import copy
from typing import Any

from verifier_plugin_contract_r2 import canonical_sha256


def _file_ref(value: object) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    digest = value.get("digest")
    sha = digest.get("sha256") if isinstance(digest, dict) else value.get("sha256")
    size = value.get("size")
    out: dict[str, Any] = {}
    for key in ("path", "name"):
        if isinstance(value.get(key), str):
            out[key] = value[key]
    if isinstance(sha, str):
        out["sha256"] = sha
    if isinstance(size, int):
        out["size"] = size
    return out or None


def legacy_stage_plugin_candidate(
    stage_result: dict[str, Any],
    canonical_profile: dict[str, Any],
    *,
    profile_ref: dict[str, Any],
) -> dict[str, Any]:
    required_evidence = canonical_profile.get("requiredEvidence")
    if not isinstance(required_evidence, dict):
        raise ValueError("profile requiredEvidence must be an object")
    receipts = stage_result.get("receipts")
    if not isinstance(receipts, dict):
        raise ValueError("stage receipts must be an object")
    claim_results: dict[str, Any] = {}
    for claim in sorted(required_evidence):
        receipt = receipts.get(claim)
        if isinstance(receipt, dict):
            refs = []
            for role in ("rawEvidence", "vsa"):
                ref = _file_ref(receipt.get(role))
                if ref:
                    refs.append({"role": role, **ref})
            status = receipt.get("status")
            if status not in {"PASS", "FAIL"}:
                status = "NOT_EVALUATED"
            claim_results[claim] = {
                "status": status,
                "observationIds": [claim],
                "evidenceRefs": refs,
                "nativePointers": [f"/receipts/{claim}"],
                "nonClaims": [],
            }
        else:
            claim_results[claim] = {
                "status": "NOT_EVALUATED",
                "observationIds": [],
                "evidenceRefs": [],
                "nativePointers": [],
                "nonClaims": [
                    "legacy verify-stage did not execute or emit this profile evidence gate"
                ],
            }
    return {
        "schemaVersion": 1,
        "kind": "artifact-verifier-plugin-result",
        "profileRef": copy.deepcopy(profile_ref),
        "subjectRef": _file_ref(stage_result.get("artifact")) or {},
        "capabilityRef": {
            "capabilityId": "artifact.compat.legacy-verify-stage",
            "standing": "COMPATIBILITY_ADAPTER",
            "entrypoint": {
                "module": "artifact_verification.stage",
                "callable": "execute_verify_stage",
            },
        },
        "claimResults": claim_results,
        "nativeResult": copy.deepcopy(stage_result),
        "nativeResultCanonicalSha256": canonical_sha256(stage_result),
        "pluginBoundary": (
            "Compatibility projection only. Missing legacy gates remain NOT_EVALUATED; "
            "stage status PASS is never promoted over missing profile evidence."
        ),
    }


def _at_pointer(root: dict[str, Any], pointer: str) -> object:
    if not pointer.startswith("/"):
        raise ValueError("pointer must be absolute JSON pointer")
    value: object = root
    for raw in pointer[1:].split("/"):
        key = raw.replace("~1", "/").replace("~0", "~")
        if not isinstance(value, dict) or key not in value:
            raise KeyError(pointer)
        value = value[key]
    return value


def assess_family_claim_mapping(
    service_result: dict[str, Any],
    canonical_profile: dict[str, Any],
    mapping: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    native = service_result.get("verification")
    if not isinstance(native, dict):
        raise ValueError("family service verification payload must be an object")
    required_evidence = canonical_profile.get("requiredEvidence")
    if not isinstance(required_evidence, dict):
        raise ValueError("profile requiredEvidence must be an object")

    claim_results: dict[str, Any] = {}
    gaps: dict[str, str] = {}
    for claim in sorted(required_evidence):
        rule = mapping.get(claim)
        if rule is None:
            gaps[claim] = "NO_SAFE_NATIVE_MAPPING"
            continue
        pointer = rule.get("pointer")
        mode = rule.get("mode")
        try:
            observed = _at_pointer(native, pointer)
        except (KeyError, ValueError):
            gaps[claim] = "NATIVE_POINTER_ABSENT"
            continue
        if mode == "status":
            if not isinstance(observed, dict) or observed.get("status") not in {"PASS", "FAIL"}:
                gaps[claim] = "EXPLICIT_STATUS_ABSENT"
                continue
            status = observed["status"]
        elif mode == "zero-return-code":
            if not isinstance(observed, int):
                gaps[claim] = "RETURN_CODE_ABSENT"
                continue
            status = "PASS" if observed == 0 else "FAIL"
        else:
            raise ValueError(f"unsupported mapping mode: {mode!r}")
        claim_results[claim] = {
            "status": status,
            "observationIds": [claim],
            "evidenceRefs": [],
            "nativePointers": [pointer],
            "nonClaims": list(rule.get("nonClaims") or []),
        }

    return {
        "profileId": canonical_profile.get("id"),
        "nativeOverallStatus": service_result.get("status"),
        "claimResults": claim_results,
        "unaddressableClaims": gaps,
        "standing": (
            "ADAPTER_SUFFICIENT"
            if not gaps
            else "NATIVE_RESULT_EXPANSION_REQUIRED"
        ),
    }


WAVE_R1_MAPPING = {
    "contractSchema": {
        "pointer": "/contractSchema",
        "mode": "status",
    },
    "referenceContainerView": {
        "pointer": "/referenceContainerView",
        "mode": "status",
    },
    "independentTechnicalView": {
        "pointer": "/independentTechnicalView",
        "mode": "status",
    },
    "decoderMatrix": {
        "pointer": "/decoderMatrix",
        "mode": "status",
    },
    "pcmIdentity": {
        "pointer": "/pcmIdentity",
        "mode": "status",
    },
}

PNG_R1_MAPPING = {
    "datastreamValidity": {
        "pointer": "/datastreamValidity",
        "mode": "status",
    },
    "metadataObservation": {
        "pointer": "/metadata",
        "mode": "status",
    },
    "decoderMatrix": {
        "pointer": "/decoderMatrix",
        "mode": "status",
    },
    "profileFacts": {
        "pointer": "/profileFacts",
        "mode": "status",
    },
}
