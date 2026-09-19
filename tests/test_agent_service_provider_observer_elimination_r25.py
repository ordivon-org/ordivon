from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import agent_service.slice1 as slice1


class WrongPlacementCarrier:
    def ensure(self, placement_id: str, agent_instance_id: str, revision_id: str) -> None:
        return None

    def retire(self, placement_id: str, agent_instance_id: str) -> None:
        return None

    def observe(self, placement_id: str) -> slice1.ProviderObservation:
        return slice1.ProviderObservation(
            placement_id="wrong-placement",
            state="READY",
            evidence_ref="test://wrong-placement",
        )


class ProviderObserverEliminationR25Tests(unittest.TestCase):
    def test_provider_observer_class_and_facade_are_deleted(self) -> None:
        self.assertFalse(hasattr(slice1, "ProviderObserver"))
        source = Path(slice1.__file__).read_text(encoding="utf-8")
        self.assertNotIn("self.observer =", source)

    def test_placement_identity_still_fails_closed_before_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = slice1.AgentServiceSlice1.open(
                Path(tmp) / "service.db",
                carrier_adapter=WrongPlacementCarrier(),
            )
            self.addCleanup(service.close)
            definition = service.definitions.create("wrong-placement-worker")
            revision = service.revisions.create(definition.id, {"harness": "test"})
            instance = service.instances.create("request:wrong-placement", revision.id)
            placement = service.placements.get_by_instance(instance.id)
            assert placement is not None

            with self.assertRaisesRegex(ValueError, "observation placement identity mismatch"):
                service.reconciler.reconcile(instance.id)

            after = service.placements.get(placement.id)
            self.assertEqual(after.observed_state, "UNKNOWN")
            self.assertIsNone(after.evidence_ref)


if __name__ == "__main__":
    unittest.main()
