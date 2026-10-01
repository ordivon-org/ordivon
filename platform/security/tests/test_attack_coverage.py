import copy
import json
import unittest
from pathlib import Path

from ordivon_security_v2.attack_coverage import project_attack_coverage
from ordivon_security_v2.subject_exposure import build_subject_exposure_snapshot
from ordivon_security_v2.threat_applicability import fuse_threat_applicability

D1 = "sha256:" + "1" * 64
D2 = "sha256:" + "2" * 64
FIXTURE = (
    Path(__file__).parents[1] / "fixtures" / "dw04" / "exchange-attack-flow-replay-r1.json"
)


def subject():
    return build_subject_exposure_snapshot(
        case_ref="case:dw04:test",
        epoch_ref="epoch:dw04:test",
        subject_ref="service:exchange:test",
        identity_observations=[
            {
                "id": "product",
                "ownerId": "fixture-owner",
                "sourceRef": "fixture://exchange/product",
                "sourceKind": "direct-owner-observation",
                "currentnessStanding": "CURRENT_DECLARED",
                "observedAt": "2026-10-01T13:00:00+08:00",
                "evidenceRefs": ["fixture:evidence:product"],
                "dimension": "product",
                "identityRef": {"scheme": "fixture-product", "value": "exchange-server"},
            },
            {
                "id": "version",
                "ownerId": "fixture-owner",
                "sourceRef": "fixture://exchange/version",
                "sourceKind": "direct-owner-observation",
                "currentnessStanding": "CURRENT_DECLARED",
                "observedAt": "2026-10-01T13:00:00+08:00",
                "evidenceRefs": ["fixture:evidence:version"],
                "dimension": "version",
                "identityRef": {"scheme": "fixture-version", "value": "test-build"},
            },
        ],
        exposure_observations=[
            {
                "id": "https",
                "ownerId": "fixture-network-owner",
                "sourceRef": "fixture://exchange/https",
                "sourceKind": "direct-owner-observation",
                "currentnessStanding": "CURRENT_DECLARED",
                "observedAt": "2026-10-01T13:00:00+08:00",
                "evidenceRefs": ["fixture:evidence:https"],
                "surfaceId": "https",
                "endpointRef": "https://mail.example.invalid",
                "originScope": "fixture",
                "transport": "tcp/443",
                "reachability": "REACHABLE",
            }
        ],
        required_identity_dimensions=["product", "version"],
        expected_exposure_surfaces=["https"],
        non_claims=["synthetic-test-subject"],
    )


SUBJECT = subject()


def subject_binding():
    return {
        "caseRef": SUBJECT["caseRef"],
        "epochRef": SUBJECT["epochRef"],
        "subjectRef": SUBJECT["subjectRef"],
        "snapshotDigest": SUBJECT["snapshotDigest"],
        "evidenceRef": SUBJECT["evidenceRef"],
    }


def dw02():
    bind = {
        "subjectRef": SUBJECT["subjectRef"],
        "snapshotDigest": SUBJECT["snapshotDigest"],
        "evidenceRef": SUBJECT["evidenceRef"],
    }
    return fuse_threat_applicability(
        subject=SUBJECT,
        vulnerability_ref="CVE-2021-26855",
        evidence=[
            {
                "evidenceRef": "vendor",
                "sourceKind": "vendor-advisory",
                "providerNativeRef": "fixture://vendor",
                "artifactDigest": D1,
                "vulnerabilityRef": "CVE-2021-26855",
                "admission": "ADMITTED",
                "currentness": "CURRENT",
                "subjectBinding": bind,
                "projectedApplicability": "AFFECTED",
            },
            {
                "evidenceRef": "kev",
                "sourceKind": "cisa-kev",
                "providerNativeRef": "fixture://kev",
                "artifactDigest": D2,
                "vulnerabilityRef": "CVE-2021-26855",
                "admission": "ADMITTED",
                "currentness": "CURRENT",
                "knownExploited": True,
            },
        ],
    )


def linear_flow():
    return {
        "schemaVersion": 1,
        "kind": "ordivon.security.dwc-attack-flow-reference",
        "flowRef": "attack-flow:test:linear",
        "sourceRef": "fixture:attack-flow:test",
        "sourceDigest": D1,
        "attackFlowVersion": "4.0",
        "subjectBinding": subject_binding(),
        "actions": [
            {
                "actionRef": "a1",
                "techniqueRef": "attack:T1190",
                "name": "Exploit Public-Facing Application",
                "sourceRefs": ["reference:MITRE-ATTACK-T1190"],
                "evidenceRefs": ["fixture:evidence:a1"],
            },
            {
                "actionRef": "a2",
                "techniqueRef": "attack:T1505.003",
                "name": "Server Software Component: Web Shell",
                "sourceRefs": ["reference:MITRE-ATTACK-T1505.003"],
                "evidenceRefs": ["fixture:evidence:a2"],
            },
        ],
        "edges": [
            {"fromActionRef": "a1", "toActionRef": "a2", "relation": "precedes"}
        ],
        "entryActionRefs": ["a1"],
        "objectiveActionRefs": ["a2"],
    }


def control(
    ref,
    mapped,
    *,
    implementation="UNKNOWN",
    observation="UNKNOWN",
    effectiveness="UNKNOWN",
    attack_refs=None,
    d3fend_refs=None,
    detection_refs=None,
):
    return {
        "controlRef": ref,
        "ownerRef": f"owner:{ref}",
        "mappedActionRefs": mapped,
        "attackMitigationRefs": attack_refs or ["attack:M1051"],
        "d3fendRefs": d3fend_refs or ["d3fend:D3-SU"],
        "detectionStrategyRefs": detection_refs or [],
        "mappingEvidenceRefs": [f"evidence:{ref}:mapping"],
        "implementationStanding": implementation,
        "implementationEvidenceRefs": (
            [f"evidence:{ref}:implementation"] if implementation != "UNKNOWN" else []
        ),
        "observationStanding": observation,
        "observationEvidenceRefs": (
            [f"evidence:{ref}:observation"] if observation != "UNKNOWN" else []
        ),
        "effectivenessStanding": effectiveness,
        "effectivenessEvidenceRefs": (
            [f"evidence:{ref}:effectiveness"] if effectiveness != "UNKNOWN" else []
        ),
    }


class AttackCoverageProjectionTests(unittest.TestCase):
    def test_historical_fixture_is_behavior_only_proxylogon_and_proxyshell(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.assertEqual(fixture["attackFlowVersion"], "4.0")
        self.assertEqual(
            {case["id"] for case in fixture["cases"]},
            {"exchange-proxylogon-2021", "exchange-proxyshell-2021"},
        )
        for case in fixture["cases"]:
            self.assertEqual(
                [action["techniqueRef"] for action in case["actions"]],
                ["attack:T1190", "attack:T1505.003"],
            )
            self.assertEqual(len(case["edges"]), 1)
        operational = json.dumps(
            [
                {"actions": case["actions"], "edges": case["edges"]}
                for case in fixture["cases"]
            ]
        ).lower()
        self.assertNotIn("payload", operational)
        self.assertNotIn("powershell -", operational)
        self.assertNotIn("cmd.exe /c", operational)

    def test_mapping_does_not_mint_local_implementation_observation_or_effectiveness(self):
        result = project_attack_coverage(
            subject=SUBJECT,
            applicability=dw02(),
            flow=linear_flow(),
            controls=[control("patch-map", ["a1"])],
        )
        self.assertEqual(result["coverageByAction"]["a1"]["mappedControlRefs"], ["patch-map"])
        self.assertEqual(result["coverageByAction"]["a1"]["implementedControlRefs"], [])
        self.assertEqual(result["coverageByAction"]["a1"]["observedControlRefs"], [])
        self.assertEqual(
            result["coverageByAction"]["a1"]["verifiedEffectiveControlRefs"], []
        )
        self.assertFalse(result["verifiedProtectionEstablished"])
        self.assertFalse(result["authorityGranted"])

    def test_verified_effective_control_at_structural_cut_is_evidence_not_global_green(self):
        result = project_attack_coverage(
            subject=SUBJECT,
            applicability=dw02(),
            flow=linear_flow(),
            controls=[
                control(
                    "verified-patch",
                    ["a1"],
                    implementation="IMPLEMENTED",
                    observation="OBSERVED",
                    effectiveness="VERIFIED_EFFECTIVE",
                )
            ],
        )
        self.assertEqual(result["structuralCutActionRefs"], ["a1", "a2"])
        self.assertEqual(result["verifiedEffectiveAtStructuralCutActionRefs"], ["a1"])
        self.assertTrue(result["paths"][0]["verifiedEffectiveControlPresent"])
        self.assertFalse(result["verifiedProtectionEstablished"])

    def test_implemented_unknown_effect_at_structural_cut_triggers_optional_dw05_candidate(self):
        result = project_attack_coverage(
            subject=SUBJECT,
            applicability=dw02(),
            flow=linear_flow(),
            controls=[
                control(
                    "implemented-patch",
                    ["a1"],
                    implementation="IMPLEMENTED",
                    observation="OBSERVED",
                    effectiveness="UNKNOWN",
                )
            ],
        )
        self.assertEqual(
            result["authorizedValidationCandidateControlRefs"], ["implemented-patch"]
        )
        self.assertEqual(
            result["validationStanding"], "OPTIONAL_MAY_CHANGE_DOWNSTREAM_DECISION"
        )

    def test_mapping_only_control_does_not_trigger_dw05(self):
        result = project_attack_coverage(
            subject=SUBJECT,
            applicability=dw02(),
            flow=linear_flow(),
            controls=[control("map-only", ["a1"])],
        )
        self.assertEqual(result["authorizedValidationCandidateControlRefs"], [])
        self.assertEqual(result["validationStanding"], "NOT_TRIGGERED_BY_DW04")

    def test_parallel_paths_compute_structural_cuts_without_ranking(self):
        flow = linear_flow()
        flow["actions"] = [
            {
                "actionRef": ref,
                "techniqueRef": f"attack:{ref}",
                "name": ref,
                "sourceRefs": [f"reference:{ref}"],
                "evidenceRefs": [],
            }
            for ref in ["a", "b", "c", "d"]
        ]
        flow["edges"] = [
            {"fromActionRef": "a", "toActionRef": "b", "relation": "precedes"},
            {"fromActionRef": "a", "toActionRef": "c", "relation": "precedes"},
            {"fromActionRef": "b", "toActionRef": "d", "relation": "precedes"},
            {"fromActionRef": "c", "toActionRef": "d", "relation": "precedes"},
        ]
        flow["entryActionRefs"] = ["a"]
        flow["objectiveActionRefs"] = ["d"]
        result = project_attack_coverage(
            subject=SUBJECT,
            applicability=dw02(),
            flow=flow,
            controls=[control("mapped-a", ["a"])],
        )
        self.assertEqual(result["structuralCutActionRefs"], ["a", "d"])
        self.assertEqual(
            [row["actionRefs"] for row in result["paths"]],
            [["a", "b", "d"], ["a", "c", "d"]],
        )

    def test_flow_cycle_fails_closed(self):
        flow = linear_flow()
        flow["edges"].append(
            {"fromActionRef": "a2", "toActionRef": "a1", "relation": "precedes"}
        )
        with self.assertRaisesRegex(ValueError, "cyclic"):
            project_attack_coverage(
                subject=SUBJECT,
                applicability=dw02(),
                flow=flow,
                controls=[],
            )

    def test_unknown_action_mapping_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "maps unknown actions"):
            project_attack_coverage(
                subject=SUBJECT,
                applicability=dw02(),
                flow=linear_flow(),
                controls=[control("broken", ["missing"])],
            )

    def test_dw02_subject_binding_mismatch_fails_closed(self):
        applicability = copy.deepcopy(dw02())
        applicability["subject"]["snapshotDigest"] = D2
        applicability["subject"]["evidenceRef"] = f"dwc-subject-exposure:{D2}"
        with self.assertRaisesRegex(ValueError, "does not match DW01 subject"):
            project_attack_coverage(
                subject=SUBJECT,
                applicability=applicability,
                flow=linear_flow(),
                controls=[],
            )

    def test_non_unknown_local_standings_require_evidence(self):
        broken = control("broken", ["a1"], implementation="IMPLEMENTED")
        broken["implementationEvidenceRefs"] = []
        with self.assertRaisesRegex(ValueError, "implementation requires evidence"):
            project_attack_coverage(
                subject=SUBJECT,
                applicability=dw02(),
                flow=linear_flow(),
                controls=[broken],
            )


if __name__ == "__main__":
    unittest.main()
