import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ArtifactVerificationDecompositionA5Tests(unittest.TestCase):
    def test_verification_package_has_stage_and_evidence_owners(self):
        for relative in (
            "artifact_verification/__init__.py",
            "artifact_verification/evidence.py",
            "artifact_verification/stage.py",
        ):
            with self.subTest(relative=relative):
                self.assertTrue((ROOT / relative).is_file(), relative)

    def test_verification_package_does_not_import_delivery_monolith(self):
        for relative in ("artifact_verification/evidence.py", "artifact_verification/stage.py"):
            source = (ROOT / relative).read_text(encoding="utf-8")
            self.assertNotIn("import artifact_delivery", source)
            self.assertNotIn("from artifact_delivery", source)

    def test_gate_receipt_writes_and_validates_local_vsa(self):
        from artifact_trust.vsa import LOCAL_VSA_VERIFIER_ID
        from artifact_verification.evidence import write_gate_receipt

        profile = ROOT / "artifact-delivery/examples/pdu-sdu-presentation-r1.json"
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            subject = root / "subject.pptx"
            subject.write_bytes(b"not-a-real-pptx-but-digest-bound")
            receipt = write_gate_receipt(
                root / "evidence",
                "profileSchema",
                subject,
                profile,
                {
                    "status": "PASS",
                    "boundary": "unit evidence only",
                },
                LOCAL_VSA_VERIFIER_ID,
                {"unit": "1"},
            )
            self.assertEqual(receipt["status"], "PASS", receipt)
            self.assertEqual(receipt["verificationResult"], "PASSED")
            self.assertTrue((root / "evidence/profileSchema.raw.json").is_file())
            self.assertTrue((root / "evidence/profileSchema.vsa.json").is_file())
            self.assertEqual(receipt["vsaValidation"]["status"], "PASS")

    def test_stage_public_api_is_owned_by_verification_package(self):
        from artifact_verification import VerificationStageHooks, execute_verify_stage
        self.assertTrue(callable(execute_verify_stage))
        self.assertTrue(hasattr(VerificationStageHooks, "__dataclass_fields__"))


if __name__ == "__main__":
    unittest.main()
