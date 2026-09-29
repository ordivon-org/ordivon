from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from artifact_core.bindings import CapabilityBinding
from artifact_core.contracts import FileCommitment, sha256_file
from artifact_core.profiles import ProfileRecord
from artifact_core.standing import derive_standing_decision

from .compatibility import adapt_production_v1_verify_stage

SCHEMA_VERSION = 1
EVALUATION_PROJECTION_KIND = "artifact-evaluation-projection"


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _file_ref(path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    return {
        "path": str(resolved),
        "sha256": sha256_file(resolved),
        "size": resolved.stat().st_size,
    }


def build_registered_v2_evaluation_request(
    profile: ProfileRecord,
    binding: CapabilityBinding,
    subject_path: Path,
    *,
    object_contract_path: Path | None,
    request_id: str,
) -> dict[str, Any]:
    if profile.source_kind != "native-v2-shadow":
        raise ValueError("registered-v2 EvaluationRequest requires native-v2-shadow profile")
    if binding.profile_id != profile.profile_id or binding.operation != "verify":
        raise ValueError("capability binding does not match profile verification")
    if binding.object_contract_required and object_contract_path is None:
        raise ValueError(f"Artifact profile requires an object contract: {profile.profile_id}")
    return {
        "schemaVersion": SCHEMA_VERSION,
        "kind": "artifact-evaluation-request",
        "requestId": request_id,
        "sourceKind": "registered-v2-family",
        "subjectRef": FileCommitment.from_path(subject_path).as_dict(),
        "objectContractRef": (
            None if object_contract_path is None else FileCommitment.from_path(object_contract_path).as_dict()
        ),
        "profileRef": {
            "id": profile.profile_id,
            "authority": "SHADOW_PROFILE_LIVE_VERIFIER",
            "canonicalV2": _file_ref(profile.canonical_path),
        },
        "profileSemantics": {
            "id": profile.profile_id,
            "requiredEvidence": copy.deepcopy(profile.canonical.get("requiredEvidence", {})),
            "targetAuthorities": copy.deepcopy(profile.canonical.get("targetAuthorities", [])),
            "nonClaims": copy.deepcopy(profile.canonical.get("nonClaims", [])),
        },
        "capabilityRef": {
            "mode": "REGISTERED_BINDING",
            "capabilityId": binding.capability_id,
            "entrypoint": {
                "module": binding.entrypoint.module,
                "callable": binding.entrypoint.callable,
            },
            "standing": binding.standing,
            "standingPath": str(binding.standing_path),
            "standingSha256": binding.standing_sha256,
            "objectContractRequired": binding.object_contract_required,
        },
        "nonClaims": [
            "profile-v2 shadow status is not production promotion",
            "EvaluationRequest does not execute verification",
            "consumer-domain acceptance remains external to Artifact standing",
        ],
    }


def _observations_from_claims(
    claims: Mapping[str, Any],
    *,
    subject_ref: Mapping[str, Any],
    capability_ref: Mapping[str, Any],
) -> list[dict[str, Any]]:
    observations: list[dict[str, Any]] = []
    subject_sha = subject_ref.get("sha256")
    if not isinstance(subject_sha, str):
        raise ValueError("EvaluationRequest subjectRef.sha256 is required")
    for claim, raw in sorted(claims.items()):
        if not isinstance(raw, Mapping):
            raise ValueError(f"claim result must be an object: {claim}")
        status = raw.get("status")
        if status not in {"PASS", "FAIL", "NOT_EVALUATED"}:
            raise ValueError(f"unsupported claim status: {claim}={status!r}")
        observations.append({
            "observationId": claim,
            "observationKind": "profileEvidenceClaim",
            "claimId": claim,
            "subjectSha256": subject_sha,
            "capabilityRef": copy.deepcopy(dict(capability_ref)),
            "status": status,
            "nativePointers": copy.deepcopy(raw.get("nativePointers", [])),
            "evidenceRefs": copy.deepcopy(raw.get("evidenceRefs", [])),
            "nonClaims": copy.deepcopy(raw.get("nonClaims", [])),
        })
    return observations


def project_registered_v2_result(
    evaluation_request: dict[str, Any],
    delegated_result: dict[str, Any],
) -> dict[str, Any]:
    if evaluation_request.get("kind") != "artifact-evaluation-request" or evaluation_request.get("sourceKind") != "registered-v2-family":
        raise ValueError("expected registered-v2 Artifact EvaluationRequest")
    semantics = evaluation_request.get("profileSemantics")
    if not isinstance(semantics, dict):
        raise ValueError("EvaluationRequest profile semantics are missing")
    claims = delegated_result.get("claimResults")
    if not isinstance(claims, dict):
        raise ValueError("registered verifier result requires explicit claimResults")
    native_status = delegated_result.get("status")
    if native_status not in {"PASS", "FAIL"}:
        raise ValueError("registered verifier status must be PASS or FAIL")
    standing = derive_standing_decision(
        {"id": semantics.get("id"), "requiredEvidence": copy.deepcopy(semantics.get("requiredEvidence", {}))},
        claims,
        profile_authority="SHADOW_PROFILE_LIVE_VERIFIER",
        native_evaluation_status=native_status,
        trust_status="UNSIGNED_LOCAL",
        release_status="NOT_EVALUATED",
    )
    return {
        "schemaVersion": SCHEMA_VERSION,
        "kind": EVALUATION_PROJECTION_KIND,
        "sourceKind": "registered-v2-family",
        "evaluationRequest": copy.deepcopy(evaluation_request),
        "evidenceObservations": _observations_from_claims(
            claims,
            subject_ref=evaluation_request["subjectRef"],
            capability_ref=evaluation_request["capabilityRef"],
        ),
        "claimResults": copy.deepcopy(claims),
        "standingDecision": standing,
        "nativeResult": copy.deepcopy(delegated_result),
        "nativeResultCanonicalSha256": canonical_sha256(delegated_result),
        "nonClaims": [
            "common projection does not change family verifier semantics",
            "shadow profile standing is not production promotion",
            "unsigned local evidence is not trusted release standing",
        ],
    }


def project_production_v1_result(
    evaluation_request: dict[str, Any],
    stage_result: dict[str, Any],
) -> dict[str, Any]:
    compatibility = adapt_production_v1_verify_stage(evaluation_request, stage_result)
    subject_sha = evaluation_request.get("subjectRef", {}).get("sha256")
    capability_ref = evaluation_request.get("capabilityRef")
    if not isinstance(subject_sha, str) or not isinstance(capability_ref, dict):
        raise ValueError("production EvaluationRequest subject/capability identity is missing")
    observations = []
    for item in compatibility["evidenceObservations"]:
        enriched = copy.deepcopy(item)
        enriched["subjectSha256"] = subject_sha
        enriched["capabilityRef"] = copy.deepcopy(capability_ref)
        observations.append(enriched)
    return {
        "schemaVersion": SCHEMA_VERSION,
        "kind": EVALUATION_PROJECTION_KIND,
        "sourceKind": "production-v1-compatibility",
        "evaluationRequest": copy.deepcopy(compatibility["evaluationRequest"]),
        "evidenceObservations": observations,
        "claimResults": copy.deepcopy(compatibility["claimResults"]),
        "standingDecision": copy.deepcopy(compatibility["standingDecision"]),
        "nativeResult": copy.deepcopy(stage_result),
        "nativeResultCanonicalSha256": canonical_sha256(stage_result),
        "nonClaims": [
            "common projection does not replace production-v1 execution routing",
            "profile-v2 is not promoted and profile-v1 is not retired",
            "unsigned local evidence is not trusted release standing",
        ],
    }


def validate_evaluation_projection(value: dict[str, Any]) -> None:
    if value.get("schemaVersion") != SCHEMA_VERSION or value.get("kind") != EVALUATION_PROJECTION_KIND:
        raise ValueError("invalid Artifact EvaluationProjection")
    native = value.get("nativeResult")
    request = value.get("evaluationRequest")
    if not isinstance(native, dict) or not isinstance(request, dict):
        raise ValueError("EvaluationProjection requires evaluationRequest and nativeResult")
    if canonical_sha256(native) != value.get("nativeResultCanonicalSha256"):
        raise ValueError("EvaluationProjection native result digest drifted")
    source = value.get("sourceKind")
    if source == "registered-v2-family":
        expected = project_registered_v2_result(request, native)
    elif source == "production-v1-compatibility":
        expected = project_production_v1_result(request, native)
    else:
        raise ValueError(f"unsupported EvaluationProjection sourceKind: {source!r}")
    for key in ("evidenceObservations", "claimResults", "standingDecision"):
        if value.get(key) != expected.get(key):
            raise ValueError(f"EvaluationProjection drifted: {key}")
