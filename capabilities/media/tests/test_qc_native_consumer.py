"""Native differential/metamorphic tests of the actual QC CLI consumer."""
from __future__ import annotations

import hashlib
import json
import math
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


def reject_constant(value):
    raise ValueError(f"not JSON: {value}")


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "native media tools required")
class SelectedAudioConsumerTests(unittest.TestCase):
    def test_selected_stream_and_finite_wire_observation(self):
        with tempfile.TemporaryDirectory(prefix="media native : [qc] ' ") as temp:
            root = Path(temp)
            original = root / "silence-first.mkv"
            swapped = root / "tone-first.mkv"
            subprocess.run([
                "ffmpeg", "-v", "error",
                "-f", "lavfi", "-i", "color=c=black:s=320x240:r=30:d=3",
                "-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono",
                "-f", "lavfi", "-i", "sine=frequency=1000:sample_rate=48000:duration=3",
                "-map", "0:v", "-map", "1:a", "-map", "2:a",
                "-vf", "setparams=range=limited:color_primaries=bt709:color_trc=bt709:colorspace=bt709",
                "-af:a:1", "volume=0.8", "-t", "3",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "pcm_s24le", str(original),
            ], check=True, capture_output=True, timeout=30)
            subprocess.run([
                "ffmpeg", "-v", "error", "-i", str(original),
                "-map", "0:v", "-map", "0:a:1", "-map", "0:a:0", "-c", "copy", str(swapped),
            ], check=True, capture_output=True, timeout=30)

            def invoke(path, index):
                return subprocess.run([
                    sys.executable, "-m", "ordivon_studio.cli", "qc-video", str(path),
                    "--width", "320", "--height", "240", "--frame-rate", "30/1",
                    "--expect-audio", "--audio-stream-count", "2", "--audio-stream-index", str(index),
                    "--audio-codec", "pcm_s24le", "--audio-sample-rate", "48000",
                    "--audio-channels", "1", "--loudness-target-lufs", "-23",
                    "--max-true-peak-dbtp", "-1",
                ], capture_output=True, text=True, timeout=30)

            measurements = {}
            fields = {
                "integratedLoudnessLufs": "input_i", "truePeakDbtp": "input_tp",
                "loudnessRangeLu": "input_lra", "thresholdLufs": "input_thresh",
            }
            for path, tone_index in ((original, 1), (swapped, 0)):
                before = hashlib.sha256(path.read_bytes()).hexdigest()
                for index in (0, 1):
                    with self.subTest(path=path.name, index=index):
                        # Independent native observation: no call to QC implementation.
                        subprocess.run([
                            "ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-map", f"0:a:{index}",
                            "-af", "loudnorm=I=-23:LRA=7:TP=-1:print_format=json:stats_file=oracle.json",
                            "-f", "null", "-",
                        ], cwd=root, check=True, capture_output=True, timeout=30)
                        raw = json.loads((root / "oracle.json").read_text())
                        expected = 0 if index == tone_index else 1
                        run = invoke(path, index)
                        self.assertEqual(run.returncode, expected, run.stdout + run.stderr)
                        result = json.loads(run.stdout, parse_constant=reject_constant)
                        self.assertEqual(result["ok"], expected == 0)
                        self.assertEqual(result["blob"]["digest"], "sha256:" + before)
                        for name, key in fields.items():
                            native = float(raw[key])
                            self.assertEqual(result["loudness"][name], native if math.isfinite(native) else None)
                            self.assertEqual(result["loudnessStanding"][name],
                                             "finite" if math.isfinite(native) else "negative-infinity")
                        measurements[(path.name, index)] = result["loudness"]
                for invalid in (-1, 2):
                    with self.subTest(path=path.name, invalid=invalid):
                        run = invoke(path, invalid)
                        self.assertEqual(run.returncode, 1, run.stderr)
                        result = json.loads(run.stdout, parse_constant=reject_constant)
                        self.assertFalse(result["ok"])
                        self.assertIsNone(result["loudness"])
                        self.assertIsNone(result["loudnessStanding"])
                        self.assertTrue(any("audio stream index" in e for e in result["errors"]))
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), before)
            self.assertEqual(measurements[(original.name, 1)], measurements[(swapped.name, 0)])
            self.assertEqual(measurements[(original.name, 0)], measurements[(swapped.name, 1)])
