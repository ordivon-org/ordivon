from __future__ import annotations

import unittest

from ordivon_security_v2.consequence_binding import (
    ConsequenceBindingError,
    compile_consequence_input,
    composition_gate_result,
    evaluate_bound_consequence,
)

D1 = "sha256:" + "1" * 64
D2 = "sha256:" + "2" * 64
D3 = "sha256:" + "3" * 64
D4 = "sha256:" + "4" * 64
D5 = "sha256:" + "5" * 64


def binding(verifier_class="configuration"):
    predicate = {
        "configuration": {
            "class": "configuration",
            "expectedConfigurationDigest": D4,
        },
        "version": {"class": "version", "expectedVersion": "2.0.0"},
        "exposure": {
            "class": "exposure",
            "expectedExposureStanding": "NOT_REACHABLE_FROM_BOUNDED_ORIGIN",
        },
        "attack-negative": {
            "class": "attack-negative",
            "scopeDigest": D4,
            "expectedResult": "NEGATIVE",
        },
    }[verifier_class]
    return {
        "schemaVersion": 1,
        "kind": "ordivon.security.dwc-consequence-verifier-binding-r1",
        "bindingRef": f"verifier-binding:{verifier_class}",
        "caseRef": "case:test",
        "subjectRef": "subject:test",
        "subjectSnapshotDigest": D1,
        "protectionClaimRef": f"protection:{verifier_class}",
        "supportScope": "DW07->DW08 exact receipt/consequence-input seam only",
        "effectBinding": {
            "proposalDigest": D5,
            "requestId": "request:test",
            "requestDigest": D3,
        },
        "verifierClass": verifier_class,
        "predicate": predicate,
        "compositionGate": {
            "circuitId": "circuit:test",
            "manifestDigest": D2,
            "gateId": "gate:dw07-dw08-effect-receipt",
            "verifierOwnerId": "security.dw08",
            "supportScope": "DW07->DW08 exact receipt/consequence-input seam only",
        },
    }


def dw07():
    receipt = {
        "requestId": "request:test",
        "requestDigest": D3,
        "effectExecuted": True,
        "worldEffectVerified": False,
        "stateDigestAfterWrite": D4,
    }
    return {
        "kind": "ordivon.security.dwc-effect-execution-result-r1",
        "proposalDigest": D5,
        "requestId": "request:test",
        "requestDigest": D3,
        "admission": {
            "kind": "ordivon.security.range-effect-admission",
            "requestId": "request:test",
            "requestDigest": D3,
            "admitted": True,
        },
        "receipt": receipt,
    }


def observation(verifier_class="configuration"):
    facts = {
        "configuration": {"configurationDigest": D4},
        "version": {"version": "2.0.0"},
        "exposure": {"exposureStanding": "NOT_REACHABLE_FROM_BOUNDED_ORIGIN"},
        "attack-negative": {
            "attackNegativeResult": "NEGATIVE",
            "scopeDigest": D4,
            "coverageStanding": "COMPLETE",
        },
    }[verifier_class]
    return {
        "schemaVersion": 1,
        "kind": "ordivon.security.dwc-authoritative-observation-r1",
        "plane": "world-truth",
        "caseRef": "case:test",
        "subjectRef": "subject:test",
        "subjectSnapshotDigest": D1,
        "requestId": "request:test",
        "requestDigest": D3,
        "stateDigest": D4,
        "ownerRef": "owner:world-observer",
        "sourceRef": "evidence:world-observation",
        "sourceDigest": D2,
        "observedAt": "2026-10-01T14:55:00+08:00",
        "currentnessStanding": "POINT_IN_TIME_OBSERVED",
        "facts": facts,
    }


VERIFIED = {
    "standing": "VERIFIED_CONSEQUENCE",
    "verifiedConsequence": {"stateDigest": D4},
}


class ConsequenceBindingTests(unittest.TestCase):
    def test_receipt_only_remains_unknown(self):
        b = binding()
        value = evaluate_bound_consequence(
            binding=b,
            dw07_result=dw07(),
            observation=None,
            consequence_decision={"standing": "EXECUTED_UNVERIFIED"},
        )
        self.assertEqual(value["standing"], "UNKNOWN")
        self.assertFalse(value["verifiedProtectionEstablished"])

    def test_configuration_predicate_can_verify_bounded_protection(self):
        b = binding("configuration")
        value = evaluate_bound_consequence(
            binding=b,
            dw07_result=dw07(),
            observation=observation("configuration"),
            consequence_decision=VERIFIED,
        )
        self.assertEqual(value["standing"], "SATISFIED")
        self.assertTrue(value["verifiedProtectionEstablished"])
        self.assertFalse(value["compromiseAbsenceEstablished"])
        self.assertFalse(value["domainAcceptanceEstablished"])

    def test_version_exposure_and_attack_negative_templates(self):
        for verifier_class in ("version", "exposure", "attack-negative"):
            with self.subTest(verifier_class=verifier_class):
                value = evaluate_bound_consequence(
                    binding=binding(verifier_class),
                    dw07_result=dw07(),
                    observation=observation(verifier_class),
                    consequence_decision=VERIFIED,
                )
                self.assertEqual(value["standing"], "SATISFIED")
                self.assertTrue(value["boundedProtectionVerified"])

    def test_stale_observation_cannot_close(self):
        obs = observation()
        obs["currentnessStanding"] = "HISTORICAL_NOT_CURRENT"
        value = evaluate_bound_consequence(
            binding=binding(),
            dw07_result=dw07(),
            observation=obs,
            consequence_decision=VERIFIED,
        )
        self.assertEqual(value["standing"], "UNKNOWN")
        self.assertFalse(value["verifiedProtectionEstablished"])

    def test_subject_snapshot_mismatch_fails_closed(self):
        obs = observation()
        obs["subjectSnapshotDigest"] = D2
        with self.assertRaisesRegex(ConsequenceBindingError, "subject snapshot mismatch"):
            compile_consequence_input(binding=binding(), dw07_result=dw07(), observation=obs)

    def test_request_digest_mismatch_fails_closed(self):
        obs = observation()
        obs["requestDigest"] = D2
        with self.assertRaisesRegex(ConsequenceBindingError, "requestDigest mismatch"):
            compile_consequence_input(binding=binding(), dw07_result=dw07(), observation=obs)

    def test_dw07_proposal_digest_must_match_exact_verifier_binding(self):
        result = dw07()
        result["proposalDigest"] = D2
        with self.assertRaisesRegex(ConsequenceBindingError, "proposalDigest"):
            compile_consequence_input(
                binding=binding(), dw07_result=result, observation=observation()
            )

    def test_dw07_request_digest_must_match_exact_verifier_binding(self):
        b = binding()
        b["effectBinding"]["requestDigest"] = D2
        with self.assertRaisesRegex(ConsequenceBindingError, "requestDigest"):
            evaluate_bound_consequence(
                binding=b,
                dw07_result=dw07(),
                observation=observation(),
                consequence_decision=VERIFIED,
            )

    def test_non_authoritative_plane_fails_closed(self):
        obs = observation()
        obs["plane"] = "sensor"
        with self.assertRaisesRegex(ConsequenceBindingError, "world-truth"):
            compile_consequence_input(binding=binding(), dw07_result=dw07(), observation=obs)

    def test_consequence_mismatch_is_unsatisfied(self):
        value = evaluate_bound_consequence(
            binding=binding(),
            dw07_result=dw07(),
            observation=observation(),
            consequence_decision={"standing": "CONSEQUENCE_MISMATCH"},
        )
        self.assertEqual(value["standing"], "UNSATISFIED")
        self.assertFalse(value["verifiedProtectionEstablished"])

    def test_attack_negative_incomplete_coverage_stays_unknown(self):
        obs = observation("attack-negative")
        obs["facts"]["coverageStanding"] = "PARTIAL"
        value = evaluate_bound_consequence(
            binding=binding("attack-negative"),
            dw07_result=dw07(),
            observation=obs,
            consequence_decision=VERIFIED,
        )
        self.assertEqual(value["standing"], "UNKNOWN")
        self.assertFalse(value["verifiedProtectionEstablished"])

    def test_gate_result_is_bounded_and_not_domain_acceptance(self):
        b = binding()
        result = evaluate_bound_consequence(
            binding=b,
            dw07_result=dw07(),
            observation=observation(),
            consequence_decision=VERIFIED,
        )
        gate = composition_gate_result(binding=b, verification_result=result)
        self.assertEqual(gate["standing"], "SATISFIED")
        self.assertEqual(gate["gateId"], "gate:dw07-dw08-effect-receipt")
        self.assertTrue(gate["evidenceRefs"])
        self.assertTrue(any("domain acceptance" in x for x in gate["nonClaims"]))

    def test_compile_input_preserves_existing_policy_shape(self):
        value = compile_consequence_input(
            binding=binding(), dw07_result=dw07(), observation=observation()
        )
        self.assertTrue(value["admission"]["admitted"])
        self.assertFalse(value["executionReceipt"]["worldEffectVerified"])
        self.assertEqual(value["observation"]["plane"], "world-truth")
        self.assertEqual(value["observation"]["payload"]["stateDigest"], D4)
        self.assertEqual(value["observation"]["payload"]["facts"]["configurationDigest"], D4)


if __name__ == "__main__":
    unittest.main()
