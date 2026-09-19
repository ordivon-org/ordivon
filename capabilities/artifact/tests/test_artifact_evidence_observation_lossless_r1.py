from __future__ import annotations

import pytest

import binascii
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]

ADAPTER_SPEC = importlib.util.spec_from_file_location(
    "evidence_observation_r1",
    ROOT / "planning/prototypes/evidence_observation_r1.py",
)
A = importlib.util.module_from_spec(ADAPTER_SPEC)
assert ADAPTER_SPEC.loader is not None
ADAPTER_SPEC.loader.exec_module(A)

DELIVERY_SPEC = importlib.util.spec_from_file_location(
    "artifact_delivery_lossless_fixture",
    ROOT / "scripts/artifact_delivery.py",
)
DELIVERY = importlib.util.module_from_spec(DELIVERY_SPEC)
assert DELIVERY_SPEC.loader is not None
DELIVERY_SPEC.loader.exec_module(DELIVERY)

SERVICE_SPEC = importlib.util.spec_from_file_location(
    "artifact_verify_lossless_fixture",
    ROOT / "scripts/artifact_verify.py",
)
SERVICE = importlib.util.module_from_spec(SERVICE_SPEC)
assert SERVICE_SPEC.loader is not None
SERVICE_SPEC.loader.exec_module(SERVICE)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def chunk(kind: bytes, payload: bytes) -> bytes:
    return (
        struct.pack(">I", len(payload))
        + kind
        + payload
        + struct.pack(">I", binascii.crc32(kind + payload) & 0xFFFFFFFF)
    )


def minimal_png(path: Path) -> None:
    signature = b"\x89PNG\r\n\x1a\n"
    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    srgb = chunk(b"sRGB", b"\x00")
    data = chunk(b"IDAT", zlib.compress(bytes([0, 32, 64, 128])))
    path.write_bytes(signature + ihdr + srgb + data + chunk(b"IEND", b""))


class ArtifactEvidenceObservationLosslessR1Tests(unittest.TestCase):
    def _legacy_stage_result(self, root: Path):
        profile = ROOT / "artifact-delivery/examples/pdu-sdu-presentation-r1.json"
        pptx = root / "artifact.pptx"
        built = DELIVERY.build_presentation_source(
            ROOT / "artifact-delivery/examples/presentation-native-smoke-source-r1.json",
            profile,
            pptx,
        )
        self.assertEqual(built["status"], "PASS", built)
        result = DELIVERY.execute_verify_stage(profile, pptx, root / "verify")
        self.assertEqual(result["status"], "PASS", result)
        return profile, result

    def _family_service_result(self, root: Path):
        subject = root / "subject.png"
        minimal_png(subject)
        profile = (
            ROOT
            / "artifact-delivery/shadow-v2/examples/still-image-png-srgb-r1-v2.json"
        )
        request = {
            "schemaVersion": 1,
            "kind": "artifact-verification-request",
            "requestId": "pressure:png:lossless-r1",
            "profile": {
                "id": "still-image-png-srgb-r1",
                "path": str(profile),
                "sha256": sha(profile),
            },
            "subject": {"path": str(subject), "sha256": sha(subject)},
            "evidenceDirectory": str(root / "family-evidence"),
        }
        request_path = root / "request.json"
        request_path.write_text(json.dumps(request), encoding="utf-8")
        result = SERVICE.verify_request(request_path)
        if any(
            "required external tool unavailable" in item
            for item in result.get("failures", [])
        ):
            self.skipTest("mature PNG verifier toolchain unavailable")
        self.assertEqual(result["status"], "PASS", result)
        return result

    @pytest.mark.integration
    def test_legacy_stage_round_trip_is_canonical_json_lossless(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            profile, source = self._legacy_stage_result(root)
            profile_ref = {
                "id": "pdu-sdu-presentation-r1",
                "path": str(profile),
                "sha256": sha(profile),
            }
            envelope = A.adapt_verify_stage_result(
                source,
                profile_ref=profile_ref,
                profile_authority="PRODUCTION",
            )
            A.validate_common_envelope(envelope)
            reconstructed = A.reconstruct_verify_stage_result(envelope)
            self.assertEqual(A.canonical_sha256(reconstructed), A.canonical_sha256(source))
            self.assertEqual(reconstructed, source)

    @pytest.mark.integration
    def test_legacy_stage_keeps_pass_separate_from_completeness(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            profile, source = self._legacy_stage_result(root)
            self.assertEqual(source["status"], "PASS")
            self.assertFalse(source["profileVerificationComplete"])
            envelope = A.adapt_verify_stage_result(
                source,
                profile_ref={
                    "id": "pdu-sdu-presentation-r1",
                    "path": str(profile),
                    "sha256": sha(profile),
                },
            )
            self.assertEqual(
                envelope["standingProjection"]["verificationStatus"], "PASS"
            )
            self.assertEqual(
                envelope["standingProjection"]["evidenceCompleteness"], "PARTIAL"
            )
            self.assertEqual(
                envelope["standingProjection"]["trustStatus"], "UNSIGNED_LOCAL"
            )

    @pytest.mark.integration
    def test_legacy_stage_preserves_each_native_gate_receipt(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            profile, source = self._legacy_stage_result(root)
            envelope = A.adapt_verify_stage_result(
                source,
                profile_ref={
                    "id": "pdu-sdu-presentation-r1",
                    "path": str(profile),
                    "sha256": sha(profile),
                },
            )
            by_id = {item["observationId"]: item for item in envelope["observations"]}
            self.assertEqual(set(by_id), set(source["receipts"]))
            for gate, receipt in source["receipts"].items():
                self.assertEqual(by_id[gate]["nativeEvidence"], receipt)

    def test_family_service_round_trip_is_canonical_json_lossless(self):
        with tempfile.TemporaryDirectory() as d:
            source = self._family_service_result(Path(d))
            envelope = A.adapt_family_service_result(source)
            A.validate_common_envelope(envelope)
            reconstructed = A.reconstruct_family_service_result(envelope)
            self.assertEqual(A.canonical_sha256(reconstructed), A.canonical_sha256(source))
            self.assertEqual(reconstructed, source)

    def test_family_service_preserves_registered_capability_and_native_payload(self):
        with tempfile.TemporaryDirectory() as d:
            source = self._family_service_result(Path(d))
            envelope = A.adapt_family_service_result(source)
            self.assertEqual(envelope["capabilityRef"]["mode"], "REGISTERED_BINDING")
            self.assertEqual(
                envelope["capabilityRef"]["standing"], "LOCAL_LIVE_PROVEN"
            )
            self.assertEqual(
                envelope["observations"][0]["nativeEvidence"],
                source["verification"],
            )
            self.assertEqual(
                envelope["standingProjection"]["profileAuthority"], "SHADOW"
            )
            self.assertEqual(
                envelope["standingProjection"]["trustStatus"], "NOT_EVALUATED"
            )

    @pytest.mark.integration
    def test_common_projection_tampering_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            profile, legacy = self._legacy_stage_result(root)
            envelope = A.adapt_verify_stage_result(
                legacy,
                profile_ref={
                    "id": "pdu-sdu-presentation-r1",
                    "path": str(profile),
                    "sha256": sha(profile),
                },
            )
            envelope["standingProjection"]["verificationStatus"] = "FAIL"
            with self.assertRaisesRegex(ValueError, "verificationStatus projection drifted"):
                A.validate_common_envelope(envelope)

    def test_native_evidence_tampering_fails_digest_fence(self):
        with tempfile.TemporaryDirectory() as d:
            source = self._family_service_result(Path(d))
            envelope = A.adapt_family_service_result(source)
            envelope["observations"][0]["nativeEvidence"]["status"] = "FAIL"
            envelope["observations"][0]["status"] = "FAIL"
            with self.assertRaisesRegex(ValueError, "round-trip digest mismatch"):
                A.validate_common_envelope(envelope)

    def test_subject_projection_tampering_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            source = self._family_service_result(Path(d))
            envelope = A.adapt_family_service_result(source)
            envelope["subjectRef"]["sha256"] = "0" * 64
            with self.assertRaisesRegex(ValueError, "subject projection drifted"):
                A.validate_common_envelope(envelope)

    @pytest.mark.integration
    def test_legacy_complete_stage_projects_complete_without_changing_source(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            base_profile = json.loads(
                (
                    ROOT
                    / "artifact-delivery/examples/pdu-sdu-presentation-r1.json"
                ).read_text(encoding="utf-8")
            )
            base_profile.pop("$schema", None)
            base_profile["id"] = "presentation-lossless-complete-r1"
            base_profile.pop("companions", None)
            for gate in list(base_profile["gates"]):
                base_profile["gates"][gate] = False
            for gate in ("profileSchema", "structural", "semantic"):
                base_profile["gates"][gate] = True
            profile = root / "profile.json"
            profile.write_text(json.dumps(base_profile), encoding="utf-8")
            pptx = root / "artifact.pptx"
            built = DELIVERY.build_presentation_source(
                ROOT
                / "artifact-delivery/examples/presentation-native-smoke-source-r1.json",
                ROOT / "artifact-delivery/examples/pdu-sdu-presentation-r1.json",
                pptx,
            )
            self.assertEqual(built["status"], "PASS", built)
            source = DELIVERY.execute_verify_stage(profile, pptx, root / "verify")
            self.assertEqual(source["status"], "PASS", source)
            self.assertTrue(source["profileVerificationComplete"], source)
            envelope = A.adapt_verify_stage_result(
                source,
                profile_ref={
                    "id": base_profile["id"],
                    "path": str(profile),
                    "sha256": sha(profile),
                },
                profile_authority="TEST_COMPATIBILITY_PROFILE",
            )
            A.validate_common_envelope(envelope)
            self.assertEqual(
                envelope["standingProjection"]["evidenceCompleteness"], "COMPLETE"
            )
            self.assertEqual(A.reconstruct_verify_stage_result(envelope), source)

    def test_family_fail_result_round_trips_without_becoming_complete(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            subject = root / "subject.png"
            signature = b"\x89PNG\r\n\x1a\n"
            ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
            data = chunk(b"IDAT", zlib.compress(bytes([0, 32, 64, 128])))
            subject.write_bytes(signature + ihdr + data + chunk(b"IEND", b""))
            profile = (
                ROOT
                / "artifact-delivery/shadow-v2/examples/still-image-png-srgb-r1-v2.json"
            )
            request = {
                "schemaVersion": 1,
                "kind": "artifact-verification-request",
                "requestId": "pressure:png:fail-r1",
                "profile": {
                    "id": "still-image-png-srgb-r1",
                    "path": str(profile),
                    "sha256": sha(profile),
                },
                "subject": {"path": str(subject), "sha256": sha(subject)},
                "evidenceDirectory": str(root / "family-fail-evidence"),
            }
            request_path = root / "request-fail.json"
            request_path.write_text(json.dumps(request), encoding="utf-8")
            source = SERVICE.verify_request(request_path)
            if any(
                "required external tool unavailable" in item
                for item in source.get("failures", [])
            ):
                self.skipTest("mature PNG verifier toolchain unavailable")
            self.assertEqual(source["status"], "FAIL", source)
            envelope = A.adapt_family_service_result(source)
            A.validate_common_envelope(envelope)
            self.assertEqual(
                envelope["standingProjection"]["verificationStatus"], "FAIL"
            )
            self.assertEqual(
                envelope["standingProjection"]["evidenceCompleteness"], "INCOMPLETE"
            )
            self.assertEqual(A.reconstruct_family_service_result(envelope), source)

    @pytest.mark.integration
    def test_common_envelope_shape_is_shared_without_shared_native_schema(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            profile, legacy = self._legacy_stage_result(root)
            family = self._family_service_result(root)
            envelopes = [
                A.adapt_verify_stage_result(
                    legacy,
                    profile_ref={
                        "id": "pdu-sdu-presentation-r1",
                        "path": str(profile),
                        "sha256": sha(profile),
                    },
                ),
                A.adapt_family_service_result(family),
            ]
            common = {
                "schemaVersion",
                "kind",
                "adapterKind",
                "sourceResultKind",
                "sourceResultSha256",
                "subjectRef",
                "profileRef",
                "capabilityRef",
                "observations",
                "standingProjection",
                "nativeSummary",
                "nonClaims",
            }
            self.assertTrue(all(set(value) == common for value in envelopes))
            self.assertNotEqual(
                set(envelopes[0]["observations"][0]["nativeEvidence"]),
                set(envelopes[1]["observations"][0]["nativeEvidence"]),
            )


if __name__ == "__main__":
    unittest.main()
