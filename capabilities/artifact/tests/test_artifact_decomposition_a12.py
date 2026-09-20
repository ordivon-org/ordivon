import hashlib
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUPPORT = ROOT / "scripts/artifact_temporal_support.py"


class ArtifactOperationTemporalAdapterA12Tests(unittest.TestCase):
    def test_operation_package_has_contract_receipt_executor_and_replaceable_provider(self):
        for relative in (
            "artifact_operations/__init__.py",
            "artifact_operations/contract.py",
            "artifact_operations/receipt.py",
            "artifact_operations/executor.py",
            "artifact_operations/providers/__init__.py",
            "artifact_operations/providers/direct_python.py",
        ):
            with self.subTest(relative=relative):
                self.assertTrue((ROOT / relative).is_file(), relative)

    def test_temporal_support_is_adapter_not_cli_or_receipt_implementation(self):
        source = SUPPORT.read_text(encoding="utf-8")
        for forbidden in (
            "subprocess.",
            "fcntl.",
            "compile-request",
            "build-request",
            "verify-stage",
            "aggregate-vsa-gates",
            "--gate-bundle",
            "--verify-report",
            "DEFAULT_ARTIFACT_CLI",
            "DEFAULT_ARTIFACT_OCI_CLI",
        ):
            self.assertNotIn(forbidden, source)
        self.assertIn("ArtifactOperationExecutor", source)
        self.assertIn("DirectPythonOperationProvider", source)
        self.assertNotIn("DeliveryCliOperationProvider", source)

    def test_operation_envelope_has_stable_kind_and_explicit_operation_kind(self):
        from artifact_operations.contract import operation_envelope, validate_operation_envelope

        value = operation_envelope(
            "wf/build",
            "build",
            {"request": {"path": "/tmp/request.json", "sha256": "a" * 64}},
        )
        self.assertEqual(value["kind"], "ordivon.artifact-operation")
        self.assertEqual(value["operationKind"], "build")
        self.assertIs(validate_operation_envelope(value), value)

    def test_generic_executor_build_replays_with_operation_receipt(self):
        from artifact_operations.contract import operation_envelope
        from artifact_operations.executor import ArtifactOperationExecutor
        from artifact_operations.providers import DirectPythonOperationProvider

        req = ROOT / "artifact-delivery/examples/presentation-native-smoke-request-r1.json"
        request = {
            "path": str(req),
            "sha256": hashlib.sha256(req.read_bytes()).hexdigest(),
        }
        with tempfile.TemporaryDirectory() as d:
            executor = ArtifactOperationExecutor(
                Path(d) / "state",
                provider=DirectPythonOperationProvider(),
            )
            operation = operation_envelope("a12/build/replay", "build", {"request": request})
            first = executor.execute(operation)
            second = executor.execute(operation)
            self.assertEqual(first["kind"], "ordivon.artifact-operation-result")
            self.assertEqual(first["operationKind"], "build")
            self.assertFalse(first["replayed"])
            self.assertTrue(second["replayed"])
            self.assertEqual(
                first["roles"]["artifact"]["sha256"],
                second["roles"]["artifact"]["sha256"],
            )

    def test_temporal_compatibility_executor_delegates_to_generic_operation_executor(self):
        source = SUPPORT.read_text(encoding="utf-8")
        self.assertIn("def build(", source)
        self.assertIn('"build"', source)
        self.assertNotIn("def _fenced(", source)
        self.assertNotIn("def _run_cli(", source)

    def test_legacy_delivery_cli_provider_is_retired(self):
        self.assertFalse((ROOT / "artifact_operations/providers/delivery_cli.py").exists())
        source = SUPPORT.read_text(encoding="utf-8")
        for retired in ("DeliveryCliOperationProvider", "artifact_cli", "artifact_oci_cli"):
            self.assertNotIn(retired, source)


if __name__ == "__main__":
    unittest.main()
