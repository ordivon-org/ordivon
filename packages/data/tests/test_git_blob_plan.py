"""Actual Git fixture: all blob admission before content, dedup by exact OID."""

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


class GitBlobPlanTests(unittest.TestCase):
    def make_repo(self, repo: Path, fmt: str, payloads: dict[str, bytes]):
        def git(*args: str):
            return (
                subprocess.run(
                    ["/usr/bin/git", "-C", str(repo), *args],
                    check=True,
                    capture_output=True,
                )
                .stdout.strip()
                .decode("ascii")
            )

        git("init", "--object-format=" + fmt)
        for name, payload in payloads.items():
            p = repo / name / "odps.json"
            p.parent.mkdir()
            p.write_bytes(payload)
        git("add", ".")
        git(
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "-m",
            "fixture",
        )
        return git("rev-parse", "HEAD")

    def test_late_oversize_metadata_rejects_before_content_batch(self):
        for fmt in ("sha1", "sha256"):
            with self.subTest(fmt=fmt), TemporaryDirectory() as tmp:
                repo = Path(tmp)
                commit = self.make_repo(
                    repo,
                    fmt,
                    {
                        "a": b"valid",
                        "z": b"X" * (2 * 1024 * 1024 + 1),
                    },
                )
                with (
                    patch.object(git_sources, "_git", wraps=git_sources._git) as native,
                    self.assertRaisesRegex(ValueError, "bounded input size"),
                ):
                    git_sources.committed_owner_products(repo, commit)
                calls = [c.args[1:] for c in native.call_args_list]
                self.assertFalse(
                    any(
                        a[:2] in (("cat-file", "blob"), ("cat-file", "--batch"))
                        for a in calls
                    ),
                    calls,
                )

    def test_duplicate_content_oid_read_once_preserves_path_multiplicity(self):
        for fmt in ("sha1", "sha256"):
            with self.subTest(fmt=fmt), TemporaryDirectory() as tmp:
                repo = Path(tmp)
                commit = self.make_repo(repo, fmt, {"a": b"A", "b": b"B", "c": b"A"})
                with patch.object(
                    git_sources, "_git", wraps=git_sources._git
                ) as native:
                    self.assertEqual(
                        git_sources.committed_owner_products(repo, commit),
                        (commit, [b"A", b"B", b"A"]),
                    )
                hashes = [
                    c.kwargs["input_bytes"]
                    for c in native.call_args_list
                    if c.args[1:2] == ("hash-object",)
                ]
                self.assertCountEqual(hashes, [b"A", b"B"])
                calls = [c.args[1:] for c in native.call_args_list]
                self.assertEqual(
                    sum(a[:2] == ("cat-file", "--batch") for a in calls), 1
                )
                self.assertFalse(any(a[:2] == ("cat-file", "blob") for a in calls))
