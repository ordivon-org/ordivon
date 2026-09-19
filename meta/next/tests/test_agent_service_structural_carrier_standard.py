from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import agent_service
from agent_service.carriers.agent_automation import AgentAutomationCarrierAdapter
from agent_service.slice1 import ProviderObservation
from tests.agent_service_test_support import open_current


class PlainCarrier:
    def ensure(self, placement_id: str, agent_instance_id: str, revision_id: str) -> None:
        return None

    def retire(self, placement_id: str, agent_instance_id: str) -> None:
        return None

    def observe(self, placement_id: str) -> ProviderObservation:
        return ProviderObservation(placement_id, "UNKNOWN", None)


class StructuralCarrierStandardTests(unittest.TestCase):
    def test_provider_contract_is_structural_not_nominal(self) -> None:
        self.assertFalse(hasattr(agent_service, "CarrierProviderAdapter"))
        self.assertFalse(hasattr(agent_service, "HostAdapter"))
        self.assertEqual(AgentAutomationCarrierAdapter.__bases__, (object,))

        with tempfile.TemporaryDirectory() as tmp:
            service = open_current(
                Path(tmp) / "service.db",
                carrier_adapter=PlainCarrier(),
            )
            service.close()

    def test_incomplete_provider_fails_before_database_creation(self) -> None:
        class MissingObserve:
            def ensure(self, placement_id, agent_instance_id, revision_id):
                return None

            def retire(self, placement_id, agent_instance_id):
                return None

        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "service.db"
            with self.assertRaises(TypeError):
                open_current(db, carrier_adapter=MissingObserve())
            self.assertFalse(db.exists())

    def test_retired_host_adapter_keyword_is_not_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, self.assertRaises(TypeError):
            open_current(
                Path(tmp) / "service.db",
                host_adapter=PlainCarrier(),
            )


if __name__ == "__main__":
    unittest.main()
