from __future__ import annotations

import pytest

import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest
import wave

ROOT = Path(__file__).resolve().parents[1]

STANDING_SPEC = importlib.util.spec_from_file_location(
    "standing_decision_r1",
    ROOT / "planning/prototypes/standing_decision_r1.py",
)
S = importlib.util.module_from_spec(STANDING_SPEC)
assert STANDING_SPEC.loader is not None
STANDING_SPEC.loader.exec_module(S)

DELIVERY_SPEC = importlib.util.spec_from_file_location(
    "artifact_delivery_standing_fixture",
    ROOT / "scripts/artifact_delivery.py",
)
DELIVERY = importlib.util.module_from_spec(DELIVERY_SPEC)
assert DELIVERY_SPEC.loader is not None
DELIVERY_SPEC.loader.exec_module(DELIVERY)

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


class ArtifactStandingDecisionPressureR1Tests(unittest.TestCase):
    def _legacy_stage(self, root: Path):
        profile_path = ROOT / "artifact-delivery/examples/pdu-sdu-presentation-r1.json"
        pptx = root / "artifact.pptx"
        built = DELIVERY.build_presentation_source(
            ROOT / "artifact-delivery/examples/presentation-native-smoke-source-r1.json",
            profile_path,
            pptx,
        )
        self.assertEqual(built["status"], "PASS", built)
        result = DELIVERY.execute_verify_stage(profile_path, pptx, root / "verify")
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
    def test_legacy_stage_pass_does_not_launder_missing_required_claims(self):
        with tempfile.TemporaryDirectory() as d:
            native = self._legacy_stage(Path(d))
            canonical = profile("pdu-sdu-presentation-r1")
            claims = S.legacy_stage_claim_results(native)
            decision = S.evaluate_standing(
                canonical, claims, profile_authority="PRODUCTION"
            )
            self.assertEqual(native["status"], "PASS")
            self.assertFalse(native["profileVerificationComplete"])
            self.assertEqual(
                decision["standingVector"]["verificationStatus"], "PENDING"
            )
            self.assertEqual(
                decision["standingVector"]["evidenceCompleteness"], "PARTIAL"
            )
            self.assertTrue(
                {"target", "visual", "deliveryReadback"}
                & set(decision["missingRequiredClaims"])
            )

    def test_wave_native_pass_is_not_profile_pass_without_explicit_contract_claim_result(self):
        with tempfile.TemporaryDirectory() as d:
            native = self._wave_service_result(Path(d))
            canonical = profile("audio-wave-pcm16-r1")
            claims = S.family_explicit_claim_results(native, canonical)
            decision = S.evaluate_standing(
                canonical, claims, profile_authority="SHADOW"
            )
            self.assertEqual(native["status"], "PASS")
            self.assertEqual(
                set(claims),
                {
                    "referenceContainerView",
                    "independentTechnicalView",
                    "decoderMatrix",
                    "pcmIdentity",
                },
            )
            self.assertEqual(decision["missingRequiredClaims"], ["contractSchema"])
            self.assertEqual(
                decision["standingVector"]["verificationStatus"], "PENDING"
            )
            self.assertEqual(
                decision["standingVector"]["evidenceCompleteness"], "PARTIAL"
            )

    def test_explicit_complete_claim_results_can_yield_pass(self):
        canonical = profile("audio-wave-pcm16-r1")
        claims = {
            key: {"status": "PASS", "source": "explicit-plugin-contract"}
            for key in S.required_claim_keys(canonical)
        }
        decision = S.evaluate_standing(
            canonical, claims, profile_authority="SHADOW"
        )
        self.assertEqual(
            decision["standingVector"]["verificationStatus"], "PASS"
        )
        self.assertEqual(
            decision["standingVector"]["evidenceCompleteness"], "COMPLETE"
        )
        self.assertEqual(decision["missingRequiredClaims"], [])

    def test_explicit_failure_dominates_complete_coverage(self):
        canonical = profile("audio-wave-pcm16-r1")
        claims = {
            key: {"status": "PASS", "source": "explicit-plugin-contract"}
            for key in S.required_claim_keys(canonical)
        }
        claims["decoderMatrix"] = {
            "status": "FAIL",
            "source": "explicit-plugin-contract",
        }
        decision = S.evaluate_standing(
            canonical, claims, profile_authority="SHADOW"
        )
        self.assertEqual(
            decision["standingVector"]["verificationStatus"], "FAIL"
        )
        self.assertEqual(
            decision["standingVector"]["evidenceCompleteness"], "COMPLETE"
        )
        self.assertEqual(decision["requiredFailures"], ["decoderMatrix"])

    def test_trust_and_release_axes_remain_independent(self):
        canonical = profile("still-image-png-srgb-r1")
        claims = {
            key: {"status": "PASS", "source": "explicit-plugin-contract"}
            for key in S.required_claim_keys(canonical)
        }
        decision = S.evaluate_standing(
            canonical,
            claims,
            profile_authority="SHADOW",
            trust_status="NOT_EVALUATED",
            release_status="NOT_EVALUATED",
        )
        vector = decision["standingVector"]
        self.assertEqual(vector["verificationStatus"], "PASS")
        self.assertEqual(vector["trustStatus"], "NOT_EVALUATED")
        self.assertEqual(vector["releaseStatus"], "NOT_EVALUATED")


if __name__ == "__main__":
    unittest.main()
