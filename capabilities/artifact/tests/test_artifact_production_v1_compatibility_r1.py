from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

import pytest

from artifact_core.contracts import file_fact
from artifact_operations.providers import DirectPythonOperationProvider
from artifact_verification.compatibility import (
    adapt_production_v1_verify_stage,
    build_production_v1_evaluation_request,
    reconstruct_production_v1_verify_stage,
    validate_production_v1_projection,
    validate_profile_compatibility,
)

ROOT = Path(__file__).resolve().parents[1]

PROFILE_PAIRS = [
    ("pdu-sdu-presentation-r1", "pdu-sdu-presentation-r1.json"),
    ("document-r1", "document-r1.json"),
    ("web-r1", "web-r1.json"),
]


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def profile_paths(profile_id: str, source_name: str) -> tuple[Path, Path]:
    return (
        ROOT / "artifact-delivery/examples" / source_name,
        ROOT / "artifact-delivery/shadow-v2/examples" / f"{profile_id}-v2.json",
    )


def make_request(root: Path, profile_id: str, source_name: str) -> tuple[dict, dict, Path]:
    source, canonical = profile_paths(profile_id, source_name)
    subject = root / {"pdu-sdu-presentation-r1": "subject.pptx", "document-r1": "subject.docx", "web-r1": "subject.html"}[profile_id]
    subject.write_bytes(b"S1E-exact-subject")
    request = build_production_v1_evaluation_request(
        source, canonical, subject, request_id=f"s1e:{profile_id}"
    )
    return request, load(canonical), subject


def synthetic_stage(
    request: dict,
    profile: dict,
    subject: Path,
    *,
    omit: set[str] | None = None,
    fail: set[str] | None = None,
    native_status: str = "PASS",
) -> dict:
    omit = omit or set()
    fail = fail or set()
    receipts = {}
    required = {
        key for key, value in profile["requiredEvidence"].items() if value.get("required") is True
    }
    for key in sorted(profile["requiredEvidence"]):
        if key in omit:
            continue
        # Optional gates are deliberately allowed to remain unexecuted.
        if key not in required:
            continue
        status = "FAIL" if key in fail else "PASS"
        receipts[key] = {
            "gate": key,
            "status": status,
            "verificationResult": "FAILED" if status == "FAIL" else "PASSED",
            "vsaValidation": {"status": "PASS"},
        }
    pending = sorted(required - set(receipts))
    return {
        "schemaVersion": 1,
        "kind": "artifact-delivery-verify-stage",
        "status": native_status,
        "profileId": request["profileRef"]["id"],
        "artifact": file_fact(subject),
        "receipts": receipts,
        "profileRequiredGates": sorted(required),
        "pendingRequiredGates": pending,
        "profileVerificationComplete": native_status == "PASS" and not pending and not fail,
        "failures": [] if native_status == "PASS" else ["synthetic native stage failure"],
    }


class ArtifactProductionV1CompatibilityR1Tests(unittest.TestCase):
    def test_three_current_production_profiles_have_exact_compatibility_semantics(self) -> None:
        for profile_id, source_name in PROFILE_PAIRS:
            source, canonical = profile_paths(profile_id, source_name)
            with self.subTest(profileId=profile_id):
                value = validate_profile_compatibility(load(source), load(canonical))
                self.assertEqual(value["profileId"], profile_id)
                self.assertEqual(value["standing"], "EXACT_COMPATIBILITY_MAPPING_PROVEN")

    def test_gate_requiredness_drift_fails_closed(self) -> None:
        source, canonical = profile_paths("pdu-sdu-presentation-r1", "pdu-sdu-presentation-r1.json")
        v1 = load(source)
        v2 = load(canonical)
        v2["requiredEvidence"]["target"]["required"] = False
        with self.assertRaisesRegex(ValueError, "requiredness differs"):
            validate_profile_compatibility(v1, v2)

    def test_output_target_and_presentation_policy_drift_fail_closed(self) -> None:
        source, canonical = profile_paths("pdu-sdu-presentation-r1", "pdu-sdu-presentation-r1.json")
        v1 = load(source)
        for mutation, message in [
            (lambda v: v["outputs"][0].update({"purpose": "different"}), "output semantics differ"),
            (lambda v: v["targetAuthorities"][0].update({"required": False}), "target authority semantics differ"),
            (lambda v: v["profilePolicy"]["presentation"].update({"aspectRatio": "4:3"}), "presentation policy semantics differ"),
        ]:
            v2 = load(canonical)
            mutation(v2)
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                validate_profile_compatibility(v1, v2)

    def test_native_pass_with_missing_required_gate_is_pending_not_pass(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            request, profile, subject = make_request(root, "pdu-sdu-presentation-r1", "pdu-sdu-presentation-r1.json")
            stage = synthetic_stage(request, profile, subject, omit={"target"})
            projection = adapt_production_v1_verify_stage(request, stage)
            self.assertEqual(stage["status"], "PASS")
            self.assertEqual(projection["claimResults"]["target"]["status"], "NOT_EVALUATED")
            vector = projection["standingDecision"]["standingVector"]
            self.assertEqual(vector["verificationStatus"], "PENDING")
            self.assertEqual(vector["evidenceCompleteness"], "PARTIAL")

    def test_all_required_pass_yields_complete_even_when_optional_gate_is_not_evaluated(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            request, profile, subject = make_request(root, "document-r1", "document-r1.json")
            stage = synthetic_stage(request, profile, subject)
            projection = adapt_production_v1_verify_stage(request, stage)
            self.assertEqual(set(projection["claimResults"]), set(profile["requiredEvidence"]))
            self.assertEqual(projection["claimResults"]["conformance"]["status"], "NOT_EVALUATED")
            vector = projection["standingDecision"]["standingVector"]
            self.assertEqual(vector["verificationStatus"], "PASS")
            self.assertEqual(vector["evidenceCompleteness"], "COMPLETE")

    def test_required_failure_and_native_failure_remain_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            request, profile, subject = make_request(root, "web-r1", "web-r1.json")
            failed_claim = synthetic_stage(request, profile, subject, fail={"target"}, native_status="FAIL")
            projection = adapt_production_v1_verify_stage(request, failed_claim)
            self.assertEqual(projection["claimResults"]["target"]["status"], "FAIL")
            self.assertEqual(projection["standingDecision"]["standingVector"]["verificationStatus"], "FAIL")

            native_fail = synthetic_stage(request, profile, subject, native_status="FAIL")
            projection = adapt_production_v1_verify_stage(request, native_fail)
            self.assertEqual(projection["standingDecision"]["standingVector"]["verificationStatus"], "FAIL")

    def test_subject_identity_and_projection_tampering_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            request, profile, subject = make_request(root, "web-r1", "web-r1.json")
            stage = synthetic_stage(request, profile, subject)
            bad = copy.deepcopy(stage)
            bad["artifact"]["digest"]["sha256"] = "0" * 64
            with self.assertRaisesRegex(ValueError, "subject identity differs"):
                adapt_production_v1_verify_stage(request, bad)

            projection = adapt_production_v1_verify_stage(request, stage)
            projection["claimResults"]["target"]["status"] = "FAIL"
            with self.assertRaisesRegex(ValueError, "projection drifted"):
                validate_production_v1_projection(projection)

    def test_native_stage_round_trip_is_exact(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            request, profile, subject = make_request(root, "web-r1", "web-r1.json")
            stage = synthetic_stage(request, profile, subject, omit={"releaseProvenance"})
            projection = adapt_production_v1_verify_stage(request, stage)
            validate_production_v1_projection(projection)
            self.assertEqual(reconstruct_production_v1_verify_stage(projection), stage)

    def test_production_stage_source_does_not_depend_on_compatibility_adapter(self) -> None:
        source = (ROOT / "artifact_verification/stage.py").read_text(encoding="utf-8")
        provider = (ROOT / "artifact_operations/providers/direct_python.py").read_text(encoding="utf-8")
        self.assertNotIn("artifact_verification.compatibility", source)
        self.assertNotIn("adapt_production_v1_verify_stage", source)
        self.assertNotIn("adapt_production_v1_verify_stage", provider)

    @pytest.mark.integration
    def test_real_presentation_stage_round_trips_without_laundering_pending_gates(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            production, canonical = profile_paths("pdu-sdu-presentation-r1", "pdu-sdu-presentation-r1.json")
            pptx = root / "artifact.pptx"
            built = DirectPythonOperationProvider().build_presentation_source(
                ROOT / "artifact-delivery/examples/presentation-native-smoke-source-r1.json",
                production,
                pptx,
            )
            self.assertEqual(built["status"], "PASS", built)
            stage = DirectPythonOperationProvider().execute_verify_stage(production, pptx, root / "verify")
            self.assertEqual(stage["status"], "PASS", stage)
            self.assertFalse(stage["profileVerificationComplete"])
            request = build_production_v1_evaluation_request(
                production, canonical, pptx, request_id="s1e:real-presentation"
            )
            projection = adapt_production_v1_verify_stage(request, stage)
            validate_production_v1_projection(projection)
            self.assertEqual(projection["standingDecision"]["standingVector"]["verificationStatus"], "PENDING")
            self.assertEqual(projection["standingDecision"]["standingVector"]["evidenceCompleteness"], "PARTIAL")
            self.assertEqual(reconstruct_production_v1_verify_stage(projection), stage)


if __name__ == "__main__":
    unittest.main()
