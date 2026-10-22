"""Prove root/eligible/protected/package portions are measured exactly once."""
from pathlib import Path
import os
import runpy
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
CACHE = runpy.run_path(str(ROOT / "ordivon-runtime-cache"))


class RootTraversalContract(unittest.TestCase):
    def test_single_root_walk_keeps_unclaimed_and_protected_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Path(tmp)
            cache = store / "cache"
            closed = cache / "build" / "closed"
            protected = cache / "workspaces" / "open"
            shared = cache / "shared" / "uv"
            legacy = cache / "build" / "sources" / "source-key"
            for child in (closed, protected, shared, legacy):
                child.mkdir(parents=True)
            (closed / "first").write_bytes(b"aaaa")
            os.link(closed / "first", closed / "link")
            (protected / "still-in-use").write_bytes(b"bbb")
            (shared / "registry").write_bytes(b"cc")
            (legacy / "reproducible").write_bytes(b"d")
            (cache / "orphan").write_bytes(b"xyz")
            expected = 4 + 4 + 3 + 2 + 1 + 3
            original_bytes = CACHE["directory_bytes"]
            with (
                patch.dict(CACHE["cache_prune_candidates"].__globals__, {
                    "active_workspace_ids": lambda _db: set(),
                    "load_open_records": lambda _root: ([{"workspaceId":"open", "sourceRepo":str(store)}], []),
                    "workspace_activity_markers": lambda _db: {},
                }),
                patch.dict(CACHE["inspect"].__globals__, {
                    "active_workspace_ids": lambda _db: set(),
                    "load_open_records": lambda _root: ([{"workspaceId":"open", "sourceRepo":str(store)}], []),
                    "workspace_activity_markers": lambda _db: {},
                }),
                patch.dict(CACHE["cache_prune_candidates"].__globals__, {
                    "directory_bytes": lambda path: (
                        (_ for _ in ()).throw(AssertionError("recursive global rescan forbidden"))
                        if Path(path) == cache
                        else original_bytes(path)
                    ),
                }),
            ):
                total, candidates = CACHE["cache_prune_candidates"](
                    store / "fake-registry.sqlite3", store, include_idle_open_build=True
                )
            self.assertEqual(total, expected)
            by_path = {Path(item["path"]): item for item in candidates}
            self.assertEqual(by_path[closed]["bytes"], 8)
            self.assertEqual(by_path[legacy]["bytes"], 1)
            self.assertNotIn(protected, by_path)
            self.assertNotIn(shared, by_path)


if __name__ == "__main__":
    unittest.main()
