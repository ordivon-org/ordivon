from __future__ import annotations

import hashlib
import importlib.util
import json
import struct
import tempfile
import unittest
import wave
from pathlib import Path

import pytest

from artifact_operations.providers import DirectPythonOperationProvider
from artifact_verification.claim_coverage import assess_required_statuses

ROOT = Path(__file__).resolve().parents[1]

SERVICE_SPEC = importlib.util.spec_from_file_location(
    "artifact_verify_standing_fixture",
    ROOT / "scripts/artifact_verify.py",
)
SERVICE = importlib.util.module_from_spec(SERVICE_SPEC)
assert SERVICE_SPEC.loader is not None
SERVICE_SPEC.loader.exec_module(SERVICE)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def profile(profile_id: str) -> dict:
    for p in (ROOT / "artifact-delivery/shadow-v2/examples").glob("*.json"):
        value = json.loads(p.read_text(encoding="utf-8"))
        if value.get("id") == profile_id:
            return value
    raise KeyError(profile_id)


def make_wave(path: Path, *, rate: int = 48000, frames: int = 240) -> bytes:
    samples = []
    for i in range(frames):
        value = (i * 97) % 32767
        samples.append(struct.pack("<h", value))
    raw = b"".join(samples)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(rate)
        handle.writeframes(raw)
    return raw


class ArtifactStandingEntrypointsTests(unittest.TestCase):
    def _legacy_stage(self, root: Path):
        profile_path = ROOT / "artifact-delivery/examples/pdu-sdu-presentation-r1.json"
        pptx = root / "artifact.pptx"
        built = DirectPythonOperationProvider().build_presentation_source(
            ROOT / "artifact-delivery/examples/presentation-native-smoke-source-r1.json",
            profile_path,
            pptx,
        )
        self.assertEqual(built["status"], "PASS", built)
        result = DirectPythonOperationProvider().execute_verify_stage(profile_path, pptx, root / "verify")
        self.assertEqual(result["status"], "PASS", result)
        return result

    def _wave_service_result(self, root: Path):
        subject = root / "subject.wav"
        raw = make_wave(subject)
        contract = {
            "contractVersion": 1,
            "id": "pressure-wave-r1",
            "profileId": "audio-wave-pcm16-r1",
            "audio": {
                "sampleRateHz": 48000,
                "channels": 1,
                "bitsPerSample": 16,
                "frameCount": 240,
                "expectedPcmSha256": hashlib.sha256(raw).hexdigest(),
            },
        }
        contract_path = root / "contract.json"
        contract_path.write_text(json.dumps(contract), encoding="utf-8")
        profile_path = (
            ROOT
            / "artifact-delivery/shadow-v2/examples/audio-wave-pcm16-r1-v2.json"
        )
        request = {
            "schemaVersion": 1,
            "kind": "artifact-verification-request",
            "requestId": "pressure:wave:standing-r1",
            "profile": {
                "id": "audio-wave-pcm16-r1",
                "path": str(profile_path),
                "sha256": sha(profile_path),
            },
            "subject": {"path": str(subject), "sha256": sha(subject)},
            "objectContract": {
                "path": str(contract_path),
                "sha256": sha(contract_path),
            },
            "evidenceDirectory": str(root / "evidence"),
        }
        request_path = root / "request.json"
        request_path.write_text(json.dumps(request), encoding="utf-8")
        result = SERVICE.verify_request(request_path)
        if any(
            "required mature external capability unavailable" in item
            for item in result.get("failures", [])
        ):
            self.skipTest("mature WAVE verifier toolchain unavailable")
        self.assertEqual(result["status"], "PASS", result)
        return result

    @pytest.mark.integration
    def test_v1_live_delivery_stage_has_bounded_coverage_not_full_profile_success(self):
        with tempfile.TemporaryDirectory() as d:
            native = self._legacy_stage(Path(d))
            self.assertEqual(native["status"], "PASS")
            self.assertFalse(native["profileVerificationComplete"])
            self.assertEqual(
                native["standingCoverage"]["required"],
                native["profileRequiredGates"],
            )
            self.assertEqual(
                native["standingCoverage"]["missing"],
                native["pendingRequiredGates"],
            )
            self.assertEqual(
                native["standingCoverage"]["verificationStatus"], "UNKNOWN"
            )
            self.assertEqual(
                native["standingCoverage"]["consumerAcceptance"],
                "EXTERNAL_NOT_EVALUATED",
            )

    def test_wave_live_native_claims_share_production_coverage_semantics(self):
        with tempfile.TemporaryDirectory() as d:
            native = self._wave_service_result(Path(d))
            canonical = profile("audio-wave-pcm16-r1")
            required = sorted(
                key for key, declaration in canonical["requiredEvidence"].items()
                if declaration["required"] is True
            )
            self.assertEqual(native["status"], "PASS")
            self.assertEqual(native["standingCoverage"]["required"], required)
            self.assertEqual(native["standingCoverage"]["missing"], [])
            self.assertEqual(native["standingCoverage"]["verificationStatus"], "PASS")
            self.assertTrue(native["standingCoverage"]["complete"])
            self.assertTrue(native["profileVerificationComplete"])
            self.assertEqual(
                native["standingCoverage"]["consumerAcceptance"],
                "EXTERNAL_NOT_EVALUATED",
            )

    def test_production_pure_coverage_preserves_required_claims_and_failures(self):
        canonical = profile("audio-wave-pcm16-r1")
        required = {
            name for name, row in canonical["requiredEvidence"].items()
            if row["required"] is True
        }
        statuses = {name: "PASS" for name in required}
        accepted_statuses = assess_required_statuses(required, statuses)
        self.assertEqual(accepted_statuses["verificationStatus"], "PASS")
        self.assertTrue(accepted_statuses["complete"])
        self.assertEqual(accepted_statuses["required"], sorted(required))
        self.assertEqual(
            accepted_statuses["consumerAcceptance"], "EXTERNAL_NOT_EVALUATED"
        )

        statuses["decoderMatrix"] = "FAIL"
        negative = assess_required_statuses(required, statuses)
        self.assertEqual(negative["verificationStatus"], "FAIL")
        self.assertEqual(negative["failed"], ["decoderMatrix"])
        self.assertFalse(negative["complete"])

        ungrounded_failure = assess_required_statuses(
            required, statuses, issues=("native status pointer mismatch",)
        )
        self.assertEqual(ungrounded_failure["verificationStatus"], "UNKNOWN")
        self.assertFalse(ungrounded_failure["complete"])

    def test_trust_release_and_domain_acceptance_are_external_to_projection(self):
        canonical = profile("still-image-png-srgb-r1")
        required = {
            name for name, row in canonical["requiredEvidence"].items()
            if row["required"] is True
        }
        decision = assess_required_statuses(
            required, {name: "PASS" for name in required}
        )
        self.assertEqual(decision["verificationStatus"], "PASS")
        self.assertNotIn("trustStatus", decision)
        self.assertNotIn("releaseStatus", decision)
        self.assertNotIn("profileAuthority", decision)
        self.assertEqual(
            decision["consumerAcceptance"], "EXTERNAL_NOT_EVALUATED"
        )


if __name__ == "__main__":
    unittest.main()
