from __future__ import annotations

import hashlib
import json
import unittest
import zipfile
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1] / "productions" / "runtime-introduction"


class RuntimeIntroductionDeliveryTests(unittest.TestCase):
    def test_all_five_declared_delivery_files_match_exact_output_bytes(self) -> None:
        production = json.loads((ROOT / "production.json").read_text())
        self.assertEqual(len(production["outputs"]), 5)
        for output in production["outputs"]:
            with self.subTest(output=output["id"]):
                self.assertIn(output["status"], {"approved", "published"})
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

    def test_standalone_portfolio_links_and_interactive_wiring(self) -> None:
        with zipfile.ZipFile(ROOT / "publish" / "runtime-introduction-portfolio.zip") as archive:
            files = set(archive.namelist())
            class References(HTMLParser):
                def __init__(self) -> None:
                    super().__init__()
                    self.links: list[str] = []
                def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
                    for attr, value in attrs:
                        if attr in {"src", "href", "poster"} and value and not value.startswith(("http://", "https://", "#")):
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
            self.assertIn('ArrowRight', interactive)
            self.assertIn("not a live simulation", interactive)


if __name__ == "__main__":
    unittest.main()
