import binascii
import importlib.util
import struct
import tempfile
import unittest
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("artifact_still_image", ROOT / "scripts/artifact_still_image.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def chunk(kind: bytes, payload: bytes) -> bytes:
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", binascii.crc32(kind + payload) & 0xFFFFFFFF)


def minimal_rgb_png(path: Path, *, srgb: bool) -> None:
    signature = b"\x89PNG\r\n\x1a\n"
    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    color = chunk(b"sRGB", b"\x00") if srgb else b""
    # one scanline: filter=0, RGB=(32,64,128)
    data = chunk(b"IDAT", zlib.compress(bytes([0, 32, 64, 128])))
    path.write_bytes(signature + ihdr + color + data + chunk(b"IEND", b""))


class ArtifactStillImageTests(unittest.TestCase):
    def require_tools(self):
        for path in (MODULE.PNGCHECK, MODULE.EXIFTOOL, MODULE.MAGICK, MODULE.VIPS, MODULE.VIPSHEADER):
            if not path.is_file():
                self.skipTest(f"required mature external tool is unavailable: {path}")

    def test_static_8bit_srgb_png_passes_bounded_shadow_profile(self):
        self.require_tools()
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); image = root / "valid.png"; evidence = root / "evidence"
            minimal_rgb_png(image, srgb=True)
            value = MODULE.verify_png_srgb(image, evidence)
            self.assertEqual(value["status"], "PASS", value)
            self.assertTrue(value["decoderMatrix"]["exactMatch"])
            self.assertEqual(value["image"]["depth"], 8)
            self.assertIn("sRGB", value["png"]["chunks"])
            self.assertTrue((evidence / "pngcheck.txt").is_file())
            self.assertTrue((evidence / "exiftool.json").is_file())

    def test_png_validity_does_not_launder_missing_profile_color_fact(self):
        self.require_tools()
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); image = root / "valid-but-not-profile.png"
            minimal_rgb_png(image, srgb=False)
            pngcheck = MODULE.run([str(MODULE.PNGCHECK), "-q", str(image)])
            self.assertEqual(pngcheck.returncode, 0, pngcheck.stderr)
            value = MODULE.verify_png_srgb(image, root / "evidence")
            self.assertEqual(value["status"], "FAIL")
            self.assertIn("missing required PNG chunk(s): sRGB", value["failures"])

    def test_corrupt_png_fails_closed(self):
        self.require_tools()
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); image = root / "corrupt.png"
            minimal_rgb_png(image, srgb=True)
            data = bytearray(image.read_bytes())
            pos = data.find(b"IDAT")
            self.assertGreater(pos, 0)
            data[pos + 5] ^= 1
            image.write_bytes(data)
            value = MODULE.verify_png_srgb(image, root / "evidence")
            self.assertEqual(value["status"], "FAIL")
            self.assertIn("pngcheck rejected the PNG datastream", value["failures"])


if __name__ == "__main__":
    unittest.main()
