from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]
for path in (ROOT, REPO_ROOT / "studies" / "security" / "ai-redteam-foundry-r5"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from foundry_r5 import InMemorySyntheticWorld, SyntheticIdentity, SyntheticService, SyntheticWorldSpec  # noqa: E402
from foundry_r6 import EffectAttempt, ReferenceEffectProxy  # noqa: E402

D = lambda c: "sha256:" + c * 64


class SchemaContractTests(unittest.TestCase):
    def load(self, name: str) -> dict[str, object]:
        return json.loads((ROOT / "schemas" / name).read_text())

    def test_effect_attempt_schema_matches_serialization(self) -> None:
        world = InMemorySyntheticWorld(SyntheticWorldSpec("world:schema", (SyntheticIdentity("agent:test"),), (SyntheticService("svc:mail", "mail"),), ()))
        attempt = EffectAttempt("effect-1", "agent:test", D("1"), world.spec.digest, "synthetic_world", "svc:mail", "send", "sink@example.test", "hello")
        value = attempt.to_dict(); schema = self.load("effect-attempt.schema.json")
        self.assertEqual(set(schema["properties"]), set(value))

    def test_effect_receipt_schema_matches_serialization(self) -> None:
        world = InMemorySyntheticWorld(SyntheticWorldSpec("world:schema", (SyntheticIdentity("agent:test"),), (SyntheticService("svc:mail", "mail"),), ()))
        proxy = ReferenceEffectProxy(world)
        attempt = EffectAttempt("effect-1", "agent:test", D("1"), world.spec.digest, "synthetic_world", "svc:mail", "send", "sink@example.test", "hello")
        value = proxy.handle(attempt).to_dict(); schema = self.load("effect-receipt.schema.json")
        self.assertEqual(set(schema["properties"]), set(value))


if __name__ == "__main__":
    unittest.main()
