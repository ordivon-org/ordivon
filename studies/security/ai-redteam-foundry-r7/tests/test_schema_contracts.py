from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]
for path in (
    ROOT,
    REPO_ROOT / "studies" / "security" / "ai-redteam-foundry-r5",
    REPO_ROOT / "studies" / "security" / "ai-redteam-foundry-r6",
):
    sys.path.insert(0, str(path))

from foundry_r5 import InMemorySyntheticWorld, SyntheticIdentity, SyntheticService, SyntheticWorldSpec  # noqa: E402
from foundry_r6 import EffectAttempt, ReferenceEffectProxy  # noqa: E402
from foundry_r7 import SyntheticWorldObserver, reconcile_receipt  # noqa: E402

ENV = "sha256:" + "a" * 64


class SchemaContractTests(unittest.TestCase):
    def schema(self, name: str) -> dict[str, object]:
        return json.loads((ROOT / "schemas" / name).read_text())

    def assert_exact_top_level(self, schema: dict[str, object], payload: dict[str, object]) -> None:
        self.assertEqual(set(schema["properties"]), set(payload))
        self.assertTrue(set(schema["required"]).issubset(payload))

    def fixture(self):
        world = InMemorySyntheticWorld(
            SyntheticWorldSpec(
                world_id="world:r7-schema",
                identities=(SyntheticIdentity("agent:test"),),
                services=(SyntheticService("mail:test", "mail"),),
                resources=(),
            )
        )
        observer = SyntheticWorldObserver()
        anchor = observer.start(world, environment_digest=ENV)
        request = EffectAttempt(
            effect_id="effect:r7-schema",
            actor_id="agent:test",
            environment_digest=ENV,
            world_spec_digest=world.spec.digest,
            scope="synthetic_world",
            service_id="mail:test",
            operation="send",
            target="sink@example.test",
            content="schema",
        )
        receipt = ReferenceEffectProxy(world).handle(request)
        observation = observer.finish(anchor, world, effect_id=request.effect_id, effect_request_digest=request.digest)
        return receipt, observation

    def test_observation_schema_matches_serialization(self) -> None:
        _, observation = self.fixture()
        self.assert_exact_top_level(self.schema("consequence-observation.schema.json"), observation.to_dict())

    def test_consistency_schema_matches_serialization(self) -> None:
        receipt, observation = self.fixture()
        consistency = reconcile_receipt(receipt, observation)
        self.assert_exact_top_level(self.schema("receipt-observation-consistency.schema.json"), consistency.to_dict())


if __name__ == "__main__":
    unittest.main()
