from __future__ import annotations

import sqlite3
import unittest
from pathlib import Path

import agent_service
import agent_service.transport_credentials as credentials
from agent_service.schema_migrations import apply_schema_migrations

ROOT = Path(__file__).resolve().parents[1]


class TransportCredentialBindingStoreEliminationR20Tests(unittest.TestCase):
    def test_specialized_binding_store_table_and_surface_are_deleted(self) -> None:
        self.assertFalse(hasattr(credentials, "TransportCredentialBindingStore"))
        self.assertFalse(hasattr(agent_service, "TransportCredentialBindingStore"))
        self.assertTrue(hasattr(credentials, "TransportCredentialBinding"))

        source = (ROOT / "agent_service" / "transport_credentials.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn(
            "CREATE TABLE IF NOT EXISTS transport_credential_bindings", source
        )
        self.assertNotIn("self.transport_credential_records", source)

    def test_transport_credential_binding_is_generic_event_projection(self) -> None:
        self.assertTrue(callable(credentials._transport_credential_binding_get))
        self.assertTrue(
            callable(credentials._transport_credential_binding_get_by_client_request)
        )
        self.assertTrue(
            callable(credentials._transport_credential_binding_list_for_binding)
        )
        self.assertTrue(
            callable(credentials._transport_credential_binding_create_in_transaction)
        )

    def test_legacy_transport_credential_binding_table_fails_closed(self) -> None:
        connection = sqlite3.connect(":memory:")
        connection.row_factory = sqlite3.Row
        self.addCleanup(connection.close)
        connection.execute(
            "CREATE TABLE transport_credential_bindings(id TEXT PRIMARY KEY)"
        )
        with self.assertRaisesRegex(RuntimeError, "legacy transport_credential_bindings"):
            apply_schema_migrations(connection)


if __name__ == "__main__":
    unittest.main()
