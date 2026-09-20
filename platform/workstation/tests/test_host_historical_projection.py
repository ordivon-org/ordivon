import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "host_historical_projection.py"


class HostHistoricalProjectionContractTests(unittest.TestCase):
    def test_projection_is_explicitly_non_authoritative_and_has_all_source_tables(self) -> None:
        text = SCRIPT.read_text()
        expected = {
            "host_metadata", "object_refs", "object_validation", "legacy_object_refs",
            "streams", "events", "event_object_refs", "task_projection",
            "task_extension_state", "task_head_validation", "leases", "board_messages",
            "news_editions", "news_publications", "schema_migrations",
        }
        constants = {n.value for n in ast.walk(ast.parse(text)) if isinstance(n, ast.Constant) and isinstance(n.value, str)}
        self.assertTrue(expected <= constants)
        self.assertIn('"duckdbIsHostAuthority": False', text)
        self.assertIn('"parquetIsHostAuthority": False', text)
        self.assertIn('"postgresRequiredForHistoricalQuery": False', text)
        self.assertNotIn('TableSpec("migration_receipts"', text)

    def test_two_way_row_equivalence_and_destructive_rebuild_are_required(self) -> None:
        text = SCRIPT.read_text()
        self.assertIn("EXCEPT ALL", text)
        self.assertIn("source_minus_projection", text)
        self.assertIn("projection_minus_source", text)
        self.assertIn("shutil.rmtree(destination)", text)
        self.assertIn("derivedProjectionCanBeDeletedAndRebuilt", text)
        self.assertIn("Recreate the catalog only", text)
        self.assertIn("final-path DuckDB catalog differs", text)


if __name__ == "__main__":
    unittest.main()
