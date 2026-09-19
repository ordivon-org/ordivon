from __future__ import annotations

import sqlite3
import unittest
from pathlib import Path

import agent_service
import agent_service.trust as trust


ROOT = Path(__file__).resolve().parents[1]


class RemoteDeliveryObservationStoreEliminationR19Tests(unittest.TestCase):
    def test_specialized_remote_observation_store_table_and_surface_are_deleted(self) -> None:
        self.assertFalse(hasattr(trust, "RemoteDeliveryObservationStore"))
        self.assertFalse(hasattr(agent_service, "RemoteDeliveryObservationStore"))
        self.assertTrue(hasattr(trust, "RemoteDeliverySnapshot"))

        source = (ROOT / "agent_service" / "trust.py").read_text(encoding="utf-8")
        self.assertNotIn("CREATE TABLE IF NOT EXISTS remote_delivery_observations", source)
        self.assertNotIn("self.remote_observations", source)

    def test_remote_observation_is_generic_event_stream_projection(self) -> None:
        self.assertTrue(callable(trust._remote_delivery_observation_list_for_binding))
        self.assertTrue(callable(trust._remote_delivery_observation_latest_for_binding))
        self.assertTrue(callable(trust._remote_delivery_observation_record))

    def test_legacy_remote_observation_table_fails_closed(self) -> None:
        connection = sqlite3.connect(":memory:")
        connection.row_factory = sqlite3.Row
        self.addCleanup(connection.close)
        connection.execute("CREATE TABLE remote_delivery_observations(id TEXT PRIMARY KEY)")
        with self.assertRaisesRegex(RuntimeError, "legacy remote_delivery_observations"):
            trust._initialize_schema(connection)


if __name__ == "__main__":
    unittest.main()
