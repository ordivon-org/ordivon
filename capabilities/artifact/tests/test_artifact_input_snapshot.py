"""File-descriptor-backed byte identity, separate from native format semantics."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from artifact_core.input_snapshot import stage_verified_input

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("snapshot_service", ROOT / "scripts/artifact_verify.py")
SERVICE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(SERVICE)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


class SnapshotIdentityTests(unittest.TestCase):
    def test_original_replacement_does_not_change_native_input(self):
        with tempfile.TemporaryDirectory() as root:
            directory = Path(root)
            original = directory / "asset.wav"
            initial = b"fixed-content-for-verification"
            original.write_bytes(initial)
            with tempfile.TemporaryDirectory() as scratch:
                bound = stage_verified_input(
                    original, digest(initial), Path(scratch), role="subject"
                )
                original.write_bytes(b"new-uncommitted-content")
                self.assertEqual(bound.path.read_bytes(), initial)
                self.assertEqual(bound.sha256, digest(initial))
                self.assertEqual(bound.size, len(initial))
                self.assertEqual(bound.path.suffix, ".wav")
            self.assertFalse(bound.path.exists())

    def test_mismatching_bytes_are_rejected_and_not_retained(self):
        with tempfile.TemporaryDirectory() as root:
            directory = Path(root)
            source = directory / "contract.json"
            source.write_bytes(b"unexpected content")
            (directory / "private").mkdir(mode=0o700)
            with self.assertRaisesRegex(ValueError, "contract bytes differ"):
                stage_verified_input(source, digest(b"expected"), directory / "private", role="contract")
            self.assertFalse((directory / "private/contract/contract.json").exists())

    @unittest.skipUnless(hasattr(os, "O_NOFOLLOW"), "requires NOFOLLOW")
    def test_symlink_is_not_followed_as_final_source(self):
        with tempfile.TemporaryDirectory() as root:
            directory = Path(root)
            actual = directory / "actual.wav"
            actual.write_bytes(b"bytes")
            alias = directory / "alias.wav"
            alias.symlink_to(actual)
            (directory / "private").mkdir(mode=0o700)
            with self.assertRaises(OSError):
                stage_verified_input(alias, digest(b"bytes"), directory / "private", role="subject")

    def test_file_descriptor_rejects_fifo_without_blocking(self):
        if not hasattr(os, "mkfifo") or not hasattr(os, "O_NONBLOCK"):
            self.skipTest("requires POSIX nonblocking FIFO")
        with tempfile.TemporaryDirectory() as root:
            directory = Path(root)
            fifo = directory / "not-a-file.wav"
            os.mkfifo(fifo)
            (directory / "private").mkdir(mode=0o700)
            with self.assertRaisesRegex(ValueError, "not a regular file"):
                stage_verified_input(fifo, digest(b"abc"), directory / "private", role="subject")

    def test_service_validates_the_pinned_bytes_not_a_later_source_path(self):
        with tempfile.TemporaryDirectory() as root:
            directory = Path(root)
            subject = directory / "sound.wav"
            contract = directory / "contract.json"
            initial = b"bounded-reference-wave-bytes"
            contract_initial = b'{"contractVersion":1,"audio":{"sampleRateHz":48000}}'
            subject.write_bytes(initial)
            contract.write_bytes(contract_initial)
            profile = ROOT / "artifact-delivery/shadow-v2/examples/audio-wave-pcm16-r1-v2.json"
            profile_data = json.loads(profile.read_text())
            request = {
                "schemaVersion": 1,
                "kind": "artifact-verification-request",
                "requestId": "snapshot-wave-service",
                "profile": {"id": "audio-wave-pcm16-r1", "path": str(profile), "sha256": digest(profile.read_bytes())},
                "subject": {"path": str(subject), "sha256": digest(initial)},
                "objectContract": {"path": str(contract), "sha256": digest(contract_initial)},
                "evidenceDirectory": str(directory / "evidence"),
            }
            request_path = directory / "request.json"
            request_path.write_text(json.dumps(request))
            observed_paths: list[Path] = []

            def substitute_verifier(_relative: str, _name: str):
                # This mutation happens after the service's exact-byte staging.
                subject.write_bytes(b"replaced-after-admission")
                contract.write_bytes(b"replaced-contract")
                def verify(staged_subject: Path, staged_contract: Path, _evidence_dir: Path):
                    observed_paths.extend((staged_subject, staged_contract))
                    self.assertEqual(staged_subject.read_bytes(), initial)
                    self.assertEqual(staged_contract.read_bytes(), contract_initial)
                    facts = {name: {"status": "PASS"} for name in profile_data["requiredEvidence"]}
                    return {
                        "status": "PASS",
                        "nativeFacts": facts,
                        "claimResults": {
                            name: {"status": "PASS", "nativePointers": [f"/nativeFacts/{name}"]}
                            for name in profile_data["requiredEvidence"]
                        },
                    }
                return verify, "f" * 64

            with mock.patch.object(SERVICE, "load_function", side_effect=substitute_verifier):
                result = SERVICE.verify_request(request_path)
            self.assertEqual(result["status"], "PASS", result)
            self.assertTrue(result["profileVerificationComplete"])
            self.assertEqual(result["subject"]["sha256"], digest(initial))
            self.assertEqual(result["inputIdentity"]["subject"], "EXACT_BYTES_SNAPSHOT")
            self.assertEqual(result["inputIdentity"]["objectContract"], "EXACT_BYTES_SNAPSHOT")
            self.assertEqual(result["inputIdentity"]["sourcePathContinuity"], "NOT_CLAIMED")
            self.assertEqual(len(observed_paths), 2)
            self.assertTrue(all(not path.exists() for path in observed_paths))
            self.assertNotEqual(subject.read_bytes(), initial)

    def test_snapshot_drift_does_not_create_a_service_receipt(self):
        with tempfile.TemporaryDirectory() as root:
            directory = Path(root)
            subject = directory / "sound.wav"
            subject.write_bytes(b"changed")
            profile = ROOT / "artifact-delivery/shadow-v2/examples/audio-wave-pcm16-r1-v2.json"
            contract = directory / "contract.json"
            contract.write_bytes(b"contract")
            request = {
                "schemaVersion": 1, "kind": "artifact-verification-request",
                "requestId": "snapshot-drift",
                "profile": {"id": "audio-wave-pcm16-r1", "path": str(profile), "sha256": digest(profile.read_bytes())},
                "subject": {"path": str(subject), "sha256": digest(b"previous")},
                "objectContract": {"path": str(contract), "sha256": digest(contract.read_bytes())},
                "evidenceDirectory": str(directory / "evidence"),
            }
            request_path = directory / "request.json"
            request_path.write_text(json.dumps(request))
            with mock.patch.object(SERVICE, "load_function") as loaded:
                result = SERVICE.verify_request(request_path)
            self.assertEqual(result["status"], "FAIL")
            self.assertIn("subject bytes differ from request digest", result["failures"])
            loaded.assert_not_called()
            self.assertFalse((directory / "evidence").exists())


if __name__ == "__main__":
    unittest.main()
