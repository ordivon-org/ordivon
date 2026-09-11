import tempfile
import unittest
from pathlib import Path

from ordivon_security_v2.attestations import (
    REFERENCE_PREDICATE,
    STATEMENT_TYPE,
    VSA_PREDICATE,
    reference_statement,
    subject_descriptor,
    vsa_statement,
)


class AttestationTests(unittest.TestCase):
    def test_reference_statement_uses_in_toto_v1(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "report.json"
            artifact.write_text("{}\n", encoding="utf-8")
            subject = subject_descriptor(name="repo", git_commit="a" * 40)
            statement = reference_statement(
                subject=subject,
                attester_id="https://example.invalid/verifier",
                reference_path=artifact,
            )
            self.assertEqual(statement["_type"], STATEMENT_TYPE)
            self.assertEqual(statement["predicateType"], REFERENCE_PREDICATE)
            self.assertEqual(statement["subject"][0]["digest"], {"gitCommit": "a" * 40})

    def test_vsa_failed_does_not_claim_slsa_level(self) -> None:
        subject = subject_descriptor(name="repo", git_commit="b" * 40)
        statement = vsa_statement(
            subject=subject,
            verifier_id="https://example.invalid/verifier",
            verifier_versions={"verifier": "1"},
            resource_uri="git+https://example.invalid/repo",
            policy_uri="file:///policy.rego",
            policy_sha256="c" * 64,
            input_attestations=[],
            passed=False,
        )
        self.assertEqual(statement["predicateType"], VSA_PREDICATE)
        self.assertEqual(statement["predicate"]["verificationResult"], "FAILED")
        self.assertEqual(statement["predicate"]["verifiedLevels"], ["FAILED"])


if __name__ == "__main__":
    unittest.main()
