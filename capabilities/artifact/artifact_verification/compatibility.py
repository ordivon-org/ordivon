from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from artifact_core.contracts import FileCommitment, sha256_file
from artifact_core.standing import derive_standing_decision
from artifact_verification.claim_results import build_explicit_claim_results

SCHEMA_VERSION = 1
EVALUATION_REQUEST_KIND = "artifact-evaluation-request"
PROJECTION_KIND = "artifact-production-v1-evaluation-projection"


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {path}")
    return value


def _profile_file_ref(path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    value = _load_json(resolved)
    return {
        "path": str(resolved),
        "sha256": sha256_file(resolved),
        "size": resolved.stat().st_size,
        "canonicalJsonSha256": canonical_sha256(value),
    }


def _v1_outputs(value: dict[str, Any]) -> list[dict[str, Any]]:
    primary = value.get("primaryOutput")
    if not isinstance(primary, dict):
        raise ValueError("production-v1 primaryOutput must be an object")
    output = [{
        "role": "primary",
        "format": primary.get("format"),
        "purpose": primary.get("purpose"),
        "required": primary.get("required"),
        "editable": primary.get("editable"),
    }]
    companions = value.get("companions", [])
    if not isinstance(companions, list):
        raise ValueError("production-v1 companions must be an array")
    for item in companions:
        if not isinstance(item, dict):
            raise ValueError("production-v1 companion must be an object")
        output.append({
            "role": "companion",
            "format": item.get("format"),
            "purpose": item.get("purpose"),
            "required": item.get("required"),
            "editable": item.get("editable"),
        })
    return sorted(output, key=lambda item: (str(item["role"]), str(item["format"])))


def _v2_outputs(value: dict[str, Any]) -> list[dict[str, Any]]:
    outputs = value.get("outputs")
    if not isinstance(outputs, list):
        raise ValueError("canonical-v2 outputs must be an array")
    result = []
    for item in outputs:
        if not isinstance(item, dict):
            raise ValueError("canonical-v2 output must be an object")
        fmt = item.get("format")
        result.append({
            "role": item.get("role"),
            "format": fmt.get("name") if isinstance(fmt, dict) else None,
            "purpose": item.get("purpose"),
            "required": item.get("required"),
            "editable": item.get("editable"),
        })
    return sorted(result, key=lambda item: (str(item["role"]), str(item["format"])))


def _v1_targets(value: dict[str, Any]) -> list[dict[str, Any]]:
    primary = value.get("targetRenderer")
    if not isinstance(primary, dict):
        raise ValueError("production-v1 targetRenderer must be an object")
    result = [{
        "name": primary.get("name"),
        "platform": primary.get("platform"),
        "required": primary.get("required"),
    }]
    secondary = value.get("secondaryRenderers", [])
    if not isinstance(secondary, list):
        raise ValueError("production-v1 secondaryRenderers must be an array")
    for item in secondary:
        if not isinstance(item, dict):
            raise ValueError("production-v1 secondary renderer must be an object")
        result.append({
            "name": item.get("name"),
            "platform": item.get("platform"),
            "required": item.get("required"),
        })
    return sorted(result, key=lambda item: (str(item["name"]), str(item["platform"])))


def _v2_targets(value: dict[str, Any]) -> list[dict[str, Any]]:
    targets = value.get("targetAuthorities")
    if not isinstance(targets, list):
        raise ValueError("canonical-v2 targetAuthorities must be an array")
    result = []
    for item in targets:
        if not isinstance(item, dict):
            raise ValueError("canonical-v2 target authority must be an object")
        result.append({
            "name": item.get("name"),
            "platform": item.get("platform"),
            "required": item.get("required"),
        })
    return sorted(result, key=lambda item: (str(item["name"]), str(item["platform"])))


def _presentation_policy_v1(value: dict[str, Any]) -> dict[str, Any] | None:
    if value.get("artifactClass") != "presentation":
        return None
    return {
        "aspectRatio": copy.deepcopy(value.get("aspectRatio")),
        "fontPolicy": copy.deepcopy(value.get("fontPolicy")),
        "fonts": copy.deepcopy(value.get("fonts", [])),
        "renderEvidence": copy.deepcopy(value.get("renderEvidence")),
        "semanticPolicy": copy.deepcopy(value.get("semanticPolicy")),
        "unsupportedTargets": copy.deepcopy(value.get("unsupportedRenderers", [])),
    }


def _presentation_policy_v2(value: dict[str, Any]) -> dict[str, Any] | None:
    classification = value.get("classification")
    if not isinstance(classification, dict) or classification.get("family") != "presentation":
        return None
    policy = value.get("profilePolicy")
    if not isinstance(policy, dict):
        raise ValueError("canonical-v2 presentation profilePolicy must be an object")
    presentation = policy.get("presentation")
    if not isinstance(presentation, dict):
        raise ValueError("canonical-v2 presentation policy must be an object")
    return {
        "aspectRatio": copy.deepcopy(presentation.get("aspectRatio")),
        "fontPolicy": copy.deepcopy(presentation.get("fontPolicy")),
        "fonts": copy.deepcopy(presentation.get("fonts", [])),
        "renderEvidence": copy.deepcopy(presentation.get("renderEvidence")),
        "semanticPolicy": copy.deepcopy(presentation.get("semanticPolicy")),
        "unsupportedTargets": copy.deepcopy(policy.get("unsupportedTargets", [])),
    }


def validate_profile_compatibility(
    production_v1: dict[str, Any], canonical_v2: dict[str, Any]
) -> dict[str, Any]:
    if production_v1.get("profileVersion") != 1:
        raise ValueError("production profileVersion must equal 1")
    if canonical_v2.get("profileVersion") != 2:
        raise ValueError("canonical shadow profileVersion must equal 2")
    if production_v1.get("id") != canonical_v2.get("id"):
        raise ValueError("production-v1 and canonical-v2 profile ids differ")

    gates = production_v1.get("gates")
    evidence = canonical_v2.get("requiredEvidence")
    if not isinstance(gates, dict) or not isinstance(evidence, dict):
        raise ValueError("profile gate/evidence mappings must be objects")
    if set(gates) != set(evidence):
        raise ValueError(
            "production-v1 gate keys differ from canonical-v2 requiredEvidence; "
            f"v1Only={sorted(set(gates) - set(evidence))} "
            f"v2Only={sorted(set(evidence) - set(gates))}"
        )
    mismatched = sorted(
        key for key in gates
        if bool(gates[key]) != bool(evidence[key].get("required"))
    )
    if mismatched:
        raise ValueError(
            "production-v1 gate requiredness differs from canonical-v2: "
            + ", ".join(mismatched)
        )

    construction = canonical_v2.get("construction")
    if not isinstance(construction, dict):
        raise ValueError("canonical-v2 construction must be an object")
    if construction.get("authorityMode") != production_v1.get("authorityMode"):
        raise ValueError("profile authorityMode semantics differ")
    if construction.get("locale") != production_v1.get("locale"):
        raise ValueError("profile locale semantics differ")
    defaults = canonical_v2.get("deliveryDefaults")
    if not isinstance(defaults, dict) or defaults.get("targets") != production_v1.get("deliveryTargets"):
        raise ValueError("profile delivery target semantics differ")
    if _v1_outputs(production_v1) != _v2_outputs(canonical_v2):
        raise ValueError("profile output semantics differ")
    if _v1_targets(production_v1) != _v2_targets(canonical_v2):
        raise ValueError("profile target authority semantics differ")
    if _presentation_policy_v1(production_v1) != _presentation_policy_v2(canonical_v2):
        raise ValueError("profile presentation policy semantics differ")
    if production_v1.get("notes") != canonical_v2.get("notes"):
        raise ValueError("profile notes boundary differs")

    return {
        "profileId": production_v1.get("id"),
        "gateKeys": sorted(gates),
        "requiredGateKeys": sorted(key for key, flag in gates.items() if flag is True),
        "outputSemantics": _v1_outputs(production_v1),
        "targetAuthorities": _v1_targets(production_v1),
        "presentationPolicy": _presentation_policy_v1(production_v1),
        "standing": "EXACT_COMPATIBILITY_MAPPING_PROVEN",
    }


def build_production_v1_evaluation_request(
    production_profile_path: Path,
    canonical_profile_path: Path,
    subject_path: Path,
    *,
    request_id: str,
) -> dict[str, Any]:
    production = _load_json(production_profile_path)
    canonical = _load_json(canonical_profile_path)
    compatibility = validate_profile_compatibility(production, canonical)
    return {
        "schemaVersion": SCHEMA_VERSION,
        "kind": EVALUATION_REQUEST_KIND,
        "requestId": request_id,
        "sourceKind": "production-v1-compatibility",
        "subjectRef": FileCommitment.from_path(subject_path).as_dict(),
        "profileRef": {
            "id": production["id"],
            "authority": "PRODUCTION",
            "productionV1": _profile_file_ref(production_profile_path),
            "canonicalV2Shadow": _profile_file_ref(canonical_profile_path),
            "compatibility": compatibility,
        },
        "profileSemantics": {
            "id": canonical["id"],
            "requiredEvidence": copy.deepcopy(canonical["requiredEvidence"]),
            "targetAuthorities": copy.deepcopy(canonical.get("targetAuthorities", [])),
            "nonClaims": copy.deepcopy(canonical.get("nonClaims", [])),
        },
        "capabilityRef": {
            "mode": "COMPATIBILITY_ADAPTER",
            "adapter": "artifact_verification.compatibility.adapt_production_v1_verify_stage",
            "executionEntrypoint": {
                "module": "artifact_verification.stage",
                "callable": "execute_verify_stage",
            },
            "productionRoutingChanged": False,
        },
        "nonClaims": [
            "profile-v2 is not promoted to production",
            "profile-v1 is not retired",
            "compatibility projection does not execute verification",
        ],
    }


def _fact_sha(value: object) -> str | None:
    if not isinstance(value, Mapping):
        return None
    digest = value.get("digest")
    if isinstance(digest, Mapping) and isinstance(digest.get("sha256"), str):
        return str(digest["sha256"])
    sha = value.get("sha256")
    return str(sha) if isinstance(sha, str) else None


def _evidence_refs(receipt: Mapping[str, Any]) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    for role in ("rawEvidence", "vsa"):
        value = receipt.get(role)
        if not isinstance(value, Mapping):
            continue
        ref: dict[str, Any] = {"role": role}
        for key in ("path", "name", "size"):
            if value.get(key) is not None:
                ref[key] = value[key]
        sha = _fact_sha(value)
        if sha is not None:
            ref["sha256"] = sha
        refs.append(ref)
    return refs


def adapt_production_v1_verify_stage(
    evaluation_request: dict[str, Any],
    stage_result: dict[str, Any],
) -> dict[str, Any]:
    if evaluation_request.get("kind") != EVALUATION_REQUEST_KIND:
        raise ValueError("expected Artifact EvaluationRequest")
    if stage_result.get("kind") != "artifact-delivery-verify-stage":
        raise ValueError("expected artifact-delivery-verify-stage result")
    profile_ref = evaluation_request.get("profileRef")
    semantics = evaluation_request.get("profileSemantics")
    if not isinstance(profile_ref, dict) or not isinstance(semantics, dict):
        raise ValueError("evaluation request profile semantics are missing")
    if stage_result.get("profileId") != profile_ref.get("id"):
        raise ValueError("verify-stage profileId differs from EvaluationRequest")
    subject_ref = evaluation_request.get("subjectRef")
    artifact = stage_result.get("artifact")
    if not isinstance(subject_ref, dict) or _fact_sha(artifact) != subject_ref.get("sha256"):
        raise ValueError("verify-stage subject identity differs from EvaluationRequest")

    required_evidence = semantics.get("requiredEvidence")
    if not isinstance(required_evidence, dict):
        raise ValueError("evaluation request requiredEvidence must be an object")
    pointers = {key: f"/receipts/{key}" for key in sorted(required_evidence)}
    claims = build_explicit_claim_results(stage_result, pointers)
    for key, item in claims.items():
        if item["status"] == "NOT_EVALUATED":
            item["nonClaims"] = [
                "legacy verify-stage did not execute or emit this profile evidence gate"
            ]

    receipts = stage_result.get("receipts")
    if not isinstance(receipts, dict):
        raise ValueError("verify-stage receipts must be an object")
    undeclared = sorted(set(receipts) - set(required_evidence))
    if undeclared:
        raise ValueError(f"verify-stage emitted undeclared profile gate(s): {undeclared}")
    observations: list[dict[str, Any]] = []
    for gate, receipt in sorted(receipts.items()):
        if not isinstance(receipt, dict):
            raise ValueError(f"verify-stage receipt must be an object: {gate}")
        status = receipt.get("status")
        observations.append({
            "observationId": gate,
            "observationKind": "profileEvidenceGate",
            "claimId": gate,
            "status": status if status in {"PASS", "FAIL"} else "NOT_EVALUATED",
            "nativePointer": f"/receipts/{gate}",
            "evidenceRefs": _evidence_refs(receipt),
            "nonClaims": [],
            "nativeEvidence": copy.deepcopy(receipt),
        })

    profile_for_standing = {
        "id": semantics.get("id"),
        "requiredEvidence": copy.deepcopy(required_evidence),
    }
    native_status = stage_result.get("status")
    if native_status not in {"PASS", "FAIL"}:
        raise ValueError("verify-stage status must be PASS or FAIL")
    standing = derive_standing_decision(
        profile_for_standing,
        claims,
        profile_authority="PRODUCTION",
        native_evaluation_status=native_status,
        trust_status="UNSIGNED_LOCAL",
        release_status="NOT_EVALUATED",
    )
    return {
        "schemaVersion": SCHEMA_VERSION,
        "kind": PROJECTION_KIND,
        "evaluationRequest": copy.deepcopy(evaluation_request),
        "evidenceObservations": observations,
        "claimResults": claims,
        "standingDecision": standing,
        "nativeStageSummary": {
            "status": stage_result.get("status"),
            "profileVerificationComplete": stage_result.get("profileVerificationComplete"),
            "profileRequiredGates": copy.deepcopy(stage_result.get("profileRequiredGates", [])),
            "pendingRequiredGates": copy.deepcopy(stage_result.get("pendingRequiredGates", [])),
        },
        "nativeResult": copy.deepcopy(stage_result),
        "nativeResultCanonicalSha256": canonical_sha256(stage_result),
        "nonClaims": [
            "compatibility projection does not alter or replace production verification routing",
            "legacy stage PASS is not profile PASS while required claims are NOT_EVALUATED",
            "unsigned local VSA evidence is not promoted to trusted standing",
            "consumer/domain acceptance remains external to Artifact kernel",
        ],
    }


def validate_production_v1_projection(value: dict[str, Any]) -> None:
    if value.get("schemaVersion") != SCHEMA_VERSION or value.get("kind") != PROJECTION_KIND:
        raise ValueError("invalid production-v1 evaluation projection")
    request = value.get("evaluationRequest")
    native = value.get("nativeResult")
    if not isinstance(request, dict) or not isinstance(native, dict):
        raise ValueError("projection requires evaluationRequest and nativeResult")
    if canonical_sha256(native) != value.get("nativeResultCanonicalSha256"):
        raise ValueError("native verify-stage digest drifted")
    expected = adapt_production_v1_verify_stage(request, native)
    for key in (
        "evidenceObservations",
        "claimResults",
        "standingDecision",
        "nativeStageSummary",
    ):
        if value.get(key) != expected.get(key):
            raise ValueError(f"production-v1 compatibility projection drifted: {key}")


def reconstruct_production_v1_verify_stage(value: dict[str, Any]) -> dict[str, Any]:
    validate_production_v1_projection(value)
    return copy.deepcopy(value["nativeResult"])
