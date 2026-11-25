"""Static object corruption counterexamples on disposable native repositories."""

from __future__ import annotations

import json
import stat
import subprocess
import sys
import unittest
import zlib
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "packages/data/src"))
from ordivon_data.git_sources import committed_owner_products


class GitCutIdentityTests(unittest.TestCase):
    def test_corrupt_commit_root_and_nested_tree_rejected(self):
        original = (
            ROOT / "catalogs/data-products/experimental-episode-corpus-r1/odps.json"
        ).read_bytes()
        changed = json.loads(original)
        changed["name"] = "Different but valid producer metadata"
        alternate = json.dumps(changed).encode()
        for algorithm in ("sha1", "sha256"):
            with self.subTest(algorithm=algorithm), TemporaryDirectory() as tmp:
                repo = Path(tmp)

                def git(*args: str) -> bytes:
                    return subprocess.run(
                        ["/usr/bin/git", "-C", tmp, *args],
                        check=True,
                        capture_output=True,
                    ).stdout.strip()

                git("init", "--object-format=" + algorithm)
                path = repo / "owner" / "nested" / "odps.json"
                path.parent.mkdir(parents=True)
                path.write_bytes(original)
                git("add", ".")
                git(
                    "-c",
                    "user.name=Test",
                    "-c",
                    "user.email=test@example.invalid",
                    "commit",
                    "-m",
                    "original",
                )
                first = git("rev-parse", "HEAD").decode()
                first_tree = git("rev-parse", first + "^{tree}").decode()
                nested = git("rev-parse", first + ":owner/nested").decode()
                path.write_bytes(alternate)
                git("add", ".")
                git(
                    "-c",
                    "user.name=Test",
                    "-c",
                    "user.email=test@example.invalid",
                    "commit",
                    "-m",
                    "alternate",
                )
                second = git("rev-parse", "HEAD").decode()
                second_tree = git("rev-parse", second + "^{tree}").decode()
                second_nested = git("rev-parse", second + ":owner/nested").decode()
                self.assertEqual(
                    committed_owner_products(repo, first), (first, [original])
                )
                self.assertEqual(
                    committed_owner_products(repo, second), (second, [alternate])
                )

                def loose(oid, repo=repo):
                    return repo / ".git" / "objects" / oid[:2] / oid[2:]

                def replace(obj, payload):
                    temp = obj.with_name(obj.name + ".fixture")
                    temp.write_bytes(payload)
                    temp.chmod(stat.S_IMODE(obj.stat().st_mode))
                    temp.replace(obj)

                for oid, replacement, kind in (
                    (first, second, "commit"),
                    (first_tree, second_tree, "tree"),
                    (nested, second_nested, "tree"),
                ):
                    with self.subTest(kind=kind, oid=oid):
                        obj = loose(oid)
                        saved = obj.read_bytes()
                        # Keep a structurally valid object and old filename/OID.
                        if kind == "commit":
                            header, payload = zlib.decompress(saved).split(b"\0", 1)
                            payload = payload.replace(
                                first_tree.encode(), second_tree.encode(), 1
                            )
                            corrupt = zlib.compress(header + b"\0" + payload)
                        else:
                            corrupt = loose(replacement).read_bytes()
                        replace(obj, corrupt)
                        try:
                            with self.assertRaisesRegex(
                                ValueError,
                                "Git .* identity mismatch|committed ODPS source cannot be resolved",
                            ):
                                committed_owner_products(repo, first)
                        finally:
                            replace(obj, saved)
                        self.assertEqual(
                            committed_owner_products(repo, first), (first, [original])
                        )
