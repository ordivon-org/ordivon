"""Hermetic adversarial checks of the exact GitHub-API cargo-deny CI installer."""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import runpy
import tarfile
import tempfile
import unittest
from unittest.mock import patch

INSTALLER = Path(__file__).with_name("install_verified_cargo_deny.py")
# Run the pure module without executing its __main__ entrypoint.
SOURCE = runpy.run_path(str(INSTALLER))
import_verified = SOURCE["install"]
check_metadata = SOURCE["_check_metadata"]
verified_archive = SOURCE["_verified_archive"]


def archive_fixture(*, binary: bytes = b"#!/bin/sh\nprintf 'cargo-deny 0.20.2\\n'\n") -> bytes:
    with io.BytesIO() as target:
        with tarfile.open(fileobj=target, mode="w:gz") as bundle:
            info = tarfile.TarInfo(name=SOURCE["MEMBER"])
            info.size = len(binary)
            info.mode = 0o755
            bundle.addfile(info, io.BytesIO(binary))
        return target.getvalue()


class VerifiedCargoDenyInstallerTests(unittest.TestCase):
    def metadata(self, data: bytes) -> bytes:
        return json.dumps(
            {
                "id": SOURCE["ASSET_ID"],
                "name": SOURCE["ASSET_NAME"],
                "size": len(data),
                "digest": "sha256:" + hashlib.sha256(data).hexdigest(),
                "state": "uploaded",
            }
        ).encode()

    def test_exact_official_archive_installs_and_cache_is_revalidated(self) -> None:
        data = archive_fixture()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            calls = []
            def fake_api(accept, *, destination=None):
                calls.append(accept)
                if destination is None:
                    return self.metadata(data)
                destination.write_bytes(data)
                return b""

            with patch.dict(import_verified.__globals__, {
                "ASSET_SHA256": hashlib.sha256(data).hexdigest(),
                "ASSET_SIZE": len(data),
                "_gh_api": fake_api,
            }):
                cache, bin_dir = root / "cache", root / "bin"
                self.assertEqual(import_verified(cache, bin_dir), "verified-api-download")
                self.assertEqual(calls, ["application/vnd.github+json", "application/octet-stream"])
                self.assertEqual(import_verified(cache, bin_dir), "verified-cache-hit")
                self.assertEqual(len(calls), 2)
                self.assertTrue((bin_dir / "cargo-deny").is_file())
                self.assertTrue(verified_archive(cache / "cargo-deny.tar.gz"))

    def test_digest_mismatch_fails_closed_before_extraction(self) -> None:
        data = archive_fixture()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            def fake_api(accept, *, destination=None):
                if destination is None:
                    return self.metadata(data)
                destination.write_bytes(data[:-20])
                return b""
            with patch.dict(import_verified.__globals__, {"_gh_api": fake_api}):
                with self.assertRaisesRegex(RuntimeError, "identity, size or digest drift"):
                    import_verified(root / "cache", root / "bin")
                self.assertFalse((root / "bin" / "cargo-deny").exists())

    def test_valid_metadata_then_partial_binary_fails_integrity(self) -> None:
        data = archive_fixture()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            def fake_api(accept, *, destination=None):
                if destination is None:
                    return self.metadata(data)
                destination.write_bytes(data[:10])
                return b""
            with patch.dict(import_verified.__globals__, {
                "ASSET_SHA256": hashlib.sha256(data).hexdigest(),
                "ASSET_SIZE": len(data),
                "_gh_api": fake_api,
            }):
                with self.assertRaisesRegex(RuntimeError, "failed SHA-256/size"):
                    import_verified(root / "cache", root / "bin")
                self.assertFalse((root / "bin" / "cargo-deny").exists())
                self.assertFalse((root / "cache" / "cargo-deny.tar.gz").exists())

    def test_forged_metadata_rejected_before_downloading(self) -> None:
        data = archive_fixture()
        bad = json.loads(self.metadata(data))
        bad["id"] += 1
        with self.assertRaisesRegex(RuntimeError, "identity.*drift"):
            check_metadata(json.dumps(bad).encode())
        bad["id"] -= 1
        bad["digest"] = "sha256:" + "0" * 64
        with self.assertRaisesRegex(RuntimeError, "identity.*drift"):
            check_metadata(json.dumps(bad).encode())

    def test_transient_api_timeout_retries_same_idempotent_get(self) -> None:
        import subprocess

        with (
            patch("subprocess.run", side_effect=[
                subprocess.TimeoutExpired("gh api", 35),
                subprocess.CompletedProcess("gh api", 0, stdout=b'{"ok":true}'),
            ]) as run,
            patch("time.sleep") as sleep,
        ):
            response = SOURCE["_gh_api"]("application/vnd.github+json")
        self.assertEqual(response, b'{"ok":true}')
        self.assertEqual(run.call_count, 2)
        sleep.assert_called_once_with(1)

    def test_corrupt_cache_is_not_used_and_api_is_reverified(self) -> None:
        data = archive_fixture()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cache = root / "cache"
            cache.mkdir()
            (cache / "cargo-deny.tar.gz").write_bytes(b"forged archive")
            calls = []
            def fake_api(accept, *, destination=None):
                calls.append(accept)
                if destination is None:
                    return self.metadata(data)
                destination.write_bytes(data)
                return b""

            with patch.dict(import_verified.__globals__, {
                "ASSET_SHA256": hashlib.sha256(data).hexdigest(),
                "ASSET_SIZE": len(data),
                "_gh_api": fake_api,
            }):
                self.assertEqual(import_verified(cache, root / "bin"), "verified-api-download")
                self.assertTrue(verified_archive(cache / "cargo-deny.tar.gz"))
                self.assertEqual(calls, ["application/vnd.github+json", "application/octet-stream"])

    def test_symlink_cache_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cache = root / "cache"
            cache.mkdir()
            (root / "other").write_bytes(b"bad")
            (cache / "cargo-deny.tar.gz").symlink_to(root / "other")
            with self.assertRaisesRegex(RuntimeError, "symlink"):
                import_verified(cache, root / "bin")

    def test_wrong_executable_version_never_installs(self) -> None:
        data = archive_fixture(binary=b"#!/bin/sh\nprintf 'cargo-deny 9.9.9\\n'\n")
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            def fake_api(accept, *, destination=None):
                if destination is None:
                    return self.metadata(data)
                destination.write_bytes(data)
                return b""
            with patch.dict(import_verified.__globals__, {
                "ASSET_SHA256": hashlib.sha256(data).hexdigest(),
                "ASSET_SIZE": len(data),
                "_gh_api": fake_api,
            }):
                with self.assertRaisesRegex(RuntimeError, "version check failed"):
                    import_verified(root / "cache", root / "bin")
                self.assertFalse((root / "bin" / "cargo-deny").exists())


if __name__ == "__main__":
    unittest.main()
