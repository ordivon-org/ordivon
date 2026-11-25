import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("awa", ROOT / "scripts/artifact_web_archive.py")
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)
BASE = ROOT / "artifact-delivery/shadow-contracts/web-archive-warc-response-smoke-r1.json"
from io import BytesIO

from warcio.statusandheaders import StatusAndHeaders
from warcio.warcwriter import WARCWriter

PAY = b"<!doctype html><html><body>ordivon-webarchive-r1</body></html>\n"


def make(
    path,
    *,
    version="WARC/1.1",
    target="https://example.invalid/archive-r1",
    date="2026-09-12T10:00:00Z",
    extra=False,
    payload=PAY,
):
    with path.open("wb") as f:
        w = WARCWriter(f, gzip=False)
        w.warc_version = version

        def wr(uri, body, rid):
            h = StatusAndHeaders(
                "200 OK",
                [("Content-Type", "text/html; charset=utf-8"), ("Content-Length", str(len(body)))],
                protocol="HTTP/1.1",
            )
            bio = BytesIO(body)
            try:
                r = w.create_warc_record(
                    uri,
                    "response",
                    payload=bio,
                    http_headers=h,
                    warc_headers_dict={"WARC-Date": date, "WARC-Record-ID": rid},
                )
                try:
                    w.write_record(r)
                finally:
                    rs = getattr(r, "raw_stream", None)
                    if rs is not None and hasattr(rs, "close"):
                        rs.close()
            finally:
                bio.close()

        wr(target, payload, "<urn:uuid:11111111-2222-4333-8444-555555555555>")
        if extra:
            wr(
                "https://example.invalid/extra",
                b"extra\n",
                "<urn:uuid:aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee>",
            )


@pytest.mark.integration
class T(unittest.TestCase):
    def test_valid(self):
        with tempfile.TemporaryDirectory() as d:
            r = Path(d)
            p = r / "x.warc"
            make(p)
            v = M.verify_warc(p, BASE, r / "e")
            self.assertEqual(v["status"], "PASS", v)

    def test_wrong_target_contract(self):
        with tempfile.TemporaryDirectory() as d:
            r = Path(d)
            p = r / "x.warc"
            make(p)
            c = json.loads(BASE.read_text())
            c["capture"]["targetUri"] = "https://example.invalid/wrong"
            cp = r / "c.json"
            cp.write_text(json.dumps(c))
            v = M.verify_warc(p, cp, r / "e")
            self.assertEqual(v["status"], "FAIL")
            self.assertEqual(v["warcIntegrity"]["status"], "PASS")

    def test_warc10_valid_but_profile_fail(self):
        with tempfile.TemporaryDirectory() as d:
            r = Path(d)
            p = r / "x.warc"
            make(p, version="WARC/1.0")
            v = M.verify_warc(p, BASE, r / "e")
            self.assertEqual(v["status"], "FAIL")
            self.assertEqual(v["warcIntegrity"]["status"], "PASS")
            self.assertIn("R1 requires WARC/1.1", v["failures"])

    def test_extra_record_valid_but_profile_fail(self):
        with tempfile.TemporaryDirectory() as d:
            r = Path(d)
            p = r / "x.warc"
            make(p, extra=True)
            v = M.verify_warc(p, BASE, r / "e")
            self.assertEqual(v["status"], "FAIL")
            self.assertEqual(v["warcIntegrity"]["status"], "PASS")

    def test_corrupt_payload_fails_integrity(self):
        with tempfile.TemporaryDirectory() as d:
            r = Path(d)
            p = r / "x.warc"
            make(p)
            b = bytearray(p.read_bytes())
            needle = b"ordivon-webarchive-r1"
            i = b.index(needle)
            b[i] ^= 1
            p.write_bytes(b)
            v = M.verify_warc(p, BASE, r / "e")
            self.assertEqual(v["status"], "FAIL")
            self.assertEqual(v["warcIntegrity"]["status"], "FAIL")

    def test_wrong_payload_digest_contract_after_crossview_agreement(self):
        with tempfile.TemporaryDirectory() as d:
            r = Path(d)
            p = r / "x.warc"
            make(p)
            c = json.loads(BASE.read_text())
            c["capture"]["payloadSha256"] = "0" * 64
            cp = r / "c.json"
            cp.write_text(json.dumps(c))
            v = M.verify_warc(p, cp, r / "e")
            self.assertEqual(v["status"], "FAIL")
            self.assertEqual(v["crossView"]["status"], "PASS")
            self.assertEqual(v["warcIntegrity"]["status"], "PASS")

    def test_managed_python_method_and_native_crossview(self):
        from importlib.metadata import version

        with tempfile.TemporaryDirectory() as d:
            r = Path(d)
            p = r / "x.warc"
            make(p)
            v = M.verify_warc(p, BASE, r / "e")
            self.assertEqual(v["status"], "PASS", v)
            self.assertEqual(v["pythonMethod"]["version"], version("warcio"))
            self.assertEqual(
                v["pythonMethod"]["scope"],
                "OBSERVED_MANAGED_PYTHON_MODULES_NOT_FULL_PACKAGE_ATTESTATION",
            )
            for row in v["pythonMethod"]["modules"].values():
                self.assertEqual(
                    hashlib.sha256(Path(row["path"]).read_bytes()).hexdigest(), row["sha256"]
                )
            self.assertEqual(v["crossView"]["status"], "PASS")

    def test_multichunk_payload_crossview_matches_exact_digest(self):
        payload = (b"<p>independent chunk witness</p>" * 120000) + b"tail"
        self.assertGreater(len(payload), 3 * 1024 * 1024)
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            path = root / "large.warc"
            make(path, payload=payload)
            contract = json.loads(BASE.read_text())
            expected = hashlib.sha256(payload).hexdigest()
            contract["capture"]["payloadSha256"] = expected
            cp = root / "contract.json"
            cp.write_text(json.dumps(contract))
            result = M.verify_warc(path, cp, root / "e")
            self.assertEqual(result["status"], "PASS", result)
            for view in ("pythonRecordView", "jsRecordView"):
                self.assertEqual(result[view]["records"][0]["payloadSha256"], expected)
            self.assertEqual(result["crossView"]["status"], "PASS")

    def test_binding_files(self):
        b = json.loads(
            (
                ROOT / "artifact-delivery/shadow-bindings/web-archive-warc-response-local-r1.json"
            ).read_text()
        )
        self.assertEqual(
            hashlib.sha256(
                Path("/opt/ordivon/external/warcio-py/1.8.1/warcio").read_bytes()
            ).hexdigest(),
            b["bindings"]["pythonWarc"]["wrapperSha256"],
        )
        self.assertEqual(
            hashlib.sha256(
                Path("/opt/ordivon/external/warcio-js/2.4.12/package-lock.json").read_bytes()
            ).hexdigest(),
            b["bindings"]["jsWarc"]["packageLockSha256"],
        )


if __name__ == "__main__":
    unittest.main()
