from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping


_DW04_KIND = "ordivon.security.dwc-attack-coverage-projection"


def canonical_digest(value: object) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode()
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} is required")
    return value


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be an object")
    return value


def compile_validation_binding(
    *,
    dw04_projection: Mapping[str, object],
    request: Mapping[str, object],
    environment: Mapping[str, object],
    sandbox_admission: Mapping[str, object],
    observer_binding: Mapping[str, object],
) -> dict[str, Any]:
    if _text(dw04_projection.get("kind"), "dw04.kind") != _DW04_KIND:
        raise ValueError(f"dw04.kind must be {_DW04_KIND}")

    subject = _mapping(dw04_projection.get("subject"), "dw04.subject")
    case_ref = _text(dw04_projection.get("caseRef"), "dw04.caseRef")
    subject_ref = _text(subject.get("subjectRef"), "dw04.subject.subjectRef")
    snapshot_digest = _text(subject.get("snapshotDigest"), "dw04.subject.snapshotDigest")

    request_ref = _text(request.get("requestRef"), "request.requestRef")
    control_ref = _text(request.get("controlRef"), "request.controlRef")
    target_kind = _text(request.get("targetKind"), "request.targetKind")
    target_ref = _text(request.get("targetRef"), "request.targetRef")
    requested_subject_ref = _text(request.get("subjectRef"), "request.subjectRef")
    requested_snapshot = _text(
        request.get("subjectSnapshotDigest"), "request.subjectSnapshotDigest"
    )
    world_spec_digest = _text(request.get("worldSpecDigest"), "request.worldSpecDigest")
    environment_digest = _text(request.get("environmentDigest"), "request.environmentDigest")

    reasons: list[str] = []

    candidates = dw04_projection.get("authorizedValidationCandidateControlRefs", [])
    if not isinstance(candidates, list):
        raise ValueError("dw04 authorizedValidationCandidateControlRefs must be an array")
    if control_ref not in candidates:
        reasons.append("control is not a DW04 decision-relevant validation candidate")
    if target_kind != "synthetic":
        reasons.append("DW05 R1 reference validation is restricted to synthetic targets")
    if requested_subject_ref != subject_ref or requested_snapshot != snapshot_digest:
        reasons.append("validation request subject binding does not match DW04")
    if _text(request.get("caseRef"), "request.caseRef") != case_ref:
        reasons.append("validation request caseRef does not match DW04")

    authority = _mapping(request.get("authority"), "request.authority")
    authority_scope = _mapping(authority.get("scope"), "request.authority.scope")
    if _text(authority.get("standing"), "request.authority.standing") != "AUTHORIZED":
        reasons.append("validation authority owner did not report AUTHORIZED")
    expected_scope = {
        "caseRef": case_ref,
        "subjectRef": subject_ref,
        "subjectSnapshotDigest": snapshot_digest,
        "controlRef": control_ref,
        "targetRef": target_ref,
        "targetKind": target_kind,
        "threatClass": "synthetic_agent",
    }
    observed_scope = {key: authority_scope.get(key) for key in expected_scope}
    if observed_scope != expected_scope:
        reasons.append("authority scope does not exactly bind case/subject/control/target/regime")

    if environment.get("kind") != "ordivon.ai-redteam-experiment-environment":
        reasons.append("environment is not an R4 experiment-environment contract")
    if environment.get("threatClass") != "synthetic_agent":
        reasons.append("DW05 R1 benign validation requires synthetic_agent threat class")
    if canonical_digest(environment) != environment_digest:
        reasons.append("environmentDigest does not bind the supplied R4 environment")
    if environment.get("syntheticWorldDigest") != world_spec_digest:
        reasons.append("R4 environment does not bind the requested synthetic world")

    isolation = environment.get("isolation", {})
    if not isinstance(isolation, Mapping):
        reasons.append("R4 isolation vector is missing")
    else:
        if isolation.get("network") == "full_egress":
            reasons.append("synthetic validation cannot use unrestricted network egress")
        if isolation.get("credentials") not in {"none", "synthetic_only"}:
            reasons.append("synthetic validation cannot expose non-synthetic credentials")
        if isolation.get("external_effects") not in {"none", "synthetic_only", "policy_proxy"}:
            reasons.append("synthetic validation cannot have direct open-world effects")
        if isolation.get("observer") != "independent":
            reasons.append("DW05 requires an independent observer declaration")

    if sandbox_admission.get("environmentDigest") != environment_digest:
        reasons.append("sandbox admission belongs to a different environment")
    if sandbox_admission.get("admitted") is not True:
        reasons.append("R4 sandbox admission is not admitted")

    applicable = observer_binding.get("applicableThreatClasses", [])
    if not isinstance(applicable, list) or "synthetic_agent" not in applicable:
        reasons.append("observer binding is not applicable to synthetic_agent")
    if observer_binding.get("independenceClass") not in {
        "process_local_independent_code_path",
        "independent_process",
        "independent_kernel",
    }:
        reasons.append("observer binding does not provide an admitted independence class")

    standing = "READY_FOR_SYNTHETIC_VALIDATION" if not reasons else "REJECTED"
    result: dict[str, Any] = {
        "schemaVersion": 1,
        "kind": "ordivon.security.dwc-authorized-validation-binding",
        "requestRef": request_ref,
        "caseRef": case_ref,
        "subjectRef": subject_ref,
        "subjectSnapshotDigest": snapshot_digest,
        "controlRef": control_ref,
        "targetKind": target_kind,
        "targetRef": target_ref,
        "environmentDigest": environment_digest,
        "worldSpecDigest": world_spec_digest,
        "authorityOwnerRef": _text(authority.get("ownerRef"), "request.authority.ownerRef"),
        "authorityDecisionRef": _text(
            authority.get("decisionRef"), "request.authority.decisionRef"
        ),
        "observerRef": _text(observer_binding.get("observerId"), "observer.observerId"),
        "observerRevision": _text(
            observer_binding.get("observerRevision"), "observer.observerRevision"
        ),
        "observerIndependenceClass": observer_binding.get("independenceClass"),
        "standing": standing,
        "rejectionReasons": reasons,
        "validationAdmissionEstablished": not reasons,
        "executionAuthorityGrantedByDW05": False,
        "productionEffectAuthorityGranted": False,
        "productionSecurityStandingEstablished": False,
        "truthBoundary": (
            "DW05 binds a decision-relevant DW04 candidate to exact synthetic target, "
            "authority scope, R4 sandbox admission, and an R7-compatible observer. "
            "READY means the declared validation regime is mechanically admissible; "
            "it does not execute an experiment, grant production effect authority, "
            "or establish production Security standing."
        ),
    }
    result["bindingDigest"] = canonical_digest(result)
    return result


def project_validation_evidence(
    *,
    binding: Mapping[str, object],
    effect_receipt: Mapping[str, object],
    observation: Mapping[str, object],
    consistency: Mapping[str, object],
    predicate: Mapping[str, object],
) -> dict[str, Any]:
    if binding.get("standing") != "READY_FOR_SYNTHETIC_VALIDATION":
        raise ValueError("validation evidence requires a READY binding")
    environment_digest = _text(binding.get("environmentDigest"), "binding.environmentDigest")
    world_spec_digest = _text(binding.get("worldSpecDigest"), "binding.worldSpecDigest")

    if observation.get("environmentDigest") != environment_digest:
        raise ValueError("observation belongs to a different environment")
    if observation.get("worldSpecDigest") != world_spec_digest:
        raise ValueError("observation belongs to a different synthetic world")
    if effect_receipt.get("effectRequestDigest") != observation.get("effectRequestDigest"):
        raise ValueError("effect receipt and observation request digests differ")
    if consistency.get("consistent") is not True:
        raise ValueError("executor receipt and independent observation are inconsistent")
    if consistency.get("observationDigest") != canonical_digest(observation):
        raise ValueError("consistency record does not bind the supplied observation")

    predicate_standing = _text(predicate.get("standing"), "predicate.standing")
    if predicate_standing not in {"SATISFIED", "UNSATISFIED", "INCONCLUSIVE"}:
        raise ValueError("unsupported validation predicate standing")
    evidence_refs = predicate.get("evidenceRefs", [])
    if not isinstance(evidence_refs, list) or (
        predicate_standing != "INCONCLUSIVE" and not evidence_refs
    ):
        raise ValueError("decisive predicate standing requires evidenceRefs")

    result: dict[str, Any] = {
        "schemaVersion": 1,
        "kind": "ordivon.security.dwc-authorized-validation-evidence",
        "bindingDigest": _text(binding.get("bindingDigest"), "binding.bindingDigest"),
        "requestRef": binding["requestRef"],
        "caseRef": binding["caseRef"],
        "controlRef": binding["controlRef"],
        "targetRef": binding["targetRef"],
        "environmentDigest": environment_digest,
        "worldSpecDigest": world_spec_digest,
        "effectReceiptDigest": canonical_digest(effect_receipt),
        "observationDigest": canonical_digest(observation),
        "consistencyDigest": canonical_digest(consistency),
        "predicateRef": _text(predicate.get("predicateRef"), "predicate.predicateRef"),
        "verifierOwnerRef": _text(
            predicate.get("verifierOwnerRef"), "predicate.verifierOwnerRef"
        ),
        "predicateStanding": predicate_standing,
        "predicateEvidenceRefs": sorted(evidence_refs),
        "studyStanding": (
            "SYNTHETIC_VALIDATION_OBSERVED"
            if predicate_standing in {"SATISFIED", "UNSATISFIED"}
            else "SYNTHETIC_VALIDATION_INCONCLUSIVE"
        ),
        "productionSecurityStandingEstablished": False,
        "verifiedProtectionEstablished": False,
        "productionEffectAuthorityGranted": False,
        "truthBoundary": (
            "This record returns exact synthetic experiment evidence to DWC. "
            "It preserves the verifier-owned predicate standing but does not promote "
            "a closed-world study verdict into production control effectiveness, "
            "verified protection, compromise absence, or recovery."
        ),
    }
    result["evidenceDigest"] = canonical_digest(result)
    return result
