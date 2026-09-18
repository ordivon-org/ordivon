from __future__ import annotations

import sqlite3
import unittest
from pathlib import Path

import agent_service.evidence as evidence


ROOT = Path(__file__).resolve().parents[1]


class VerificationRecordStoreEliminationR14Tests(unittest.TestCase):
    def test_specialized_verification_store_table_and_service_surface_are_deleted(self) -> None:
        self.assertFalse(hasattr(evidence, "VerificationRecordStore"))
        self.assertTrue(hasattr(evidence, "VerificationRecord"))

        source = (ROOT / "agent_service" / "evidence.py").read_text(encoding="utf-8")
        self.assertNotIn("CREATE TABLE IF NOT EXISTS task_verifications", source)
        self.assertNotIn("self.verifications", source)

    def test_verification_record_is_generic_event_projection(self) -> None:
        self.assertTrue(callable(evidence._verification_record_get_by_assignment))
        self.assertTrue(callable(evidence._verification_record_create_in_transaction))

    def test_legacy_verification_table_fails_closed(self) -> None:
        connection = sqlite3.connect(":memory:")
        connection.row_factory = sqlite3.Row
        self.addCleanup(connection.close)
        connection.execute("CREATE TABLE task_verifications(id TEXT PRIMARY KEY)")
        with self.assertRaisesRegex(RuntimeError, "legacy task_verifications"):
            evidence.AgentServiceR6._initialize_schema(connection)


if __name__ == "__main__":
    unittest.main()
