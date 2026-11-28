"""Portable multi-file Artifact -> independent native consumer verification.

The source Workspace must not be needed after the archive is created.
These tests use the public portable-bundle entrypoint and real WAVE verifiers.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import struct
import tempfile
import unittest
import wave
import zipfile
from pathlib import Path

import pytest

from artifact_operations.portable_bundle import build_bundle, verify_bundle
from scripts import artifact_verify, artifact_wave


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class PortableBundleConsumerTests(unittest.TestCase):
    @staticmethod
    def require_native() -> None:
        for executable in (
            artifact_wave.SNDFILE_INFO, artifact_wave.SOX,
            artifact_wave.SOXI, artifact_wave.FFMPEG, artifact_wave.FFPROBE,
        ):
            if not executable.is_file():
                raise unittest.SkipTest(f"native WAVE consumer unavailable: {executable}")

    def producer(self, root: Path) -> Path:
        root.mkdir(parents=True, exist_ok=True)
        subject = root / "asset.wav"
        frames = 1000
        pcm = b"".join(
            struct.pack("<hh", (n * 17 % 16000) - 8000, (n * 19 % 16000) - 8000)
            for n in range(frames)
        )
        with wave.open(str(subject), "wb") as writer:
            writer.setnchannels(2)
            writer.setsampwidth(2)
            writer.setframerate(48000)
            writer.writeframes(pcm)
        contract = root / "contract.json"
        contract.write_text(json.dumps({
            "contractVersion": 1,
            "id": "portable-native-wave-consumer",
            "profileId": "audio-wave-pcm16-r1",
            "audio": {
                "sampleRateHz": 48000, "channels": 2, "bitsPerSample": 16,
                "frameCount": frames, "expectedPcmSha256": sha(pcm),
            },
        }))
        profile = artifact_verify.PROFILE_REGISTRY.resolve("audio-wave-pcm16-r1")
        request = root / "request.json"
        request.write_text(json.dumps({
            "schemaVersion": 1,
            "kind": "artifact-verification-request",
            "requestId": "portable-bundle-native-acceptance",
            "profile": {
                "id": profile.profile_id,
                "path": str(profile.canonical_path),
                "sha256": profile.canonical_sha256,
            },
            "subject": {"path": str(subject), "sha256": sha(subject.read_bytes())},
            "objectContract": {"path": str(contract), "sha256": sha(contract.read_bytes())},
            "evidenceDirectory": str(root / "source-evidence"),
            "consumer": {"id": "independent-native-wave-consumer"},
        }))
        return request

    @staticmethod
    def modify_zip(source: Path, target: Path, edits: dict[str, bytes | None]) -> None:
        with zipfile.ZipFile(source) as original, zipfile.ZipFile(
            target, "w", compression=zipfile.ZIP_DEFLATED
        ) as replacement:
            for member in original.namelist():
                if member in edits:
                    if edits[member] is not None:
                        replacement.writestr(member, edits[member])
                else:
                    replacement.writestr(member, original.read(member))

    @pytest.mark.integration
    def test_moved_bundle_reverifies_with_original_workspace_deleted(self):
        self.require_native()
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            request = self.producer(root / "producer")
            bundle = root / "handoff.zip"
            built = build_bundle(request, bundle)
            self.assertEqual(built["status"], "PASS", built)
            self.assertTrue(built["profileVerificationComplete"])
            with zipfile.ZipFile(bundle) as package:
                names = package.namelist()
                self.assertIn("profile/profile.json", names)
                self.assertIn("evidence/service-result.json", names)
                self.assertIn("provenance/original-request.json", names)
                self.assertIn("subject/asset.wav", names)
                self.assertIn("contract/object-contract.json", names)
            shutil.rmtree(root / "producer")
            imported = root / "downstream" / "renamed-output.zip"
            imported.parent.mkdir()
            shutil.copy2(bundle, imported)
            checked = verify_bundle(imported)
            self.assertEqual(checked["status"], "PASS", checked)
            self.assertTrue(checked["profileVerificationComplete"])
            self.assertEqual(checked["consumer"]["id"], "independent-native-wave-consumer")

    @pytest.mark.integration
    def test_changed_subject_fails_even_if_original_report_claimed_pass(self):
        self.require_native()
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            bundle = root / "handoff.zip"
            build_bundle(self.producer(root / "producer"), bundle)
            changed = root / "changed.zip"
            self.modify_zip(bundle, changed, {"subject/asset.wav": b"invalid-subject"})
            checked = verify_bundle(changed)
            self.assertEqual(checked["status"], "FAIL", checked)
            self.assertFalse(checked.get("profileVerificationComplete", False))

    @pytest.mark.integration
    def test_missing_required_object_contract_fails(self):
        self.require_native()
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            bundle = root / "handoff.zip"
            build_bundle(self.producer(root / "producer"), bundle)
            changed = root / "missing-contract.zip"
            self.modify_zip(bundle, changed, {"contract/object-contract.json": None})
            checked = verify_bundle(changed)
            self.assertEqual(checked["status"], "FAIL", checked)

    @pytest.mark.integration
    def test_embedded_profile_cannot_replace_canonical_authority(self):
        self.require_native()
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            bundle = root / "handoff.zip"
            build_bundle(self.producer(root / "producer"), bundle)
            with zipfile.ZipFile(bundle) as package:
                manifest = json.loads(package.read("bundle.json"))
                profile = json.loads(package.read("profile/profile.json"))
            profile["description"] = "different claimed canonical profile"
            changed_profile = json.dumps(profile).encode()
            manifest["profile"]["sha256"] = sha(changed_profile)
            changed = root / "profile-forged.zip"
            self.modify_zip(bundle, changed, {
                "profile/profile.json": changed_profile,
                "bundle.json": json.dumps(manifest).encode(),
            })
            checked = verify_bundle(changed)
            self.assertEqual(checked["status"], "FAIL", checked)
            self.assertFalse(checked.get("profileVerificationComplete", False))

    @pytest.mark.integration
    def test_original_request_is_provenance_only_not_reexecution_authority(self):
        self.require_native()
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            request = self.producer(root / "producer")
            bundle = root / "handoff.zip"
            build_bundle(request, bundle)
            with zipfile.ZipFile(bundle) as package:
                original = json.loads(package.read("provenance/original-request.json"))
            self.assertTrue(original["subject"]["path"].startswith(str(root / "producer")))
            shutil.rmtree(root / "producer")
            verified = verify_bundle(bundle)
            self.assertEqual(verified["status"], "PASS", verified)

    @pytest.mark.integration
    def test_forged_provenance_cannot_relabel_verified_bundle(self):
        self.require_native()
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            original_zip = root / "handoff.zip"
            build_bundle(self.producer(root / "producer"), original_zip)
            with zipfile.ZipFile(original_zip) as package:
                original = json.loads(package.read("provenance/original-request.json"))
                manifest = json.loads(package.read("bundle.json"))
            original["subject"]["sha256"] = "a" * 64
            rewritten = json.dumps(original).encode()
            manifest["originalRequest"]["sha256"] = sha(rewritten)
            forged = root / "forged-provenance.zip"
            self.modify_zip(original_zip, forged, {
                "provenance/original-request.json": rewritten,
                "bundle.json": json.dumps(manifest).encode(),
            })
            result = verify_bundle(forged)
            self.assertEqual(result["status"], "FAIL", result)
            self.assertIn("identity", " ".join(result["failures"]))

    def test_packaging_cannot_promote_a_stale_source_pass(self):
        # The source identity rejection precedes native verification.
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            request = self.producer(root / "producer")
            (root / "producer" / "asset.wav").write_bytes(b"this file has changed")
            output = root / "stale.zip"
            with self.assertRaisesRegex(ValueError, "subject bytes differ from request digest"):
                build_bundle(request, output)
            self.assertFalse(output.exists())

    @pytest.mark.integration
    def test_zip_with_unsafe_relative_member_is_rejected(self):
        self.require_native()
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            bundle = root / "handoff.zip"
            build_bundle(self.producer(root / "producer"), bundle)
            with zipfile.ZipFile(bundle, "a") as package:
                package.writestr("../untrusted-file", b"untrusted")
            result = verify_bundle(bundle)
            self.assertEqual(result["status"], "FAIL", result)
            self.assertIn("unsafe", " ".join(result["failures"]))
