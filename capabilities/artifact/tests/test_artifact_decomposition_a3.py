from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ArtifactDecompositionA3TrustTests(unittest.TestCase):
    def test_trust_gate_api_is_owned_by_artifact_trust_package(self) -> None:
        from artifact_trust.vsa import (
            LOCAL_VSA_VERIFIER_ID,
            SIGSTORE_BUNDLE_V03,
            aggregate_vsa_gates,
            cosign_tool_fact,
            validate_vsa_trust_policy,
            verification_summary_statement,
            verify_signed_verification_summary,
            verify_verification_summary,
        )

        self.assertTrue(LOCAL_VSA_VERIFIER_ID.startswith("https://"))
        self.assertEqual(SIGSTORE_BUNDLE_V03, "application/vnd.dev.sigstore.bundle.v0.3+json")
        for value in (
            aggregate_vsa_gates,
            cosign_tool_fact,
            validate_vsa_trust_policy,
            verification_summary_statement,
            verify_signed_verification_summary,
            verify_verification_summary,
        ):
            self.assertTrue(callable(value))

    def test_verification_summary_round_trip_is_independent_of_delivery_monolith(self) -> None:
        from artifact_trust.vsa import (
            LOCAL_VSA_VERIFIER_ID,
            verification_summary_statement,
            verify_verification_summary,
        )

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            subject = root / "artifact.bin"
            subject.write_bytes(b"artifact-a3")
            profile = ROOT / "artifact-delivery/examples/pdu-sdu-presentation-r1.json"
            statement_path = root / "structural.vsa.json"
            statement_path.write_text(json.dumps(verification_summary_statement(
                subject,
                profile,
                LOCAL_VSA_VERIFIER_ID,
                {"fixture": "1"},
                True,
            )), encoding="utf-8")
            result = verify_verification_summary(statement_path, subject, profile, [LOCAL_VSA_VERIFIER_ID])
            self.assertEqual(result["status"], "PASS", result)
            self.assertEqual(result["verificationResult"], "PASSED")
            self.assertEqual(result["authenticity"], "NOT_VERIFIED")

    def test_oci_consumes_trust_package_not_delivery_trust_symbols(self) -> None:
        source = (ROOT / "scripts/artifact_oci_package.py").read_text(encoding="utf-8")
        self.assertIn("from artifact_trust.vsa import", source)
        self.assertIn("aggregate_vsa_gates", source)
        self.assertNotIn("from artifact_delivery import", source)
        self.assertNotIn("import artifact_delivery", source)
        for retired_dead_import in (
            "LOCAL_VSA_VERIFIER_ID",
            "SIGSTORE_BUNDLE_V03",
            "cosign_tool_fact",
        ):
            self.assertNotIn(retired_dead_import, source)

    def test_trust_package_does_not_import_delivery_monolith(self) -> None:
        source = (ROOT / "artifact_trust/vsa.py").read_text(encoding="utf-8")
        self.assertNotIn("artifact_delivery", source)
        self.assertIn("from artifact_core.contracts import", source)
        self.assertIn("from artifact_core.profile_v1 import", source)


if __name__ == "__main__":
    unittest.main()
