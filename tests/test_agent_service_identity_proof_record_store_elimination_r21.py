from __future__ import annotations

import sqlite3
import unittest
from pathlib import Path

import agent_service
import agent_service.trust as trust


ROOT = Path(__file__).resolve().parents[1]


class IdentityProofRecordStoreEliminationR21Tests(unittest.TestCase):
    def test_specialized_identity_proof_store_table_and_surface_are_deleted(self) -> None:
        self.assertFalse(hasattr(trust, "IdentityProofRecordStore"))
        self.assertFalse(hasattr(agent_service, "IdentityProofRecordStore"))
        self.assertTrue(hasattr(trust, "IdentityProofRecord"))

        source = (ROOT / "agent_service" / "trust.py").read_text(encoding="utf-8")
        self.assertNotIn("CREATE TABLE IF NOT EXISTS identity_proof_records", source)
        self.assertNotIn("self.identity_proof_records", source)

    def test_identity_proof_is_generic_event_projection(self) -> None:
        self.assertTrue(callable(trust._identity_proof_record_get))
        self.assertTrue(callable(trust._identity_proof_record_get_by_client_request))
        self.assertTrue(callable(trust._identity_proof_record_create))

    def test_legacy_identity_proof_table_fails_closed(self) -> None:
        connection = sqlite3.connect(":memory:")
        connection.row_factory = sqlite3.Row
        self.addCleanup(connection.close)
        connection.execute("CREATE TABLE identity_proof_records(id TEXT PRIMARY KEY)")
        with self.assertRaisesRegex(RuntimeError, "legacy identity_proof_records"):
            trust._initialize_schema(connection)


if __name__ == "__main__":
    unittest.main()
