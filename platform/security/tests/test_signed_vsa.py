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


if __name__ == "__main__":
    unittest.main()
