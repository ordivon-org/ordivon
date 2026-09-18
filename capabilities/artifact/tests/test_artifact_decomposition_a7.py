import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
DELIVERY = ROOT / "scripts/artifact_delivery.py"


class ArtifactDocumentVerifierDecompositionA7Tests(unittest.TestCase):
    def test_document_verifier_package_has_semantic_and_dependency_owners(self):
        for relative in (
            "artifact_verifiers/document/__init__.py",
            "artifact_verifiers/document/semantics.py",
            "artifact_verifiers/document/dependencies.py",
        ):
            with self.subTest(relative=relative):
                self.assertTrue((ROOT / relative).is_file(), relative)

    def test_delivery_keeps_only_thin_document_verifier_wrappers(self):
        source = DELIVERY.read_text(encoding="utf-8")
        tree = ast.parse(source)
        funcs = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
        for name in (
            "verify_document_semantic_correspondence",
            "verify_document_dependencies",
        ):
            node = funcs.get(name)
            self.assertIsNotNone(node, name)
            self.assertLessEqual(node.end_lineno - node.lineno + 1, 18, name)
        for name in (
            "_pandoc_inline_text",
            "_pandoc_semantic_projection",
            "_pandoc_meta_text",
            "_run_pandoc_ast",
        ):
            self.assertNotIn(name, funcs)

    def test_document_verifier_package_does_not_import_delivery_monolith(self):
        for relative in (
            "artifact_verifiers/document/semantics.py",
            "artifact_verifiers/document/dependencies.py",
        ):
            source = (ROOT / relative).read_text(encoding="utf-8")
            self.assertNotIn("import artifact_delivery", source)
            self.assertNotIn("from artifact_delivery", source)

    def test_package_exports_document_verifier_surface(self):
        from artifact_verifiers.document import (
            DocumentDependencyHooks,
            verify_document_dependencies,
            verify_document_semantic_correspondence,
        )
        self.assertTrue(callable(verify_document_dependencies))
        self.assertTrue(callable(verify_document_semantic_correspondence))
        self.assertTrue(hasattr(DocumentDependencyHooks, "__dataclass_fields__"))

    def test_verify_stage_wiring_targets_document_verifier_package(self):
        source = (
            ROOT / "artifact_operations/providers/direct_python.py"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "verify_document_semantic_correspondence=verify_document_semantic_correspondence",
            source,
        )
        self.assertIn(
            "verify_document_dependencies=self._document_dependency_stage_verifier",
            source,
        )


if __name__ == "__main__":
    unittest.main()
