"""Native Git object identity regression, independent of the projection parser."""

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
from ordivon_data.odps_projection import project_catalog


class GitSourceIdentityTests(unittest.TestCase):
    def test_same_length_corrupt_blob_cannot_attest_committed_metadata(self) -> None:
        source = (
            ROOT / "catalogs/data-products/experimental-episode-corpus-r1/odps.json"
        )
        original = source.read_bytes()
        product = json.loads(original)
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
                path = repo / "owner" / "odps.json"
                path.parent.mkdir()
                path.write_bytes(original)
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
                commit = git("rev-parse", "HEAD").decode()
                oid = git("rev-parse", "HEAD:owner/odps.json").decode()
                self.assertEqual(
                    committed_owner_products(repo, commit), (commit, [original])
                )
                self.assertEqual(
                    project_catalog([original])["dcat:dataset"][0]["dct:title"],
                    product["name"],
                )

                old_name = product["name"].encode()
                changed = original.replace(old_name, b"X" * len(old_name), 1)
                self.assertNotEqual(changed, original)
                self.assertEqual(len(changed), len(original))
                self.assertNotEqual(json.loads(changed)["name"], product["name"])
                obj = repo / ".git" / "objects" / oid[:2] / oid[2:]
                saved = obj.read_bytes()
                header, raw = zlib.decompress(saved).split(b"\0", 1)
                self.assertEqual(raw, original)
                # Git loose objects are read-only for ordinary users. Replace
                # the entry only inside this disposable repository, using the
                # writable parent directory, without elevating privileges.
                mode = stat.S_IMODE(obj.stat().st_mode)

                def replace_fixture_object(
                    obj: Path, mode: int, content: bytes
                ) -> None:
                    replacement = obj.with_name(obj.name + ".fixture")
                    replacement.write_bytes(content)
                    replacement.chmod(mode)
                    replacement.replace(obj)

                replace_fixture_object(
                    obj, mode, zlib.compress(header + b"\0" + changed)
                )
                # Git cat-file itself accepts this corrupt, same-length object.
                self.assertEqual(git("cat-file", "blob", oid), changed.strip())
                self.assertNotEqual(
                    project_catalog([changed]), project_catalog([original])
                )
                with self.assertRaisesRegex(
                    ValueError, "Git ODPS blob identity mismatch"
                ):
                    committed_owner_products(repo, commit)
                replace_fixture_object(obj, mode, saved)
                self.assertEqual(
                    committed_owner_products(repo, commit), (commit, [original])
                )
