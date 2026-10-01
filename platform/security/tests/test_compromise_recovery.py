from __future__ import annotations

import unittest

from ordivon_security_v2.compromise_recovery import (
    CompromiseRecoveryError,
    composition_gate_result,
    project_compromise_recovery,
)

D1 = "sha256:" + "1" * 64
D2 = "sha256:" + "2" * 64
D3 = "sha256:" + "3" * 64
D4 = "sha256:" + "4" * 64


def coverage(dimension: str, standing: str = "COMPLETE") -> dict:
    return {
        "coverageRef": f"coverage:{dimension.lower()}",
        "caseRef": "case:test",
        "subjectRef": "subject:test",
        "subjectSnapshotDigest": D1,
        "dimension": dimension,
        "standing": standing,
        "scopeDigest": D2,
        "ownerRef": f"owner:{dimension.lower()}-detector",
        "sourceRef": f"evidence:{dimension.lower()}-coverage",
        "sourceDigest": D3,
    }


def signal(
    signal_class: str,
    *,
    currentness: str = "POINT_IN_TIME_OBSERVED",
    finding: str = "OBSERVED",
) -> dict:
    return {
        "caseRef": "case:test",
        "subjectRef": "subject:test",
        "subjectSnapshotDigest": D1,
        "signalClass": signal_class,
        "findingStanding": finding,
        "currentnessStanding": currentness,
        "evidenceRef": f"evidence:{signal_class.lower()}",
        "ownerRef": f"owner:{signal_class.lower()}-observer",
        "sourceRef": f"source:{signal_class.lower()}",
        "sourceDigest": D4,
    }


def obligation(
    ref: str,
    cls: str,
    phase: str,
    *,
    standing: str = "SATISFIED",
) -> dict:
    return {
        "obligationRef": ref,
        "caseRef": "case:test",
        "subjectRef": "subject:test",
        "subjectSnapshotDigest": D1,
        "phase": phase,
        "class": cls,
        "required": True,
        "standing": standing,
        "ownerRef": f"owner:{cls}",
        "verifierRef": f"verifier:{cls}",
        "evidenceRefs": [f"evidence:{cls}"] if standing == "SATISFIED" else [],
    }


def base_case() -> dict:
    return {
        "schemaVersion": 1,
        "kind": "ordivon.security.dwc-compromise-recovery-case-r1",
        "caseRef": "case:test",
        "subjectRef": "subject:test",
        "subjectSnapshotDigest": D1,
        "protection": {"verifiedProtectionEstablished": False},
        "signals": [],
        "detectorCoverage": [],
        "recoveryObligations": [],
        "requalification": None,
        "compositionGate": {
            "circuitId": "circuit:test",
            "manifestDigest": D2,
            "gateId": "gate:dw06-dw09-compromise-hunt",
            "verifierOwnerId": "security.dw09",
            "supportScope": "DW06->DW09 incident-case admission seam only",
        },
    }


class CompromiseRecoveryTests(unittest.TestCase):
    def test_verified_protection_does_not_close_compromise_without_coverage(self):
        case = base_case()
        case["protection"]["verifiedProtectionEstablished"] = True
        result = project_compromise_recovery(case)
        self.assertEqual(result["compromise"]["standing"], "UNKNOWN")
        self.assertEqual(result["persistence"]["standing"], "UNKNOWN")
        self.assertFalse(result["compromiseAbsenceEstablished"])

    def test_current_compromise_signal_confirms_compromise(self):
        case = base_case()
        case["signals"] = [signal("COMPROMISE")]
        result = project_compromise_recovery(case)
        self.assertEqual(result["compromise"]["standing"], "CONFIRMED")
        self.assertEqual(result["recovery"]["standing"], "RECOVERY_OPEN")

    def test_current_persistence_signal_confirms_persistence(self):
        case = base_case()
        case["signals"] = [signal("PERSISTENCE")]
        result = project_compromise_recovery(case)
        self.assertEqual(result["persistence"]["standing"], "CONFIRMED")
        self.assertEqual(result["recovery"]["standing"], "RECOVERY_OPEN")

    def test_historical_adverse_never_becomes_current_compromise(self):
        case = base_case()
        case["signals"] = [signal("PERSISTENCE", currentness="HISTORICAL_NOT_CURRENT")]
        result = project_compromise_recovery(case)
        self.assertEqual(
            result["persistence"]["standing"],
            "HISTORICAL_ADVERSE_REQUIRES_CURRENT_INVESTIGATION",
        )
        self.assertEqual(result["recovery"]["standing"], "UNKNOWN_CURRENT_INCIDENT_STATE")

    def test_complete_coverage_without_adverse_signal_is_bounded_negative_only(self):
        case = base_case()
        case["detectorCoverage"] = [coverage("COMPROMISE"), coverage("PERSISTENCE")]
        result = project_compromise_recovery(case)
        self.assertEqual(
            result["compromise"]["standing"],
            "NO_COMPROMISE_OBSERVED_COMPLETE_COVERAGE",
        )
        self.assertEqual(
            result["persistence"]["standing"],
            "NO_PERSISTENCE_OBSERVED_COMPLETE_COVERAGE",
        )
        self.assertTrue(result["compromise"]["boundedNegativeEvidenceEstablished"])
        self.assertFalse(result["compromise"]["globalAbsenceEstablished"])
        self.assertFalse(result["compromiseAbsenceEstablished"])
        self.assertEqual(result["recovery"]["standing"], "NOT_TRIGGERED_BOUNDED_NEGATIVE")

    def test_partial_coverage_preserves_unknown(self):
        case = base_case()
        case["detectorCoverage"] = [
            coverage("COMPROMISE", "PARTIAL"),
            coverage("PERSISTENCE", "COMPLETE"),
        ]
        result = project_compromise_recovery(case)
        self.assertEqual(result["compromise"]["standing"], "UNKNOWN")
        self.assertEqual(result["recovery"]["standing"], "UNKNOWN")

    def test_recovery_requires_explicit_obligations_and_fresh_requalification(self):
        case = base_case()
        case["signals"] = [signal("COMPROMISE"), signal("PERSISTENCE")]
        case["recoveryObligations"] = [
            obligation("obl:cred", "credential-rotation", "ERADICATION"),
            obligation("obl:key", "key-rotation", "ERADICATION"),
            obligation("obl:rebuild", "rebuild", "RECOVERY"),
            obligation("obl:requal", "requalify", "REQUALIFICATION"),
        ]
        case["requalification"] = {
            "caseRef": "case:test",
            "subjectRef": "subject:test",
            "subjectSnapshotDigest": D1,
            "standing": "SATISFIED",
            "currentnessStanding": "POINT_IN_TIME_OBSERVED",
            "ownerRef": "owner:requalification",
            "sourceRef": "evidence:requalification",
            "sourceDigest": D3,
        }
        result = project_compromise_recovery(case)
        self.assertTrue(result["recovery"]["eradicationEstablished"])
        self.assertTrue(result["recovery"]["recoveryEstablished"])
        self.assertEqual(result["recovery"]["standing"], "RECOVERY_VERIFIED")

    def test_stale_requalification_cannot_verify_recovery(self):
        case = base_case()
        case["signals"] = [signal("COMPROMISE")]
        case["recoveryObligations"] = [
            obligation("obl:cred", "credential-rotation", "ERADICATION"),
            obligation("obl:rebuild", "rebuild", "RECOVERY"),
        ]
        case["requalification"] = {
            "caseRef": "case:test",
            "subjectRef": "subject:test",
            "subjectSnapshotDigest": D1,
            "standing": "SATISFIED",
            "currentnessStanding": "HISTORICAL_NOT_CURRENT",
            "ownerRef": "owner:requalification",
            "sourceRef": "evidence:requalification",
            "sourceDigest": D3,
        }
        result = project_compromise_recovery(case)
        self.assertFalse(result["recovery"]["recoveryEstablished"])
        self.assertEqual(result["recovery"]["standing"], "RECOVERY_OPEN")

    def test_pending_required_obligation_keeps_recovery_open(self):
        case = base_case()
        case["signals"] = [signal("PERSISTENCE")]
        case["recoveryObligations"] = [
            obligation(
                "obl:cred",
                "credential-rotation",
                "ERADICATION",
                standing="PENDING",
            )
        ]
        result = project_compromise_recovery(case)
        self.assertIn("obl:cred", result["recovery"]["pendingRequiredObligationRefs"])
        self.assertEqual(result["recovery"]["standing"], "RECOVERY_OPEN")

    def test_signal_subject_mismatch_fails_closed(self):
        case = base_case()
        bad = signal("COMPROMISE")
        bad["subjectSnapshotDigest"] = D2
        case["signals"] = [bad]
        with self.assertRaisesRegex(CompromiseRecoveryError, "subject snapshot mismatch"):
            project_compromise_recovery(case)

    def test_gate_result_discharge_is_only_admission_seam(self):
        case = base_case()
        case["detectorCoverage"] = [coverage("COMPROMISE"), coverage("PERSISTENCE")]
        result = project_compromise_recovery(case)
        gate = composition_gate_result(case=case, projection=result)
        self.assertEqual(gate["standing"], "SATISFIED")
        self.assertEqual(gate["gateId"], "gate:dw06-dw09-compromise-hunt")
        self.assertTrue(
            any("does not establish compromise absence" in item for item in gate["nonClaims"])
        )


if __name__ == "__main__":
    unittest.main()
