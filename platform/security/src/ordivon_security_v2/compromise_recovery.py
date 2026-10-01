from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .admission import canonical_digest

_CASE_KIND = "ordivon.security.dwc-compromise-recovery-case-r1"
_CURRENT = {"CURRENT_DECLARED", "POINT_IN_TIME_OBSERVED"}
_CURRENTNESS = _CURRENT | {"HISTORICAL_NOT_CURRENT", "CURRENTNESS_UNKNOWN"}
_COVERAGE = {"COMPLETE", "PARTIAL", "UNKNOWN"}
_SIGNAL_CLASSES = {"COMPROMISE", "PERSISTENCE"}
_FINDINGS = {"OBSERVED", "NOT_OBSERVED"}
_OBLIGATION_PHASES = {"ERADICATION", "RECOVERY", "REQUALIFICATION"}
_OBLIGATION_STANDINGS = {"PENDING", "SATISFIED", "UNSATISFIED", "UNKNOWN"}
_OBLIGATION_CLASSES = {
    "credential-rotation",
    "key-rotation",
    "persistence-removal",
    "rebuild",
    "containment-release",
    "requalify",
    "other-owner-defined",
}


class CompromiseRecoveryError(ValueError):
    pass


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CompromiseRecoveryError(f"{label} is required")
    return value


def _sha(value: object, label: str) -> str:
    text = _text(value, label)
    if not text.startswith("sha256:") or len(text) != 71:
        raise CompromiseRecoveryError(f"{label} must be sha256:<64 hex>")
    return text


def _mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise CompromiseRecoveryError(f"{label} must be an object")
    return value


def _rows(value: object, label: str) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        raise CompromiseRecoveryError(f"{label} must be an array")
    rows: list[Mapping[str, Any]] = []
    for index, item in enumerate(value):
        rows.append(_mapping(item, f"{label}[{index}]"))
    return rows


def _validate_exact_binding(case: Mapping[str, Any], row: Mapping[str, Any], label: str) -> None:
    if _text(row.get("caseRef"), f"{label}.caseRef") != case["caseRef"]:
        raise CompromiseRecoveryError(f"{label} caseRef mismatch")
    if _text(row.get("subjectRef"), f"{label}.subjectRef") != case["subjectRef"]:
        raise CompromiseRecoveryError(f"{label} subjectRef mismatch")
    if (
        _sha(row.get("subjectSnapshotDigest"), f"{label}.subjectSnapshotDigest")
        != case["subjectSnapshotDigest"]
    ):
        raise CompromiseRecoveryError(f"{label} subject snapshot mismatch")


def validate_case(case: Mapping[str, Any]) -> None:
    if case.get("schemaVersion") != 1 or case.get("kind") != _CASE_KIND:
        raise CompromiseRecoveryError("unsupported DW09 case schema")
    _text(case.get("caseRef"), "caseRef")
    _text(case.get("subjectRef"), "subjectRef")
    _sha(case.get("subjectSnapshotDigest"), "subjectSnapshotDigest")
    protection = _mapping(case.get("protection"), "protection")
    if not isinstance(protection.get("verifiedProtectionEstablished"), bool):
        raise CompromiseRecoveryError("protection.verifiedProtectionEstablished must be boolean")

    for index, signal in enumerate(_rows(case.get("signals", []), "signals")):
        label = f"signals[{index}]"
        _validate_exact_binding(case, signal, label)
        signal_class = _text(signal.get("signalClass"), f"{label}.signalClass")
        if signal_class not in _SIGNAL_CLASSES:
            raise CompromiseRecoveryError(f"{label} unsupported signalClass")
        finding = _text(signal.get("findingStanding"), f"{label}.findingStanding")
        if finding not in _FINDINGS:
            raise CompromiseRecoveryError(f"{label} unsupported findingStanding")
        currentness = _text(signal.get("currentnessStanding"), f"{label}.currentnessStanding")
        if currentness not in _CURRENTNESS:
            raise CompromiseRecoveryError(f"{label} unsupported currentnessStanding")
        _text(signal.get("evidenceRef"), f"{label}.evidenceRef")
        _text(signal.get("ownerRef"), f"{label}.ownerRef")
        _text(signal.get("sourceRef"), f"{label}.sourceRef")
        _sha(signal.get("sourceDigest"), f"{label}.sourceDigest")

    for index, coverage in enumerate(_rows(case.get("detectorCoverage", []), "detectorCoverage")):
        label = f"detectorCoverage[{index}]"
        _validate_exact_binding(case, coverage, label)
        dimension = _text(coverage.get("dimension"), f"{label}.dimension")
        if dimension not in _SIGNAL_CLASSES:
            raise CompromiseRecoveryError(f"{label} unsupported dimension")
        standing = _text(coverage.get("standing"), f"{label}.standing")
        if standing not in _COVERAGE:
            raise CompromiseRecoveryError(f"{label} unsupported standing")
        _text(coverage.get("coverageRef"), f"{label}.coverageRef")
        _text(coverage.get("ownerRef"), f"{label}.ownerRef")
        _text(coverage.get("sourceRef"), f"{label}.sourceRef")
        _sha(coverage.get("sourceDigest"), f"{label}.sourceDigest")
        _sha(coverage.get("scopeDigest"), f"{label}.scopeDigest")

    for index, obligation in enumerate(
        _rows(case.get("recoveryObligations", []), "recoveryObligations")
    ):
        label = f"recoveryObligations[{index}]"
        _validate_exact_binding(case, obligation, label)
        _text(obligation.get("obligationRef"), f"{label}.obligationRef")
        phase = _text(obligation.get("phase"), f"{label}.phase")
        if phase not in _OBLIGATION_PHASES:
            raise CompromiseRecoveryError(f"{label} unsupported phase")
        obligation_class = _text(obligation.get("class"), f"{label}.class")
        if obligation_class not in _OBLIGATION_CLASSES:
            raise CompromiseRecoveryError(f"{label} unsupported class")
        if not isinstance(obligation.get("required"), bool):
            raise CompromiseRecoveryError(f"{label}.required must be boolean")
        standing = _text(obligation.get("standing"), f"{label}.standing")
        if standing not in _OBLIGATION_STANDINGS:
            raise CompromiseRecoveryError(f"{label} unsupported standing")
        _text(obligation.get("ownerRef"), f"{label}.ownerRef")
        _text(obligation.get("verifierRef"), f"{label}.verifierRef")
        evidence_refs = obligation.get("evidenceRefs", [])
        if not isinstance(evidence_refs, list) or not all(
            isinstance(item, str) and item for item in evidence_refs
        ):
            raise CompromiseRecoveryError(f"{label}.evidenceRefs must be string array")

    requalification = case.get("requalification")
    if requalification is not None:
        row = _mapping(requalification, "requalification")
        _validate_exact_binding(case, row, "requalification")
        standing = _text(row.get("standing"), "requalification.standing")
        if standing not in {"SATISFIED", "UNSATISFIED", "UNKNOWN"}:
            raise CompromiseRecoveryError("unsupported requalification.standing")
        currentness = _text(row.get("currentnessStanding"), "requalification.currentnessStanding")
        if currentness not in _CURRENTNESS:
            raise CompromiseRecoveryError("unsupported requalification.currentnessStanding")
        _text(row.get("ownerRef"), "requalification.ownerRef")
        _text(row.get("sourceRef"), "requalification.sourceRef")
        _sha(row.get("sourceDigest"), "requalification.sourceDigest")

    gate = _mapping(case.get("compositionGate"), "compositionGate")
    _text(gate.get("circuitId"), "compositionGate.circuitId")
    _sha(gate.get("manifestDigest"), "compositionGate.manifestDigest")
    if _text(gate.get("gateId"), "compositionGate.gateId") != "gate:dw06-dw09-compromise-hunt":
        raise CompromiseRecoveryError("DW09 must target the DW06->DW09 composition gate")
    if _text(gate.get("verifierOwnerId"), "compositionGate.verifierOwnerId") != "security.dw09":
        raise CompromiseRecoveryError("DW09 composition gate verifier owner mismatch")
    _text(gate.get("supportScope"), "compositionGate.supportScope")


def _coverage_standing(case: Mapping[str, Any], dimension: str) -> tuple[str, list[str]]:
    rows = [
        row
        for row in _rows(case.get("detectorCoverage", []), "detectorCoverage")
        if row["dimension"] == dimension
    ]
    if not rows:
        return "UNKNOWN", []
    refs = sorted(row["coverageRef"] for row in rows)
    standings = {row["standing"] for row in rows}
    if standings == {"COMPLETE"}:
        return "COMPLETE", refs
    if "PARTIAL" in standings or "COMPLETE" in standings:
        return "PARTIAL", refs
    return "UNKNOWN", refs


def _dimension_projection(case: Mapping[str, Any], dimension: str) -> dict[str, Any]:
    signals = [
        row for row in _rows(case.get("signals", []), "signals") if row["signalClass"] == dimension
    ]
    current_adverse = [
        row
        for row in signals
        if row["findingStanding"] == "OBSERVED" and row["currentnessStanding"] in _CURRENT
    ]
    historical_adverse = [
        row
        for row in signals
        if row["findingStanding"] == "OBSERVED"
        and row["currentnessStanding"] == "HISTORICAL_NOT_CURRENT"
    ]
    coverage_standing, coverage_refs = _coverage_standing(case, dimension)

    if current_adverse:
        standing = "CONFIRMED"
        bounded_negative = False
    elif historical_adverse:
        standing = "HISTORICAL_ADVERSE_REQUIRES_CURRENT_INVESTIGATION"
        bounded_negative = False
    elif coverage_standing == "COMPLETE":
        standing = f"NO_{dimension}_OBSERVED_COMPLETE_COVERAGE"
        bounded_negative = True
    else:
        standing = "UNKNOWN"
        bounded_negative = False

    return {
        "standing": standing,
        "coverageStanding": coverage_standing,
        "coverageRefs": coverage_refs,
        "currentAdverseEvidenceRefs": sorted(row["evidenceRef"] for row in current_adverse),
        "historicalAdverseEvidenceRefs": sorted(row["evidenceRef"] for row in historical_adverse),
        "boundedNegativeEvidenceEstablished": bounded_negative,
        "globalAbsenceEstablished": False,
    }


def _recovery_projection(
    case: Mapping[str, Any],
    compromise: Mapping[str, Any],
    persistence: Mapping[str, Any],
) -> dict[str, Any]:
    obligations = _rows(case.get("recoveryObligations", []), "recoveryObligations")
    required = [row for row in obligations if row["required"]]
    pending = sorted(row["obligationRef"] for row in required if row["standing"] != "SATISFIED")
    eradication_required = [row for row in required if row["phase"] == "ERADICATION"]
    eradication_complete = bool(eradication_required) and all(
        row["standing"] == "SATISFIED" for row in eradication_required
    )
    requalification = case.get("requalification")
    requalification_satisfied = False
    if isinstance(requalification, Mapping):
        requalification_satisfied = (
            requalification.get("standing") == "SATISFIED"
            and requalification.get("currentnessStanding") in _CURRENT
        )

    current_adverse = (
        compromise["standing"] == "CONFIRMED" or persistence["standing"] == "CONFIRMED"
    )
    historical_adverse = (
        compromise["standing"] == "HISTORICAL_ADVERSE_REQUIRES_CURRENT_INVESTIGATION"
        or persistence["standing"] == "HISTORICAL_ADVERSE_REQUIRES_CURRENT_INVESTIGATION"
    )
    bounded_negative = (
        compromise["boundedNegativeEvidenceEstablished"]
        and persistence["boundedNegativeEvidenceEstablished"]
    )

    all_required_satisfied = bool(required) and not pending
    recovery_established = bool(
        current_adverse and all_required_satisfied and requalification_satisfied
    )

    if recovery_established:
        standing = "RECOVERY_VERIFIED"
    elif current_adverse:
        standing = "RECOVERY_OPEN"
    elif historical_adverse:
        standing = "UNKNOWN_CURRENT_INCIDENT_STATE"
    elif bounded_negative:
        standing = "NOT_TRIGGERED_BOUNDED_NEGATIVE"
    else:
        standing = "UNKNOWN"

    return {
        "standing": standing,
        "requiredObligationRefs": sorted(row["obligationRef"] for row in required),
        "pendingRequiredObligationRefs": pending,
        "eradicationEstablished": bool(current_adverse and eradication_complete),
        "requalificationSatisfied": requalification_satisfied,
        "recoveryEstablished": recovery_established,
    }


def project_compromise_recovery(case: Mapping[str, Any]) -> dict[str, Any]:
    validate_case(case)
    compromise = _dimension_projection(case, "COMPROMISE")
    persistence = _dimension_projection(case, "PERSISTENCE")
    recovery = _recovery_projection(case, compromise, persistence)

    invalidation_keys = [f"subjectSnapshotDigest:{case['subjectSnapshotDigest']}"]
    for row in _rows(case.get("signals", []), "signals"):
        invalidation_keys.append(f"signalSourceDigest:{row['sourceDigest']}")
    for row in _rows(case.get("detectorCoverage", []), "detectorCoverage"):
        invalidation_keys.append(f"coverageSourceDigest:{row['sourceDigest']}")
    for row in _rows(case.get("recoveryObligations", []), "recoveryObligations"):
        invalidation_keys.append(f"recoveryObligationDigest:{canonical_digest(dict(row))}")
    if isinstance(case.get("requalification"), Mapping):
        invalidation_keys.append(
            f"requalificationSourceDigest:{case['requalification']['sourceDigest']}"
        )

    result: dict[str, Any] = {
        "schemaVersion": 1,
        "kind": "ordivon.security.dwc-compromise-recovery-projection-r1",
        "caseRef": case["caseRef"],
        "subjectRef": case["subjectRef"],
        "subjectSnapshotDigest": case["subjectSnapshotDigest"],
        "incidentProfileRef": "meta/next/planning/incident-case-profile-r1.json",
        "protectionVerifiedInput": case["protection"]["verifiedProtectionEstablished"],
        "compromise": compromise,
        "persistence": persistence,
        "recovery": recovery,
        "compromiseAbsenceEstablished": False,
        "domainAcceptanceEstablished": False,
        "invalidationKeys": sorted(set(invalidation_keys)),
        "truthBoundary": (
            "DW09 projects compromise, persistence and recovery independently of protection. "
            "Complete detector coverage with no adverse signal establishes only a bounded negative "
            "observation, never global compromise absence. Recovery requires explicit owner-authored "
            "obligations plus fresh owner-native requalification."
        ),
    }
    result["resultDigest"] = canonical_digest(result)
    return result


def composition_gate_result(
    *, case: Mapping[str, Any], projection: Mapping[str, Any]
) -> dict[str, Any]:
    validate_case(case)
    if projection.get("caseRef") != case["caseRef"]:
        raise CompromiseRecoveryError("projection caseRef mismatch")
    if projection.get("subjectSnapshotDigest") != case["subjectSnapshotDigest"]:
        raise CompromiseRecoveryError("projection subject snapshot mismatch")
    gate = _mapping(case["compositionGate"], "compositionGate")
    evidence_refs = sorted(
        {
            *(row["evidenceRef"] for row in _rows(case.get("signals", []), "signals")),
            *(
                row["sourceRef"]
                for row in _rows(case.get("detectorCoverage", []), "detectorCoverage")
            ),
        }
    )
    if not evidence_refs:
        evidence_refs = [f"subjectSnapshotDigest:{case['subjectSnapshotDigest']}"]
    return {
        "schemaVersion": 1,
        "kind": "ordivon.composition-gate-result",
        "circuitId": gate["circuitId"],
        "manifestDigest": gate["manifestDigest"],
        "gateId": gate["gateId"],
        "verifierOwnerId": gate["verifierOwnerId"],
        "standing": "SATISFIED",
        "evidenceRefs": evidence_refs,
        "supportScope": gate["supportScope"],
        "nonClaims": [
            "SATISFIED proves only exact DW06->DW09 case/subject admission into this projection.",
            "It does not establish compromise absence, eradication, recovery, protection or domain acceptance.",
        ],
    }
