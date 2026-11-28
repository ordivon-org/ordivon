"""Actual one-frame review and aspect-preserving native contact-sheet pixels."""
from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from ordivon_studio.perception_video_io import build_contact_sheet
from ordivon_studio.qc import probe_media
from ordivon_studio.review import build_video_review_packet

FFMPEG = "/usr/bin/ffmpeg"


def fixture(path: Path, size: str, color: str) -> None:
    args = [FFMPEG, "-v", "error", "-f", "lavfi", "-i",
            f"color=c={color}:s={size}:r=30", "-frames:v", "1"]
    if path.suffix == ".mp4":
        args.extend(["-vf", "setparams=range=limited:color_primaries=bt709:color_trc=bt709:colorspace=bt709",
                     "-c:v", "libx264", "-pix_fmt", "yuv420p"])
    subprocess.run([*args, str(path)], check=True, timeout=30)


def rgb(path: Path, width: int, height: int):
    stream = probe_media(path)["streams"][0]
    if (stream["width"], stream["height"]) != (width, height):
        raise AssertionError(stream)
    raw = subprocess.check_output([FFMPEG, "-v", "error", "-i", str(path),
                                   "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                                  timeout=30)
    if len(raw) != width * height * 3:
        raise AssertionError("native RGB byte count disagrees with dimensions")

    def pixel(x, y):
        offset = 3 * (y * width + x)
        return tuple(raw[offset:offset + 3])

    return pixel


class NativePerceptionGeometryTests(unittest.TestCase):
    def test_one_frame_public_review_preserves_geometry(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            production = root / "production"
            production.mkdir()
            (production / "production.json").write_text(json.dumps({
                "id": "single-frame", "workingProfile": {
                    "canvas": {"width": 320, "height": 240},
                    "frameRate": {"numerator": 30, "denominator": 1},
                }, "sources": {},
            }))
            source = root / "one.mp4"
            fixture(source, "320x240", "white")
            output = root / "review"
            packet = build_video_review_packet(
                production_root=production, video_path=source, source_paths=[],
                output_directory=output, repository_root=root,
            )
            self.assertTrue(packet["technicalQc"]["ok"])
            perception = packet["perception"]
            self.assertEqual(perception["totalFrames"], 1)
            self.assertEqual([row["frame"] for row in perception["selectedFrames"]], [0])
            view = perception["modelViews"][0]
            self.assertEqual(view["layout"]["frameOrder"], [0])
            self.assertEqual((view["layout"]["columns"], view["layout"]["rows"]), (1, 1))
            pixel = rgb(output / view["path"], 480, 270)
            self.assertLess(max(pixel(20, 135)), 15)
            self.assertGreater(min(pixel(240, 135)), 235)
            self.assertLess(max(pixel(460, 135)), 15)

    def test_multiple_tiles_preserve_distinct_order_and_fit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            portrait = root / "portrait.png"
            wide = root / "wide.png"
            fixture(portrait, "160x320", "white")
            fixture(wide, "320x160", "red")
            out = root / "sheet.png"
            result = build_contact_sheet([portrait, wide], output_path=out, ffmpeg=FFMPEG)
            self.assertEqual((result["layout"]["columns"], result["layout"]["rows"]), (2, 1))
            self.assertEqual(result["layout"]["thumbnailFit"], "aspect-preserving-fit-with-black-padding")
            pixel = rgb(out, 960, 270)
            self.assertLess(max(pixel(20, 135)), 15)
            self.assertGreater(min(pixel(240, 135)), 235)
            self.assertLess(max(pixel(720, 5)), 15)
            r, g, b = pixel(720, 135)
            self.assertGreater(r, 220)
            self.assertLess(max(g, b), 25)
            for kwargs in ({"columns": 0}, {"columns": True}, {"thumbnail_width": 3}, {"thumbnail_height": -2}):
                with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                    build_contact_sheet([portrait], output_path=root / "invalid.png", ffmpeg=FFMPEG, **kwargs)
                self.assertFalse((root / "invalid.png").exists())
