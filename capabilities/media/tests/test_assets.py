from __future__ import annotations

import hashlib
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from ordivon_studio.assets import archive_blob, hash_file, materialize_blob, r2_object_key


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

    def test_hash_stream_size_and_digest_are_one_observation(self) -> None:
        payload = bytes(range(256)) * 41
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "large.bin"
            source.write_bytes(payload)
            for chunk_size in (1, 19, 1024, len(payload) + 100):
                with self.subTest(chunk_size=chunk_size):
                    result = hash_file(source, chunk_size=chunk_size)
                    self.assertEqual(result.size_bytes, len(payload))
                    self.assertEqual(result.digest, "sha256:" + hashlib.sha256(payload).hexdigest())
            with self.assertRaisesRegex(ValueError, "positive integer"):
                hash_file(source, chunk_size=0)

    def test_hash_rejects_source_metadata_drift_on_open_descriptor(self) -> None:
        payload = b"content under concurrent writer pressure"
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "selected.bin"
            source.write_bytes(payload)
            real_fstat = os.fstat
            calls = 0

            def changed_on_second_observation(fd):
                nonlocal calls
                calls += 1
                observed = real_fstat(fd)
                if calls == 1:
                    return observed
                return SimpleNamespace(
                    st_dev=observed.st_dev,
                    st_ino=observed.st_ino,
                    st_size=observed.st_size + 1,
                    st_mtime_ns=observed.st_mtime_ns,
                    st_ctime_ns=observed.st_ctime_ns,
                )

            with patch("ordivon_studio.assets.os.fstat", side_effect=changed_on_second_observation):
                with self.assertRaisesRegex(RuntimeError, "changed during hashing"):
                    hash_file(source)
            self.assertEqual(calls, 2)
            self.assertEqual(source.read_bytes(), payload)

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

    def test_materialize_blob_recovers_and_reuses_exact_cached_bytes(self) -> None:
        payload = b"recoverable selected bytes\n"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "selected.bin"
            cache = root / "cache"
            recovered = root / "working" / "selected.bin"
            source.write_bytes(payload)
            archived = archive_blob(source, cache)
            source.unlink()

            first = materialize_blob(str(archived["blob"]["digest"]), cache, recovered)
            second = materialize_blob(str(archived["blob"]["digest"]), cache, recovered)

            self.assertEqual(first["disposition"], "created")
            self.assertEqual(second["disposition"], "existing")
            self.assertEqual(recovered.read_bytes(), payload)
            self.assertEqual(first["blob"]["digest"], archived["blob"]["digest"])
            self.assertEqual(second["blob"], first["blob"])

    def test_materialize_blob_rejects_conflicting_destination(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "selected.bin"
            cache = root / "cache"
            recovered = root / "selected.recovered.bin"
            source.write_bytes(b"expected bytes")
            archived = archive_blob(source, cache)
            recovered.write_bytes(b"different bytes")

            with self.assertRaises(RuntimeError):
                materialize_blob(str(archived["blob"]["digest"]), cache, recovered)

    def test_materialize_blob_rejects_corrupt_cached_object(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "selected.bin"
            cache = root / "cache"
            source.write_bytes(b"expected bytes")
            blob = hash_file(source)
            cached = cache / r2_object_key(blob.digest)
            cached.parent.mkdir(parents=True)
            cached.write_bytes(b"corrupt bytes")

            with self.assertRaises(RuntimeError):
                materialize_blob(blob.digest, cache, root / "recovered.bin")

    def test_rejects_non_sha256_key(self) -> None:
        with self.assertRaises(ValueError):
            r2_object_key("md5:deadbeef")


if __name__ == "__main__":
    unittest.main()
