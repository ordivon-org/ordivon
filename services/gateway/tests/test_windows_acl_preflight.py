from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "packaging/windows/protect_candidate_acl.ps1"


@unittest.skipUnless(os.name == "nt", "native Windows ACL preflight")
class WindowsAclPreflightTests(unittest.TestCase):
    def test_missing_pinned_python_fails_before_service_lookup(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            commit = "a" * 40
            release = root / "releases" / commit
            (release / ".venv/Scripts").mkdir(parents=True)
            (release / ".venv/Scripts/ordivon-gateway.exe").touch()
            (release / ".python-version").write_text("3.14.7")
            for name in ("python", "logs", "credentials"):
                (root / name).mkdir()
            shawl = root / "shawl.exe"
            shawl.touch()
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
                    str(root),
                    "-ReleaseCommit",
                    commit,
                    "-ServiceName",
                    "OrdivonGatewayAbsentPreflightTest",
                    "-ShawlPath",
                    str(shawl),
                ],
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("ACL read-back probe missing:", result.stderr)
            self.assertIn("cpython-3.14.7-windows-x86_64-none", result.stderr)
            self.assertFalse((root / "receipts").exists())


if __name__ == "__main__":
    unittest.main()
