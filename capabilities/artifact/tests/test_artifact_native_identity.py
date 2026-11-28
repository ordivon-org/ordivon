"""Identity contradiction is an explicit service failure, not an aggregate PASS."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from artifact_verification.native_identity import assess_native_identity

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "artifact_native_identity_service", ROOT / "scripts/artifact_verify.py"
)
SERVICE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(SERVICE)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class NativeIdentityServiceTests(unittest.TestCase):
    def _request(self, directory: Path, profile_id: str) -> tuple[Path, dict]:
        profile = ROOT / f"artifact-delivery/shadow-v2/examples/{profile_id}-v2.json"
        subject = directory / "sample.wav"
        subject.write_bytes(b"identity-test-bytes")
        contract = directory / "contract.json"
        contract.write_text('{"example":true}')
        request = {
            "schemaVersion": 1,
            "kind": "artifact-verification-request",
            "requestId": "native-identity-" + profile_id,
            "profile": {
                "id": profile_id, "path": str(profile), "sha256": digest(profile)
            },
            "subject": {"path": str(subject), "sha256": digest(subject)},
            "objectContract": {"path": str(contract), "sha256": digest(contract)},
            "evidenceDirectory": str(directory / "evidence"),
        }
        path = directory / "request.json"
        path.write_text(json.dumps(request))
        return path, request

    def _strict_native(self, staged_subject: Path, staged_contract: Path) -> dict:
        profile = json.loads((
            ROOT / "artifact-delivery/shadow-v2/examples/audio-wave-pcm16-r1-v2.json"
        ).read_text())
        observed = {name: {"status": "PASS"} for name in profile["requiredEvidence"]}
        return {
            "profileId": "audio-wave-pcm16-r1",
            "status": "PASS",
            "artifact": {
                "path": str(staged_subject),
                "sha256": digest(staged_subject),
                "size": staged_subject.stat().st_size,
            },
            "contract": {"sha256": digest(staged_contract)},
            "observed": observed,
            "claimResults": {
                name: {"status": "PASS", "nativePointers": [f"/observed/{name}"]}
                for name in observed
            },
            "failures": [],
        }

    def test_strict_native_identity_is_verified_and_subject_can_be_ephemeral(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            request_path, _ = self._request(directory, "audio-wave-pcm16-r1")
            recorded: list[Path] = []

            def verify(subject: Path, contract: Path, _evidence: Path) -> dict:
                recorded.extend((subject, contract))
                return self._strict_native(subject, contract)

            with mock.patch.object(SERVICE, "load_function", return_value=(verify, "f" * 64)):
                result = SERVICE.verify_request(request_path)
            self.assertEqual(result["status"], "PASS", result)
            self.assertTrue(result["profileVerificationComplete"], result)
            self.assertEqual(result["nativeIdentityAssessment"]["status"], "COMPLETE")
            self.assertTrue(all(not path.exists() for path in recorded))

    def test_every_reported_identity_contradiction_invalidates_strict_pass(self):
        for field in ("profileId", "artifact.sha256", "artifact.size", "contract.sha256"):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temporary:
                directory = Path(temporary)
                request_path, _ = self._request(directory, "audio-wave-pcm16-r1")

                def verify(subject: Path, contract: Path, _evidence: Path) -> dict:
                    result = self._strict_native(subject, contract)
                    obj = result
                    bits = field.split(".")
                    for bit in bits[:-1]:
                        obj = obj[bit]
                    obj[bits[-1]] = "wrong" if bits[-1] != "size" else 1_000_000
                    return result

                with mock.patch.object(SERVICE, "load_function", return_value=(verify, "f" * 64)):
                    result = SERVICE.verify_request(request_path)
                self.assertEqual(result["status"], "FAIL", result)
                self.assertFalse(result["profileVerificationComplete"], result)
                self.assertIn(
                    "native evidence identity mismatch: " + field, result["failures"]
                )
                self.assertTrue(result["nativeIdentityAssessment"]["rejected"])

    def test_missing_strict_identity_never_promotes_an_aggregate_pass(self):
        for field in ("profileId", "artifact", "contract"):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temporary:
                directory = Path(temporary)
                request_path, _ = self._request(directory, "audio-wave-pcm16-r1")

                def verify(subject: Path, contract: Path, _evidence: Path) -> dict:
                    result = self._strict_native(subject, contract)
                    del result[field]
                    return result

                with mock.patch.object(SERVICE, "load_function", return_value=(verify, "f" * 64)):
                    result = SERVICE.verify_request(request_path)
                self.assertEqual(result["status"], "FAIL", result)
                self.assertEqual(result["nativeIdentityAssessment"]["status"], "NOT_EVALUATED")
                self.assertFalse(result["profileVerificationComplete"])

    def test_legacy_missing_identity_is_unknown_and_contradiction_is_fatal(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            request_path, _ = self._request(directory, "dataset-parquet-flat-r1")
            with mock.patch.object(
                SERVICE, "load_function",
                return_value=(lambda *_: {"status": "PASS"}, "f" * 64),
            ):
                result = SERVICE.verify_request(request_path)
            self.assertEqual(result["status"], "PASS", result)
            self.assertFalse(result["profileVerificationComplete"])
            self.assertEqual(result["nativeIdentityAssessment"]["status"], "NOT_EVALUATED")

            with mock.patch.object(
                SERVICE, "load_function",
                return_value=(
                    lambda *_: {"status": "PASS", "profileId": "wrong-profile"},
                    "f" * 64,
                ),
            ):
                contradicted = SERVICE.verify_request(request_path)
            self.assertEqual(contradicted["status"], "FAIL")
            self.assertIn(
                "native evidence identity mismatch: profileId",
                contradicted["failures"]
            )

    def test_non_mapping_or_raised_native_result_never_promotes_pass(self):
        for provider in (
            lambda *_: None,
            lambda *_: ["PASS"],
            lambda *_: (_ for _ in ()).throw(ValueError("provider unavailable")),
        ):
            with self.subTest(provider=provider), tempfile.TemporaryDirectory() as temporary:
                directory = Path(temporary)
                request_path, _ = self._request(directory, "audio-wave-pcm16-r1")
                with mock.patch.object(
                    SERVICE, "load_function", return_value=(provider, "f" * 64)
                ):
                    result = SERVICE.verify_request(request_path)
                self.assertEqual(result["status"], "FAIL", result)
                self.assertTrue(
                    any("native verifier" in error for error in result["failures"])
                )
                self.assertFalse((directory / "evidence/service-result.json").exists())

    def test_malformed_native_identity_does_not_bypass_rejection(self):
        native = {
            "profileId": "audio-wave-pcm16-r1",
            "status": "PASS",
            "artifact": {"sha256": "a" * 64, "size": True},
            "contract": {"sha256": "b" * 64},
        }
        result = assess_native_identity(
            native,
            profile_id="audio-wave-pcm16-r1",
            subject_sha256="a" * 64,
            subject_size=1,
            contract_sha256="b" * 64,
            require_complete=True,
        )
        self.assertTrue(result["rejected"])
        self.assertIn("native evidence identity mismatch: artifact.size", result["mismatches"])


if __name__ == "__main__":
    unittest.main()
