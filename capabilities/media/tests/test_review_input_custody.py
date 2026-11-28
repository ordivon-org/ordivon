"""Actual FFprobe and perception consume one privately selected video."""
from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ordivon_studio.assets import UnstableBlobError, hash_file
from ordivon_studio.input_custody import private_input_observation
from ordivon_studio.qc import probe_media
from ordivon_studio.review import build_video_review_packet


def make_video(path: Path, size: str, color: str) -> None:
    subprocess.run([
        "/usr/bin/ffmpeg", "-v", "error", "-f", "lavfi", "-i",
        f"color=c={color}:s={size}:r=30:d=0.5",
        "-vf", "setparams=range=limited:color_primaries=bt709:color_trc=bt709:colorspace=bt709",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(path),
    ], check=True, timeout=30)


class ReviewInputCustodyTests(unittest.TestCase):
    @unittest.skipUnless(
        Path("/usr/bin/ffmpeg").is_file() and Path("/usr/bin/ffprobe").is_file(),
        "native FFmpeg equipment unavailable",
    )
    def test_real_probe_and_perception_use_same_video_after_source_replacement(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            production = root / "production"
            production.mkdir()
            (production / "production.json").write_text(json.dumps({
                "id": "fixture", "workingProfile": {
                    "canvas": {"width": 1920, "height": 1080},
                    "frameRate": {"numerator": 30, "denominator": 1},
                }, "sources": {},
            }))
            source = root / "video.mp4"
            replacement = root / "replacement.mp4"
            make_video(source, "1920x1080", "black")
            make_video(replacement, "320x240", "white")
            original = hash_file(source)
            changed = hash_file(replacement)
            snapshots = []

            def replace_after_probe(path, ffprobe):
                result = probe_media(path, ffprobe)
                snapshots.append(path)
                replacement.replace(source)
                return result

            with patch("ordivon_studio.review.probe_media", side_effect=replace_after_probe):
                packet = build_video_review_packet(
                    production_root=production, video_path=source, source_paths=[],
                    output_directory=root / "review", repository_root=root,
                )
            self.assertEqual(hash_file(source), changed)
            self.assertEqual(packet["reviewedArtifact"]["blob"], original.as_dict())
            self.assertTrue(packet["technicalQc"]["ok"])
            self.assertEqual(packet["reviewedArtifact"]["technical"]["width"], 1920)
            self.assertEqual(packet["reviewedArtifact"]["path"], "video.mp4")
            self.assertEqual(packet["reviewedArtifact"]["observationMode"], "attempt-private-copy-retired")
            self.assertNotEqual(snapshots[0], source)
            self.assertFalse(snapshots[0].exists())
            for record in packet["perception"]["selectedFrames"]:
                frame = root / "review" / record["path"]
                self.assertEqual(hash_file(frame).as_dict(), record["blob"])
                observed = probe_media(frame)["streams"][0]
                self.assertEqual((observed["width"], observed["height"]), (1920, 1080))
            self.assertTrue((root / "review/review.json").is_file())

    def test_snapshot_mutation_rejected_and_cleaned(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "fixture.mp4"
            source.write_bytes(b"initial")
            with self.assertRaisesRegex(UnstableBlobError, "changed during observation"):
                with private_input_observation(source) as (snapshot, blob):
                    self.assertEqual(blob, hash_file(source))
                    snapshot.write_bytes(b"changed")
            self.assertFalse(snapshot.exists())
            with self.assertRaisesRegex(RuntimeError, "controlled"):
                with private_input_observation(source) as (snapshot, _):
                    raise RuntimeError("controlled")
            self.assertFalse(snapshot.exists())

    def test_source_drift_during_copy_refuses_observation(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "fixture.mp4"
            source.write_bytes(b"original")
            snapshots = []

            def drifting_copy(src, dst):
                snapshots.append(dst)
                dst.write_bytes(src.read_bytes())
                src.write_bytes(b"changed after copy")

            with patch("ordivon_studio.input_custody.shutil.copyfile", side_effect=drifting_copy):
                with self.assertRaisesRegex(UnstableBlobError, "source changed during private copy"):
                    with private_input_observation(source):
                        self.fail("drifting source admitted")
            self.assertFalse(snapshots[0].exists())
