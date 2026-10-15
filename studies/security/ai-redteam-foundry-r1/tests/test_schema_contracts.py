from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from foundry import (  # noqa: E402
    AttackCandidate,
    AttackSpec,
    HardenedMockTarget,
    ThreatModel,
    VulnerableMockTarget,
    run_attack,
    verify_patch,
)


class SchemaContractTests(unittest.TestCase):
    def load_schema(self, name: str) -> dict[str, object]:
        return json.loads((ROOT / "schemas" / name).read_text())

    def setUp(self) -> None:
        self.threat = ThreatModel(
            threat_model_id="tm-schema-r1",
            attacker_knowledge="gray-box",
            access="synthetic",
            adaptive=True,
            state_scope="run",
            success_object="invariant-violation",
        )
        self.attack = AttackSpec(
            attack_id="schema-attack",
            family="indirect_injection",
            budget=1,
            seed=99,
            candidates=(
                AttackCandidate(
                    candidate_id="schema-c1",
                    family="indirect_injection",
                    channel="untrusted_tool",
                    operation="request_canary",
                ),
            ),
        )

    def assert_schema_keys_match(self, schema: dict[str, object], payload: dict[str, object]) -> None:
        properties = schema["properties"]
        self.assertIsInstance(properties, dict)
        self.assertEqual(set(properties), set(payload))
        required = schema["required"]
        self.assertTrue(set(required).issubset(payload))

    def test_attack_spec_schema_matches_dataclass_serialization(self) -> None:
        schema = self.load_schema("attack-spec.schema.json")
        payload = asdict(self.attack)
        payload["candidates"] = [asdict(candidate) for candidate in self.attack.candidates]
        self.assert_schema_keys_match(schema, payload)
        candidate_schema = schema["properties"]["candidates"]["items"]
        self.assertEqual(set(candidate_schema["properties"]), set(payload["candidates"][0]))

    def test_finding_schema_matches_emitted_finding(self) -> None:
        schema = self.load_schema("finding.schema.json")
        finding = run_attack(VulnerableMockTarget(), self.threat, self.attack)
        self.assertIsNotNone(finding)
        assert finding is not None
        self.assert_schema_keys_match(schema, finding.to_dict())

    def test_regression_receipt_schema_matches_emitted_receipt(self) -> None:
        schema = self.load_schema("regression-receipt.schema.json")
        finding = run_attack(VulnerableMockTarget(), self.threat, self.attack)
        self.assertIsNotNone(finding)
        assert finding is not None
        receipt = verify_patch(
            original_finding=finding,
            repaired_target_factory=HardenedMockTarget,
            threat_model=self.threat,
            original_attack=self.attack,
            adaptive_attacks=[self.attack],
            patch_owner="synthetic-control-data-boundary",
        )
        self.assert_schema_keys_match(schema, receipt.to_dict())


if __name__ == "__main__":
    unittest.main()
