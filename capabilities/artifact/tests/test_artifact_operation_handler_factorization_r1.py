from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from artifact_operations.contract import operation_envelope
from artifact_operations.providers import (
    BuildOperationHandler,
    DirectPythonOperationProvider,
    PackageOperationHandler,
    PrepareOperationHandler,
    TrustOperationHandler,
    VerifyOperationHandler,
)
from artifact_operations.providers.trust import validate_trust_material

ROOT = Path(__file__).resolve().parents[1]


def fact(path: Path) -> dict[str, object]:
    return {
        "path": str(path),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "size": path.stat().st_size,
    }


class ArtifactOperationHandlerFactorizationR1Tests(unittest.TestCase):
    def test_direct_provider_is_registry_backed_composition_root(self):
        provider = DirectPythonOperationProvider()
        self.assertEqual(
            set(provider.operation_handlers),
            {"prepare", "build", "verify", "verify-trust", "package"},
        )
        self.assertIsInstance(provider.operation_handlers["prepare"], PrepareOperationHandler)
        self.assertIsInstance(provider.operation_handlers["build"], BuildOperationHandler)
        self.assertIsInstance(provider.operation_handlers["verify"], VerifyOperationHandler)
        self.assertIsInstance(provider.operation_handlers["verify-trust"], TrustOperationHandler)
        self.assertIsInstance(provider.operation_handlers["package"], PackageOperationHandler)
        source = (ROOT / "artifact_operations/providers/direct_python.py").read_text(encoding="utf-8")
        self.assertNotIn("if operation_kind ==", source)
        self.assertNotIn("aggregate_vsa_gates", source)
        self.assertNotIn("execute_oci_package_stage", source)
        with self.assertRaisesRegex(RuntimeError, "unsupported Artifact operation kind"):
            provider._operation_handler("not-a-kind")

    def test_prepare_handler_preserves_plan_projection_shape(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            request = root / "request.json"; request.write_text("{}")
            profile = root / "profile.json"; profile.write_text("{}")
            source = root / "source.txt"; source.write_text("source")
            plan = {
                "status": "PASS",
                "requestId": "d02/prepare",
                "resolvedInputs": {
                    "profile": fact(profile),
                    "source": fact(source),
                },
                "requiredGates": ["structural"],
            }
            handler = PrepareOperationHandler(lambda _: plan)
            operation = operation_envelope("d02/prepare", "prepare", {"request": fact(request)})
            prepared = handler.prepare(operation)
            roles, metadata = handler.produce(prepared.context, root / "out")
            self.assertEqual(roles, {"plan": "derived-plan.json"})
            self.assertEqual(metadata["requestId"], "d02/prepare")
            self.assertEqual(metadata["profile"]["sha256"], fact(profile)["sha256"])
            self.assertEqual(metadata["source"]["sha256"], fact(source)["sha256"])
            self.assertEqual(metadata["requiredGates"], ["structural"])

    def test_build_handler_preserves_output_confinement_and_metadata(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            request = root / "request.json"; request.write_text("{}")
            def execute(_request: Path, out: Path | None) -> dict:
                assert out is not None
                out.mkdir(parents=True, exist_ok=True)
                artifact = out / "artifact.bin"; artifact.write_bytes(b"artifact")
                return {
                    "status": "PASS",
                    "artifact": fact(artifact),
                    "plan": {"buildAdapter": "fake-adapter"},
                    "failures": [],
                }
            handler = BuildOperationHandler(execute)
            prepared = handler.prepare(operation_envelope("d02/build", "build", {"request": fact(request)}))
            roles, metadata = handler.produce(prepared.context, root / "out")
            self.assertEqual(roles["artifact"], "artifacts/artifact.bin")
            self.assertEqual(metadata["adapter"], "fake-adapter")

    def test_trust_material_and_handler_remain_exact_and_fail_closed(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            profile = root / "profile.json"; profile.write_text("{}")
            artifact = root / "artifact.bin"; artifact.write_bytes(b"artifact")
            policy = root / "policy.json"; policy.write_text("{}")
            bundle = root / "bundle.json"; bundle.write_text("{}")
            gate = root / "gate.vsa.json"; gate.write_text("{}")
            material = {
                "trustPolicy": fact(policy),
                "bundles": {"structural": fact(bundle)},
                "signerIds": {"structural": "signer-1"},
            }
            validated = validate_trust_material(material)
            self.assertEqual(validated["commitment"]["signerIds"], {"structural": "signer-1"})
            handler = TrustOperationHandler()
            op = operation_envelope(
                "d02/trust",
                "verify-trust",
                {
                    "profile": fact(profile),
                    "artifact": fact(artifact),
                    "gateVsas": {"structural": fact(gate)},
                    "trustMaterial": material,
                },
            )
            prepared = handler.prepare(op)
            fake = {"status": "PASS", "components": {"structural": {"status": "PASS"}}, "failures": []}
            with patch("artifact_operations.providers.trust.trust_vsa.aggregate_vsa_gates", return_value=fake), patch("artifact_operations.providers.trust.trust_vsa.default_trust_toolchain_config", return_value={}):
                roles, metadata = handler.produce(prepared.context, root / "out")
            self.assertEqual(roles, {"trustAggregation": "trusted-vsa-aggregation.json"})
            self.assertEqual(metadata["trustedGates"], ["structural"])
            broken = dict(material); broken["signerIds"] = {}
            with self.assertRaisesRegex(RuntimeError, "exactly match"):
                validate_trust_material(broken)

    def test_package_handler_preserves_local_unsigned_boundary_and_layout_roles(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            profile = root / "profile.json"; profile.write_text("{}")
            artifact = root / "artifact.bin"; artifact.write_bytes(b"artifact")
            report = root / "verify.json"; report.write_text("{}")
            handler = PackageOperationHandler()
            op = operation_envelope(
                "d02/package",
                "package",
                {
                    "profile": fact(profile),
                    "artifact": fact(artifact),
                    "verifyReport": fact(report),
                },
                {"allowLocalUnsignedDevelopment": True},
            )
            prepared = handler.prepare(op)
            self.assertTrue(prepared.context["local"])
            self.assertIsNone(prepared.context["trust"])
            def fake_stage(_profile, _artifact, _report, package, **kwargs):
                layout = package / "layout"
                (layout / "blobs/sha256").mkdir(parents=True, exist_ok=True)
                (layout / "index.json").write_text("{}")
                (layout / "oci-layout").write_text("{}")
                (layout / "blobs/sha256/abc").write_bytes(b"blob")
                self.assertTrue(kwargs["allow_local_unsigned"])
                return {
                    "status": "PASS",
                    "releaseReady": False,
                    "trustStanding": "LOCAL_UNSIGNED_DEVELOPMENT",
                    "oci": {"subject": {"digest": "sha256:subject"}, "discover": {"referrers": []}},
                    "failures": [],
                }
            with patch("artifact_operations.providers.package.execute_oci_package_stage", side_effect=fake_stage):
                roles, metadata = handler.produce(prepared.context, root / "out")
            self.assertEqual(roles["ociBlob:abc"], "package/layout/blobs/sha256/abc")
            self.assertFalse(metadata["releaseReady"])
            self.assertEqual(metadata["trustStanding"], "LOCAL_UNSIGNED_DEVELOPMENT")


if __name__ == "__main__":
    unittest.main()
