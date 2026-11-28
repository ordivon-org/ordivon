"""Pure cross-platform identity and Windows receipt negatives, not native PASS."""
import copy
import io
import stat
import subprocess
import sys
from pathlib import Path
import unittest
import zipfile

from hosted_product_acceptance import verify_archive
from product_acceptance_contract import digest
import test_hosted_product_acceptance as fixtures
from test_hosted_product_acceptance import PRODUCT, SOURCE
from windows_render_acceptance import verify_capture_receipt


def inner_zip(*, rename=None, link=False, omit=False):
    raw = io.BytesIO()
    with zipfile.ZipFile(raw, "w") as z:
        names = ["room-encounter.exe", "DIALOGUE_MANAGER_LICENSE.txt", "KENNEY_ASSETS_LICENSE.txt"]
        if omit:
            names.pop()
        for name in names:
            is_exe = name.endswith(".exe")
            item = zipfile.ZipInfo(rename if is_exe and rename is not None else name)
            item.create_system = 3
            item.external_attr = ((stat.S_IFLNK if link and is_exe else stat.S_IFREG) | 0o644) << 16
            z.writestr(item, b"win-fixture" if is_exe else b"license")
    return raw.getvalue()


class WindowsArchive(unittest.TestCase):
    def setUp(self):
        self.case = fixtures.ArtifactContract("test_valid_identity")
        self.case.setUp()
        self.addCleanup(self.case.doCleanups)

    def verify(self, **kwargs):
        self.case.fixture(windows_payload=inner_zip(**kwargs))
        return verify_archive(self.case.zip, digest(self.case.zip), SOURCE, PRODUCT,
                              self.case.output, platform="windows")

    def test_shared_identity(self):
        exe, receipt = self.verify()
        self.assertEqual(exe.read_bytes(), b"win-fixture")
        self.assertEqual(receipt["executable_sha256"], digest(exe))

    def test_traversal(self):
        with self.assertRaisesRegex(ValueError, "Windows native member inventory"):
            self.verify(rename="../room-encounter.exe")

    def test_symlink(self):
        with self.assertRaisesRegex(ValueError, "Windows native member not regular"):
            self.verify(link=True)

    def test_missing_license(self):
        with self.assertRaisesRegex(ValueError, "Windows native member inventory"):
            self.verify(omit=True)

    def test_unknown_platform(self):
        self.case.fixture()
        with self.assertRaisesRegex(ValueError, "unknown native platform"):
            verify_archive(self.case.zip, digest(self.case.zip), SOURCE, PRODUCT,
                           self.case.output, platform="other")


class SharedContractBoundary(unittest.TestCase):
    def test_shared_contract_has_no_platform_executor_dependency(self):
        script = (
            "import sys; sys.path.insert(0, sys.argv[1]); "
            "import product_acceptance_contract; "
            "assert not ({'rendered_product_acceptance', 'windows_render_acceptance', "
            "'x11_interaction_acceptance', 'mixed_audio_acceptance', "
            "'hosted_product_acceptance'} & set(sys.modules))"
        )
        result = subprocess.run(
            [sys.executable, "-I", "-c", script, str(Path(__file__).resolve().parent)],
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


class WindowsReceipt(unittest.TestCase):
    def setUp(self):
        self.identity = dict(product=PRODUCT, executable_sha256="a"*64)
        self.receipt = dict(**self.identity, pid=12, session=1, exit_code=0, hwnd=0,
                            frames=[dict(name=f"frame{i:08d}.png", sha256="b"*64)
                                    for i in range(8)])

    def test_valid_and_optional_hwnd(self):
        verify_capture_receipt(self.receipt, self.identity)
        self.receipt["hwnd"] = 123
        verify_capture_receipt(self.receipt, self.identity)

    def test_invalid_fields(self):
        for field, value in (("session", 0), ("session", True), ("exit_code", 1),
                             ("exit_code", False), ("pid", 0), ("hwnd", -1),
                             ("product", "beacon-relay"), ("executable_sha256", "f"*64)):
            with self.subTest(field=field, value=value):
                data = copy.deepcopy(self.receipt)
                data[field] = value
                with self.assertRaisesRegex(ValueError, "identity/session"):
                    verify_capture_receipt(data, self.identity)

    def test_invalid_frame_inventory(self):
        for action in ("missing", "wrong_name", "wrong_hash", "extra_field"):
            with self.subTest(action=action):
                data = copy.deepcopy(self.receipt)
                if action == "missing":
                    data["frames"].pop()
                elif action == "wrong_name":
                    data["frames"][0]["name"] = "frame00000001.png"
                elif action == "wrong_hash":
                    data["frames"][0]["sha256"] = "0"
                else:
                    data["frames"][0]["unknown"] = True
                with self.assertRaisesRegex(ValueError, "frame inventory"):
                    verify_capture_receipt(data, self.identity)


if __name__ == "__main__":
    unittest.main(verbosity=2)
