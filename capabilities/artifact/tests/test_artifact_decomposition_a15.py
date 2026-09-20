import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ArtifactOwnerExtractionA15Tests(unittest.TestCase):
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

    def test_direct_provider_exposes_public_presentation_services(self):
        source = (
            ROOT / "artifact_operations/providers/direct_python.py"
        ).read_text(encoding="utf-8")
        self.assertIn("def build_presentation_source(", source)
        self.assertIn("def build_semantic_svg_presentation_source(", source)

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
