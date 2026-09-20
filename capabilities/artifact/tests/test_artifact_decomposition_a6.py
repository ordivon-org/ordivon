import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ArtifactPresentationVerifierDecompositionA6Tests(unittest.TestCase):
    def test_presentation_verifier_package_has_distinct_owners(self):
        for relative in (
            "artifact_verifiers/__init__.py",
            "artifact_verifiers/presentation/__init__.py",
            "artifact_verifiers/presentation/inspection.py",
            "artifact_verifiers/presentation/semantics.py",
            "artifact_verifiers/presentation/gate.py",
        ):
            with self.subTest(relative=relative):
                self.assertTrue((ROOT / relative).is_file(), relative)

    def test_presentation_verifier_package_does_not_import_delivery_monolith(self):
        for relative in (
            "artifact_verifiers/presentation/inspection.py",
            "artifact_verifiers/presentation/semantics.py",
            "artifact_verifiers/presentation/gate.py",
        ):
            source = (ROOT / relative).read_text(encoding="utf-8")
            self.assertNotIn("import artifact_delivery", source)
            self.assertNotIn("from artifact_delivery", source)

    def test_package_exports_verifier_surface(self):
        from artifact_verifiers.presentation import (
            PresentationGateHooks,
            inspect_pptx,
            presentation_gate,
            verify_font_manifest,
            verify_openxml_evidence,
            verify_presentation_semantics,
        )
        for item in (
            inspect_pptx,
            presentation_gate,
            verify_font_manifest,
            verify_openxml_evidence,
            verify_presentation_semantics,
        ):
            self.assertTrue(callable(item))
        self.assertTrue(hasattr(PresentationGateHooks, "__dataclass_fields__"))

    def test_authoring_and_verify_stage_can_consume_verifier_package_without_delivery(self):
        from artifact_verification.stage import VerificationStageHooks
        from artifact_verifiers.presentation import inspect_pptx, verify_presentation_semantics

        self.assertTrue(callable(inspect_pptx))
        self.assertTrue(callable(verify_presentation_semantics))
        fields = VerificationStageHooks.__dataclass_fields__
        self.assertIn("inspect_pptx", fields)
        self.assertIn("verify_presentation_semantics", fields)


if __name__ == "__main__":
    unittest.main()
