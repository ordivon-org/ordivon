from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .admission import canonical_digest

_BINDING_KIND = "ordivon.security.dwc-consequence-verifier-binding-r1"
_VERIFIER_CLASSES = {"version", "configuration", "exposure", "attack-negative"}
_CURRENTNESS = {"CURRENT_DECLARED", "POINT_IN_TIME_OBSERVED", "HISTORICAL_NOT_CURRENT", "CURRENTNESS_UNKNOWN"}


class ConsequenceBindingError(ValueError):
    pass


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConsequenceBindingError(f"{label} is required")
    return value


def _sha(value: object, label: str) -> str:
    text = _text(value, label)
    if not text.startswith("sha256:") or len(text) != 71:
        raise ConsequenceBindingError(f"{label} must be sha256:<64 hex>")
    return text


def _mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ConsequenceBindingError(f"{label} must be an object")
    return value


def validate_verifier_binding(binding: Mapping[str, Any]) -> None:
    if binding.get("schemaVersion") != 1 or binding.get("kind") != _BINDING_KIND:
        raise ConsequenceBindingError("unsupported consequence verifier binding")
    verifier_class = _text(binding.get("verifierClass"), "verifierClass")
    if verifier_class not in _VERIFIER_CLASSES:
        raise ConsequenceBindingError("unsupported verifierClass")
    _text(binding.get("bindingRef"), "bindingRef")
    _text(binding.get("caseRef"), "caseRef")
    _text(binding.get("subjectRef"), "subjectRef")
    _sha(binding.get("subjectSnapshotDigest"), "subjectSnapshotDigest")
    _text(binding.get("protectionClaimRef"), "protectionClaimRef")
    _text(binding.get("supportScope"), "supportScope")
    predicate = _mapping(binding.get("predicate"), "predicate")
    if predicate.get("class") != verifier_class:
        raise ConsequenceBindingError("predicate.class must equal verifierClass")

    if verifier_class == "version":
        _text(predicate.get("expectedVersion"), "predicate.expectedVersion")
    elif verifier_class == "configuration":
        _sha(
            predicate.get("expectedConfigurationDigest"),
            "predicate.expectedConfigurationDigest",
        )
    elif verifier_class == "exposure":
        _text(predicate.get("expectedExposureStanding"), "predicate.expectedExposureStanding")
    else:
        _sha(predicate.get("scopeDigest"), "predicate.scopeDigest")
        _text(predicate.get("expectedResult"), "predicate.expectedResult")
        if predicate["expectedResult"] != "NEGATIVE":
            raise ConsequenceBindingError(
                "attack-negative R1 predicate expectedResult must be NEGATIVE"
            )

    gate = _mapping(binding.get("compositionGate"), "compositionGate")
    _text(gate.get("circuitId"), "compositionGate.circuitId")
    _sha(gate.get("manifestDigest"), "compositionGate.manifestDigest")
    if _text(gate.get("gateId"), "compositionGate.gateId") != "gate:dw07-dw08-effect-receipt":
        raise ConsequenceBindingError("DW08 binding must target the DW07->DW08 gate")
    if _text(gate.get("verifierOwnerId"), "compositionGate.verifierOwnerId") != "security.dw08":
        raise ConsequenceBindingError("DW08 composition gate verifier owner mismatch")
    if _text(gate.get("supportScope"), "compositionGate.supportScope") != binding["supportScope"]:
        raise ConsequenceBindingError("composition gate supportScope mismatch")


def compile_consequence_input(
    *,
    binding: Mapping[str, Any],
    dw07_result: Mapping[str, Any],
    observation: Mapping[str, Any] | None,
) -> dict[str, Any]:
    validate_verifier_binding(binding)
    if dw07_result.get("kind") != "ordivon.security.dwc-effect-execution-result-r1":
        raise ConsequenceBindingError("unsupported DW07 effect result")
    admission = _mapping(dw07_result.get("admission"), "dw07.admission")
    receipt = dw07_result.get("receipt")
    if receipt is not None and not isinstance(receipt, Mapping):
        raise ConsequenceBindingError("dw07.receipt must be an object or null")
    if dw07_result.get("requestId") != admission.get("requestId"):
        raise ConsequenceBindingError("DW07 result/admission requestId mismatch")
    if dw07_result.get("requestDigest") != admission.get("requestDigest"):
        raise ConsequenceBindingError("DW07 result/admission requestDigest mismatch")
    if receipt is not None:
        if receipt.get("requestId") != dw07_result["requestId"]:
            raise ConsequenceBindingError("DW07 receipt requestId mismatch")
        if receipt.get("requestDigest") != dw07_result["requestDigest"]:
            raise ConsequenceBindingError("DW07 receipt requestDigest mismatch")
        if receipt.get("worldEffectVerified") is not False:
            raise ConsequenceBindingError("DW07 receipt must remain unverified world evidence")

    opa_observation = None
    if observation is not None:
        _validate_observation(binding, dw07_result, observation)
        opa_observation = {
            "plane": observation["plane"],
            "payload": {
                "stateDigest": observation["stateDigest"],
                "facts": dict(_mapping(observation.get("facts"), "observation.facts")),
            },
        }
    return {
        "admission": dict(admission),
        "executionReceipt": None if receipt is None else dict(receipt),
        "observation": opa_observation,
    }


def _validate_observation(
    binding: Mapping[str, Any],
    dw07_result: Mapping[str, Any],
    observation: Mapping[str, Any],
) -> None:
    if observation.get("kind") != "ordivon.security.dwc-authoritative-observation-r1":
        raise ConsequenceBindingError("unsupported authoritative observation")
    if _text(observation.get("plane"), "observation.plane") != "world-truth":
        raise ConsequenceBindingError("observation plane must be world-truth")
    if _text(observation.get("caseRef"), "observation.caseRef") != binding["caseRef"]:
        raise ConsequenceBindingError("observation caseRef mismatch")
    if _text(observation.get("subjectRef"), "observation.subjectRef") != binding["subjectRef"]:
        raise ConsequenceBindingError("observation subjectRef mismatch")
    if _sha(
        observation.get("subjectSnapshotDigest"),
        "observation.subjectSnapshotDigest",
    ) != binding["subjectSnapshotDigest"]:
        raise ConsequenceBindingError("observation subject snapshot mismatch")
    if _text(observation.get("requestId"), "observation.requestId") != dw07_result["requestId"]:
        raise ConsequenceBindingError("observation requestId mismatch")
    if _sha(
        observation.get("requestDigest"), "observation.requestDigest"
    ) != dw07_result["requestDigest"]:
        raise ConsequenceBindingError("observation requestDigest mismatch")
    _sha(observation.get("stateDigest"), "observation.stateDigest")
    _text(observation.get("ownerRef"), "observation.ownerRef")
    _text(observation.get("sourceRef"), "observation.sourceRef")
    _sha(observation.get("sourceDigest"), "observation.sourceDigest")
    _text(observation.get("observedAt"), "observation.observedAt")
    currentness = _text(
        observation.get("currentnessStanding"), "observation.currentnessStanding"
    )
    if currentness not in _CURRENTNESS:
        raise ConsequenceBindingError("unsupported observation currentnessStanding")
    _mapping(observation.get("facts"), "observation.facts")


def _predicate_standing(
    binding: Mapping[str, Any], observation: Mapping[str, Any]
) -> tuple[str, list[str]]:
    currentness = observation["currentnessStanding"]
    if currentness in {"HISTORICAL_NOT_CURRENT", "CURRENTNESS_UNKNOWN"}:
        return "UNKNOWN", ["authoritative observation is not current enough for consequence closure"]

    predicate = _mapping(binding["predicate"], "predicate")
    facts = _mapping(observation["facts"], "observation.facts")
    verifier_class = binding["verifierClass"]

    if verifier_class == "version":
        actual = facts.get("version")
        if not isinstance(actual, str):
            return "UNKNOWN", ["version fact missing from authoritative observation"]
        return (
            ("SATISFIED", [])
            if actual == predicate["expectedVersion"]
            else ("UNSATISFIED", ["observed version does not satisfy expected version"])
        )
    if verifier_class == "configuration":
        actual = facts.get("configurationDigest")
        if not isinstance(actual, str):
            return "UNKNOWN", ["configurationDigest fact missing from authoritative observation"]
        return (
            ("SATISFIED", [])
            if actual == predicate["expectedConfigurationDigest"]
            else (
                "UNSATISFIED",
                ["observed configuration digest does not satisfy expected configuration"],
            )
        )
    if verifier_class == "exposure":
        actual = facts.get("exposureStanding")
        if not isinstance(actual, str):
            return "UNKNOWN", ["exposureStanding fact missing from authoritative observation"]
        return (
            ("SATISFIED", [])
            if actual == predicate["expectedExposureStanding"]
            else (
                "UNSATISFIED",
                ["observed exposure standing does not satisfy expected exposure standing"],
            )
        )

    actual_result = facts.get("attackNegativeResult")
    scope_digest = facts.get("scopeDigest")
    coverage = facts.get("coverageStanding")
    if not isinstance(actual_result, str) or not isinstance(scope_digest, str):
        return "UNKNOWN", ["bounded attack-negative facts are incomplete"]
    if coverage != "COMPLETE":
        return "UNKNOWN", ["attack-negative observation coverage is not COMPLETE"]
    if scope_digest != predicate["scopeDigest"]:
        return "UNSATISFIED", ["attack-negative scope digest mismatch"]
    return (
        ("SATISFIED", [])
        if actual_result == predicate["expectedResult"]
        else ("UNSATISFIED", ["bounded attack-negative result does not satisfy predicate"])
    )


def evaluate_bound_consequence(
    *,
    binding: Mapping[str, Any],
    dw07_result: Mapping[str, Any],
    observation: Mapping[str, Any] | None,
    consequence_decision: Mapping[str, Any],
) -> dict[str, Any]:
    validate_verifier_binding(binding)
    if observation is not None:
        _validate_observation(binding, dw07_result, observation)

    decision_standing = _text(
        consequence_decision.get("standing"), "consequenceDecision.standing"
    )
    if decision_standing != "VERIFIED_CONSEQUENCE":
        standing = (
            "UNSATISFIED"
            if decision_standing
            in {
                "NOT_ADMITTED",
                "EXECUTION_BINDING_ERROR",
                "EXECUTION_RECEIPT_INVALID",
                "OBSERVATION_NOT_AUTHORITATIVE",
                "CONSEQUENCE_MISMATCH",
            }
            else "UNKNOWN"
        )
        reasons = [f"consequence policy standing is {decision_standing}"]
    elif observation is None:
        standing = "UNKNOWN"
        reasons = ["authoritative observation is absent"]
    else:
        standing, reasons = _predicate_standing(binding, observation)

    satisfied = standing == "SATISFIED" and decision_standing == "VERIFIED_CONSEQUENCE"
    evidence_refs: list[str] = []
    if observation is not None:
        evidence_refs = [
            _text(observation.get("sourceRef"), "observation.sourceRef"),
            f"observation-digest:{canonical_digest(observation)}",
        ]

    result: dict[str, Any] = {
        "schemaVersion": 1,
        "kind": "ordivon.security.dwc-consequence-verification-result-r1",
        "bindingRef": binding["bindingRef"],
        "bindingDigest": canonical_digest(binding),
        "caseRef": binding["caseRef"],
        "subjectRef": binding["subjectRef"],
        "subjectSnapshotDigest": binding["subjectSnapshotDigest"],
        "protectionClaimRef": binding["protectionClaimRef"],
        "supportScope": binding["supportScope"],
        "verifierClass": binding["verifierClass"],
        "requestId": dw07_result["requestId"],
        "requestDigest": dw07_result["requestDigest"],
        "consequencePolicyStanding": decision_standing,
        "standing": standing,
        "reasons": reasons,
        "evidenceRefs": evidence_refs,
        "boundedProtectionVerified": satisfied,
        "verifiedProtectionEstablished": satisfied,
        "compromiseAbsenceEstablished": False,
        "eradicationEstablished": False,
        "recoveryEstablished": False,
        "domainAcceptanceEstablished": False,
        "invalidationKeys": [
            f"subjectSnapshotDigest:{binding['subjectSnapshotDigest']}",
            f"bindingDigest:{canonical_digest(binding)}",
            *(
                [f"observationSourceDigest:{observation['sourceDigest']}"]
                if observation is not None
                else []
            ),
        ],
        "truthBoundary": (
            "DW08 verifies only the explicit bounded protection predicate in supportScope "
            "from an authoritative post-effect observation plus the existing consequence "
            "policy. Verified protection does not establish absence of compromise, "
            "eradication, recovery, or domain acceptance."
        ),
    }
    result["resultDigest"] = canonical_digest(result)
    return result


def composition_gate_result(
    *, binding: Mapping[str, Any], verification_result: Mapping[str, Any]
) -> dict[str, Any]:
    validate_verifier_binding(binding)
    gate = _mapping(binding["compositionGate"], "compositionGate")
    standing = verification_result.get("standing")
    if standing not in {"SATISFIED", "UNSATISFIED", "UNKNOWN"}:
        raise ConsequenceBindingError("verification_result has invalid standing")
    evidence_refs = list(verification_result.get("evidenceRefs", []))
    if standing in {"SATISFIED", "UNSATISFIED"} and not evidence_refs:
        raise ConsequenceBindingError("decisive gate standing requires evidence refs")
    return {
        "schemaVersion": 1,
        "kind": "ordivon.composition-gate-result",
        "circuitId": gate["circuitId"],
        "manifestDigest": gate["manifestDigest"],
        "gateId": gate["gateId"],
        "verifierOwnerId": gate["verifierOwnerId"],
        "standing": standing,
        "evidenceRefs": sorted(set(evidence_refs)),
        "supportScope": gate["supportScope"],
        "nonClaims": [
            "This gate result discharges only the named DW07->DW08 task-local composition obligation.",
            "SATISFIED does not establish compromise absence, eradication, recovery, or domain acceptance.",
        ],
    }
