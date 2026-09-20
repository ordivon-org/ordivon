import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ArtifactOpenXmlVerifierDecompositionA9Tests(unittest.TestCase):
    def test_openxml_verifier_package_has_validator_and_toolchain_owners(self):
        for relative in (
            "artifact_verifiers/openxml/__init__.py",
            "artifact_verifiers/openxml/validator.py",
            "artifact_verifiers/openxml/toolchain.py",
        ):
            with self.subTest(relative=relative):
                self.assertTrue((ROOT / relative).is_file(), relative)

    def test_openxml_verifier_package_does_not_import_delivery_monolith(self):
        for relative in (
            "artifact_verifiers/openxml/validator.py",
            "artifact_verifiers/openxml/toolchain.py",
        ):
            source = (ROOT / relative).read_text(encoding="utf-8")
            self.assertNotIn("import artifact_delivery", source)
            self.assertNotIn("from artifact_delivery", source)

    def test_package_exports_openxml_verifier_surface(self):
        from artifact_verifiers.openxml import (
            openxml_validator_executable,
            verify_openxml_artifact,
        )
        self.assertTrue(callable(openxml_validator_executable))
        self.assertTrue(callable(verify_openxml_artifact))

    def test_verify_stage_wires_directly_to_openxml_verifier(self):
        source = (
            ROOT / "artifact_operations/providers/direct_python.py"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "verify_openxml_artifact=verify_openxml_artifact",
            source,
        )

    def test_document_dependency_reuses_openxml_toolchain_owner(self):
        document_toolchain = (
            ROOT / "artifact_verifiers/document/toolchain.py"
        ).read_text(encoding="utf-8")
        dependencies = (
            ROOT / "artifact_verifiers/document/dependencies.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn("DEFAULT_OPENXML_VALIDATOR", document_toolchain)
        self.assertIn("openxml_validator_executable", dependencies)


if __name__ == "__main__":
    unittest.main()
