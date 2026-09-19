from __future__ import annotations

import sqlite3
import unittest
from pathlib import Path

import agent_service
from agent_service import delivery
from agent_service.schema_migrations import apply_schema_migrations

ROOT = Path(__file__).resolve().parents[1]


class DeliveryReceiptStoreEliminationR12Tests(unittest.TestCase):
    def test_specialized_delivery_receipt_store_and_table_are_deleted(self) -> None:
        self.assertFalse(hasattr(delivery, "DeliveryReceiptStore"))
        self.assertFalse(hasattr(agent_service, "DeliveryReceiptStore"))
        self.assertTrue(hasattr(delivery, "DeliveryReceipt"))

        source = (ROOT / "agent_service" / "delivery.py").read_text(encoding="utf-8")
        self.assertNotIn("CREATE TABLE IF NOT EXISTS delivery_receipts", source)
        self.assertNotIn("self.delivery_receipts", source)

    def test_delivery_receipt_projection_reads_generic_event_journal(self) -> None:
        self.assertTrue(callable(delivery._delivery_receipt_get_by_binding))
        self.assertTrue(callable(delivery._delivery_receipt_create))

    def test_legacy_delivery_receipt_table_fails_closed(self) -> None:
        connection = sqlite3.connect(":memory:")
        connection.row_factory = sqlite3.Row
        self.addCleanup(connection.close)
        connection.execute("CREATE TABLE delivery_receipts(id TEXT PRIMARY KEY)")
        with self.assertRaisesRegex(RuntimeError, "legacy delivery_receipts"):
            apply_schema_migrations(connection)


if __name__ == "__main__":
    unittest.main()
