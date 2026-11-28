from __future__ import annotations

import ast
import hashlib
import tempfile
import unittest
from pathlib import Path

from ordivon_security_v2.attestations import sha256_file as attestation_sha256_file
from ordivon_security_v2.hashing import sha256_file_digest, sha256_file_hex
from ordivon_security_v2.signed_vsa import sha256_file as signed_vsa_sha256_file

OWNER = Path(__file__).resolve().parents[1]


class SecurityHashingTests(unittest.TestCase):
    def test_file_hash_has_one_byte_implementation_and_two_explicit_representations(self) -> None:
        payload = (b"ordivon-security-hash\n" * 65537) + b"tail"
        expected = hashlib.sha256(payload).hexdigest()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "payload.bin"
            path.write_bytes(payload)
            self.assertEqual(sha256_file_hex(path), expected)
            self.assertEqual(sha256_file_digest(path), "sha256:" + expected)

    def test_existing_public_hash_imports_delegate_to_canonical_implementation(self) -> None:
        self.assertIs(attestation_sha256_file, sha256_file_hex)
        self.assertIs(signed_vsa_sha256_file, sha256_file_digest)

    def test_security_owner_does_not_reintroduce_legacy_file_hash_functions(self) -> None:
        offenders: list[str] = []
        for root in (OWNER / "src" / "ordivon_security_v2", OWNER / "scripts"):
            for path in sorted(root.rglob("*.py")):
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in {
                        "_sha256",
                        "sha256_file",
                    }:
                        offenders.append(f"{path.relative_to(OWNER)}:{node.lineno}:{node.name}")
        self.assertEqual(offenders, [], "use ordivon_security_v2.hashing for file SHA-256")


if __name__ == "__main__":
    unittest.main()
