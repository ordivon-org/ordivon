from __future__ import annotations

import sqlite3
import unittest

from agent_service.schema_migrations import apply_schema_migrations
from pathlib import Path

import agent_service
import agent_service.failover as failover


ROOT = Path(__file__).resolve().parents[1]


class ExecutionClaimTransferStoreEliminationR16Tests(unittest.TestCase):
    def test_specialized_claim_transfer_store_table_and_surface_are_deleted(self) -> None:
        self.assertFalse(hasattr(failover, "ExecutionClaimTransferStore"))
        self.assertFalse(hasattr(agent_service, "ExecutionClaimTransferStore"))
        self.assertTrue(hasattr(failover, "ExecutionClaimTransferRecord"))

        source = (ROOT / "agent_service" / "failover.py").read_text(encoding="utf-8")
        self.assertNotIn("CREATE TABLE IF NOT EXISTS execution_claim_transfers", source)
        self.assertNotIn("self.claim_transfer_records", source)

    def test_claim_transfer_record_is_generic_event_projection(self) -> None:
        self.assertTrue(callable(failover._execution_claim_transfer_get_by_client_request))
        self.assertTrue(callable(failover._execution_claim_transfer_create_in_transaction))
        self.assertTrue(callable(failover._execution_claim_transfer_has_binding_history))

    def test_legacy_claim_transfer_table_fails_closed(self) -> None:
        connection = sqlite3.connect(":memory:")
        connection.row_factory = sqlite3.Row
        self.addCleanup(connection.close)
        connection.execute("CREATE TABLE execution_claim_transfers(id TEXT PRIMARY KEY)")
        with self.assertRaisesRegex(RuntimeError, "legacy execution_claim_transfers"):
            apply_schema_migrations(connection)


if __name__ == "__main__":
    unittest.main()
