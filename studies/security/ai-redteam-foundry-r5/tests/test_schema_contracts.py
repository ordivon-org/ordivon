from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from foundry_r5 import InMemorySyntheticWorld, SyntheticIdentity, SyntheticService, SyntheticWorldSpec  # noqa: E402


class SchemaContractTests(unittest.TestCase):
    def load(self, name: str) -> dict[str, object]:
        return json.loads((ROOT / "schemas" / name).read_text())

    def test_world_spec_schema_matches_serialization(self) -> None:
        value = SyntheticWorldSpec(
            "world:schema",
            (SyntheticIdentity("agent:test"),),
            (SyntheticService("svc:files", "files"),),
            (),
        ).to_dict()
        schema = self.load("synthetic-world-spec.schema.json")
        self.assertEqual(set(schema["properties"]), set(value))
        self.assertTrue(set(schema["required"]).issubset(value))

    def test_receipt_schema_matches_serialization(self) -> None:
        world = InMemorySyntheticWorld(SyntheticWorldSpec("world:schema", (SyntheticIdentity("agent:test"),), (SyntheticService("svc:files", "files"),), ()))
        value = world.receipt().to_dict()
        schema = self.load("world-state-receipt.schema.json")
        self.assertEqual(set(schema["properties"]), set(value))
        self.assertTrue(set(schema["required"]).issubset(value))


if __name__ == "__main__":
    unittest.main()
