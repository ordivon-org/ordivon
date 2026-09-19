from __future__ import annotations

import sqlite3
import unittest
from pathlib import Path

import agent_service
from agent_service import failover
from agent_service.schema_migrations import apply_schema_migrations

ROOT = Path(__file__).resolve().parents[1]


class ReplaySafetyDecisionStoreEliminationR17Tests(unittest.TestCase):
    def test_specialized_replay_safety_store_table_and_surface_are_deleted(self) -> None:
        self.assertFalse(hasattr(failover, "ReplaySafetyDecisionStore"))
        self.assertFalse(hasattr(agent_service, "ReplaySafetyDecisionStore"))
        self.assertTrue(hasattr(failover, "ReplaySafetyDecision"))

        source = (ROOT / "agent_service" / "failover.py").read_text(encoding="utf-8")
        self.assertNotIn("CREATE TABLE IF NOT EXISTS replay_safety_decisions", source)
        self.assertNotIn("self.replay_safety_decisions", source)

    def test_replay_safety_decision_is_generic_event_projection(self) -> None:
        self.assertTrue(callable(failover._replay_safety_decision_get))
        self.assertTrue(callable(failover._replay_safety_decision_get_by_client_request))
        self.assertTrue(callable(failover._replay_safety_decision_create_in_transaction))

    def test_legacy_replay_safety_table_fails_closed(self) -> None:
        connection = sqlite3.connect(":memory:")
        connection.row_factory = sqlite3.Row
        self.addCleanup(connection.close)
        connection.execute("CREATE TABLE replay_safety_decisions(id TEXT PRIMARY KEY)")
        with self.assertRaisesRegex(RuntimeError, "legacy replay_safety_decisions"):
            apply_schema_migrations(connection)


if __name__ == "__main__":
    unittest.main()
