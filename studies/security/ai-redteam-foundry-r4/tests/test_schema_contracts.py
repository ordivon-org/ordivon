from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from foundry_r4 import (  # noqa: E402
    ExperimentEnvironmentSpec,
    IsolationVector,
    ResourceBudget,
    SandboxProviderBinding,
    SandboxRealizationReceipt,
    admit_environment,
    canonical_digest,
)

D = lambda c: "sha256:" + c * 64


def fixture() -> ExperimentEnvironmentSpec:
    return ExperimentEnvironmentSpec(
        environment_id="environment:schema-r4",
        threat_class="hostile_code",
        base_image_digest=D("1"),
        synthetic_world_digest=D("2"),
        tool_surface_digest=D("3"),
        observer_spec_digest=D("4"),
        isolation=IsolationVector(
            process="vm",
            kernel="separate_guest_kernel",
            filesystem="disposable_overlay",
            network="none",
            credentials="none",
            devices="none",
            external_effects="none",
            lifecycle="disposable",
            observer="independent",
        ),
        budget=ResourceBudget(60, 45, 1024, 2048, 128, 0),
        provider=SandboxProviderBinding(
            provider_id="sandbox-provider:schema",
            provider_revision="r1",
            provider_kind="libvirt-qemu-kvm",
            provider_evidence_digest=D("5"),
        ),
    )


class SchemaContractTests(unittest.TestCase):
    def schema(self, name: str) -> dict[str, object]:
        return json.loads((ROOT / "schemas" / name).read_text())

    def assert_exact_top_level(self, schema: dict[str, object], payload: dict[str, object]) -> None:
        properties = schema["properties"]
        self.assertIsInstance(properties, dict)
        self.assertEqual(set(properties), set(payload))
        self.assertTrue(set(schema["required"]).issubset(payload))

    def test_environment_schema_matches_serialization(self) -> None:
        payload = fixture().to_dict()
        schema = self.schema("experiment-environment.schema.json")
        self.assert_exact_top_level(schema, payload)
        self.assertEqual(set(schema["properties"]["isolation"]["properties"]), set(payload["isolation"]))
        self.assertEqual(set(schema["properties"]["budget"]["properties"]), set(payload["budget"]))
        self.assertEqual(set(schema["properties"]["provider"]["properties"]), set(payload["provider"]))

    def test_admission_schema_matches_serialization(self) -> None:
        payload = admit_environment(fixture()).to_dict()
        self.assert_exact_top_level(self.schema("sandbox-admission.schema.json"), payload)

    def test_realization_schema_matches_serialization(self) -> None:
        env = fixture()
        payload = SandboxRealizationReceipt(
            requested_environment_digest=env.digest,
            realized_provider_id=env.provider.provider_id,
            realized_provider_revision=env.provider.provider_revision,
            realized_base_image_digest=env.base_image_digest,
            realized_isolation_digest=canonical_digest(env.isolation.to_dict()),
            realization_evidence_digest=D("6"),
            disposable_instance_id="vm:schema-fixture",
        ).to_dict()
        self.assert_exact_top_level(self.schema("sandbox-realization-receipt.schema.json"), payload)


if __name__ == "__main__":
    unittest.main()
