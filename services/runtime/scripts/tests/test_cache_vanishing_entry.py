"""Fault injection for an evolving cache tree during retention measurement."""

import runpy
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
MEASURE = runpy.run_path(str(ROOT / "ordivon-runtime-cache"))["cache_retention_measurement"]


class VanishingCacheEntryTests(unittest.TestCase):
    @staticmethod
    def exercise(failure: type[OSError]) -> dict[str, object]:
        class Entry:
            def is_symlink(self):
                return False

            def is_dir(self, follow_symlinks=False):
                return False

            def is_file(self, follow_symlinks=False):
                raise failure("injected race")

        @contextmanager
        def directory_scan(_path):
            yield [Entry()]

        with tempfile.TemporaryDirectory() as tmp, patch("os.scandir", side_effect=directory_scan):
            return MEASURE(Path(tmp))

    def test_removed_cache_entry_during_scan_is_not_permanent_storage_failure(self):
        result = self.exercise(FileNotFoundError)
        self.assertEqual(result["standing"], "measured")
        self.assertEqual(result["errors"], 0)
        self.assertEqual(result["bytes"], 0)

    def test_permission_denied_during_scan_remains_fail_closed(self):
        result = self.exercise(PermissionError)
        self.assertEqual(result["standing"], "incomplete")
        self.assertEqual(result["errors"], 1)
        self.assertIsNone(result["bytes"])

    @staticmethod
    def exercise_queued_directory(failure: type[OSError]) -> dict[str, object]:
        class Entry:
            def __init__(self, path: Path):
                self.path = str(path)

            def is_symlink(self):
                return False

            def is_dir(self, follow_symlinks=False):
                return True

        @contextmanager
        def directory_scan(path):
            if Path(path) == Path(tmp):
                yield [Entry(Path(tmp) / "removed")]
            else:
                raise failure("queued directory vanished or became inaccessible")

        with tempfile.TemporaryDirectory() as tmp, patch("os.scandir", side_effect=directory_scan):
            return MEASURE(Path(tmp))

    def test_queued_directory_removed_after_scan_is_not_permanent_storage_failure(self):
        result = self.exercise_queued_directory(FileNotFoundError)
        self.assertEqual(result["standing"], "measured")
        self.assertEqual(result["errors"], 0)
        self.assertEqual(result["bytes"], 0)

    def test_queued_directory_permission_denied_remains_incomplete(self):
        result = self.exercise_queued_directory(PermissionError)
        self.assertEqual(result["standing"], "incomplete")
        self.assertEqual(result["errors"], 1)
        self.assertIsNone(result["bytes"])


if __name__ == "__main__":
    unittest.main()
