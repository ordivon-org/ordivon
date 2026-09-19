import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments/browser-security-r4/cf07_metadata_snapshot.py"
)
SPEC = importlib.util.spec_from_file_location("cf07_metadata_snapshot", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
snapshot = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(snapshot)


class Cf07MetadataSnapshotTests(unittest.TestCase):
    def test_file_age_summary_is_count_and_age_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = root / "a"
            b = root / "b"
            a.write_text("secret-a")
            b.write_text("secret-b")
            result = snapshot._file_age_summary(
                [a, b], now=max(a.stat().st_mtime, b.stat().st_mtime) + 10
            )
        self.assertEqual(result["count"], 2)
        self.assertIn("newestAgeSeconds", result)
        self.assertIn("oldestAgeSeconds", result)
        self.assertNotIn("secret-a", str(result))
        self.assertNotIn("secret-b", str(result))

    def test_percentile_is_deterministic(self) -> None:
        self.assertEqual(snapshot._percentile([], 0.9), None)
        self.assertEqual(snapshot._percentile([5.0], 0.9), 5.0)
        self.assertAlmostEqual(snapshot._percentile([1.0, 2.0, 3.0, 4.0], 0.5), 2.5)

    def test_forbidden_data_classes_cover_content_bearing_sources(self) -> None:
        text = " ".join(snapshot.FORBIDDEN_DATA_CLASSES)
        for required in (
            "cookie values",
            "prompt text",
            "turn text",
            "handoff URLs",
            "SQLite request_json",
            "SQLite detail",
            "SQLite provider_coordinate",
            "provider page content",
        ):
            self.assertIn(required, text)

    def test_ledger_query_source_does_not_select_content_columns(self) -> None:
        source = MODULE_PATH.read_text(encoding="utf-8")
        self.assertIn(
            "SELECT standing,effect_generation,created_at_ms,updated_at_ms",
            source,
        )
        self.assertNotIn("SELECT request_json", source)
        self.assertNotIn("SELECT detail", source)
        self.assertNotIn("SELECT provider_coordinate", source)


if __name__ == "__main__":
    unittest.main()
