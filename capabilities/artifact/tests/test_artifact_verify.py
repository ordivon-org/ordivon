import binascii
import hashlib
import importlib.util
import json
import struct
import tempfile
import unittest
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MONOREPO_ROOT = ROOT.parents[1]
GAME_ROOT = MONOREPO_ROOT / "domains" / "game"
SPEC = importlib.util.spec_from_file_location("artifact_verify", ROOT / "scripts/artifact_verify.py")
M = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(M)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def chunk(kind: bytes, payload: bytes) -> bytes:
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", binascii.crc32(kind + payload) & 0xFFFFFFFF)


def minimal_png(path: Path) -> None:
    signature = b"\x89PNG\r\n\x1a\n"
    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    srgb = chunk(b"sRGB", b"\x00")
    data = chunk(b"IDAT", zlib.compress(bytes([0, 32, 64, 128])))
    path.write_bytes(signature + ihdr + srgb + data + chunk(b"IEND", b""))


class ArtifactVerifyServiceTests(unittest.TestCase):
    def profile(self):
        p = ROOT / "artifact-delivery/shadow-v2/examples/still-image-png-srgb-r1-v2.json"
        return p, {"id": "still-image-png-srgb-r1", "path": str(p), "sha256": sha(p)}

    def request(self, root: Path, subject: Path) -> tuple[Path, dict]:
        profile_path, profile = self.profile()
        value = {
            "schemaVersion": 1,
            "kind": "artifact-verification-request",
            "requestId": "test:still-image:1",
            "profile": profile,
            "subject": {"path": str(subject), "sha256": sha(subject)},
            "evidenceDirectory": str(root / "evidence"),
            "consumer": {"id": "test-consumer", "purpose": "bounded verification"}
        }
        path = root / "request.json"
        path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
        return path, value

    def require_png_tools(self):
        mod = M.load_function("scripts/artifact_still_image.py", "verify_png_srgb")[0]
        # Importing through the service is enough; delegate itself reports tool absence.
        self.assertTrue(callable(mod))

    def test_exact_still_image_request_delegates_and_digest_binds_result(self):
        self.require_png_tools()
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); subject = root / "subject.png"; minimal_png(subject)
            request_path, request = self.request(root, subject)
            result = M.verify_request(request_path)
            if any("required external tool unavailable" in x for x in result.get("failures", [])):
                self.skipTest("mature still-image tools unavailable")
            self.assertEqual(result["status"], "PASS", result)
            self.assertEqual(result["subject"]["sha256"], sha(subject))
            self.assertEqual(result["profile"]["id"], request["profile"]["id"])
            self.assertEqual(result["capabilityBinding"]["standing"], "LOCAL_LIVE_PROVEN")
            self.assertEqual(result["requestDigest"], M.canonical_sha256(request))
            self.assertTrue((root / "evidence/service-result.json").is_file())

    def test_subject_digest_drift_fails_before_family_verifier(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); subject = root / "subject.png"; minimal_png(subject)
            request_path, _ = self.request(root, subject)
            subject.write_bytes(subject.read_bytes() + b"drift")
            result = M.verify_request(request_path)
            self.assertEqual(result["status"], "FAIL")
            self.assertIn("subject bytes differ from request digest", result["failures"])
            self.assertFalse((root / "evidence/service-result.json").exists())

    def test_profile_digest_drift_fails_before_family_verifier(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); subject = root / "subject.png"; minimal_png(subject)
            request_path, value = self.request(root, subject)
            value["profile"]["sha256"] = "0" * 64
            request_path.write_text(json.dumps(value))
            result = M.verify_request(request_path)
            self.assertEqual(result["status"], "FAIL")
            self.assertIn("profile bytes differ from request digest", result["failures"])

    def test_contract_required_profile_fails_without_contract(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); subject = root / "x.flac"; subject.write_bytes(b"not-flac")
            p = ROOT / "artifact-delivery/shadow-v2/examples/audio-flac-pcm16-r1-v2.json"
            request = {
                "schemaVersion": 1, "kind": "artifact-verification-request", "requestId": "test:audio:1",
                "profile": {"id": "audio-flac-pcm16-r1", "path": str(p), "sha256": sha(p)},
                "subject": {"path": str(subject), "sha256": sha(subject)},
                "evidenceDirectory": str(root / "evidence")
            }
            rp = root / "request.json"; rp.write_text(json.dumps(request))
            result = M.verify_request(rp)
            self.assertEqual(result["status"], "FAIL")
            self.assertIn("profile requires an object contract: audio-flac-pcm16-r1", result["failures"])

    def test_frozen_game_consumer_smoke_keeps_artifact_owned_authorities_exact(self):
        receipt = json.loads((ROOT / "artifact-delivery/consumer-acceptance/game-station-zero-still-image-r1.json").read_text())
        self.assertEqual(receipt["standing"], "CONSUMER_SMOKE_PASS_SHADOW_PROFILE")
        self.assertEqual(receipt["verification"]["serviceStatus"], "PASS")
        self.assertTrue(receipt["verification"]["decoderExactMatch"])
        for value in receipt["artifactOwnedAuthorities"].values():
            path = ROOT / value["relativePath"]
            self.assertEqual(sha(path), value["sha256"], value["relativePath"])
        self.assertEqual(receipt["externalSubject"]["identityStanding"], "EXACT_BYTES_OBSERVED_AT_CONSUMER_REVISION_NOT_ARTIFACT_OWNED")

    def test_frozen_wave_game_consumer_smoke_keeps_artifact_owned_authorities_exact(self):
        receipt = json.loads((ROOT / "artifact-delivery/consumer-acceptance/game-veilwild-wave-pcm16-r1.json").read_text())
        self.assertEqual(receipt["standing"], "CONSUMER_SMOKE_PASS_SHADOW_PROFILE")
        self.assertEqual(receipt["verification"]["serviceStatus"], "PASS")
        self.assertTrue(receipt["verification"]["decoderExactMatch"])
        for value in receipt["artifactOwnedAuthorities"].values():
            path = ROOT / value["relativePath"]
            self.assertEqual(sha(path), value["sha256"], value["relativePath"])

    def test_frozen_ogg_game_evidence_preserves_target_divergence_instead_of_claiming_acceptance(self):
        receipt=json.loads((ROOT/'artifact-delivery/consumer-acceptance/game-station-zero-ogg-vorbis-r1.json').read_text())
        self.assertEqual(receipt['standing'],'STANDARD_PASS_TARGET_DIVERGENCE_GAME_FUNCTIONALLY_ACCEPTED')
        self.assertEqual(receipt['gameAcceptance']['standing'],'GAME_FUNCTIONAL_ACCEPTANCE_PASS_TARGET_BOUNDARY_DIVERGENCE_PRESERVED')
        self.assertEqual(receipt['gameAcceptance']['decision'],'ACCEPT_FOR_CURRENT_STATION_ZERO_FUNCTIONAL_CONSUMPTION')
        game=GAME_ROOT/receipt['gameAcceptance']['relativePath']
        self.assertEqual(hashlib.sha256(game.read_bytes()).hexdigest(),receipt['gameAcceptance']['sha256'])
        self.assertEqual(len(receipt['subjects']),3)
        self.assertTrue(all(x['serviceCandidateStatus']=='PASS' for x in receipt['subjects']))
        self.assertTrue(all(x['browserStanding']=='TARGET_SAMPLE_BOUNDARY_DIVERGENCE_OBSERVED' for x in receipt['subjects']))
        self.assertTrue(all(x['firefoxSamples']-x['chromiumSamples']==128 for x in receipt['subjects']))
        for value in receipt['artifactOwnedAuthorities'].values():
            path=ROOT/value['relativePath'];self.assertEqual(sha(path),value['sha256'],value['relativePath'])
        for subject in receipt['subjects']:
            c=subject['contract'];self.assertEqual(sha(ROOT/c['relativePath']),c['sha256'],c['relativePath'])

    def test_frozen_svg_game_consumer_smoke_preserves_renderer_pixel_divergence(self):
        receipt=json.loads((ROOT/'artifact-delivery/consumer-acceptance/game-station-zero-svg-static-r1.json').read_text())
        self.assertEqual(receipt['standing'],'CONSUMER_SMOKE_PASS_TARGET_PIXEL_DIVERGENCE_OBSERVED')
        self.assertEqual(len(receipt['subjects']),3)
        self.assertTrue(all(x['intrinsicDimensionAgreement'] for x in receipt['subjects']))
        self.assertTrue(all(x['nonTransparentPixelCountAgreement'] for x in receipt['subjects']))
        self.assertTrue(all(not x['pixelChecksumAgreement'] for x in receipt['subjects']))
        for value in receipt['artifactOwnedAuthorities'].values():
            path=ROOT/value['relativePath'];self.assertEqual(sha(path),value['sha256'],value['relativePath'])

    def test_frozen_tiled_game_consumer_smoke_keeps_native_authority_and_game_semantics_separate(self):
        receipt=json.loads((ROOT/'artifact-delivery/consumer-acceptance/game-station-zero-tiled-tmj-r1.json').read_text())
        self.assertEqual(receipt['standing'],'CONSUMER_SMOKE_PASS_NATIVE_CANONICAL_ROUNDTRIP')
        self.assertEqual(receipt['technicalFacts']['layerCount'],2)
        self.assertEqual(receipt['technicalFacts']['objectCount'],40)
        self.assertEqual(receipt['technicalFacts']['objectShapeCounts'],{'polyline':20,'rectangle':20,'unsupported':0})
        self.assertEqual(receipt['nativeTmjRoundTrip']['status'],'PASS')
        self.assertEqual(receipt['nativeCrossFormatRoundTrip']['status'],'PASS')
        self.assertEqual(receipt['nativeRasterReadback']['status'],'PASS')
        self.assertEqual(receipt['gameMigrationEvidence']['layoutDigest'],'21efdf5b69858953aaef55abd0bb143f5eb24f5be8f3a3c3bcfe6cb86cc5b527')
        for value in receipt['artifactOwnedAuthorities'].values():
            path=ROOT/value['relativePath'];self.assertEqual(sha(path),value['sha256'],value['relativePath'])

    def test_frozen_aseprite_game_consumer_smoke_separates_native_and_game_owned_metadata(self):
        receipt=json.loads((ROOT/'artifact-delivery/consumer-acceptance/game-station-zero-aseprite-horizontal-sheet-r1.json').read_text())
        self.assertEqual(receipt['standing'],'CONSUMER_SOURCE_TO_RUNTIME_DERIVATIVE_PASS')
        self.assertEqual(len(receipt['subjects']),2)
        by={x['asset']:x for x in receipt['subjects']}
        self.assertTrue(by['expression']['retainedNativeMetadata']['exactlyEqualsNativeExport'])
        self.assertEqual(by['specialists']['callerOwnedMetadata']['authority'],'Game')
        self.assertEqual(by['specialists']['callerOwnedMetadata']['artifactInterpretation'],'NOT_CLAIMED')
        self.assertTrue(all(x['nativeDeterministicExport']=='PASS' for x in receipt['subjects']))
        self.assertTrue(all(x['derivedPngProfileStatus']=='PASS' for x in receipt['subjects']))
        self.assertTrue(all(x['runtimeDerivative']['sha256']==x['derivativeIdentity']['generatedPngSha256'] for x in receipt['subjects']))
        for value in receipt['artifactOwnedAuthorities'].values():
            path=ROOT/value['relativePath'];self.assertEqual(sha(path),value['sha256'],value['relativePath'])
        for x in receipt['subjects']:
            c=x['contract'];self.assertEqual(sha(ROOT/c['relativePath']),c['sha256'],c['relativePath'])

    def test_frozen_glb_game_consumer_smokes_keep_profile_boundaries_exact(self):
        for name, profile_id in [
            ("game-veilwild-glb-material-scene-r1.json", "design-3d-glb-material-scene-r1"),
            ("game-veilwild-glb-skinned-animation-r1.json", "design-3d-glb-skinned-animation-r1"),
        ]:
            receipt=json.loads((ROOT/"artifact-delivery/consumer-acceptance"/name).read_text())
            self.assertEqual(receipt["standing"],"CONSUMER_SMOKE_PASS_SHADOW_PROFILE")
            self.assertEqual(receipt["artifactOwnedAuthorities"]["profile"]["id"],profile_id)
            self.assertEqual(receipt["verification"]["serviceStatus"],"PASS")
            self.assertEqual(receipt["verification"]["khronos"]["errors"],0)
            self.assertEqual(receipt["verification"]["khronos"]["warnings"],0)
            self.assertEqual(receipt["verification"]["assimpStatus"],"PASS")
            self.assertEqual(receipt["verification"]["blenderStatus"],"PASS")
            self.assertEqual(receipt["verification"]["godotStatus"],"PASS")
            for value in receipt["artifactOwnedAuthorities"].values():
                path=ROOT/value["relativePath"];self.assertEqual(sha(path),value["sha256"],value["relativePath"])
            self.assertEqual(receipt["externalSubject"]["identityStanding"],"EXACT_BYTES_OBSERVED_AT_CONSUMER_REVISION_NOT_ARTIFACT_OWNED")

    def test_frozen_game_godot_linux_elf_release_preserves_producer_and_artifact_authorities(self):
        receipt=json.loads((ROOT/'artifact-delivery/consumer-acceptance/game-godot-production-smoke-linux-elf-r1.json').read_text())
        self.assertEqual(receipt['standing'],'CONSUMER_RELEASE_READBACK_PASS_PRODUCER_BOUNDARY_PRESERVED')
        self.assertEqual(receipt['artifactVerification']['serviceStatus'],'PASS')
        self.assertEqual(receipt['artifactVerification']['runtimeReadback'],'PASS')
        self.assertEqual(receipt['artifactVerification']['networkNamespace'],'UNSHARED')
        for value in receipt['artifactOwnedAuthorities'].values():
            path=ROOT/value['relativePath'];self.assertEqual(sha(path),value['sha256'],value['relativePath'])
        game=GAME_ROOT
        for key in ('harness','acceptedReproducibilityBoundary'):
            value=receipt['producerEvidence'][key];self.assertEqual(sha(game/value['relativePath']),value['sha256'],value['relativePath'])
        self.assertEqual(receipt['producerEvidence']['currentRuntimeProof']['firstBuildSha256'],receipt['externalSubject']['sha256'])
        self.assertEqual(receipt['producerEvidence']['currentRuntimeProof']['secondBuildSha256'],receipt['externalSubject']['sha256'])
        self.assertIn('Steam or other store upload/release',receipt['boundary']['notEstablished'])

    def test_unrouted_profile_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); subject = root / "subject.bin"; subject.write_bytes(b"x")
            p = ROOT / "artifact-delivery/shadow-v2/examples/web-r1-v2.json"
            request = {
                "schemaVersion": 1, "kind": "artifact-verification-request", "requestId": "test:web:1",
                "profile": {"id": "web-r1", "path": str(p), "sha256": sha(p)},
                "subject": {"path": str(subject), "sha256": sha(subject)},
                "evidenceDirectory": str(root / "evidence")
            }
            rp = root / "request.json"; rp.write_text(json.dumps(request))
            result = M.verify_request(rp)
            self.assertEqual(result["status"], "FAIL")
            self.assertIn("profile is not on the Artifact verification R1 service surface: web-r1", result["failures"])


    def test_verification_routes_are_owned_by_capability_registry_not_python_constant(self):
        self.assertFalse(hasattr(M, "ROUTES"))
        binding = M.BINDING_REGISTRY.resolve("still-image-png-srgb-r1", "verify")
        self.assertEqual(binding.entrypoint.module, "scripts/artifact_still_image.py")
        self.assertEqual(binding.entrypoint.callable, "verify_png_srgb")


if __name__ == "__main__":
    unittest.main()
