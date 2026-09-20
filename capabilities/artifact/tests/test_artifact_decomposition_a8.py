import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ArtifactPdfVerifierDecompositionA8Tests(unittest.TestCase):
    def test_pdf_verifier_package_has_structural_conformance_and_toolchain_owners(self):
        for relative in (
            "artifact_verifiers/pdf/__init__.py",
            "artifact_verifiers/pdf/structural.py",
            "artifact_verifiers/pdf/conformance.py",
            "artifact_verifiers/pdf/toolchain.py",
        ):
            with self.subTest(relative=relative):
                self.assertTrue((ROOT / relative).is_file(), relative)

    def test_pdf_verifier_package_does_not_import_delivery_monolith(self):
        for relative in (
            "artifact_verifiers/pdf/structural.py",
            "artifact_verifiers/pdf/conformance.py",
            "artifact_verifiers/pdf/toolchain.py",
        ):
            source = (ROOT / relative).read_text(encoding="utf-8")
            self.assertNotIn("import artifact_delivery", source)
            self.assertNotIn("from artifact_delivery", source)

    def test_package_exports_pdf_verifier_surface(self):
        from artifact_verifiers.pdf import (
            qpdf_executable,
            verapdf_executable,
            verify_pdf,
            verify_pdf_conformance,
        )
        for item in (
            qpdf_executable,
            verapdf_executable,
            verify_pdf,
            verify_pdf_conformance,
        ):
            self.assertTrue(callable(item))


if __name__ == "__main__":
    unittest.main()
