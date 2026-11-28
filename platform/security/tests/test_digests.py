from __future__ import annotations

import ast
import tempfile
import unittest
from pathlib import Path

from ordivon_security_v2 import attestations, provenance, scorecard, signed_vsa, vex
from ordivon_security_v2.digests import (
    sha256_bytes,
    sha256_file,
    sha256_file_hex,
    sha256_file_hex_and_size,
)


class DigestSingleSourceTests(unittest.TestCase):
    def test_digest_formats_share_one_file_implementation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "subject.bin"
            path.write_bytes(b"abc")
            hex_digest = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"

            self.assertEqual(sha256_file_hex_and_size(path), (hex_digest, 3))
            self.assertEqual(sha256_file_hex(path), hex_digest)
            self.assertEqual(sha256_file(path), "sha256:" + hex_digest)
            self.assertEqual(sha256_bytes(path.read_bytes()), "sha256:" + hex_digest)

    def test_security_consumers_alias_the_canonical_digest_functions(self) -> None:
        self.assertIs(attestations.sha256_file, sha256_file_hex)
        self.assertIs(provenance._sha256, sha256_file_hex)
        self.assertIs(scorecard._sha256, sha256_file)
        self.assertIs(signed_vsa.sha256_file, sha256_file)
        self.assertIs(signed_vsa.sha256_bytes, sha256_bytes)
        self.assertIs(vex._sha256, sha256_file)

    def test_browser_pool_promotion_does_not_reintroduce_a_local_digest(self) -> None:
        script = Path(__file__).parents[1] / "scripts/promote_browser_security_pool_lkg.py"
        tree = ast.parse(script.read_text(encoding="utf-8"))
        local_names = {
            node.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        self.assertNotIn("sha256_file", local_names)


if __name__ == "__main__":
    unittest.main()
