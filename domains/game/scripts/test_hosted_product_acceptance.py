"""Artifact identity and archive adversarial fixtures; no synthetic product PASS."""
import hashlib
import io
from pathlib import Path
import tarfile
import tempfile
import unittest
import zipfile

from hosted_product_acceptance import verify_archive, names
from product_acceptance_contract import digest

SOURCE = "a" * 40
PRODUCT = "room-encounter"


class ArtifactContract(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.zip = self.root / "artifact.zip"
        self.output = self.root / "out"
        self.output.mkdir()

    def fixture(self, *, bad_source=False, bad_manifest=False, extra=False,
                link=False, traversal=False, missing_template=False, duplicate=False,
                fields_override=None, native_name=None, payload=b"fixture", reverse=False,
                substituted_payload=None, windows_payload=b"fixture-windows"):
        native = io.BytesIO()
        with tarfile.open(fileobj=native, mode="w:gz") as t:
            for name in ("room-encounter.x86_64", "DIALOGUE_MANAGER_LICENSE.txt",
                         "KENNEY_ASSETS_LICENSE.txt"):
                data = payload if name.endswith("x86_64") else b"fixture"
                item = tarfile.TarInfo(native_name if native_name is not None and name.endswith("x86_64") else name)
                item.size = len(data)
                if link and name.endswith("x86_64"):
                    item.type, item.linkname, item.size = tarfile.SYMTYPE, "/tmp/other", 0
                if traversal and name.endswith("x86_64"):
                    item.name = "../outside"
                t.addfile(item, io.BytesIO(data))
        linux, windows, receipt, manifest, ready = names(PRODUCT)
        fields = dict(BUILD_SCHEMA="1", PRODUCT=PRODUCT, SOURCE_COMMIT=SOURCE,
                      SOURCE_TREE="b"*40, SOURCE_WORKTREE="clean", ENGINE="4.7.2.stable.official.123abc",
                      ENGINE_SHA256="c"*64, TEMPLATE_LINUX_SHA256="d"*64,
                      TEMPLATE_WINDOWS_SHA256="e"*64, RELEASE_PUBLISHED="false",
                      QUALIFICATION="native_headless_preview", LINUX_SCOPE="native_headless_smoke",
                      WINDOWS_SCOPE="export_only")
        if missing_template:
            del fields["TEMPLATE_WINDOWS_SHA256"]
        fields.update(fields_override or {})
        entries = {linux: native.getvalue(), windows: windows_payload,
                   receipt: "".join(f"{k}={v}\n" for k,v in fields.items()).encode()}
        sums = "".join(f"{hashlib.sha256(data).hexdigest()}  {name}\n" for name,data in entries.items())
        if bad_manifest:
            sums = "0"*64 + sums[64:]
        if duplicate:
            sums += sums.splitlines()[0] + "\n"
        entries[manifest] = sums.encode()
        if substituted_payload is not None:
            entries[windows] = substituted_payload
        entries[ready] = f"COMPLETE_SOURCE_COMMIT={'f'*40 if bad_source else SOURCE}\n".encode()
        if extra:
            entries["../outside"] = b"unexpected"
        with zipfile.ZipFile(self.zip, "w") as z:
            for name,data in (reversed(list(entries.items())) if reverse else entries.items()):
                z.writestr(name,data)

    def verify(self, sha=None):
        return verify_archive(self.zip, sha or digest(self.zip), SOURCE, PRODUCT, self.output)

    def test_valid_identity(self):
        self.fixture()
        exe, receipt = self.verify()
        self.assertEqual(exe.read_bytes(), b"fixture")
        self.assertEqual(receipt["executable_sha256"], digest(exe))

    def test_wrong_outer_digest(self):
        self.fixture()
        with self.assertRaisesRegex(ValueError, "outer archive digest"):
            self.verify("0"*64)

    def test_wrong_source(self):
        self.fixture(bad_source=True)
        with self.assertRaisesRegex(ValueError, "READY source"):
            self.verify()

    def test_bad_manifest(self):
        self.fixture(bad_manifest=True)
        with self.assertRaisesRegex(ValueError, "manifest digest"):
            self.verify()

    def test_extra_outer(self):
        self.fixture(extra=True)
        with self.assertRaisesRegex(ValueError, "outer member inventory"):
            self.verify()

    def test_link(self):
        self.fixture(link=True)
        with self.assertRaisesRegex(ValueError, "native member not allowed"):
            self.verify()

    def test_traversal(self):
        self.fixture(traversal=True)
        with self.assertRaisesRegex(ValueError, "native member not allowed"):
            self.verify()

    def test_missing_template(self):
        self.fixture(missing_template=True)
        with self.assertRaisesRegex(ValueError, "incomplete build identity"):
            self.verify()

    def test_duplicate_manifest(self):
        self.fixture(duplicate=True)
        with self.assertRaisesRegex(ValueError, "invalid manifest"):
            self.verify()


if __name__ == "__main__":
    unittest.main(verbosity=2)
