import ast
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DELIVERY = ROOT / "scripts/artifact_delivery.py"
MANIFEST = ROOT / "artifact-delivery/compatibility-retirement-manifest-v1.json"


class ArtifactManifestDrivenFacadeReductionA15Tests(unittest.TestCase):
    def _delivery_functions(self):
        tree = ast.parse(DELIVERY.read_text(encoding="utf-8"))
        return {
            node.name: node
            for node in tree.body
            if isinstance(node, ast.FunctionDef)
        }

    def test_reference_projection_has_canonical_presentation_owner(self):
        path = ROOT / "artifact_capabilities/presentation/reference_projection.py"
        self.assertTrue(path.is_file())
        source = path.read_text(encoding="utf-8")
        self.assertIn("def project_opc_members(", source)
        self.assertIn("def compose_reference_hybrid_source(", source)
        self.assertNotIn("artifact_delivery", source)

    def test_snapshot_has_canonical_evidence_owner(self):
        path = ROOT / "artifact_evidence/snapshot.py"
        self.assertTrue(path.is_file())
        source = path.read_text(encoding="utf-8")
        self.assertIn("def utc_now(", source)
        self.assertIn("def snapshot_materials(", source)
        self.assertNotIn("artifact_delivery", source)

    def test_delivery_reference_snapshot_and_operation_entries_are_thin_wrappers(self):
        funcs = self._delivery_functions()
        limits = {
            "project_opc_members": 8,
            "compose_reference_hybrid_source": 10,
            "snapshot_materials": 4,
            "validate_delivery_request": 8,
            "compile_delivery_plan": 4,
            "execute_build_stage": 5,
            "execute_verify_stage": 8,
            "build_presentation_source": 8,
            "build_semantic_svg_presentation_source": 8,
        }
        for name, limit in limits.items():
            with self.subTest(name=name):
                node = funcs[name]
                self.assertLessEqual(node.end_lineno - node.lineno + 1, limit)

    def test_a14_drop_private_wiring_is_gone(self):
        funcs = self._delivery_functions()
        for name in (
            "_selected_external_file",
            "_presentation_build_hooks",
            "_resolve_request_path",
            "_admit_presentation_source",
            "_admit_semantic_svg_source",
            "_primary_suffix",
            "_request_output_name",
            "_document_dependency_hooks",
            "_document_dependency_stage_verifier",
            "_verification_stage_hooks",
        ):
            self.assertNotIn(name, funcs)

    def test_moved_private_reference_helpers_are_gone_from_delivery(self):
        funcs = self._delivery_functions()
        for name in (
            "utc_now",
            "_normalized_posix_relative",
            "_normalized_sha256",
            "_safe_zip_names",
            "_relationship_base",
            "_resolve_relationship_target",
        ):
            self.assertNotIn(name, funcs)

    def test_direct_provider_exposes_public_presentation_compatibility_services(self):
        source = (
            ROOT / "artifact_operations/providers/direct_python.py"
        ).read_text(encoding="utf-8")
        self.assertIn("def build_presentation_source(", source)
        self.assertIn("def build_semantic_svg_presentation_source(", source)

    def test_manifest_tracks_new_live_surface_and_a15_retirements(self):
        value = json.loads(MANIFEST.read_text(encoding="utf-8"))
        funcs = set(self._delivery_functions())
        entries = {item["symbol"]: item for item in value["symbols"]}
        self.assertEqual(set(entries), funcs)
        retired = {item["symbol"]: item for item in value["retiredSymbols"]}
        for name in (
            "_selected_external_file",
            "_presentation_build_hooks",
            "_resolve_request_path",
            "_admit_presentation_source",
            "_admit_semantic_svg_source",
            "_primary_suffix",
            "_request_output_name",
            "_document_dependency_hooks",
            "_document_dependency_stage_verifier",
            "_verification_stage_hooks",
            "utc_now",
            "_normalized_posix_relative",
            "_normalized_sha256",
            "_safe_zip_names",
            "_relationship_base",
            "_resolve_relationship_target",
        ):
            self.assertEqual(retired[name]["wave"], "A15")

        for name in (
            "project_opc_members",
            "compose_reference_hybrid_source",
            "snapshot_materials",
            "validate_delivery_request",
            "compile_delivery_plan",
            "execute_build_stage",
            "execute_verify_stage",
        ):
            self.assertEqual(entries[name]["disposition"], "KEEP_COMPAT_WRAPPER")

    def test_reference_projection_owner_executes_exact_projection(self):
        import hashlib
        import zipfile

        from artifact_capabilities.presentation.reference_projection import (
            project_opc_members,
        )

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            package = root / "one.pptx"
            payload = b"a15"
            with zipfile.ZipFile(package, "w") as archive:
                archive.writestr("ppt/media/one.jpeg", payload)
            manifest = {
                "schemaVersion": 1,
                "kind": "artifact-delivery-opc-member-projection",
                "projectionId": "a15-owner-smoke",
                "parentPackage": {
                    "format": "pptx",
                    "sha256": "sha256:" + hashlib.sha256(package.read_bytes()).hexdigest(),
                    "expectedSizeBytes": package.stat().st_size,
                },
                "members": [{
                    "part": "ppt/media/one.jpeg",
                    "sha256": "sha256:" + hashlib.sha256(payload).hexdigest(),
                    "expectedSizeBytes": len(payload),
                    "outputRelativePath": "slide-01.jpeg",
                }],
                "nonClaims": ["test-only"],
            }
            path = root / "projection.json"
            path.write_text(json.dumps(manifest))
            result = project_opc_members(package, path, root / "out")
            self.assertEqual(result["status"], "PASS")
            self.assertEqual((root / "out/slide-01.jpeg").read_bytes(), payload)


if __name__ == "__main__":
    unittest.main()
