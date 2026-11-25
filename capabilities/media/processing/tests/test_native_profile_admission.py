"""Actual provider profile counterexamples, independent of the validator."""
from __future__ import annotations

import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class NativeProfileAdmissionTests(unittest.TestCase):
    def test_native_av_and_audio_policy(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            av = json.loads((ROOT / "processing/profiles/av-sdr-web-1080p30-noaudio.json").read_bytes())
            audio = json.loads((ROOT / "processing/profiles/audio-program-48k-mono-lufs23.json").read_bytes())
            video = work / "withaudio.mp4"
            unknown = work / "unknown.mp4"
            loud = work / "loud.wav"
            subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i",
                            "color=c=black:s=1920x1080:r=30:d=0.5", "-f", "lavfi", "-i",
                            "sine=frequency=1000:sample_rate=48000:duration=0.5",
                            "-vf", "setparams=range=limited:color_primaries=bt709:color_trc=bt709:colorspace=bt709",
                            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
                            "-shortest", str(video)], check=True, timeout=30)
            subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i",
                            "color=c=black:s=1920x1080:r=30:d=0.5",
                            "-c:v", "libx264", "-pix_fmt", "yuv420p", str(unknown)],
                           check=True, timeout=30)
            subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i",
                            "sine=frequency=1000:sample_rate=48000:duration=3",
                            "-af", "volume=+6dB", "-c:a", "pcm_s24le", str(loud)],
                           check=True, timeout=30)

            def invoke(name, kind, artifact, profile, code):
                path = work / f"{name}.json"
                path.write_text(json.dumps(profile), encoding="utf-8")
                out = work / name
                result = subprocess.run(["bash", str(ROOT / f"processing/bin/probe-{kind}.sh"),
                                         str(artifact), str(path), str(out)],
                                        capture_output=True, text=True, timeout=30)
                self.assertEqual(result.returncode, code, result.stderr)
                if code == 65:
                    self.assertFalse((out / "evidence.json").exists())
                    self.assertFalse((out / "raw/ffprobe.json").exists())
                else:
                    self.assertEqual(json.loads((out / "evidence.json").read_bytes())["technicalQc"]["ok"], code == 0)

            for presence, code in (("forbiden", 65), (None, 65), (False, 65),
                                   ("optional", 0), ("required", 0), ("forbidden", 2)):
                with self.subTest(presence=presence):
                    p = copy.deepcopy(av)
                    p["audio"]["presence"] = presence
                    invoke(f"av-{presence}", "av", video, p, code)
            p = copy.deepcopy(av)
            for field in ("colorPrimaries", "colorTransfer", "colorSpace", "colorRange"):
                del p["video"][field]
            with self.subTest("missing color contract"):
                invoke("missing-color", "av", unknown, p, 65)
            with self.subTest("known color contract, unknown observation"):
                invoke("unknown-color", "av", unknown, av, 2)
            for tolerance, code in (("1.0", 65), (None, 65), (True, 65), (-1, 65), (1, 2)):
                with self.subTest(tolerance=tolerance):
                    p = copy.deepcopy(audio)
                    p["loudness"]["toleranceLu"] = tolerance
                    invoke(f"audio-{tolerance}", "audio", loud, p, code)
            p = copy.deepcopy(audio)
            p["audio"]["streamIndex"] = False
            with self.subTest("boolean stream index"):
                invoke("audio-index-bool", "audio", loud, p, 65)
