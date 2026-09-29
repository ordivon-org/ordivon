from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from foundry_r2 import (  # noqa: E402
    EvaluationTargetBinding,
    ModelRequestBinding,
    RealizedTargetBinding,
    TargetBoundObservation,
)

D1 = "sha256:" + "1" * 64
D2 = "sha256:" + "2" * 64
D3 = "sha256:" + "3" * 64
D4 = "sha256:" + "4" * 64
D5 = "sha256:" + "5" * 64
D6 = "sha256:" + "6" * 64


def requested() -> EvaluationTargetBinding:
    return EvaluationTargetBinding(
        security_subject_ref="security-subject:schema-fixture",
        security_subject_revision="rev-schema-001",
        target_kind="agent",
        model=ModelRequestBinding("provider", "model-x", provider_model_revision="rev-x"),
        harness_revision="harness-schema-001",
        harness_config_digest=D1,
        instruction_bundle_digest=D2,
        tool_catalog_digest=D3,
        authority_surface_digest=D4,
        monitor_bundle_digest=D5,
        environment_digest=D6,
        adapter_id="adapter.schema",
        adapter_revision="adapter-schema-001",
        generation={"temperature": 0.0, "max_tokens": 512},
    )


class SchemaContractTests(unittest.TestCase):
    def load(self, name: str) -> dict[str, object]:
        return json.loads((ROOT / "schemas" / name).read_text())

    def assert_exact_keys(self, schema: dict[str, object], value: dict[str, object]) -> None:
        properties = schema["properties"]
        self.assertIsInstance(properties, dict)
        self.assertEqual(set(properties), set(value))
        self.assertTrue(set(schema["required"]).issubset(value))

    def test_evaluation_target_schema_matches_serialization(self) -> None:
        value = requested().to_dict()
        schema = self.load("evaluation-target-binding.schema.json")
        self.assert_exact_keys(schema, value)
        self.assertEqual(set(schema["properties"]["model"]["properties"]), set(value["model"]))

    def test_realized_target_schema_matches_serialization(self) -> None:
        req = requested()
        value = RealizedTargetBinding(
            req.digest,
            "model-x",
            D1,
            provider_model_revision="rev-x",
            provider_system_fingerprint="fp_schema",
        ).to_dict()
        schema = self.load("realized-target-binding.schema.json")
        self.assert_exact_keys(schema, value)

    def test_observation_schema_matches_serialization(self) -> None:
        req = requested()
        realized = RealizedTargetBinding(req.digest, "model-x", D1, provider_model_revision="rev-x")
        value = TargetBoundObservation(realized.digest, D2, D3, D4, D5).to_dict()
        schema = self.load("target-bound-observation.schema.json")
        self.assert_exact_keys(schema, value)


if __name__ == "__main__":
    unittest.main()
