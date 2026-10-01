from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

_SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_DW01_KIND = "ordivon.security.dwc-subject-exposure-snapshot"

_SOURCE_KINDS = {
    "vendor-advisory",
    "csaf",
    "cyclonedx-vex",
    "local-observation",
    "cisa-kev",
    "first-epss",
}
_SUBJECT_BOUND_KINDS = {
    "vendor-advisory",
    "csaf",
    "cyclonedx-vex",
    "local-observation",
}
_CURRENTNESS = {"CURRENT", "STALE", "UNKNOWN"}
_ADMISSION = {"ADMITTED", "UNVERIFIED"}
_APPLICABILITY = {"AFFECTED", "NOT_AFFECTED", "UNDER_INVESTIGATION"}

_CSAF_STATUS = {
    "first_affected": "AFFECTED",
    "known_affected": "AFFECTED",
    "last_affected": "AFFECTED",
    "first_fixed": "NOT_AFFECTED",
    "fixed": "NOT_AFFECTED",
    "known_not_affected": "NOT_AFFECTED",
    "under_investigation": "UNDER_INVESTIGATION",
    # CSAF 2.1 CSD03 adds explicit unknown. It is never a clearance.
    "unknown": "UNDER_INVESTIGATION",
}
_CYCLONEDX_STATE = {
    "exploitable": "AFFECTED",
    "resolved": "NOT_AFFECTED",
    "resolved_with_pedigree": "NOT_AFFECTED",
    "false_positive": "NOT_AFFECTED",
    "not_affected": "NOT_AFFECTED",
    "in_triage": "UNDER_INVESTIGATION",
}


def project_csaf_product_status(status: str) -> str:
    """Project one exact CSAF product-status bucket without copying the advisory."""
    try:
        return _CSAF_STATUS[status]
    except KeyError as exc:
        raise ValueError(f"CSAF status is not an applicability state: {status}") from exc


def project_cyclonedx_vex_state(state: str) -> str:
    """Project one CycloneDX VEX analysis state for an exact subject binding."""
    try:
        return _CYCLONEDX_STATE[state]
    except KeyError as exc:
        raise ValueError(f"unsupported CycloneDX VEX analysis state: {state}") from exc


def _required_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} is required")
    return value


def _digest(value: object, label: str) -> str:
    text = _required_text(value, label)
    if not _SHA256.fullmatch(text):
        raise ValueError(f"{label} must be sha256:<64 lowercase hex>")
    return text


def _required_text_list(value: object, label: str) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be an array")
    result = [_required_text(item, f"{label} item") for item in value]
    if not result:
        raise ValueError(f"{label} must contain at least one identity dimension")
    if len(result) != len(set(result)):
        raise ValueError(f"{label} must not contain duplicates")
    return sorted(result)


def _dw01_subject_snapshot(value: Mapping[str, object]) -> dict[str, object]:
    kind = _required_text(value.get("kind"), "subject.kind")
    if kind != _DW01_KIND:
        raise ValueError(f"subject.kind must be {_DW01_KIND}")

    snapshot_digest = _digest(value.get("snapshotDigest"), "subject.snapshotDigest")
    evidence_ref = _required_text(value.get("evidenceRef"), "subject.evidenceRef")
    expected_ref = f"dwc-subject-exposure:{snapshot_digest}"
    if evidence_ref != expected_ref:
        raise ValueError("subject.evidenceRef does not bind subject.snapshotDigest")

    return {
        "kind": kind,
        "caseRef": _required_text(value.get("caseRef"), "subject.caseRef"),
        "epochRef": _required_text(value.get("epochRef"), "subject.epochRef"),
        "subjectRef": _required_text(value.get("subjectRef"), "subject.subjectRef"),
        "snapshotDigest": snapshot_digest,
        "evidenceRef": evidence_ref,
        "requiredIdentityDimensions": _required_text_list(
            value.get("requiredIdentityDimensions"),
            "subject.requiredIdentityDimensions",
        ),
        "identityCoverageStanding": _required_text(
            value.get("identityCoverageStanding"),
            "subject.identityCoverageStanding",
        ),
        "exposureCoverageStanding": _required_text(
            value.get("exposureCoverageStanding"),
            "subject.exposureCoverageStanding",
        ),
        "observationHorizonStanding": _required_text(
            value.get("observationHorizonStanding"),
            "subject.observationHorizonStanding",
        ),
        "mechanicalBindingStanding": _required_text(
            value.get("mechanicalBindingStanding"),
            "subject.mechanicalBindingStanding",
        ),
    }


def _subject_binding(value: Mapping[str, object], *, label: str) -> dict[str, str]:
    snapshot_digest = _digest(value.get("snapshotDigest"), f"{label}.snapshotDigest")
    evidence_ref = _required_text(value.get("evidenceRef"), f"{label}.evidenceRef")
    if evidence_ref != f"dwc-subject-exposure:{snapshot_digest}":
        raise ValueError(f"{label}.evidenceRef does not bind snapshotDigest")
    return {
        "subjectRef": _required_text(value.get("subjectRef"), f"{label}.subjectRef"),
        "snapshotDigest": snapshot_digest,
        "evidenceRef": evidence_ref,
    }


def _currentness(values: list[str]) -> str:
    if not values:
        return "UNKNOWN"
    present = set(values)
    if present == {"CURRENT"}:
        return "CURRENT"
    if "CURRENT" in present:
        return "MIXED_HORIZON"
    if "STALE" in present:
        return "STALE_ONLY"
    return "UNKNOWN"


def _normalize_evidence(
    raw: Mapping[str, object],
    *,
    subject_binding: Mapping[str, str],
    vulnerability_ref: str,
) -> dict[str, Any]:
    evidence_ref = _required_text(raw.get("evidenceRef"), "evidenceRef")
    source_kind = _required_text(raw.get("sourceKind"), f"{evidence_ref}.sourceKind")
    if source_kind not in _SOURCE_KINDS:
        raise ValueError(f"unsupported sourceKind for {evidence_ref}: {source_kind}")

    native_ref = _required_text(
        raw.get("providerNativeRef"), f"{evidence_ref}.providerNativeRef"
    )
    artifact_digest = _digest(raw.get("artifactDigest"), f"{evidence_ref}.artifactDigest")
    evidence_vulnerability = _required_text(
        raw.get("vulnerabilityRef"), f"{evidence_ref}.vulnerabilityRef"
    )
    if evidence_vulnerability != vulnerability_ref:
        raise ValueError(
            f"{evidence_ref} vulnerabilityRef does not match requested vulnerability"
        )

    admission = _required_text(raw.get("admission"), f"{evidence_ref}.admission")
    if admission not in _ADMISSION:
        raise ValueError(f"unsupported admission for {evidence_ref}: {admission}")
    currentness = _required_text(raw.get("currentness"), f"{evidence_ref}.currentness")
    if currentness not in _CURRENTNESS:
        raise ValueError(f"unsupported currentness for {evidence_ref}: {currentness}")

    projected = raw.get("projectedApplicability")
    if projected is not None:
        projected = _required_text(projected, f"{evidence_ref}.projectedApplicability")
        if projected not in _APPLICABILITY:
            raise ValueError(
                f"unsupported projectedApplicability for {evidence_ref}: {projected}"
            )

    binding = raw.get("subjectBinding")
    if source_kind in _SUBJECT_BOUND_KINDS or projected is not None:
        if not isinstance(binding, Mapping):
            raise ValueError(f"{evidence_ref} requires exact subjectBinding")
        bound = _subject_binding(binding, label=f"{evidence_ref}.subjectBinding")
        if bound != subject_binding:
            raise ValueError(f"{evidence_ref} subjectBinding does not match DW01 subject")
    elif binding is not None:
        raise ValueError(f"{evidence_ref} global threat signal must not mint subject binding")

    known_exploited = raw.get("knownExploited")
    epss = raw.get("epss")

    if source_kind == "cisa-kev":
        if known_exploited is not True:
            raise ValueError(f"{evidence_ref} CISA KEV evidence must represent catalog membership")
        if projected is not None or epss is not None:
            raise ValueError(f"{evidence_ref} CISA KEV cannot determine local applicability")
    elif known_exploited is not None:
        raise ValueError(f"{evidence_ref} knownExploited is reserved for CISA KEV evidence")

    normalized_epss: dict[str, object] | None = None
    if source_kind == "first-epss":
        if not isinstance(epss, Mapping):
            raise ValueError(f"{evidence_ref} FIRST EPSS evidence requires epss fields")
        probability = epss.get("probability")
        percentile = epss.get("percentile")
        date = epss.get("date")
        if (
            not isinstance(probability, (int, float))
            or isinstance(probability, bool)
            or not 0 <= float(probability) <= 1
        ):
            raise ValueError(f"{evidence_ref} EPSS probability must be within [0, 1]")
        if (
            not isinstance(percentile, (int, float))
            or isinstance(percentile, bool)
            or not 0 <= float(percentile) <= 1
        ):
            raise ValueError(f"{evidence_ref} EPSS percentile must be within [0, 1]")
        if not isinstance(date, str) or not _DATE.fullmatch(date):
            raise ValueError(f"{evidence_ref} EPSS date must be YYYY-MM-DD")
        if projected is not None:
            raise ValueError(f"{evidence_ref} EPSS cannot determine local applicability")
        normalized_epss = {
            "probability": float(probability),
            "percentile": float(percentile),
            "date": date,
        }
    elif epss is not None:
        raise ValueError(f"{evidence_ref} epss fields are reserved for FIRST EPSS evidence")

    result: dict[str, Any] = {
        "evidenceRef": evidence_ref,
        "sourceKind": source_kind,
        "providerNativeRef": native_ref,
        "artifactDigest": artifact_digest,
        "vulnerabilityRef": vulnerability_ref,
        "admission": admission,
        "currentness": currentness,
    }
    if binding is not None:
        result["subjectBinding"] = dict(subject_binding)
    if projected is not None:
        result["projectedApplicability"] = projected
    if known_exploited is True:
        result["knownExploited"] = True
    if normalized_epss is not None:
        result["epss"] = normalized_epss
    return result


def fuse_threat_applicability(
    *,
    subject: Mapping[str, object],
    vulnerability_ref: str,
    evidence: list[Mapping[str, object]],
) -> dict[str, Any]:
    """
    Fuse admitted, digest-bound threat/applicability projections for one DW01 subject.

    This function deliberately does not fetch, cache, or normalize provider documents.
    Every projection retains the provider-native locator and exact artifact digest.
    KEV and EPSS enrich prioritization only; neither can make a local subject AFFECTED
    or NOT_AFFECTED.
    """
    normalized_subject = _dw01_subject_snapshot(subject)
    subject_binding = _subject_binding(normalized_subject, label="subject")
    vulnerability_ref = _required_text(vulnerability_ref, "vulnerability_ref")
    if not evidence:
        raise ValueError("at least one evidence reference is required")

    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in evidence:
        item = _normalize_evidence(
            raw,
            subject_binding=subject_binding,
            vulnerability_ref=vulnerability_ref,
        )
        ref = item["evidenceRef"]
        if ref in seen:
            raise ValueError(f"duplicate evidenceRef: {ref}")
        seen.add(ref)
        normalized.append(item)

    admitted = [item for item in normalized if item["admission"] == "ADMITTED"]
    unadmitted_refs = [
        item["evidenceRef"] for item in normalized if item["admission"] != "ADMITTED"
    ]
    applicability = [
        item for item in admitted if item.get("projectedApplicability") is not None
    ]
    current_applicability = [
        item for item in applicability if item["currentness"] == "CURRENT"
    ]
    noncurrent_applicability = [
        item for item in applicability if item["currentness"] != "CURRENT"
    ]

    current_affected = [
        item
        for item in current_applicability
        if item["projectedApplicability"] == "AFFECTED"
    ]
    current_clear = [
        item
        for item in current_applicability
        if item["projectedApplicability"] == "NOT_AFFECTED"
    ]
    current_investigation = [
        item
        for item in current_applicability
        if item["projectedApplicability"] == "UNDER_INVESTIGATION"
    ]
    noncurrent_affected = [
        item
        for item in noncurrent_applicability
        if item["projectedApplicability"] == "AFFECTED"
    ]

    conflicts: list[dict[str, object]] = []
    if normalized_subject["identityCoverageStanding"] != "COMPLETE":
        conflicts.append(
            {
                "kind": "DW01_IDENTITY_BINDING_NOT_CURRENT_COMPLETE",
                "subjectEvidenceRef": normalized_subject["evidenceRef"],
                "identityCoverageStanding": normalized_subject[
                    "identityCoverageStanding"
                ],
            }
        )
    if current_affected and current_clear:
        conflicts.append(
            {
                "kind": "CURRENT_APPLICABILITY_CONTRADICTION",
                "evidenceRefs": sorted(
                    item["evidenceRef"] for item in current_affected + current_clear
                ),
            }
        )
    if current_clear and noncurrent_affected:
        conflicts.append(
            {
                "kind": "NONCURRENT_ADVERSE_VS_CURRENT_CLEARANCE",
                "evidenceRefs": sorted(
                    item["evidenceRef"] for item in current_clear + noncurrent_affected
                ),
            }
        )

    if normalized_subject["identityCoverageStanding"] != "COMPLETE":
        claim = "UNDER_INVESTIGATION"
        basis = current_applicability or noncurrent_applicability
    elif current_affected and current_clear:
        claim = "UNDER_INVESTIGATION"
        basis = current_affected + current_clear
    elif current_affected:
        # Current adverse evidence is not weakened by stale clearances.
        claim = "AFFECTED"
        basis = current_affected
    elif current_clear and (current_investigation or noncurrent_affected):
        claim = "UNDER_INVESTIGATION"
        basis = current_clear + current_investigation + noncurrent_affected
    elif current_clear:
        claim = "NOT_AFFECTED"
        basis = current_clear
    else:
        claim = "UNDER_INVESTIGATION"
        basis = current_investigation or noncurrent_applicability

    current_kev = [
        item
        for item in admitted
        if item["sourceKind"] == "cisa-kev"
        and item["currentness"] == "CURRENT"
        and item.get("knownExploited") is True
    ]
    current_epss = [
        item
        for item in admitted
        if item["sourceKind"] == "first-epss"
        and item["currentness"] == "CURRENT"
        and item.get("epss") is not None
    ]

    return {
        "schemaVersion": 1,
        "kind": "ordivon.security.threat-applicability-fusion",
        "subject": normalized_subject,
        "vulnerabilityRef": vulnerability_ref,
        "claim": claim,
        "claimBasisEvidenceRefs": sorted(item["evidenceRef"] for item in basis),
        "currentness": {
            "evidenceStanding": _currentness([item["currentness"] for item in admitted]),
            "applicabilityStanding": _currentness(
                [item["currentness"] for item in applicability]
            ),
            "staleEvidenceRefs": sorted(
                item["evidenceRef"] for item in admitted if item["currentness"] == "STALE"
            ),
            "unknownCurrentnessEvidenceRefs": sorted(
                item["evidenceRef"]
                for item in admitted
                if item["currentness"] == "UNKNOWN"
            ),
        },
        "threatSignals": {
            "knownExploited": True if current_kev else None,
            "kevEvidenceRefs": sorted(item["evidenceRef"] for item in current_kev),
            "epss": sorted(
                (
                    {
                        "evidenceRef": item["evidenceRef"],
                        **item["epss"],
                    }
                    for item in current_epss
                ),
                key=lambda row: (row["date"], row["evidenceRef"]),
            ),
        },
        "conflicts": conflicts,
        "unadmittedEvidenceRefs": sorted(unadmitted_refs),
        "evidenceRefs": sorted(normalized, key=lambda item: item["evidenceRef"]),
        "truthBoundary": (
            "DW02 is a digest-bound applicability/threat projection for one exact DW01 "
            "SubjectExposureSnapshot. Provider-native artifacts remain authoritative. "
            "CISA KEV catalog membership and FIRST EPSS probability never establish "
            "local applicability. Definitive applicability requires DW01 identity "
            "coverage COMPLETE. A NOT_AFFECTED claim is never minted from stale, unknown, "
            "unadmitted, KEV-only, or EPSS-only evidence."
        ),
    }
