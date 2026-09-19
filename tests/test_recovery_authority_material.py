from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("backup_authority_material_test", ROOT / "recovery" / "backup_authority_material.py")
assert SPEC and SPEC.loader
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)

class BackupAuthorityMaterialTests(unittest.TestCase):
    def test_dpapi_receipt_reuse_is_recipient_and_digest_bound(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root=Path(raw); blob=root/M.REC["dpapi_blob"]; restore=root/M.REC["dpapi_recovery_script"]
            blob.write_bytes(b"blob-v1"); restore.write_text("restore-v1")
            receipt=M.write_dpapi_receipt(root,"age1fixture",verification_basis="windows-dpapi-roundtrip")
            self.assertEqual(M.reusable_dpapi_receipt(root,"age1fixture"),receipt)
            self.assertIsNone(M.reusable_dpapi_receipt(root,"age1other"))
            blob.write_bytes(b"changed")
            self.assertIsNone(M.reusable_dpapi_receipt(root,"age1fixture"))

    def test_seal_reuses_valid_receipt_without_windows_interop(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root=Path(raw); (root/M.REC["dpapi_blob"]).write_bytes(b"blob"); (root/M.REC["dpapi_recovery_script"]).write_text("restore")
            M.write_dpapi_receipt(root,"age1fixture",verification_basis="legacy-successor-bootstrap",evidence={"source":"test"})
            with mock.patch.object(M,"run_windows_powershell_json",side_effect=AssertionError("must not call Windows")):
                result=M.seal_age_key_dpapi(root,"age1fixture")
            self.assertTrue(result["reused"]); self.assertEqual(result["verificationBasis"],"legacy-successor-bootstrap")

if __name__ == "__main__":
    unittest.main()
