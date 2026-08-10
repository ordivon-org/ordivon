from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ordivon_studio.assets import hash_file, r2_object_key
from ordivon_studio.r2 import replicate_r2_blob, restore_r2_blob


class R2Tests(unittest.TestCase):
    def _credentials(self, root: Path) -> Path:
        path = root / "cloudflare.json"
        path.write_text(
            json.dumps(
                {
                    "account_id": "0123456789abcdef0123456789abcdef",
                    "api_token": "test-token-value",
                    "api_base": "https://api.example.invalid/client/v4",
                }
            ),
            encoding="utf-8",
        )
        return path

    def test_replicate_reuses_verified_existing_remote_object(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "selected.bin"
            source.write_bytes(b"selected bytes")
            credentials = self._credentials(root)

            def download(**kwargs: object) -> tuple[int, Path | None]:
                target = root / "remote.bin"
                target.write_bytes(source.read_bytes())
                return 200, target

            with (
                patch("ordivon_studio.r2._verified_remote_download", side_effect=download),
                patch("ordivon_studio.r2._curl_upload") as upload,
            ):
                result = replicate_r2_blob(source, bucket="bucket-one", credentials_path=credentials)

            self.assertEqual(result["disposition"], "existing")
            self.assertTrue(result["verified"])
            upload.assert_not_called()

    def test_replicate_uploads_then_redownloads_exact_remote_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "selected.bin"
            source.write_bytes(b"selected bytes")
            credentials = self._credentials(root)
            calls = 0

            def download(**kwargs: object) -> tuple[int, Path | None]:
                nonlocal calls
                calls += 1
                if calls == 1:
                    return 404, None
                target = root / "verified.bin"
                target.write_bytes(source.read_bytes())
                return 200, target

            with (
                patch("ordivon_studio.r2._verified_remote_download", side_effect=download),
                patch("ordivon_studio.r2._curl_upload", return_value=200) as upload,
            ):
                result = replicate_r2_blob(source, bucket="bucket-one", credentials_path=credentials)

            self.assertEqual(result["disposition"], "created")
            self.assertTrue(result["verified"])
            self.assertEqual(calls, 2)
            upload.assert_called_once()

    def test_replicate_rejects_divergent_remote_digest_address(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "selected.bin"
            source.write_bytes(b"selected bytes")
            credentials = self._credentials(root)

            def download(**kwargs: object) -> tuple[int, Path | None]:
                raise RuntimeError("R2 digest address contains different bytes")

            with patch("ordivon_studio.r2._verified_remote_download", side_effect=download):
                with self.assertRaisesRegex(RuntimeError, "different bytes"):
                    replicate_r2_blob(source, bucket="bucket-one", credentials_path=credentials)

    def test_restore_creates_and_reuses_verified_local_cache_object(self) -> None:
        payload = b"remote selected bytes"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            credentials = self._credentials(root)
            source = root / "source.bin"
            source.write_bytes(payload)
            blob = hash_file(source)
            cache = root / "cache"

            def download(**kwargs: object) -> tuple[int, Path | None]:
                target = root / "remote-download.bin"
                target.write_bytes(payload)
                return 200, target

            with patch("ordivon_studio.r2._verified_remote_download", side_effect=download):
                first = restore_r2_blob(blob.digest, cache, bucket="bucket-one", credentials_path=credentials)
                second = restore_r2_blob(blob.digest, cache, bucket="bucket-one", credentials_path=credentials)

            destination = cache / r2_object_key(blob.digest)
            self.assertEqual(first["disposition"], "created")
            self.assertEqual(second["disposition"], "existing")
            self.assertEqual(destination.read_bytes(), payload)
            self.assertEqual(first["blob"]["digest"], blob.digest)

    def test_restore_rejects_conflicting_local_digest_address(self) -> None:
        payload = b"remote selected bytes"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            credentials = self._credentials(root)
            source = root / "source.bin"
            source.write_bytes(payload)
            blob = hash_file(source)
            cache = root / "cache"
            destination = cache / r2_object_key(blob.digest)
            destination.parent.mkdir(parents=True)
            destination.write_bytes(b"wrong local bytes")

            def download(**kwargs: object) -> tuple[int, Path | None]:
                target = root / "remote-download.bin"
                target.write_bytes(payload)
                return 200, target

            with patch("ordivon_studio.r2._verified_remote_download", side_effect=download):
                with self.assertRaisesRegex(RuntimeError, "local digest address contains different bytes"):
                    restore_r2_blob(blob.digest, cache, bucket="bucket-one", credentials_path=credentials)

    def test_restore_rejects_missing_remote_object(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            credentials = self._credentials(root)
            digest = "sha256:" + "1" * 64

            with patch("ordivon_studio.r2._verified_remote_download", return_value=(404, None)):
                with self.assertRaises(FileNotFoundError):
                    restore_r2_blob(digest, root / "cache", bucket="bucket-one", credentials_path=credentials)


if __name__ == "__main__":
    unittest.main()
