from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from artifact_core.bindings import CapabilityBindingRegistry
from artifact_core.contracts import file_fact
from artifact_core.profiles import ProfileRegistry
from artifact_verification.compatibility import build_production_v1_evaluation_request
from artifact_verification.evaluation import (
    build_registered_v2_evaluation_request,
    project_production_v1_result,
    project_registered_v2_result,
    validate_evaluation_projection,
)
from artifact_verification.plugins import resolve_verifier_plugin

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifact-delivery"
PROFILES = ProfileRegistry(ART)
BINDINGS = CapabilityBindingRegistry(ART)


def explicit_claims(profile: dict, *, pending: set[str] | None = None) -> dict:
    pending = pending or set()
    return {
        key: {
            "status": "NOT_EVALUATED" if key in pending else "PASS",
            "observationIds": [] if key in pending else [key],
            "evidenceRefs": [],
            "nativePointers": [] if key in pending else [f"/{key}"],
            "nonClaims": [],
        }
        for key in sorted(profile["requiredEvidence"])
    }


def production_stage(request: dict, profile: dict, subject: Path) -> dict:
    required = {
        key for key, value in profile["requiredEvidence"].items() if value.get("required") is True
    }
    receipts = {
        key: {"status": "PASS", "verificationResult": "PASSED"}
        for key in sorted(required)
    }
    return {
        "schemaVersion": 1,
        "kind": "artifact-delivery-verify-stage",
        "status": "PASS",
        "profileId": request["profileRef"]["id"],
        "artifact": file_fact(subject),
        "receipts": receipts,
        "profileRequiredGates": sorted(required),
        "pendingRequiredGates": [],
        "profileVerificationComplete": True,
        "failures": [],
    }


class ArtifactEvaluationProjectionR1Tests(unittest.TestCase):
    def test_registered_v2_projection_uses_exact_claims_and_common_standing(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            subject = root / "subject.wav"
            contract = root / "contract.json"
            subject.write_bytes(b"RIFF-not-executed-by-this-contract-test")
            contract.write_text("{}", encoding="utf-8")
            profile = PROFILES.resolve("audio-wave-pcm16-r1")
            binding = BINDINGS.resolve(profile.profile_id, "verify")
            request = build_registered_v2_evaluation_request(
                profile,
                binding,
                subject,
                object_contract_path=contract,
                request_id="d01:registered-v2",
            )
            delegated = {
                "schemaVersion": 1,
                "kind": "artifact-wave-verification",
                "profileId": profile.profile_id,
                "status": "PASS",
                "claimResults": explicit_claims(profile.canonical),
                "failures": [],
            }
            projection = project_registered_v2_result(request, delegated)
            validate_evaluation_projection(projection)
            self.assertEqual(projection["kind"], "artifact-evaluation-projection")
            self.assertEqual(projection["sourceKind"], "registered-v2-family")
            self.assertEqual(
                set(projection["claimResults"]), set(profile.canonical["requiredEvidence"])
            )
            self.assertEqual(
                projection["standingDecision"]["standingVector"]["verificationStatus"],
                "PASS",
            )
            self.assertEqual(
                {item["claimId"] for item in projection["evidenceObservations"]},
                set(profile.canonical["requiredEvidence"]),
            )
            subject_sha = projection["evaluationRequest"]["subjectRef"]["sha256"]
            capability = projection["evaluationRequest"]["capabilityRef"]
            self.assertTrue(all(item["subjectSha256"] == subject_sha for item in projection["evidenceObservations"]))
            self.assertTrue(all(item["capabilityRef"] == capability for item in projection["evidenceObservations"]))

    def test_registered_native_pass_cannot_upgrade_not_evaluated_required_claim(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            subject = root / "subject.wav"; subject.write_bytes(b"x")
            contract = root / "contract.json"; contract.write_text("{}")
            profile = PROFILES.resolve("audio-wave-pcm16-r1")
            binding = BINDINGS.resolve(profile.profile_id, "verify")
            request = build_registered_v2_evaluation_request(
                profile, binding, subject, object_contract_path=contract, request_id="d01:pending"
            )
            pending = next(iter(profile.canonical["requiredEvidence"]))
            delegated = {
                "status": "PASS",
                "claimResults": explicit_claims(profile.canonical, pending={pending}),
            }
            projection = project_registered_v2_result(request, delegated)
            self.assertEqual(
                projection["standingDecision"]["standingVector"]["verificationStatus"],
                "PENDING",
            )
            self.assertIn(
                pending,
                projection["standingDecision"]["requiredNotEvaluated"],
            )

    def test_production_v1_projects_to_same_common_envelope_without_route_change(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            subject = root / "subject.pptx"; subject.write_bytes(b"production-subject")
            source = ART / "examples/pdu-sdu-presentation-r1.json"
            canonical = ART / "shadow-v2/examples/pdu-sdu-presentation-r1-v2.json"
            request = build_production_v1_evaluation_request(
                source, canonical, subject, request_id="d01:production-v1"
            )
            profile = PROFILES.resolve("pdu-sdu-presentation-r1").canonical
            stage = production_stage(request, profile, subject)
            projection = project_production_v1_result(request, stage)
            validate_evaluation_projection(projection)
            self.assertEqual(projection["kind"], "artifact-evaluation-projection")
            self.assertEqual(projection["sourceKind"], "production-v1-compatibility")
            self.assertFalse(request["capabilityRef"]["productionRoutingChanged"])
            self.assertEqual(
                set(projection["claimResults"]), set(profile["requiredEvidence"])
            )
            subject_sha = projection["evaluationRequest"]["subjectRef"]["sha256"]
            capability = projection["evaluationRequest"]["capabilityRef"]
            self.assertTrue(all(item["subjectSha256"] == subject_sha for item in projection["evidenceObservations"]))
            self.assertTrue(all(item["capabilityRef"] == capability for item in projection["evidenceObservations"]))

    def test_projection_tampering_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            subject = root / "subject.pptx"; subject.write_bytes(b"production-subject")
            source = ART / "examples/pdu-sdu-presentation-r1.json"
            canonical = ART / "shadow-v2/examples/pdu-sdu-presentation-r1-v2.json"
            request = build_production_v1_evaluation_request(
                source, canonical, subject, request_id="d01:tamper"
            )
            profile = PROFILES.resolve("pdu-sdu-presentation-r1").canonical
            stage = production_stage(request, profile, subject)
            projection = project_production_v1_result(request, stage)
            bad = copy.deepcopy(projection)
            first = next(iter(bad["claimResults"]))
            bad["claimResults"][first]["status"] = "FAIL"
            with self.assertRaisesRegex(ValueError, "drifted"):
                validate_evaluation_projection(bad)

    def test_formal_verifier_plugin_is_binding_owned_and_enforces_object_contract(self) -> None:
        binding = BINDINGS.resolve("audio-wave-pcm16-r1", "verify")
        plugin = resolve_verifier_plugin(binding, artifact_root=ROOT)
        identity = plugin.identity()
        self.assertEqual(identity["capabilityId"], binding.capability_id)
        self.assertEqual(identity["implementationSha256"], plugin.implementation_sha256)
        self.assertTrue(identity["objectContractRequired"])
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            subject = root / "subject.wav"; subject.write_bytes(b"x")
            evidence = root / "evidence"
            with self.assertRaisesRegex(ValueError, "requires an object contract"):
                plugin.verify(subject, evidence)


if __name__ == "__main__":
    unittest.main()
