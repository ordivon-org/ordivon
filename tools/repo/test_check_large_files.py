"""Tracked-file size guard: unlisted large files, growth and stale entries fail."""
from __future__ import annotations

import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("check_large_files.py")
SPEC = importlib.util.spec_from_file_location("check_large_files", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)

LIMIT = 100


class CheckTests(unittest.TestCase):
    def test_small_files_pass(self) -> None:
        self.assertEqual(module.check({"a": 100, "b": 1}, LIMIT, {}), [])

    def test_unlisted_large_file_fails(self) -> None:
        errors = module.check({"big.bin": 101}, LIMIT, {})
        self.assertEqual(len(errors), 1)
        self.assertIn("big.bin", errors[0])

    def test_listed_file_within_max_passes(self) -> None:
        self.assertEqual(module.check({"big.bin": 150}, LIMIT, {"big.bin": 150}), [])

    def test_listed_file_that_grew_fails(self) -> None:
        errors = module.check({"big.bin": 151}, LIMIT, {"big.bin": 150})
        self.assertEqual(len(errors), 1)
        self.assertIn("grew", errors[0])

    def test_stale_entry_for_missing_file_fails(self) -> None:
        errors = module.check({}, LIMIT, {"gone.bin": 150})
        self.assertEqual(len(errors), 1)
        self.assertIn("stale", errors[0])

    def test_stale_entry_for_shrunk_file_fails(self) -> None:
        errors = module.check({"small.bin": 50}, LIMIT, {"small.bin": 150})
        self.assertEqual(len(errors), 1)
        self.assertIn("stale", errors[0])


class AllowlistTests(unittest.TestCase):
    def write(self, text: str) -> Path:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        path = Path(temp.name) / "allow.toml"
        path.write_text(text, encoding="utf-8")
        return path

    def test_valid_allowlist(self) -> None:
        path = self.write(
            'limit_bytes = 10\n[[file]]\npath = "a"\nmax_bytes = 20\nreason = "why"\n'
        )
        self.assertEqual(module.load_allowlist(path), (10, {"a": 20}))

    def test_reason_is_required(self) -> None:
        path = self.write('limit_bytes = 10\n[[file]]\npath = "a"\nmax_bytes = 20\n')
        with self.assertRaises(module.AllowlistError):
            module.load_allowlist(path)

    def test_duplicate_path_is_rejected(self) -> None:
        entry = '[[file]]\npath = "a"\nmax_bytes = 20\nreason = "why"\n'
        path = self.write("limit_bytes = 10\n" + entry + entry)
        with self.assertRaises(module.AllowlistError):
            module.load_allowlist(path)

    def test_limit_must_be_positive(self) -> None:
        path = self.write("limit_bytes = 0\n")
        with self.assertRaises(module.AllowlistError):
            module.load_allowlist(path)


class TrackedSizesTests(unittest.TestCase):
    def test_only_tracked_regular_files_are_measured(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            subprocess.check_call(["git", "init", "-q", str(root)])
            (root / "tracked.bin").write_bytes(b"x" * 7)
            (root / "untracked.bin").write_bytes(b"x" * 9)
            (root / "link").symlink_to("tracked.bin")
            subprocess.check_call(["git", "-C", str(root), "add", "tracked.bin", "link"])
            self.assertEqual(module.tracked_sizes(root), {"tracked.bin": 7})


class CurrentTreeTests(unittest.TestCase):
    def test_current_tree_satisfies_the_allowlist(self) -> None:
        limit, allowed = module.load_allowlist(module.ALLOWLIST)
        self.assertEqual(module.check(module.tracked_sizes(module.ROOT), limit, allowed), [])


if __name__ == "__main__":
    unittest.main()
