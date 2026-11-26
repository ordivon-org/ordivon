"""Independent native Git fixtures challenge whole-row omission and substitution."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "packages/data/src"))

from ordivon_data import git_sources


class GitListingCommitmentTests(unittest.TestCase):
    def test_listing_is_bound_to_root_and_every_direct_tree(self):
        for fmt in ("sha1", "sha256"):
            with self.subTest(fmt=fmt), TemporaryDirectory() as tmp:
                repo = Path(tmp)

                def git(*args):
                    return subprocess.check_output(["/usr/bin/git", "-C", tmp, *args])

                git("init", "-q", "--object-format=" + fmt)
                payloads = {"a": b"A", "b": b"B", "same": b"A", "z\t\n": b"Z"}
                for name, payload in payloads.items():
                    path = repo / name / "odps.json"
                    path.parent.mkdir()
                    path.write_bytes(payload)
                # a.c sorts before directory a/ in canonical tree bytes.
                (repo / "a.c").write_bytes(b"unrelated")
                (repo / "a" / "extra").write_bytes(b"unrelated nested")
                (repo / "same" / "extra").write_bytes(b"unrelated nested")
                executable = repo / "script"
                executable.write_bytes(b"#!/bin/sh\n")
                executable.chmod(0o755)
                (repo / "link").symlink_to("a.c")
                git("add", ".")
                git(
                    "-c",
                    "user.name=Test",
                    "-c",
                    "user.email=test@example.invalid",
                    "commit",
                    "-qm",
                    "fixture",
                )
                first = git("rev-parse", "HEAD").strip().decode("ascii")
                git("update-index", "--add", "--cacheinfo", f"160000,{first},submodule")
                git(
                    "-c",
                    "user.name=Test",
                    "-c",
                    "user.email=test@example.invalid",
                    "commit",
                    "-qm",
                    "gitlink",
                )
                commit = git("rev-parse", "HEAD").strip().decode("ascii")
                root = git("rev-parse", commit + "^{tree}").strip().decode("ascii")
                raw = git("ls-tree", "-r", "-t", "-z", "--full-tree", commit)
                rows = raw[:-1].split(b"\0")
                by_path = {row.partition(b"\t")[2]: row for row in rows}
                self.assertEqual(
                    by_path[b"a"].split(b" ")[2].split(b"\t")[0],
                    by_path[b"same"].split(b" ")[2].split(b"\t")[0],
                )
                native = git_sources._git
                expected = (commit, [payloads[k] for k in sorted(payloads)])
                self.assertEqual(
                    git_sources.committed_owner_products(repo, commit), expected
                )
                # A valid permutation of the native projection is semantically
                # identical: tree sorting must not depend on input row order.
                cases = (
                    (
                        "omit selected leaf",
                        [r for r in rows if r != by_path[b"b/odps.json"]],
                    ),
                    (
                        "omit shared subtree",
                        [
                            r
                            for r in rows
                            if not (
                                r == by_path[b"same"]
                                or r.partition(b"\t")[2].startswith(b"same/")
                            )
                        ],
                    ),
                    (
                        "omit unrelated nested leaf",
                        [r for r in rows if r != by_path[b"a/extra"]],
                    ),
                    (
                        "omit unrelated root leaf",
                        [r for r in rows if r != by_path[b"a.c"]],
                    ),
                    ("omit parent row", [r for r in rows if r != by_path[b"b"]]),
                    ("omit gitlink", [r for r in rows if r != by_path[b"submodule"]]),
                    ("omit symlink", [r for r in rows if r != by_path[b"link"]]),
                    (
                        "rename leaf",
                        [r.replace(b"\tb/odps.json", b"\tb/other") for r in rows],
                    ),
                    (
                        "substitute known blob",
                        [
                            by_path[b"a/odps.json"].replace(
                                b"\ta/odps.json", b"\tb/odps.json"
                            )
                            if r == by_path[b"b/odps.json"]
                            else r
                            for r in rows
                        ],
                    ),
                    (
                        "change regular mode",
                        [
                            r.replace(b"100644 blob ", b"100755 blob ", 1)
                            if r == by_path[b"b/odps.json"]
                            else r
                            for r in rows
                        ],
                    ),
                )
                for name, altered in (*cases, ("permutation", list(reversed(rows)))):
                    with self.subTest(fault=name):
                        wire = b"\0".join(altered) + b"\0"

                        def observe(repo, *args, _wire=wire, _native=native, **kwargs):
                            if args[0] == "ls-tree":
                                return _wire
                            return _native(repo, *args, **kwargs)

                        with patch.object(
                            git_sources, "_git", side_effect=observe
                        ) as calls:
                            if name == "permutation":
                                self.assertEqual(
                                    git_sources.committed_owner_products(repo, commit),
                                    expected,
                                )
                                continue
                            with self.assertRaisesRegex(
                                ValueError, "Git tree identity mismatch"
                            ):
                                git_sources.committed_owner_products(repo, commit)
                        self.assertFalse(
                            any(
                                c.args[1] in ("cat-file", "hash-object")
                                for c in calls.call_args_list
                            ),
                            calls.call_args_list,
                        )
                self.assertEqual(
                    git("rev-parse", commit + "^{tree}").strip().decode("ascii"), root
                )
