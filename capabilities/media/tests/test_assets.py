from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from ordivon_studio.assets import archive_blob, hash_file, r2_object_key


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

    def test_archive_blob_creates_and_reuses_verified_object(self) -> None:
        payload = b"selected production bytes\n"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "master.bin"
            cache = root / "cache"
            source.write_bytes(payload)

            first = archive_blob(source, cache)
            second = archive_blob(source, cache)

            self.assertEqual(first["disposition"], "created")
            self.assertEqual(second["disposition"], "existing")
            destination = Path(str(first["cachePath"]))
            self.assertEqual(destination.read_bytes(), payload)
            self.assertEqual(first["blob"], second["blob"])

    def test_archive_blob_rejects_conflicting_existing_object(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "master.bin"
            cache = root / "cache"
            source.write_bytes(b"expected bytes")
            blob = hash_file(source)
            destination = cache / r2_object_key(blob.digest)
            destination.parent.mkdir(parents=True)
            destination.write_bytes(b"different bytes")

            with self.assertRaises(RuntimeError):
                archive_blob(source, cache)

    def test_rejects_non_sha256_key(self) -> None:
        with self.assertRaises(ValueError):
            r2_object_key("md5:deadbeef")


if __name__ == "__main__":
    unittest.main()
