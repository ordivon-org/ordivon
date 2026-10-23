"""Performance CDC: one candidate tree traversal preserves retention semantics."""
import os
import runpy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
CACHE = runpy.run_path(str(ROOT / "ordivon-runtime-cache"))


class SingleWalkTests(unittest.TestCase):
    def test_candidate_size_and_mtime_from_one_walk_without_path_rglob(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "cache" / "build"
            child = root / "workspace-closed"
            nested = child / "nested"
            nested.mkdir(parents=True)
            (child / "alpha").write_bytes(b"abcd")
            (nested / "beta").write_bytes(b"hello")
            os.link(child / "alpha", child / "alpha-hardlink")
            (child / "symlink").symlink_to(nested / "beta")
            # The candidate and its children have distinct mtimes.
            os.utime(child / "alpha", (1_700_000_001, 1_700_000_001))
            os.utime(nested / "beta", (1_700_000_012, 1_700_000_012))
            os.utime(child / "symlink", (1_700_000_002, 1_700_000_002), follow_symlinks=False)
            os.utime(nested, (1_700_000_004, 1_700_000_004))
            os.utime(child, (1_700_000_005, 1_700_000_005))
            expected_bytes = 4 + 4 + 5 + (child / "symlink").lstat().st_size
            with patch.object(Path, "rglob", side_effect=AssertionError("redundant path walk")):
                result = CACHE["measure_candidate"](child)
            self.assertEqual(result["bytes"], expected_bytes)
            self.assertEqual(result["modifiedUnixMs"], 1_700_000_012_000)

    def test_permission_failure_still_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            with patch.object(CACHE["os"], "scandir", side_effect=PermissionError("DENY")):
                with self.assertRaisesRegex(RuntimeError, "incomplete"):
                    CACHE["measure_candidate"](p)


if __name__ == "__main__":
    unittest.main()
