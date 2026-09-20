import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DELIVERY = ROOT / "scripts/artifact_delivery.py"


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

    def test_delivery_keeps_only_thin_pdf_verifier_compatibility_surface(self):
        source = DELIVERY.read_text(encoding="utf-8")
        tree = ast.parse(source)
        funcs = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
        for name in ("verify_pdf", "_verapdf_executable", "verify_pdf_conformance"):
            node = funcs.get(name)
            self.assertIsNotNone(node, name)
            self.assertLessEqual(node.end_lineno - node.lineno + 1, 8, name)

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

    def test_verify_stage_and_presentation_gate_wire_directly_to_pdf_verifier(self):
        provider = (
            ROOT / "artifact_operations/providers/direct_python.py"
        ).read_text(encoding="utf-8")
        delivery = DELIVERY.read_text(encoding="utf-8")
        self.assertIn("verify_pdf=verify_pdf", provider)
        self.assertIn("verify_pdf_conformance=verify_pdf_conformance", provider)
        self.assertIn(
            "hooks=PresentationGateHooks(verify_pdf=pdf_verify_structural)",
            delivery,
        )


if __name__ == "__main__":
    unittest.main()
