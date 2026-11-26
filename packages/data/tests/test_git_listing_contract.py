"""Native ls-tree wire framing must qualify before object dispatch."""

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


class GitListingContractTests(unittest.TestCase):
    def test_exact_listing_and_multiplicity_before_object_dispatch(self):
        for fmt in ("sha1", "sha256"):
            with self.subTest(fmt=fmt), TemporaryDirectory() as tmp:
                repo = Path(tmp)

                def git(*args):
                    return subprocess.check_output(["/usr/bin/git", "-C", tmp, *args])

                git("init", "-q", "--object-format=" + fmt)
                # Distinct paths with equal bytes are not duplicate rows.
                # A tab and LF in a path are valid in native -z framing.
                payloads = {"a": b"A", "b\t\n": b"B", "c": b"A"}
                for name, payload in payloads.items():
                    path = repo / name / "odps.json"
                    path.parent.mkdir()
                    path.write_bytes(payload)
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
                commit = git("rev-parse", "HEAD").strip().decode("ascii")
                raw = git("ls-tree", "-r", "-t", "-z", "--full-tree", commit)
                self.assertTrue(raw.endswith(b"\0"))
                self.assertEqual(
                    git_sources.committed_owner_products(repo, commit),
                    (commit, [payloads[k] for k in sorted(payloads)]),
                )
                native = git_sources._git
                rows = raw[:-1].split(b"\0")
                for name, altered in (
                    ("missing terminal NUL", raw[:-1]),
                    ("interior empty row", raw.replace(b"\0", b"\0\0", 1)),
                    ("extra terminal NUL", raw + b"\0"),
                    ("duplicate leaf path", raw + rows[-1] + b"\0"),
                    ("duplicate tree path", raw + rows[0] + b"\0"),
                    ("empty path", raw + rows[-1].split(b"\t", 1)[0] + b"\t\0"),
                    ("missing separator", raw + b"malformed\0"),
                ):
                    with self.subTest(fault=name):

                        def observe(
                            repo, *args, _altered=altered, _native=native, **kwargs
                        ):
                            if args[0] == "ls-tree":
                                return _altered
                            return _native(repo, *args, **kwargs)

                        with (
                            patch.object(
                                git_sources, "_git", side_effect=observe
                            ) as commands,
                            self.assertRaisesRegex(ValueError, "Git tree listing"),
                        ):
                            git_sources.committed_owner_products(repo, commit)
                        self.assertFalse(
                            any(
                                call.args[1] in ("cat-file", "hash-object")
                                for call in commands.call_args_list
                            ),
                            commands.call_args_list,
                        )
