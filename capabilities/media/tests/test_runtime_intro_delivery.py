from __future__ import annotations

import base64
import hashlib
import json
import re
import unittest
import zipfile
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "productions" / "runtime-introduction"


class RuntimeIntroductionDeliveryTests(unittest.TestCase):
    def test_all_five_declared_delivery_files_match_exact_output_bytes(self) -> None:
        production = json.loads((ROOT / "production.json").read_text())
        self.assertEqual(len(production["outputs"]), 5)
        for output in production["outputs"]:
            with self.subTest(output=output["id"]):
                self.assertIn(output["status"], {"approved", "published", "rendered"})
                path = ROOT / output["outputCarrier"]
                self.assertTrue(path.is_file())
                actual = hashlib.sha256(path.read_bytes()).hexdigest()
                self.assertEqual(output["blobDigest"], "sha256:" + actual)

    def test_portfolio_contents_survive_zip_readback_and_full_sha256_manifest(self) -> None:
        package = ROOT / "publish" / "runtime-introduction-portfolio.zip"
        with zipfile.ZipFile(package) as archive:
            self.assertIsNone(archive.testzip())
            manifest = json.loads(archive.read("manifest.json"))
            self.assertEqual(manifest["productionId"], "runtime-introduction")
            self.assertEqual(set(archive.namelist()), {*manifest["assets"], "manifest.json"})
            for name, metadata in manifest["assets"].items():
                with self.subTest(asset=name):
                    data = archive.read(name)
                    self.assertEqual(len(data), metadata["bytes"])
                    self.assertEqual(hashlib.sha256(data).hexdigest(), metadata["sha256"])

    def test_offline_caption_track_matches_downloadable_source_bytes(self) -> None:
        with zipfile.ZipFile(ROOT / "publish" / "runtime-introduction-portfolio.zip") as archive:
            page = archive.read("index.html").decode("utf-8")
            tracks = re.findall(
                r'<track kind="captions" src="data:text/vtt;base64,([A-Za-z0-9+/=]+)"',
                page,
            )
            self.assertEqual(len(tracks), 1)
            self.assertEqual(
                base64.b64decode(tracks[0], validate=True),
                archive.read("captions/narration.en.vtt"),
            )
            self.assertIn("captions/narration.en.srt", archive.namelist())

    def test_offline_reader_is_semantic_html_and_preserves_editable_markdown(self) -> None:
        with zipfile.ZipFile(ROOT / "publish" / "runtime-introduction-portfolio.zip") as archive:
            members = set(archive.namelist())
            self.assertIn("article/runtime-introduction-en.md", members)
            self.assertIn("article/runtime-introduction-en.html", members)
            page = archive.read("article/runtime-introduction-en.html").decode("utf-8")
            self.assertIn('<html lang="en">', page)
            self.assertIn("<article", page)
            self.assertIn("<h1>", page)
            self.assertIn("<table>", page)
            self.assertIn("<th>", page)
            self.assertIn("00:37", page)
            self.assertIn("historical", page.lower())
            self.assertIn('href="../index.html"', page)
            self.assertIn('href="runtime-introduction-en.md"', page)
            self.assertNotIn('src="https://', page)
            self.assertIn("article/runtime-introduction-en.html", archive.read("index.html").decode())
            self.assertIn("../article/runtime-introduction-en.html", archive.read("interactive/index.html").decode())

    def test_standalone_interactive_links_reach_real_source_carriers(self) -> None:
        source = ROOT / "interactive" / "runtime-architecture.html"
        links = re.findall(r'href="([^"]+)"', source.read_text(encoding="utf-8"))
        self.assertEqual(len(links), 3)
        for relative in links:
            with self.subTest(link=relative):
                self.assertTrue((source.parent / relative).is_file(), relative)

    def test_standalone_portfolio_links_and_interactive_wiring(self) -> None:
        with zipfile.ZipFile(ROOT / "publish" / "runtime-introduction-portfolio.zip") as archive:
            files = set(archive.namelist())

            class References(HTMLParser):
                def __init__(self) -> None:
                    super().__init__()
                    self.links: list[str] = []

                def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
                    for attr, value in attrs:
                        if (
                            attr in {"src", "href", "poster"}
                            and value
                            and not value.startswith(("http://", "https://", "#", "data:"))
                        ):
                            self.links.append(value)

            for page in ("index.html", "interactive/index.html"):
                parser = References()
                parser.feed(archive.read(page).decode())
                parent = Path(page).parent
                for relative in parser.links:
                    with self.subTest(page=page, ref=relative):
                        destination = (parent / relative).as_posix()
                        normal = __import__("posixpath").normpath(destination)
                        self.assertIn(normal, files)
            interactive = archive.read("interactive/index.html").decode()
            self.assertIn('addEventListener("click"', interactive)
            self.assertIn("ArrowRight", interactive)
            self.assertIn("not a live simulation", interactive)


if __name__ == "__main__":
    unittest.main()
