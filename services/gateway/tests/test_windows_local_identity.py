from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ordivon_gateway.access_auth import AccessAuthError, _read_private_token_file

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "packaging/windows/materialize_credentials.ps1"


@unittest.skipUnless(os.name == "nt", "native Windows private identity")
class WindowsLocalIdentityTests(unittest.TestCase):
    def test_generated_identity_is_private_and_readable_by_gateway(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            prefix = Path(temporary)
            result = subprocess.run(
                [
                    "powershell.exe",
                    "-NoProfile",
                    "-NonInteractive",
                    "-ExecutionPolicy",
                    "RemoteSigned",
                    "-File",
                    str(SCRIPT),
                    "-Prefix",
                    str(prefix),
                    "-ServiceName",
                    "OrdivonGatewayCandidateR5",
                    "-CreateLocalServiceBearer",
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, "credential owner helper failed")
            receipt = json.loads(result.stdout.lstrip("\ufeff"))
            self.assertEqual(len(receipt["credentials"]), 1)
            self.assertEqual(receipt["credentials"][0]["label"], "local-service-bearer")
            credential = prefix / "credentials/local-service-bearer"
            with patch.dict(
                os.environ, {"ORDIVON_GATEWAY_WINDOWS_SERVICE_NAME": "OrdivonGatewayCandidateR5"}
            ):
                value = _read_private_token_file(str(credential))
                self.assertEqual(len(value), 64)
                self.assertTrue(all(c in "0123456789abcdef" for c in value))
                # Windows mode bits cannot prove a DACL. A broad explicit ACE must fail.
                result = subprocess.run(
                    ["icacls.exe", str(credential), "/grant", "*S-1-1-0:(R)"],
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 0)
                with self.assertRaises(AccessAuthError):
                    _read_private_token_file(str(credential))

    def test_locked_source_failure_removes_private_temporary_file(self) -> None:
        import win32con
        import win32file

        with tempfile.TemporaryDirectory() as temporary:
            prefix = Path(temporary)
            source = prefix / "source-fixture"
            source.write_text("test-only-value-" * 4)
            handle = win32file.CreateFile(
                str(source),
                win32con.GENERIC_READ,
                0,
                None,
                win32con.OPEN_EXISTING,
                win32con.FILE_ATTRIBUTE_NORMAL,
                None,
            )
            try:
                result = subprocess.run(
                    [
                        "powershell.exe",
                        "-NoProfile",
                        "-NonInteractive",
                        "-ExecutionPolicy",
                        "RemoteSigned",
                        "-File",
                        str(SCRIPT),
                        "-Prefix",
                        str(prefix),
                        "-ServiceName",
                        "OrdivonGatewayCandidateR5",
                        "-HostBearerSource",
                        str(source),
                    ],
                    capture_output=True,
                    text=True,
                )
            finally:
                handle.Close()
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(list((prefix / "credentials").glob(".host-bearer.tmp-*")))
            self.assertFalse((prefix / "credentials/host-bearer").exists())


if __name__ == "__main__":
    unittest.main()
