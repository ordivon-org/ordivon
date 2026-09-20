import ast
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DELIVERY = ROOT / "scripts/artifact_delivery.py"
SUPPORT = ROOT / "scripts/artifact_delivery_temporal_support.py"


class ArtifactDirectPythonProviderA13Tests(unittest.TestCase):
    def test_presentation_canonicalization_has_real_owner_and_delivery_wrappers_are_thin(self):
        module = ROOT / "artifact_capabilities/presentation/canonicalization.py"
        self.assertTrue(module.is_file())
        source = DELIVERY.read_text(encoding="utf-8")
        tree = ast.parse(source)
        funcs = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
        for name in (
            "normalize_zip_member_timestamps",
            "canonicalize_generated_ooxml_metadata",
        ):
            node = funcs.get(name)
            self.assertIsNotNone(node, name)
            self.assertLessEqual(node.end_lineno - node.lineno + 1, 4, name)
        private_wrapper = funcs.get("_canonicalize_ppt_creation_ids")
        self.assertIsNotNone(private_wrapper)
        self.assertLessEqual(
            private_wrapper.end_lineno - private_wrapper.lineno + 1, 4
        )
        for name in (
            "_dos_datetime_fields",
            "_canonicalize_opc_core_xml",
            "_canonicalize_generated_zip_bytes",
        ):
            self.assertNotIn(name, funcs)

    def test_direct_python_provider_exists_without_delivery_or_subprocess_dependency(self):
        path = ROOT / "artifact_operations/providers/direct_python.py"
        self.assertTrue(path.is_file())
        source = path.read_text(encoding="utf-8")
        self.assertNotIn("artifact_delivery", source)
        self.assertNotIn("subprocess", source)
        self.assertNotIn("delivery_cli", source)
        self.assertIn("execute_build_adapter", source)
        self.assertIn("execute_verify_stage", source)
        self.assertIn("aggregate_vsa_gates", source)
        self.assertIn("execute_oci_package_stage", source)

    def test_temporal_adapter_defaults_to_direct_python_provider(self):
        spec = importlib.util.spec_from_file_location("a13_temporal_support", SUPPORT)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        from artifact_operations.providers import DirectPythonOperationProvider

        with tempfile.TemporaryDirectory() as d:
            executor = module.ReceiptFencedArtifactExecutor(Path(d) / "state")
            self.assertIsInstance(executor.provider, DirectPythonOperationProvider)

    def test_cli_provider_remains_explicit_fallback_not_default(self):
        support = SUPPORT.read_text(encoding="utf-8")
        self.assertIn("DirectPythonOperationProvider", support)
        self.assertNotIn("self.provider = DeliveryCliOperationProvider", support)
        self.assertTrue(
            (ROOT / "artifact_operations/providers/delivery_cli.py").is_file()
        )

    @pytest.mark.integration
    def test_direct_provider_build_and_verify_smoke(self):
        from artifact_operations import ArtifactOperationExecutor, operation_envelope
        from artifact_operations.providers import DirectPythonOperationProvider

        request = ROOT / "artifact-delivery/examples/presentation-native-smoke-request-r1.json"
        request_fact = {
            "path": str(request),
            "sha256": hashlib.sha256(request.read_bytes()).hexdigest(),
        }
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            executor = ArtifactOperationExecutor(
                root / "state", provider=DirectPythonOperationProvider()
            )
            built = executor.execute(
                operation_envelope(
                    "a13/build",
                    "build",
                    {"request": request_fact},
                )
            )
            self.assertEqual(built["operationKind"], "build")
            artifact = built["roles"]["artifact"]

            profile = json.loads(
                (ROOT / "artifact-delivery/examples/pdu-sdu-presentation-r1.json").read_text()
            )
            profile.pop("$schema", None)
            profile["id"] = "a13-direct-verify-r1"
            profile.pop("companions", None)
            for gate in list(profile["gates"]):
                profile["gates"][gate] = False
            for gate in ("profileSchema", "structural", "semantic"):
                profile["gates"][gate] = True
            profile_path = root / "profile.json"
            profile_path.write_text(json.dumps(profile), encoding="utf-8")
            profile_fact = {
                "path": str(profile_path),
                "sha256": hashlib.sha256(profile_path.read_bytes()).hexdigest(),
            }
            verified = executor.execute(
                operation_envelope(
                    "a13/verify",
                    "verify",
                    {"profile": profile_fact, "artifact": artifact},
                )
            )
            self.assertEqual(verified["operationKind"], "verify")
            self.assertTrue(verified["metadata"]["profileVerificationComplete"])
            self.assertIn("verifyReport", verified["roles"])


if __name__ == "__main__":
    unittest.main()
