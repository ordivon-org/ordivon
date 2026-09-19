from __future__ import annotations

import sqlite3
import unittest
from pathlib import Path

import agent_service
import agent_service.remote_evidence as remote_evidence


ROOT = Path(__file__).resolve().parents[1]


class RemoteTaskVerificationStoreEliminationR15Tests(unittest.TestCase):
    def test_specialized_remote_verification_store_table_and_surface_are_deleted(self) -> None:
        self.assertFalse(hasattr(remote_evidence, "RemoteTaskVerificationStore"))
        self.assertFalse(hasattr(agent_service, "RemoteTaskVerificationStore"))
        self.assertTrue(hasattr(remote_evidence, "RemoteTaskVerificationRecord"))

        source = (ROOT / "agent_service" / "remote_evidence.py").read_text(encoding="utf-8")
        self.assertNotIn("CREATE TABLE IF NOT EXISTS remote_task_verifications", source)
        self.assertNotIn("self.remote_verifications", source)

    def test_remote_verification_record_is_generic_event_projection(self) -> None:
        self.assertTrue(callable(remote_evidence._remote_task_verification_get_by_task))
        self.assertTrue(callable(remote_evidence._remote_task_verification_create_in_transaction))

    def test_legacy_remote_verification_table_fails_closed(self) -> None:
        connection = sqlite3.connect(":memory:")
        connection.row_factory = sqlite3.Row
        self.addCleanup(connection.close)
        connection.execute("CREATE TABLE remote_task_verifications(id TEXT PRIMARY KEY)")
        with self.assertRaisesRegex(RuntimeError, "legacy remote_task_verifications"):
            remote_evidence._initialize_schema(connection)


if __name__ == "__main__":
    unittest.main()
