from __future__ import annotations

import binascii
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest
import wave
import zlib

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
PROTO = ROOT / "planning/prototypes"

CONTRACT_SPEC = importlib.util.spec_from_file_location(
    "verifier_plugin_contract_r2", PROTO / "verifier_plugin_contract_r2.py"
)
CONTRACT = importlib.util.module_from_spec(CONTRACT_SPEC)
assert CONTRACT_SPEC.loader is not None
CONTRACT_SPEC.loader.exec_module(CONTRACT)

import sys
sys.modules["verifier_plugin_contract_r2"] = CONTRACT

ADAPTER_SPEC = importlib.util.spec_from_file_location(
    "claim_results_adapter_r1", PROTO / "claim_results_adapter_r1.py"
)
A = importlib.util.module_from_spec(ADAPTER_SPEC)
assert ADAPTER_SPEC.loader is not None
ADAPTER_SPEC.loader.exec_module(A)

DELIVERY_SPEC = importlib.util.spec_from_file_location(
    "artifact_delivery_claim_fixture", ROOT / "scripts/artifact_delivery.py"
)
DELIVERY = importlib.util.module_from_spec(DELIVERY_SPEC)
assert DELIVERY_SPEC.loader is not None
DELIVERY_SPEC.loader.exec_module(DELIVERY)

SERVICE_SPEC = importlib.util.spec_from_file_location(
    "artifact_verify_claim_fixture", ROOT / "scripts/artifact_verify.py"
)
SERVICE = importlib.util.module_from_spec(SERVICE_SPEC)
assert SERVICE_SPEC.loader is not None
SERVICE_SPEC.loader.exec_module(SERVICE)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def profile(profile_id: str) -> tuple[Path, dict]:
    for p in (ROOT / "artifact-delivery/shadow-v2/examples").glob("*.json"):
        value = json.loads(p.read_text(encoding="utf-8"))
        if value.get("id") == profile_id:
            return p, value
    raise KeyError(profile_id)


def make_wave(path: Path, *, frames: int = 240) -> bytes:
    raw = b"".join(struct.pack("<h", (i * 97) % 32767) for i in range(frames))
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(48000)
        handle.writeframes(raw)
    return raw


def chunk(kind: bytes, payload: bytes) -> bytes:
    return (
        struct.pack(">I", len(payload))
        + kind
        + payload
        + struct.pack(">I", binascii.crc32(kind + payload) & 0xFFFFFFFF)
    )


def make_png(path: Path) -> None:
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
        + chunk(b"sRGB", b"\x00")
        + chunk(b"IDAT", zlib.compress(bytes([0, 32, 64, 128])))
        + chunk(b"IEND", b"")
    )


class ArtifactClaimResultsAdapterR1Tests(unittest.TestCase):
    def test_legacy_stage_can_emit_exact_profile_claim_key_set(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            source_profile = (
                ROOT / "artifact-delivery/examples/pdu-sdu-presentation-r1.json"
            )
            canonical_path, canonical = profile("pdu-sdu-presentation-r1")
            pptx = root / "artifact.pptx"
            built = DELIVERY.build_presentation_source(
                ROOT
                / "artifact-delivery/examples/presentation-native-smoke-source-r1.json",
                source_profile,
                pptx,
            )
            self.assertEqual(built["status"], "PASS", built)
            stage = DELIVERY.execute_verify_stage(source_profile, pptx, root / "verify")
            candidate = A.legacy_stage_plugin_candidate(
                stage,
                canonical,
                profile_ref={
                    "id": canonical["id"],
                    "path": str(canonical_path),
                    "sha256": sha(canonical_path),
                    "authority": "PRODUCTION",
                },
            )
            CONTRACT.validate_plugin_result(candidate, canonical)
            schema = json.loads(
                (
                    ROOT
                    / "planning/verifier-plugin-result-r2-candidate.schema.json"
                ).read_text(encoding="utf-8")
            )
            jsonschema.Draft202012Validator(schema).validate(candidate)
            self.assertEqual(
                set(candidate["claimResults"]), set(canonical["requiredEvidence"])
            )
            self.assertEqual(
                candidate["claimResults"]["structural"]["status"], "PASS"
            )
            self.assertEqual(
                candidate["claimResults"]["target"]["status"], "NOT_EVALUATED"
            )

    def test_wave_current_native_result_requires_contract_schema_expansion(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            subject = root / "subject.wav"
            raw = make_wave(subject)
            contract = {
                "contractVersion": 1,
                "id": "claim-wave-r1",
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
            profile_path, canonical = profile("audio-wave-pcm16-r1")
            req = {
                "schemaVersion": 1,
                "kind": "artifact-verification-request",
                "requestId": "claim:wave:r1",
                "profile": {
                    "id": canonical["id"],
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
            rp = root / "request.json"
            rp.write_text(json.dumps(req), encoding="utf-8")
            result = SERVICE.verify_request(rp)
            if any(
                "required mature external capability unavailable" in x
                for x in result.get("failures", [])
            ):
                self.skipTest("mature WAVE toolchain unavailable")
            self.assertEqual(result["status"], "PASS", result)
            assessed = A.assess_family_claim_mapping(
                result, canonical, A.WAVE_R1_MAPPING
            )
            self.assertEqual(
                assessed["standing"], "NATIVE_RESULT_EXPANSION_REQUIRED"
            )
            self.assertEqual(
                assessed["unaddressableClaims"],
                {"contractSchema": "NO_SAFE_NATIVE_MAPPING"},
            )
            self.assertEqual(
                set(assessed["claimResults"]),
                set(canonical["requiredEvidence"]) - {"contractSchema"},
            )

    def test_png_current_native_result_requires_profile_facts_expansion(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            subject = root / "subject.png"
            make_png(subject)
            profile_path, canonical = profile("still-image-png-srgb-r1")
            req = {
                "schemaVersion": 1,
                "kind": "artifact-verification-request",
                "requestId": "claim:png:r1",
                "profile": {
                    "id": canonical["id"],
                    "path": str(profile_path),
                    "sha256": sha(profile_path),
                },
                "subject": {"path": str(subject), "sha256": sha(subject)},
                "evidenceDirectory": str(root / "evidence"),
            }
            rp = root / "request.json"
            rp.write_text(json.dumps(req), encoding="utf-8")
            result = SERVICE.verify_request(rp)
            if any(
                "required external tool unavailable" in x
                for x in result.get("failures", [])
            ):
                self.skipTest("mature PNG toolchain unavailable")
            self.assertEqual(result["status"], "PASS", result)
            assessed = A.assess_family_claim_mapping(
                result, canonical, A.PNG_R1_MAPPING
            )
            self.assertEqual(
                assessed["standing"], "NATIVE_RESULT_EXPANSION_REQUIRED"
            )
            self.assertEqual(
                assessed["unaddressableClaims"],
                {"profileFacts": "NO_SAFE_NATIVE_MAPPING"},
            )
            self.assertEqual(
                set(assessed["claimResults"]),
                set(canonical["requiredEvidence"]) - {"profileFacts"},
            )

    def test_contract_rejects_missing_profile_claim_even_when_native_result_passes(self):
        _, canonical = profile("still-image-png-srgb-r1")
        native = {"status": "PASS", "decoderMatrix": {"status": "PASS"}}
        candidate = {
            "schemaVersion": 1,
            "kind": "artifact-verifier-plugin-result",
            "profileRef": {
                "id": canonical["id"],
                "sha256": "0" * 64,
                "authority": "SHADOW",
            },
            "subjectRef": {"sha256": "1" * 64, "size": 1},
            "capabilityRef": {
                "capabilityId": "test",
                "standing": "LOCAL_LIVE_PROVEN",
            },
            "claimResults": {
                "decoderMatrix": {
                    "status": "PASS",
                    "observationIds": ["decoderMatrix"],
                    "evidenceRefs": [],
                    "nativePointers": ["/decoderMatrix"],
                    "nonClaims": [],
                }
            },
            "nativeResult": native,
            "nativeResultCanonicalSha256": CONTRACT.canonical_sha256(native),
            "pluginBoundary": "test-only",
        }
        with self.assertRaisesRegex(ValueError, "must exactly equal"):
            CONTRACT.validate_plugin_result(candidate, canonical)


if __name__ == "__main__":
    unittest.main()
