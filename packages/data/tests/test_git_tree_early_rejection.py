"""Invalid early tree rows must not materialize an unexamined wire tail."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "packages/data/src"))

from ordivon_data.git_tree import qualify_tree_listing


class GitTreeEarlyRejectionTests(unittest.TestCase):
    def test_first_invalid_row_does_not_split_entire_wire(self):
        class Wire(bytes):
            def split(self, *args, **kwargs):
                raise AssertionError("whole wire materialized before row qualification")

            def find(self, *args, **kwargs):
                self.observed_find += 1
                return super().find(*args, **kwargs)

        for algorithm, width in (("sha1", 40), ("sha256", 64)):
            for prefix in (b"\0", b"malformed\0"):
                with self.subTest(algorithm=algorithm, prefix=prefix):
                    wire = Wire(prefix + b"x\0" * 1_000_000)
                    wire.observed_find = 0
                    with self.assertRaisesRegex(
                        ValueError, "incomplete Git tree listing"
                    ):
                        qualify_tree_listing(wire, "a" * width, algorithm)
                    self.assertEqual(wire.observed_find, 1)
