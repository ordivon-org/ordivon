import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "creative_library.py"
spec = importlib.util.spec_from_file_location("creative_library", MODULE_PATH)
creative_library = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(creative_library)


class CreativeLibraryUnitTests(unittest.TestCase):
    def test_presentation_kind_major_media(self):
        cases = {
            "x.PNG": "image", "x.svg": "image", "x.wav": "audio", "x.mp4": "video",
            "x.html": "html", "x.pdf": "pdf", "x.step": "cad", "x.kicad_pcb": "eda",
            "project.godot": "godot", "x.mdx": "text", "x.py": "source", "x.bin": "other",
        }
        for path, expected in cases.items():
            self.assertEqual(creative_library.presentation_kind(path), expected)

    def test_safe_relative_path_rejects_escape(self):
        self.assertEqual(creative_library.safe_relative_path("assets/a.png"), "assets/a.png")
        for bad in ["../secret", "/etc/passwd", "a/../secret", "./x", "a//b", "a\x00b"]:
            with self.assertRaises(ValueError, msg=bad):
                creative_library.safe_relative_path(bad)

    def test_byte_ranges(self):
        self.assertEqual(creative_library.parse_range(None, 100), None)
        self.assertEqual(creative_library.parse_range("bytes=0-9", 100), (0, 9))
        self.assertEqual(creative_library.parse_range("bytes=90-", 100), (90, 99))
        self.assertEqual(creative_library.parse_range("bytes=-10", 100), (90, 99))
        with self.assertRaises(ValueError):
            creative_library.parse_range("bytes=100-101", 100)
        with self.assertRaises(ValueError):
            creative_library.parse_range("items=0-1", 100)

    def test_output_carrier_beats_evidence_carrier(self):
        carriers = [
            {"relativePath": "evidence/preview-validation.png", "kind": "image"},
            {"relativePath": "output/artwork.png", "kind": "image"},
        ]
        self.assertEqual(creative_library.choose_carrier(carriers, launch=False)["relativePath"], "output/artwork.png")

    def test_exact_revision_tree_does_not_follow_current_checkout(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            subprocess.check_call(["git", "init", "-q", str(repo)])
            subprocess.check_call(["git", "-C", str(repo), "config", "user.email", "test@example.invalid"])
            subprocess.check_call(["git", "-C", str(repo), "config", "user.name", "Creative Library Test"])
            (repo / "work").mkdir()
            (repo / "work" / "index.html").write_text("v1", encoding="utf-8")
            subprocess.check_call(["git", "-C", str(repo), "add", "."])
            subprocess.check_call(["git", "-C", str(repo), "commit", "-qm", "v1"])
            rev1 = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
            (repo / "work" / "index.html").write_text("v2", encoding="utf-8")
            subprocess.check_call(["git", "-C", str(repo), "commit", "-qam", "v2"])
            base, carriers = creative_library.git_tree(str(repo), rev1, "work")
            self.assertEqual(base, "work")
            self.assertEqual([c["relativePath"] for c in carriers], ["index.html"])
            body = creative_library._run_git(str(repo), ["cat-file", "blob", f"{rev1}:work/index.html"], binary=True)
            self.assertEqual(body, b"v1")

    def test_catalog_digest_recomputes(self):
        payload = {"a": 1, "b": [2, 3]}
        self.assertEqual(creative_library.canonical_digest(payload), creative_library.canonical_digest(json.loads(json.dumps(payload))))


if __name__ == "__main__":
    unittest.main()


class CreativeLibraryHttpTests(unittest.TestCase):
    def test_raw_server_is_revision_bound_range_capable_and_traversal_closed(self):
        import http.client
        import threading
        import urllib.parse

        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            subprocess.check_call(["git", "init", "-q", str(repo)])
            subprocess.check_call(["git", "-C", str(repo), "config", "user.email", "test@example.invalid"])
            subprocess.check_call(["git", "-C", str(repo), "config", "user.name", "Creative Library HTTP Test"])
            (repo / "work").mkdir()
            (repo / "work" / "artifact.txt").write_text("historical-v1", encoding="utf-8")
            (repo / "work" / "sound.wav").write_bytes(bytes(range(128)))
            subprocess.check_call(["git", "-C", str(repo), "add", "."])
            subprocess.check_call(["git", "-C", str(repo), "commit", "-qm", "v1"])
            rev1 = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
            base, carriers = creative_library.git_tree(str(repo), rev1, "work")
            work = {
                "workId": "test:work", "sourceRepo": str(repo), "sourceRevision": rev1,
                "sourcePath": "work", "sourceBase": base, "carriers": carriers,
            }
            catalog = {"catalogDigest": "test", "works": [work], "relations": []}
            server = creative_library.LibraryServer(("127.0.0.1", 0), catalog)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                # Change current HEAD after the server has frozen rev1.
                (repo / "work" / "artifact.txt").write_text("current-v2", encoding="utf-8")
                subprocess.check_call(["git", "-C", str(repo), "commit", "-qam", "v2"])
                conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
                wid = urllib.parse.quote("test:work", safe="")
                conn.request("GET", f"/raw/{wid}/artifact.txt")
                res = conn.getresponse()
                self.assertEqual(res.status, 200)
                self.assertEqual(res.read(), b"historical-v1")
                conn.close()

                conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
                conn.request("GET", f"/raw/{wid}/sound.wav", headers={"Range": "bytes=10-19"})
                res = conn.getresponse()
                self.assertEqual(res.status, 206)
                self.assertEqual(res.getheader("Content-Range"), "bytes 10-19/128")
                self.assertEqual(res.read(), bytes(range(10, 20)))
                conn.close()

                conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
                conn.request("GET", f"/raw/{wid}/%2e%2e/artifact.txt")
                res = conn.getresponse()
                self.assertEqual(res.status, 400)
                res.read()
                conn.close()
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)


class CreativeLibraryDerivedPreviewTests(unittest.TestCase):
    def test_committed_derived_manifest_is_digest_bound(self):
        previews = creative_library.load_derived_previews(creative_library.DEFAULT_DERIVED_MANIFEST)
        self.assertEqual(len(previews), 6)
        self.assertEqual(previews["game:seen-not-approved-pcb"]["mediaType"], "image/svg+xml")
        self.assertTrue(all(value["standing"].startswith("DERIVED_") for value in previews.values()))

    def test_derived_endpoint_is_separate_digest_checked_and_svg_sandboxed(self):
        import http.client
        import threading
        import urllib.parse

        preview = creative_library.load_derived_previews(creative_library.DEFAULT_DERIVED_MANIFEST)["game:seen-not-approved-pcb"]
        work = {"workId": "game:seen-not-approved-pcb", "carriers": [], "derivedPreview": preview}
        catalog = {"catalogDigest": "test", "works": [work], "relations": []}
        server = creative_library.LibraryServer(("127.0.0.1", 0), catalog)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            wid = urllib.parse.quote(work["workId"], safe="")
            conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
            conn.request("GET", f"/derived/{wid}")
            res = conn.getresponse()
            body = res.read()
            self.assertEqual(res.status, 200)
            self.assertEqual(res.getheader("X-Ordivon-Preview-Standing"), preview["standing"])
            self.assertIn("sandbox", res.getheader("Content-Security-Policy") or "")
            self.assertEqual("sha256:" + __import__("hashlib").sha256(body).hexdigest(), preview["sha256"])
            conn.close()

            bad = dict(preview)
            bad["sha256"] = "sha256:" + "0" * 64
            bad_catalog = {"catalogDigest": "test", "works": [{"workId": work["workId"], "carriers": [], "derivedPreview": bad}], "relations": []}
            bad_server = creative_library.LibraryServer(("127.0.0.1", 0), bad_catalog)
            bad_thread = threading.Thread(target=bad_server.serve_forever, daemon=True)
            bad_thread.start()
            try:
                bad_conn = http.client.HTTPConnection("127.0.0.1", bad_server.server_port, timeout=5)
                bad_conn.request("GET", f"/derived/{wid}")
                bad_res = bad_conn.getresponse()
                self.assertEqual(bad_res.status, 409)
                bad_res.read()
                bad_conn.close()
            finally:
                bad_server.shutdown()
                bad_server.server_close()
                bad_thread.join(timeout=5)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)
