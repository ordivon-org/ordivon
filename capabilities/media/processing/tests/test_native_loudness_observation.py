"""Native provider differential and nonfinite measurement boundary."""
from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROFILE = ROOT / "processing/profiles/audio-program-48k-mono-lufs23.json"
PROBE = ROOT / "processing/bin/probe-audio.sh"


class NativeLoudnessObservationTests(unittest.TestCase):
    def test_native_finite_and_silence_with_filter_special_path(self):
        with tempfile.TemporaryDirectory(prefix="media loudness : [test] ' ") as tmp:
            work = Path(tmp)
            for kind, source, filters, expected_code in (
                ("tone", "sine=frequency=1000:sample_rate=48000:duration=3", ["-af", "volume=0.8"], 0),
                ("silence", "anullsrc=r=48000:cl=mono", [], 2),
            ):
                with self.subTest(kind=kind):
                    artifact = work / f"{kind}.wav"
                    subprocess.run(
                        ["ffmpeg", "-v", "error", "-f", "lavfi", "-i", source,
                         "-t", "3", *filters, "-c:a", "pcm_s24le", str(artifact)],
                        check=True, timeout=30,
                    )
                    oracle = subprocess.run(
                        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(artifact),
                         "-map", "0:a:0", "-af", "loudnorm=I=-23:LRA=7:TP=-1:print_format=json",
                         "-f", "null", "-"], capture_output=True, text=True, check=True, timeout=30,
                    )
                    # Independent legacy observation, parse the complete emitted JSON object.
                    start = oracle.stderr.index("{")
                    raw, _ = json.JSONDecoder().raw_decode(oracle.stderr[start:])
                    out = work / f"{kind}-evidence"
                    run = subprocess.run(
                        ["bash", str(PROBE), str(artifact), str(PROFILE), str(out)],
                        capture_output=True, text=True, timeout=30,
                    )
                    self.assertEqual(run.returncode, expected_code, run.stderr)
                    native = out / "raw/ffmpeg-loudnorm.json"
                    self.assertEqual(json.loads(native.read_bytes()), raw)
                    evidence = json.loads((out / "evidence.json").read_bytes())
                    self.assertEqual(evidence["evidence"]["rawLoudnormJsonDigest"],
                                     "sha256:" + hashlib.sha256(native.read_bytes()).hexdigest())
                    self.assertEqual(evidence["technicalQc"]["ok"], expected_code == 0)
                    if kind == "tone":
                        self.assertEqual(evidence["measurement"]["integratedLoudnessLufs"], float(raw["input_i"]))
                        self.assertEqual(evidence["measurementStanding"]["integratedLoudnessLufs"], "finite")
                    else:
                        self.assertEqual(raw["input_i"], "-inf")
                        self.assertIsNone(evidence["measurement"]["integratedLoudnessLufs"])
                        self.assertIsNone(evidence["measurement"]["truePeakDbtp"])
                        self.assertEqual(evidence["measurementStanding"]["integratedLoudnessLufs"], "negative-infinity")
                        self.assertEqual(evidence["measurementStanding"]["truePeakDbtp"], "negative-infinity")
                        assertions = json.loads((out / "assertions.json").read_bytes())
                        for name in ("loudness.integratedLufs", "loudness.truePeakDbtp"):
                            check = next(c for c in assertions["checks"] if c["name"] == name)
                            self.assertIsNone(check["actual"])
                            self.assertFalse(check["ok"])
