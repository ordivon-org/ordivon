from __future__ import annotations
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import browserless_display_auth as A  # noqa: E402


class DisplayAuthTests(unittest.TestCase):
    def test_instance_mapping_is_bounded(self):
        self.assertEqual(A.display_number(11), 111)
        self.assertEqual(A.display_number(13), 113)
        self.assertEqual(A.display_number(21), 121)
        self.assertEqual(A.display_number(22), 122)
        self.assertEqual(A.display_number(A.QUALIFICATION_INSTANCE), 191)
        self.assertEqual(A.PRODUCTION_INSTANCES, frozenset({11, 12, 13, 21, 22}))
        for value in (10, 14, 20, 23, 90, 92, "x"):
            with self.assertRaises(ValueError):
                A.validate_instance(value)

    def test_prepare_materializes_familywild_cookie_without_exposing_cookie(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            original = A.XAUTH_ROOT
            A.XAUTH_ROOT = root
            calls = []
            cookie = b"0123456789abcdef0123456789abcdef\n"

            def run(args, *, input_bytes=None):
                calls.append((list(args), input_bytes))

                class P:
                    stdout = b""
                    stderr = b""

                if args[0] == "/usr/bin/mcookie":
                    P.stdout = cookie
                elif "nlist" in args:
                    # family=0100, address/name/protocol/data are synthetic valid numeric fields.
                    P.stdout = b"0100 0004 74657374 0003 313131 0012 4d49542d4d414749432d434f4f4b49452d31 0010 00112233445566778899aabbccddeeff\n"
                return P()

            with (
                mock.patch.object(A, "run", side_effect=run),
                mock.patch.object(os, "chown") as chown,
            ):
                value = A.prepare(11)
            A.XAUTH_ROOT = original
            path = root / "11"
            self.assertTrue(path.is_file())
            self.assertEqual(path.stat().st_mode & 0o777, 0o400)
            chown.assert_called_once_with(path, 999, 999)
            merge = next(inp for args, inp in calls if "nmerge" in args)
            self.assertTrue(merge.startswith(b"ffff"))
            self.assertFalse(value["credentialExposed"])
            self.assertNotIn(cookie.decode().strip(), str(value))


if __name__ == "__main__":
    unittest.main()
