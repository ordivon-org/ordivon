import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OCI = ROOT / "scripts/artifact_oci_package.py"


class ArtifactOciDecouplingA11Tests(unittest.TestCase):
    def test_core_owns_generic_json_schema_validation(self):
        module = ROOT / "artifact_core/json_validation.py"
        self.assertTrue(module.is_file())
        source = module.read_text(encoding="utf-8")
        self.assertIn("def validate_json_document(", source)

    def test_oci_has_zero_delivery_import_or_delivery_facade_projection(self):
        source = OCI.read_text(encoding="utf-8")
        self.assertNotIn("from artifact_delivery import", source)
        self.assertNotIn("import artifact_delivery", source)
        self.assertNotIn("SimpleNamespace", source)
        tree = ast.parse(source)
        top_level_artifact_assignments = [
            node for node in tree.body
            if isinstance(node, (ast.Assign, ast.AnnAssign))
            and any(
                isinstance(target, ast.Name) and target.id == "artifact"
                for target in (
                    node.targets if isinstance(node, ast.Assign) else [node.target]
                )
            )
        ]
        self.assertEqual(top_level_artifact_assignments, [])

    def test_oci_request_admission_consumes_core_owner(self):
        source = OCI.read_text(encoding="utf-8")
        self.assertIn("from artifact_core.admission import", source)
        self.assertIn("from artifact_core.json_validation import", source)
        self.assertIn("admit_delivery_request(", source)

    def test_oci_tests_do_not_depend_on_oci_fake_artifact_facade(self):
        source = (ROOT / "tests/test_artifact_oci_package.py").read_text(encoding="utf-8")
        self.assertNotIn("ARTIFACT = MODULE.artifact", source)
        self.assertNotIn("ARTIFACT.", source)


if __name__ == "__main__":
    unittest.main()
