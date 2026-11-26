"""Compare real AV tool observations with core QC on rational equivalence."""
from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from ordivon_studio.qc import validate_video_probe

ROOT = Path(__file__).resolve().parents[2]


class NativeExactQcNumbersTests(unittest.TestCase):
    def test_native_rational_equivalence_and_distinct_neighbor(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "video.mp4"
            subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i",
                            "color=c=black:s=1920x1080:r=30:d=0.3", "-vf",
                            "setparams=range=limited:color_primaries=bt709:color_trc=bt709:colorspace=bt709",
                            "-c:v", "libx264", "-pix_fmt", "yuv420p", str(source)], check=True, timeout=30)
            profile = json.loads((ROOT / "processing/profiles/av-sdr-web-1080p30-noaudio.json").read_bytes())
            path = root / "profile.json"
            for index, (rate, accepted) in enumerate((("30/1", True), ("60/2", True),
                                                       ("3000000000000000090/100000000000000003", True),
                                                       ("3000000000000000091/100000000000000003", False))):
                with self.subTest(rate=rate):
                    profile["video"]["frameRate"] = rate
                    path.write_text(json.dumps(profile))
                    out = root / f"evidence-{index}"
                    run = subprocess.run(["bash", str(ROOT / "processing/bin/probe-av.sh"),
                                          str(source), str(path), str(out)], capture_output=True, text=True, timeout=30)
                    self.assertEqual(run.returncode, 0 if accepted else 2, run.stderr)
                    probe = json.loads((out / "raw/ffprobe.json").read_bytes())
                    errors = validate_video_probe(probe, width=1920, height=1080, frame_rate=rate,
                                                  codec="h264", pixel_format="yuv420p", color_space="bt709",
                                                  color_range="tv", expect_audio=False)
                    self.assertEqual(not errors, accepted)
                    checks = json.loads((out / "assertions.json").read_bytes())["checks"]
                    row = next(row for row in checks if row["name"] == "video.frameRate")
                    self.assertEqual(row["actual"], "30/1")
                    self.assertEqual(row["expected"], rate)
                    self.assertEqual(row["ok"], accepted)
