from __future__ import annotations

import sqlite3
import unittest
from pathlib import Path

from agent_service import goals
from agent_service.schema_migrations import apply_schema_migrations

ROOT = Path(__file__).resolve().parents[1]


class BoardProjectionReceiptStoreEliminationR13Tests(unittest.TestCase):
    def test_specialized_board_projection_store_and_table_are_deleted(self) -> None:
        self.assertFalse(hasattr(goals, "BoardProjectionReceiptStore"))
        self.assertTrue(hasattr(goals, "BoardProjectionReceipt"))

        source = (ROOT / "agent_service" / "goals.py").read_text(encoding="utf-8")
        self.assertNotIn("CREATE TABLE IF NOT EXISTS board_projection_receipts", source)
        self.assertNotIn("self.board_receipts", source)

    def test_board_projection_receipt_is_event_projection(self) -> None:
        self.assertTrue(callable(goals._board_projection_receipt_get_by_event))
        self.assertTrue(callable(goals._board_projection_receipt_create))

    def test_legacy_board_projection_table_fails_closed(self) -> None:
        connection = sqlite3.connect(":memory:")
        connection.row_factory = sqlite3.Row
        self.addCleanup(connection.close)
        connection.execute("CREATE TABLE board_projection_receipts(id TEXT PRIMARY KEY)")
        with self.assertRaisesRegex(RuntimeError, "legacy board_projection_receipts"):
            apply_schema_migrations(connection)


if __name__ == "__main__":
    unittest.main()
