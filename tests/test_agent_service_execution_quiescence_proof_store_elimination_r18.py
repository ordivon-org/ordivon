from __future__ import annotations

import sqlite3
import unittest
from pathlib import Path

import agent_service
import agent_service.failover as failover


ROOT = Path(__file__).resolve().parents[1]


class ExecutionQuiescenceProofStoreEliminationR18Tests(unittest.TestCase):
    def test_specialized_quiescence_proof_store_table_and_surface_are_deleted(self) -> None:
        self.assertFalse(hasattr(failover, "ExecutionQuiescenceProofStore"))
        self.assertFalse(hasattr(agent_service, "ExecutionQuiescenceProofStore"))
        self.assertTrue(hasattr(failover, "ExecutionQuiescenceProofRecord"))
        self.assertTrue(hasattr(failover, "ExecutionQuiescenceRequestStore"))

        source = (ROOT / "agent_service" / "failover.py").read_text(encoding="utf-8")
        self.assertNotIn("CREATE TABLE IF NOT EXISTS execution_quiescence_proofs", source)
        self.assertNotIn("self.quiescence_proof_records", source)

    def test_quiescence_proof_is_generic_event_projection(self) -> None:
        self.assertTrue(callable(failover._execution_quiescence_proof_get))
        self.assertTrue(callable(failover._execution_quiescence_proof_get_by_client_request))
        self.assertTrue(callable(failover._execution_quiescence_proof_latest_for_binding))
        self.assertTrue(callable(failover._execution_quiescence_proof_create_in_transaction))

    def test_legacy_quiescence_proof_table_fails_closed(self) -> None:
        connection = sqlite3.connect(":memory:")
        connection.row_factory = sqlite3.Row
        self.addCleanup(connection.close)
        connection.execute("CREATE TABLE execution_quiescence_proofs(id TEXT PRIMARY KEY)")
        with self.assertRaisesRegex(RuntimeError, "legacy execution_quiescence_proofs"):
            failover.AgentServiceR12._initialize_schema(connection)


if __name__ == "__main__":
    unittest.main()
