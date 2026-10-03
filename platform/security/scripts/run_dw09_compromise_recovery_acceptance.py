#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ordivon_security_v2.admission import canonical_digest
from ordivon_security_v2.compromise_recovery import (
    composition_gate_result,
    project_compromise_recovery,
)


def gate(circuit_id: str, manifest_digest: str) -> dict[str, Any]:
    return {
        "circuitId": circuit_id,
        "manifestDigest": manifest_digest,
        "gateId": "gate:dw06-dw09-compromise-hunt",
        "verifierOwnerId": "security.dw09",
        "supportScope": "DW06->DW09 incident-case admission seam only",
    }


def binding_fields(case_ref: str, subject_ref: str, snapshot: str) -> dict[str, str]:
    return {
        "caseRef": case_ref,
        "subjectRef": subject_ref,
        "subjectSnapshotDigest": snapshot,
    }


def coverage(
    *,
    case_ref: str,
    subject_ref: str,
    snapshot: str,
    dimension: str,
    source_ref: str,
    scope_digest: str,
) -> dict[str, Any]:
    base = binding_fields(case_ref, subject_ref, snapshot)
    return {
        **base,
        "coverageRef": f"coverage:{case_ref}:{dimension.lower()}",
        "dimension": dimension,
        "standing": "COMPLETE",
        "scopeDigest": scope_digest,
        "ownerRef": f"observer:{case_ref}:{dimension.lower()}",
        "sourceRef": source_ref,
        "sourceDigest": canonical_digest(
            {
                "caseRef": case_ref,
                "dimension": dimension,
                "sourceRef": source_ref,
                "standing": "COMPLETE",
            }
        ),
    }


def signal(
    *,
    case_ref: str,
    subject_ref: str,
    snapshot: str,
    signal_class: str,
    evidence_ref: str,
    currentness: str,
    source_ref: str,
) -> dict[str, Any]:
    return {
        **binding_fields(case_ref, subject_ref, snapshot),
        "signalClass": signal_class,
        "findingStanding": "OBSERVED",
        "currentnessStanding": currentness,
        "evidenceRef": evidence_ref,
        "ownerRef": f"observer:{signal_class.lower()}",
        "sourceRef": source_ref,
        "sourceDigest": canonical_digest(
            {
                "signalClass": signal_class,
                "evidenceRef": evidence_ref,
                "currentness": currentness,
                "sourceRef": source_ref,
            }
        ),
    }


def obligation(
    *,
    case_ref: str,
    subject_ref: str,
    snapshot: str,
    obligation_ref: str,
    phase: str,
    cls: str,
) -> dict[str, Any]:
    return {
        **binding_fields(case_ref, subject_ref, snapshot),
        "obligationRef": obligation_ref,
        "phase": phase,
        "class": cls,
        "required": True,
        "standing": "SATISFIED",
        "ownerRef": f"owner:{cls}",
        "verifierRef": f"verifier:{cls}",
        "evidenceRefs": [f"evidence:{obligation_ref}"],
    }


def main() -> int:
    repo = Path(__file__).resolve().parents[3]
    out = repo / "platform/security/evidence/acceptance"
    composition_binding = json.loads(
        (
            repo
            / "platform/security/fixtures/dw09/historical-exchange-composition-binding-r1.json"
        ).read_text()
    )

    case_binding = composition_binding["caseBinding"]
    circuit = composition_binding["compositionGate"]

    historical = {
        "schemaVersion": 1,
        "kind": "ordivon.security.dwc-compromise-recovery-case-r1",
        "caseRef": case_binding["caseRef"],
        "subjectRef": case_binding["subjectRef"],
        "subjectSnapshotDigest": case_binding["subjectSnapshotDigest"],
        "protection": {"verifiedProtectionEstablished": False},
        "signals": [
            signal(
                case_ref=case_binding["caseRef"],
                subject_ref=case_binding["subjectRef"],
                snapshot=case_binding["subjectSnapshotDigest"],
                signal_class="PERSISTENCE",
                evidence_ref="historical:Microsoft-HAFNIUM-2021-03-02:web-shell-persistence",
                currentness="HISTORICAL_NOT_CURRENT",
                source_ref="platform/security/evidence/acceptance/dw04-attack-coverage-r1-20261001.json",
            )
        ],
        "detectorCoverage": [],
        "recoveryObligations": [],
        "requalification": None,
        "compositionGate": gate(circuit["circuitId"], circuit["manifestDigest"]),
    }
    historical_projection = project_compromise_recovery(historical)
    historical_gate = composition_gate_result(
        case=historical, projection=historical_projection
    )

    benign_case = "case:dw09:benign-persistence-canary"
    benign_subject = "fixture:dw09:benign-host"
    benign_snapshot = canonical_digest(
        {"caseRef": benign_case, "subjectRef": benign_subject, "state": "clean-fixture"}
    )
    benign_scope = canonical_digest({"scope": "synthetic-complete-detector-fixture-r1"})
    benign_manifest = canonical_digest(
        {"circuitId": "circuit:dw09:benign-canary", "gate": "gate:dw06-dw09-compromise-hunt"}
    )
    benign = {
        "schemaVersion": 1,
        "kind": "ordivon.security.dwc-compromise-recovery-case-r1",
        "caseRef": benign_case,
        "subjectRef": benign_subject,
        "subjectSnapshotDigest": benign_snapshot,
        "protection": {"verifiedProtectionEstablished": True},
        "signals": [],
        "detectorCoverage": [
            coverage(
                case_ref=benign_case,
                subject_ref=benign_subject,
                snapshot=benign_snapshot,
                dimension="COMPROMISE",
                source_ref="fixture:dw09:benign-compromise-detector",
                scope_digest=benign_scope,
            ),
            coverage(
                case_ref=benign_case,
                subject_ref=benign_subject,
                snapshot=benign_snapshot,
                dimension="PERSISTENCE",
                source_ref="fixture:dw09:benign-persistence-detector",
                scope_digest=benign_scope,
            ),
        ],
        "recoveryObligations": [],
        "requalification": None,
        "compositionGate": gate("circuit:dw09:benign-canary", benign_manifest),
    }
    benign_projection = project_compromise_recovery(benign)
    benign_gate = composition_gate_result(case=benign, projection=benign_projection)

    recovery_case = "case:dw09:synthetic-recovery-canary"
    recovery_subject = "fixture:dw09:synthetic-compromised-host"
    recovery_snapshot = canonical_digest(
        {
            "caseRef": recovery_case,
            "subjectRef": recovery_subject,
            "state": "synthetic-incident-fixture",
        }
    )
    recovery_scope = canonical_digest({"scope": "synthetic-incident-detectors-r1"})
    recovery_manifest = canonical_digest(
        {"circuitId": "circuit:dw09:recovery-canary", "gate": "gate:dw06-dw09-compromise-hunt"}
    )
    recovery = {
        "schemaVersion": 1,
        "kind": "ordivon.security.dwc-compromise-recovery-case-r1",
        "caseRef": recovery_case,
        "subjectRef": recovery_subject,
        "subjectSnapshotDigest": recovery_snapshot,
        "protection": {"verifiedProtectionEstablished": True},
        "signals": [
            signal(
                case_ref=recovery_case,
                subject_ref=recovery_subject,
                snapshot=recovery_snapshot,
                signal_class="COMPROMISE",
                evidence_ref="fixture:dw09:current-compromise",
                currentness="POINT_IN_TIME_OBSERVED",
                source_ref="fixture:dw09:compromise-observer",
            ),
            signal(
                case_ref=recovery_case,
                subject_ref=recovery_subject,
                snapshot=recovery_snapshot,
                signal_class="PERSISTENCE",
                evidence_ref="fixture:dw09:current-persistence",
                currentness="POINT_IN_TIME_OBSERVED",
                source_ref="fixture:dw09:persistence-observer",
            ),
        ],
        "detectorCoverage": [
            coverage(
                case_ref=recovery_case,
                subject_ref=recovery_subject,
                snapshot=recovery_snapshot,
                dimension="COMPROMISE",
                source_ref="fixture:dw09:compromise-detector",
                scope_digest=recovery_scope,
            ),
            coverage(
                case_ref=recovery_case,
                subject_ref=recovery_subject,
                snapshot=recovery_snapshot,
                dimension="PERSISTENCE",
                source_ref="fixture:dw09:persistence-detector",
                scope_digest=recovery_scope,
            ),
        ],
        "recoveryObligations": [
            obligation(
                case_ref=recovery_case,
                subject_ref=recovery_subject,
                snapshot=recovery_snapshot,
                obligation_ref="obl:credential-rotation",
                phase="ERADICATION",
                cls="credential-rotation",
            ),
            obligation(
                case_ref=recovery_case,
                subject_ref=recovery_subject,
                snapshot=recovery_snapshot,
                obligation_ref="obl:key-rotation",
                phase="ERADICATION",
                cls="key-rotation",
            ),
            obligation(
                case_ref=recovery_case,
                subject_ref=recovery_subject,
                snapshot=recovery_snapshot,
                obligation_ref="obl:rebuild",
                phase="RECOVERY",
                cls="rebuild",
            ),
            obligation(
                case_ref=recovery_case,
                subject_ref=recovery_subject,
                snapshot=recovery_snapshot,
                obligation_ref="obl:requalify",
                phase="REQUALIFICATION",
                cls="requalify",
            ),
        ],
        "requalification": {
            **binding_fields(recovery_case, recovery_subject, recovery_snapshot),
            "standing": "SATISFIED",
            "currentnessStanding": "POINT_IN_TIME_OBSERVED",
            "ownerRef": "observer:dw09:requalification",
            "sourceRef": "fixture:dw09:fresh-requalification",
            "sourceDigest": canonical_digest(
                {"caseRef": recovery_case, "standing": "SATISFIED", "fresh": True}
            ),
        },
        "compositionGate": gate("circuit:dw09:recovery-canary", recovery_manifest),
    }
    recovery_projection = project_compromise_recovery(recovery)
    recovery_gate = composition_gate_result(
        case=recovery, projection=recovery_projection
    )

    assert historical_projection["persistence"]["standing"] == (
        "HISTORICAL_ADVERSE_REQUIRES_CURRENT_INVESTIGATION"
    )
    assert historical_projection["recovery"]["standing"] == "UNKNOWN_CURRENT_INCIDENT_STATE"
    assert historical_projection["compromiseAbsenceEstablished"] is False
    assert historical_gate["standing"] == "SATISFIED"

    assert benign_projection["compromise"]["standing"] == (
        "NO_COMPROMISE_OBSERVED_COMPLETE_COVERAGE"
    )
    assert benign_projection["persistence"]["standing"] == (
        "NO_PERSISTENCE_OBSERVED_COMPLETE_COVERAGE"
    )
    assert benign_projection["compromiseAbsenceEstablished"] is False
    assert benign_projection["recovery"]["standing"] == "NOT_TRIGGERED_BOUNDED_NEGATIVE"
    assert benign_gate["standing"] == "SATISFIED"

    assert recovery_projection["compromise"]["standing"] == "CONFIRMED"
    assert recovery_projection["persistence"]["standing"] == "CONFIRMED"
    assert recovery_projection["recovery"]["eradicationEstablished"] is True
    assert recovery_projection["recovery"]["recoveryEstablished"] is True
    assert recovery_projection["recovery"]["standing"] == "RECOVERY_VERIFIED"
    assert recovery_projection["domainAcceptanceEstablished"] is False
    assert recovery_gate["standing"] == "SATISFIED"

    census = {
        "schemaVersion": 1,
        "kind": "ordivon.security.dw09-detector-owner-census-r1",
        "observedAt": "2026-10-01T15:38:00+08:00",
        "standing": "OWNER_SCOPED_CENSUS_NO_GLOBAL_DETECTOR_REGISTRY",
        "targetClasses": [
            {
                "targetClass": "historical-exchange-replay",
                "telemetryOrDetectorOwner": None,
                "standing": "CURRENT_COVERAGE_UNKNOWN",
                "evidenceRefs": [
                    "platform/security/evidence/acceptance/dw04-attack-coverage-r1-20261001.json"
                ],
                "reason": (
                    "Historical Attack Flow/ATT&CK persistence evidence is not current local "
                    "telemetry and cannot establish present detector coverage."
                ),
            },
            {
                "targetClass": "linux-runtime",
                "telemetryOrDetectorOwner": "OpenTelemetry-capable substrate only",
                "standing": "COMPROMISE_DETECTOR_BINDING_UNKNOWN",
                "evidenceRefs": ["catalogs/capabilities/providers/opentelemetry.md"],
                "reason": (
                    "Generic telemetry capability exists, but this census found no exact "
                    "DW09 compromise/persistence detector binding for Linux Runtime."
                ),
            },
            {
                "targetClass": "windows-runtime",
                "telemetryOrDetectorOwner": "owner-native Runtime/Windows evidence only",
                "standing": "COMPROMISE_DETECTOR_BINDING_UNKNOWN",
                "evidenceRefs": [],
                "reason": (
                    "No exact Security-owned DW09 compromise/persistence detector binding was "
                    "found; Runtime recovery evidence is outside current Security detector "
                    "authority and is not treated as detector coverage."
                ),
            },
            {
                "targetClass": "browser-security",
                "telemetryOrDetectorOwner": "browser-security study owner",
                "standing": "OWNER_SPECIFIC_NOT_TRANSFERABLE",
                "evidenceRefs": [
                    "catalogs/knowledge/graphs/browser-security-detector-coverage-r9.json"
                ],
                "reason": (
                    "Browser-security detector coverage artifacts are owner/target specific "
                    "and cannot be reused as Exchange or Runtime compromise evidence."
                ),
            },
        ],
        "nonClaims": [
            "This is not a global detector inventory.",
            "Repository presence does not prove a detector is live, current or complete.",
            "Absence of an exact binding is UNKNOWN coverage, not evidence of no compromise.",
        ],
    }
    census["evidenceDigest"] = canonical_digest(census)
    census_path = out / "dw09-detector-owner-census-r1-20261001.json"
    census_path.write_text(json.dumps(census, indent=2, sort_keys=True) + "\n")

    evidence = {
        "schemaVersion": 1,
        "kind": "ordivon.security.dw09-compromise-recovery-r1-acceptance",
        "observedAt": "2026-10-01T15:38:00+08:00",
        "workRef": "work:security:dwc-r21:dw09-compromise-recovery:20261001",
        "standing": "DW09_COMPROMISE_PERSISTENCE_RECOVERY_PROJECTION_QUALIFIED",
        "baseRevision": "57fe5429c1c58ae427ca0a897afc27066b010ec2",
        "historicalCompositionBinding": {
            "fixtureRef": "platform/security/fixtures/dw09/historical-exchange-composition-binding-r1.json",
            **composition_binding["provenance"],
        },
        "detectorOwnerCensus": {
            "path": str(census_path.relative_to(repo)),
            "evidenceDigest": census["evidenceDigest"],
        },
        "historicalExchangeReplay": {
            "case": historical,
            "projection": historical_projection,
            "compositionGateResult": historical_gate,
            "claimBoundary": (
                "Historical web-shell persistence evidence opens current investigation "
                "uncertainty only; it does not claim a present Exchange subject is compromised."
            ),
        },
        "benignPersistenceCanary": {
            "case": benign,
            "projection": benign_projection,
            "compositionGateResult": benign_gate,
            "claimBoundary": (
                "Complete synthetic detector coverage with no adverse signal establishes only "
                "bounded negative evidence; global compromise absence remains false."
            ),
        },
        "syntheticRecoveryCanary": {
            "case": recovery,
            "projection": recovery_projection,
            "compositionGateResult": recovery_gate,
            "claimBoundary": (
                "Synthetic recovery mechanics require explicit credential/key rotation, rebuild, "
                "requalification obligations and a fresh requalification observation. No production "
                "recovery truth is established."
            ),
        },
        "invariants": [
            "Verified protection does not close compromise or persistence standing.",
            "No adverse signal with incomplete/unknown detector coverage remains UNKNOWN.",
            "Historical adverse evidence does not become current compromise truth.",
            "Complete bounded detector coverage may establish bounded negative evidence only, never global compromise absence.",
            "Recovery requires owner-authored required obligations plus fresh owner-native requalification.",
            "DW06->DW09 gate SATISFIED proves only exact case/subject admission into the projection.",
        ],
        "nonClaims": [
            "No live Exchange, Linux Runtime, Windows Runtime or browser target is declared clean or compromised by this acceptance.",
            "No containment/recovery effect is executed.",
            "The synthetic recovery canary is mechanics-only.",
            "No global incident registry, detector registry, root-cause oracle or automatic recovery controller is created.",
        ],
    }
    evidence["evidenceDigest"] = canonical_digest(evidence)
    path = out / "dw09-compromise-recovery-r1-20261001.json"
    path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")

    print(
        json.dumps(
            {
                "standing": evidence["standing"],
                "evidenceDigest": evidence["evidenceDigest"],
                "detectorCensusDigest": census["evidenceDigest"],
                "historicalPersistence": historical_projection["persistence"]["standing"],
                "historicalRecovery": historical_projection["recovery"]["standing"],
                "benignCompromise": benign_projection["compromise"]["standing"],
                "benignPersistence": benign_projection["persistence"]["standing"],
                "benignGlobalAbsence": benign_projection["compromiseAbsenceEstablished"],
                "recoveryCompromise": recovery_projection["compromise"]["standing"],
                "recoveryPersistence": recovery_projection["persistence"]["standing"],
                "recoveryStanding": recovery_projection["recovery"]["standing"],
                "recoveryEstablished": recovery_projection["recovery"]["recoveryEstablished"],
                "domainAcceptanceEstablished": recovery_projection["domainAcceptanceEstablished"],
                "output": str(path.relative_to(repo)),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
