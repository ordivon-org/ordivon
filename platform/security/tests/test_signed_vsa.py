import base64
import json
import tempfile
import unittest
from pathlib import Path

from ordivon_security_v2.signed_vsa import (
    DSSE_PAYLOAD_TYPE,
    VSA_PREDICATE,
    decode_bundle_statement,
    load_trust_mapping,
    verify_vsa_semantics,
)


class SignedVsaTests(unittest.TestCase):
    def _statement(self) -> dict[str, object]:
        return {
            "_type": "https://in-toto.io/Statement/v1",
            "subject": [{"name": "repo", "digest": {"gitCommit": "a" * 40}}],
            "predicateType": VSA_PREDICATE,
            "predicate": {
                "verifier": {"id": "https://example.invalid/verifier", "version": {"v": "1"}},
                "resourceUri": "git+file:///repo",
                "policy": {"uri": "file:///policy", "digest": {"sha256": "b" * 64}},
                "inputAttestations": [],
                "verificationResult": "PASSED",
                "verifiedLevels": ["SECURITY_PRODUCT_POLICY"],
                "dependencyLevels": {},
                "slsaVersion": "1.2",
            },
        }

    def test_decode_and_verify_exact_signed_payload(self) -> None:
        statement = self._statement()
        payload = (json.dumps(statement, sort_keys=True) + "\n").encode()
        bundle = {
            "mediaType": "application/vnd.dev.sigstore.bundle.v0.3+json",
            "verificationMaterial": {},
            "dsseEnvelope": {
                "payload": base64.b64encode(payload).decode(),
                "payloadType": DSSE_PAYLOAD_TYPE,
                "signatures": [{"sig": "ZmFrZQ=="}],
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bundle.json"
            path.write_text(json.dumps(bundle), encoding="utf-8")
            decoded, signed = decode_bundle_statement(path)
        verify_vsa_semantics(
            statement=decoded,
            expected_subject_git_commit="a" * 40,
            expected_verifier_id="https://example.invalid/verifier",
            expected_level="SECURITY_PRODUCT_POLICY",
            public_key_sha256="sha256:" + "c" * 64,
            trust_mapping={"https://example.invalid/verifier": "sha256:" + "c" * 64},
            expected_statement_bytes=payload,
            signed_payload_bytes=signed,
        )

    def test_signed_vsa_rejects_duplicate_json_semantic_names(self) -> None:
        """An authentic DSSE signature does not make ambiguous JSON meaningful."""
        statement = self._statement()
        canonical = json.dumps(statement, sort_keys=True)
        duplicate = canonical.replace(
            '"verificationResult": "PASSED"',
            '"verificationResult": "FAILED", "verificationResult": "PASSED"',
            1,
        )
        self.assertNotEqual(duplicate, canonical)
        envelope = {
            "mediaType": "application/vnd.dev.sigstore.bundle.v0.3+json",
            "verificationMaterial": {},
            "dsseEnvelope": {
                "payload": base64.b64encode(duplicate.encode()).decode(),
                "payloadType": DSSE_PAYLOAD_TYPE,
                "signatures": [{"sig": "ZmFrZQ=="}],
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle = root / "signed-bundle.json"
            bundle.write_text(json.dumps(envelope), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate"):
                decode_bundle_statement(bundle)

            # The outer Sigstore bundle can also have conflicting envelopes.
            first = json.dumps(envelope)
            second = first.replace(
                '"verificationMaterial": {}',
                '"verificationMaterial": {}, "verificationMaterial": {"other": true}',
                1,
            )
            self.assertNotEqual(second, first)
            bundle.write_text(second, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate"):
                decode_bundle_statement(bundle)

            # A verifier-to-public-key trust map is likewise an authority input.
            trust = root / "trust.json"
            trust.write_text(
                '{"schemaVersion":1,"verifiers":{'
                '"verifier":{"publicKeySha256":"sha256:111"},'
                '"verifier":{"publicKeySha256":"sha256:222"}}}',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "duplicate"):
                load_trust_mapping(trust)

    def test_untrusted_key_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "not bound"):
            verify_vsa_semantics(
                statement=self._statement(),
                expected_subject_git_commit="a" * 40,
                expected_verifier_id="https://example.invalid/verifier",
                expected_level="SECURITY_PRODUCT_POLICY",
                public_key_sha256="sha256:" + "d" * 64,
                trust_mapping={"https://example.invalid/verifier": "sha256:" + "c" * 64},
            )

    def test_failed_vsa_fails_closed(self) -> None:
        statement = self._statement()
        statement["predicate"]["verificationResult"] = "FAILED"  # type: ignore[index]
        with self.assertRaisesRegex(ValueError, "not PASSED"):
            verify_vsa_semantics(
                statement=statement,
                expected_subject_git_commit="a" * 40,
                expected_verifier_id="https://example.invalid/verifier",
                expected_level="SECURITY_PRODUCT_POLICY",
                public_key_sha256="sha256:" + "c" * 64,
                trust_mapping={"https://example.invalid/verifier": "sha256:" + "c" * 64},
            )


class SignedVsaCompositionTests(unittest.TestCase):
    """Native shell orchestration, with an explicitly synthetic crypto seam."""

    def test_semantics_consumes_the_same_bundle_and_key_as_crypto(self):
        import os
        import subprocess
        import sys
        from hashlib import sha256

        script = Path(__file__).resolve().parents[1] / "scripts/verify_vsa_cosign.sh"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            statement = SignedVsaTests()._statement()
            invalid = json.loads(json.dumps(statement))
            invalid["predicate"]["verificationResult"] = "FAILED"

            def bundle(value):
                return json.dumps({"dsseEnvelope": {
                    "payloadType": DSSE_PAYLOAD_TYPE,
                    "payload": base64.b64encode(json.dumps(value).encode()).decode(),
                    "signatures": [{"sig": "ZmFrZQ=="}],
                }}).encode()

            original = root / "original.json"
            replacement = root / "replacement.json"
            original.write_bytes(bundle(invalid))
            replacement.write_bytes(bundle(statement))
            key = root / "key.pub"
            key.write_bytes(b"synthetic key")
            trust = root / "trust.json"
            trust.write_text(json.dumps({"schemaVersion": 1, "verifiers": {
                "https://example.invalid/verifier": {"publicKeySha256": "sha256:" + sha256(key.read_bytes()).hexdigest()}
            }}))
            carrier = root / "carrier"
            carrier.write_bytes(b"synthetic carrier")
            fake = root / "cosign"
            fake.write_text(
                "#!/bin/sh\n"
                "set -eu\n"
                "while [ $# -gt 0 ]; do\n"
                "  case \"$1\" in --bundle) shift; cmp \"$1\" \"$ORIGINAL\" ;; "
                "--key) shift; cmp \"$1\" \"$ORIGINAL_KEY\" ;; esac\n"
                "  shift\n"
                "done\n"
                "cp \"$REPLACEMENT\" \"$ORIGINAL\"\n"
                "printf 'synthetic crypto success\\n'\n"
            )
            fake.chmod(0o700)
            env = {
                **os.environ,
                "PATH": str(root) + os.pathsep + str(Path(sys.executable).parent) + os.pathsep + os.environ["PATH"],
                "ORIGINAL": str(original), "REPLACEMENT": str(replacement),
                "ORIGINAL_KEY": str(key),
            }
            result = subprocess.run(
                ["bash", str(script), str(original), str(carrier), str(key), str(trust),
                 "a" * 40, "https://example.invalid/verifier", "SECURITY_PRODUCT_POLICY"],
                env=env, capture_output=True, text=True,
            )
            self.assertIn("synthetic crypto success", result.stdout)
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("not PASSED", result.stderr)
            original.write_bytes(bundle(statement))
            replacement.write_bytes(bundle(invalid))
            result = subprocess.run(
                ["bash", str(script), str(original), str(carrier), str(key), str(trust),
                 "a" * 40, "https://example.invalid/verifier", "SECURITY_PRODUCT_POLICY"],
                env=env, capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("VSA semantic verification: PASSED", result.stdout)
            self.assertEqual(original.read_bytes(), bundle(invalid))
            # Verify the key identity independently: the provider consumes the
            # original key; a changed source key cannot satisfy the trust map.
            original.write_bytes(bundle(statement))
            replacement_key = root / "replacement.pub"
            replacement_key.write_bytes(b"synthetic other key")
            trust.write_text(json.dumps({"schemaVersion": 1, "verifiers": {
                "https://example.invalid/verifier": {
                    "publicKeySha256": "sha256:" + sha256(replacement_key.read_bytes()).hexdigest()
                }
            }}))
            fake.write_text(
                "#!/bin/sh\nset -eu\n"
                "while [ $# -gt 0 ]; do\n"
                "  case \"$1\" in --key) shift; cmp \"$1\" \"$ORIGINAL_KEY\" ;; esac\n"
                "  shift\ndone\n"
                "cp \"$REPLACEMENT_KEY\" \"$ORIGINAL_KEY\"\n"
                "printf 'synthetic crypto success\\n'\n"
            )
            env["REPLACEMENT_KEY"] = str(replacement_key)
            result = subprocess.run(
                ["bash", str(script), str(original), str(carrier), str(key), str(trust),
                 "a" * 40, "https://example.invalid/verifier", "SECURITY_PRODUCT_POLICY"],
                env=env, capture_output=True, text=True,
            )
            self.assertIn("synthetic crypto success", result.stdout)
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("not bound", result.stderr)
            # A failed provider must not enter semantic verification.
            fake.write_text("#!/bin/sh\nexit 19\n")
            result = subprocess.run(
                ["bash", str(script), str(original), str(carrier), str(key), str(trust),
                 "a" * 40, "https://example.invalid/verifier", "SECURITY_PRODUCT_POLICY"],
                env=env, capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 19)
            self.assertNotIn("VSA semantic verification", result.stdout)



if __name__ == "__main__":
    unittest.main()
