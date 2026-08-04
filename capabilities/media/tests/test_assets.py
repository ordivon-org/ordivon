from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from ordivon_studio.assets import hash_file, r2_object_key


class AssetTests(unittest.TestCase):
    def test_hash_and_content_addressed_key(self) -> None:
        payload = b"ordivon-studio\n"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "asset.txt"
            path.write_bytes(payload)
            blob = hash_file(path)

        expected = hashlib.sha256(payload).hexdigest()
        self.assertEqual(blob.digest, f"sha256:{expected}")
        self.assertEqual(blob.size_bytes, len(payload))
        self.assertEqual(r2_object_key(blob.digest), f"objects/sha256/{expected[:2]}/{expected}")

    def test_rejects_non_sha256_key(self) -> None:
        with self.assertRaises(ValueError):
            r2_object_key("md5:deadbeef")


if __name__ == "__main__":
    unittest.main()
