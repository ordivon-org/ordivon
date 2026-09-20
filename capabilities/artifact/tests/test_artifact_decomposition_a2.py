from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ArtifactDecompositionA2Tests(unittest.TestCase):
    def test_build_binding_registry_owns_build_adapter_selection(self) -> None:
        from artifact_core.build_bindings import BuildCapabilityBindingRegistry

        registry = BuildCapabilityBindingRegistry(ROOT / "artifact-delivery")
        ppt = registry.resolve("presentation", "presentation-source-v1")
        doc = registry.resolve("document", "markdown")
        self.assertEqual(ppt.adapter_id, "python-pptx-presentation-source-v1")
        self.assertEqual(ppt.capability_id, "artifact.presentation.python-pptx.build")
        self.assertEqual(doc.adapter_id, "pandoc-docx")
        self.assertEqual(doc.capability_id, "artifact.document.pandoc.build")

    def test_request_admission_is_owned_by_core_module(self) -> None:
        source = (ROOT / "artifact_operations/providers/direct_python.py").read_text(encoding="utf-8")
        self.assertIn("admit_delivery_request", source)
        self.assertIn("AdmissionHooks", source)

    def test_document_provider_owns_source_date_epoch_behavior(self) -> None:
        from artifact_capabilities.document import build_pandoc_docx

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            source = root / "source.md"
            source.write_text("# hi\n", encoding="utf-8")
            output = root / "out.docx"
            pandoc = root / "pandoc"
            pandoc.write_text(
                "#!/usr/bin/env python3\n"
                "import os,sys\n"
                "from pathlib import Path\n"
                "Path(sys.argv[sys.argv.index('-o')+1]).write_text(os.environ.get('SOURCE_DATE_EPOCH','ABSENT'))\n",
                encoding="utf-8",
            )
            pandoc.chmod(0o755)
            result = build_pandoc_docx(source, output, pandoc, environment={"SOURCE_DATE_EPOCH": "123"})
            self.assertEqual(result["status"], "PASS", result)
            self.assertEqual(result["reproducibleBuildEnvironment"]["unixSeconds"], 123)
            self.assertEqual(output.read_text(), "123")

            output.unlink()
            bad = build_pandoc_docx(source, output, pandoc, environment={"SOURCE_DATE_EPOCH": "bad"})
            self.assertEqual(bad["status"], "FAIL")
            self.assertIn("SOURCE_DATE_EPOCH", bad["error"])
            self.assertFalse(output.exists())

    def test_pass_through_provider_binds_exact_bytes(self) -> None:
        from artifact_capabilities.passthrough import copy_exact

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            source = root / "source.bin"
            output = root / "out.bin"
            source.write_bytes(b"exact-artifact-bytes")
            result = copy_exact(source, output)
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["source"]["digest"]["sha256"], result["artifact"]["digest"]["sha256"])


    def test_build_stage_dispatch_is_owned_by_capability_layer(self) -> None:
        source = (ROOT / "artifact_operations/providers/direct_python.py").read_text(encoding="utf-8")
        self.assertNotIn('if adapter == "python-pptx-presentation-source-v1"', source)
        self.assertIn("execute_build_adapter", source)


    def test_slsa_release_provenance_is_owned_by_trust_module(self) -> None:
        from artifact_trust.provenance import slsa_statement, verify_release_provenance

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            subject = root / "artifact.bin"
            material = root / "source.txt"
            subject.write_bytes(b"artifact")
            material.write_bytes(b"source")
            profile = ROOT / "artifact-delivery/examples/document-r1.json"
            statement = slsa_statement(
                [subject], [material], profile,
                "https://builder.example/test", "https://build.example/test",
                invocation_id="artifact-build-test",
            )
            statement_path = root / "provenance.json"
            statement_path.write_text(json.dumps(statement), encoding="utf-8")
            result = verify_release_provenance(statement_path, [subject])
            self.assertEqual(result["status"], "PASS", result)

    def test_oci_uses_core_identity_and_trust_provenance_instead_of_delivery_monolith(self) -> None:
        source = (ROOT / "scripts/artifact_oci_package.py").read_text(encoding="utf-8")
        self.assertNotIn("artifact.sha256_file", source)
        self.assertNotIn("artifact.file_fact", source)
        self.assertNotIn("artifact.verify_file_fact", source)
        self.assertNotIn("artifact.verify_release_provenance", source)
        self.assertNotIn("artifact.slsa_statement", source)
        self.assertIn("from artifact_core.contracts import", source)
        self.assertIn("from artifact_trust.provenance import", source)


    def test_oci_has_no_broad_delivery_monolith_import(self) -> None:
        source = (ROOT / "scripts/artifact_oci_package.py").read_text(encoding="utf-8")
        self.assertNotIn("import artifact_delivery", source)
        self.assertNotIn("from artifact_delivery import", source)
        self.assertIn("aggregate_vsa_gates,", source)
        self.assertIn("from artifact_core.admission import", source)


if __name__ == "__main__":
    unittest.main()
