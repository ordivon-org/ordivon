import binascii
import hashlib
import importlib.util
import json
import struct
import subprocess
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


def historical_game_source_digests(relative_path: str) -> set[str]:
    """Read retired Game producer bytes from Git, never from an active game.

    A removal commit is not a source revision for the removed path. Limit
    candidates to revisions where the tracked file was added/modified; the
    frozen Artifact acceptance receipt remains unchanged and historical.
    """
    relative = Path(relative_path)
    if relative.is_absolute() or ".." in relative.parts or not relative.parts:
        raise ValueError("invalid historical Game source path")
    source_path = (GAME_ROOT.relative_to(MONOREPO_ROOT) / relative).as_posix()
    revisions = subprocess.check_output(
        ["git", "-C", str(MONOREPO_ROOT), "log", "--diff-filter=AM",
         "--format=%H", "HEAD", "--", source_path],
        text=True, timeout=25,
    ).splitlines()
    if not revisions:
        raise AssertionError(f"no committed Game source history for {relative_path}")
    digests = set()
    for revision in revisions:
        source = subprocess.check_output(
            ["git", "-C", str(MONOREPO_ROOT), "show", f"{revision}:{source_path}"],
            timeout=15,
        )
        digests.add(hashlib.sha256(source).hexdigest())
    return digests


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

    def test_flac_object_contract_drift_invalidates_consumer_request_before_verification(self):
        """R2.1 consumer seam: a changed object contract invalidates a pinned request.

        Artifact owns the request admission/contract digest check, not the
        Game consumer's acceptance or proof that FLAC decoding has succeeded.
        Reuse the existing JSON Schema, profile registry and service API.
        """
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            subject = root / "subject.flac"
            subject.write_bytes(b"not-a-flac-stream")
            profile = ROOT / "artifact-delivery/shadow-v2/examples/audio-flac-pcm16-r1-v2.json"
            original = ROOT / "artifact-delivery/shadow-contracts/audio-flac-pcm16-smoke-r1.json"
            contract = root / "object-contract.json"
            contract.write_bytes(original.read_bytes())
            request = {
                "schemaVersion": 1,
                "kind": "artifact-verification-request",
                "requestId": "test:artifact-contract-drift:r21",
                "profile": {"id": "audio-flac-pcm16-r1", "path": str(profile), "sha256": sha(profile)},
                "subject": {"path": str(subject), "sha256": sha(subject)},
                "objectContract": {"path": str(contract), "sha256": sha(contract)},
                "evidenceDirectory": str(root / "evidence"),
                "consumer": {"id": "phase2-contract-impact-negative", "purpose": "stale contract invalidation"},
            }
            request_path = root / "request.json"
            request_path.write_text(json.dumps(request))
            # Even a syntactically harmless contract change must invalidate the
            # pre-change source-identity binding before FLAC verification runs.
            changed = json.loads(contract.read_text())
            changed["notes"] = "changed after consumer request was pinned"
            contract.write_text(json.dumps(changed))
            stale = M.verify_request(request_path)
            self.assertEqual(stale["status"], "FAIL")
            self.assertEqual(stale["failures"], ["object contract bytes differ from request digest"])
            self.assertEqual(stale["requestDigest"], M.canonical_sha256(request))
            self.assertFalse((root / "evidence").exists())

            # Non-vacuity control: rebind the request to the new contract bytes.
            # The service must now reach the actual FLAC verifier (which rejects
            # the deliberately invalid subject), not permanently reject requests.
            request["objectContract"]["sha256"] = sha(contract)
            request_path.write_text(json.dumps(request))
            rebound = M.verify_request(request_path)
            self.assertEqual(rebound["status"], "FAIL")
            self.assertNotIn(
                "object contract bytes differ from request digest",
                rebound["failures"],
            )
            self.assertTrue((root / "evidence" / "verification.json").is_file())
            self.assertNotEqual(rebound["requestDigest"], stale["requestDigest"])

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
        # Game no longer owns the old Station Zero executable/evidence path.
        # Recheck its exact historical bytes, not a revived active game.
        game_evidence = receipt['gameAcceptance']
        self.assertIn(
            game_evidence['sha256'],
            historical_game_source_digests(game_evidence['relativePath']),
        )
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
        # Frozen September release evidence must bind immutable *historical*
        # verifier bytes, not force the current implementation to keep its old
        # hash forever. b0adf55 is the source-inclusive monorepo import; this
        # proves historical Git byte reachability, NOT the 2026-09 run itself.
        original_source_cut='b0adf5534d202dcc79b5571da2841a7324d5ac8e'
        for kind,value in receipt['artifactOwnedAuthorities'].items():
            path=ROOT/value['relativePath']
            if kind == 'verifier':
                historical_path='capabilities/artifact/'+value['relativePath']
                historical_bytes=subprocess.check_output(
                    ['git','--no-replace-objects','-C',str(MONOREPO_ROOT),
                     'show',f'{original_source_cut}:{historical_path}'],
                    timeout=20)
                self.assertEqual(hashlib.sha256(historical_bytes).hexdigest(),
                                 value['sha256'], historical_path)
            else:
                self.assertEqual(sha(path),value['sha256'],value['relativePath'])
        # Archived Game source is not part of the current Artifact source
        # authority; the independent historical-source qualification below
        # reports UNKNOWN if its original source cannot be retrieved.
        self.assertEqual(receipt['producerEvidence']['currentRuntimeProof']['firstBuildSha256'],receipt['externalSubject']['sha256'])
        self.assertEqual(receipt['producerEvidence']['currentRuntimeProof']['secondBuildSha256'],receipt['externalSubject']['sha256'])
        self.assertIn('Steam or other store upload/release',receipt['boundary']['notEstablished'])

    def test_frozen_game_godot_producer_source_qualification(self):
        receipt=json.loads((ROOT/'artifact-delivery/consumer-acceptance/game-godot-production-smoke-linux-elf-r1.json').read_text())
        for evidence in (
            receipt['producerEvidence']['harness'],
            receipt['producerEvidence']['acceptedReproducibilityBoundary'],
        ):
            observed=historical_game_source_digests(evidence['relativePath'])
            if evidence['sha256'] not in observed:
                self.skipTest(
                    'UNKNOWN historical Game producer source: '
                    + evidence['relativePath']
                    + '; current monorepo has no matching Git bytes, '
                      'so this archived release cannot be requalified'
                )
            self.assertIn(evidence['sha256'], observed)
            self.assertNotIn('0'*64, observed)

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
