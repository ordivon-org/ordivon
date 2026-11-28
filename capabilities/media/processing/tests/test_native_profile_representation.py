"""Raw profile admission and exact snapshot custody across real adapters."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from ordivon_studio.agent_processing import processing_profiles

ROOT = Path(__file__).resolve().parents[2]


def digest(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()


class NativeProfileRepresentationTests(unittest.TestCase):
    def test_actual_native_adapters_refuse_ambiguous_profile_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            work = Path(temp)
            catalog = work / "processing/profiles"
            catalog.mkdir(parents=True)
            av = work / "video.mp4"
            audio = work / "audio.wav"
            subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i",
                            "color=c=black:s=1920x1080:r=30:d=0.5",
                            "-vf", "setparams=range=limited:color_primaries=bt709:color_trc=bt709:colorspace=bt709",
                            "-c:v", "libx264", "-pix_fmt", "yuv420p", str(av)], check=True, timeout=30)
            subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i",
                            "sine=frequency=1000:sample_rate=48000:duration=3",
                            "-af", "volume=-2dB", "-c:a", "pcm_s24le", str(audio)], check=True, timeout=30)
            cases = (
                ("av", av, "av-sdr-web-1080p30-noaudio"),
                ("audio", audio, "audio-program-48k-mono-lufs23"),
                ("timed-text", ROOT / "productions/runtime-introduction/timed-text/standard/narration.en.ttml",
                 "timed-text-runtime-introduction-en"),
                ("otio", ROOT / "productions/runtime-introduction/timeline/assembly.v2.otio",
                 "otio-runtime-introduction-v2"),
            )
            for kind, source, name in cases:
                raw = (ROOT / f"processing/profiles/{name}.json").read_bytes()
                profile = catalog / "profile.json"
                # Include decoded-key equality (escaped duplicate), nesting,
                # exact version type, non-standard literals and overflow.
                invalid = {
                    "duplicate": raw.replace(b'{', b'{"id":"shadow",', 1),
                    "escaped-duplicate": raw.replace(b'{', b'{"\\u0069d":"shadow",', 1),
                    "nested": raw.replace(b'{', b'{"extra":{"x":1,"x":2},', 1),
                    "bool": raw.replace(b'"schemaVersion": 1', b'"schemaVersion": true'),
                    "float-version": raw.replace(b'"schemaVersion": 1', b'"schemaVersion": 1.0'),
                    "nan": raw.replace(b'{', b'{"extra":NaN,', 1),
                    "overflow": raw.replace(b'{', b'{"extra":1e999,', 1),
                    "two-documents": raw + b'{}',
                }
                for label, data in invalid.items():
                    with self.subTest(kind=kind, label=label):
                        self.assertNotEqual(data, raw)
                        profile.write_bytes(data)
                        with self.assertRaises(ValueError):
                            processing_profiles(work)
                        out = work / f"{kind}-{label}"
                        run = subprocess.run(["bash", str(ROOT / f"processing/bin/probe-{kind}.sh"),
                                              str(source), str(profile), str(out)],
                                             capture_output=True, text=True, timeout=60)
                        self.assertEqual(run.returncode, 65, run.stderr)
                        self.assertFalse((out / "raw").exists())
                        self.assertFalse((out / "evidence.json").exists())
                profile.write_bytes(raw)
                self.assertEqual(processing_profiles(work)["profiles"][0]["profileDigest"], digest(raw))
                out = work / f"{kind}-good"
                run = subprocess.run(["bash", str(ROOT / f"processing/bin/probe-{kind}.sh"),
                                      str(source), str(profile), str(out)],
                                     capture_output=True, text=True, timeout=60)
                self.assertEqual(run.returncode, 0, run.stderr)
                receipt = json.loads((out / "evidence.json").read_bytes())
                self.assertEqual(receipt["profile"]["digest"], digest(raw))
                self.assertEqual(receipt["profile"]["path"], str(profile))
                self.assertEqual((out / receipt["profile"]["snapshotPath"]).read_bytes(), raw)

    def test_profile_source_replacement_during_real_probe_does_not_change_receipt(self):
        with tempfile.TemporaryDirectory() as temp:
            work = Path(temp)
            profile = work / "profile.json"
            raw = (ROOT / "processing/profiles/audio-program-48k-mono-lufs23.json").read_bytes()
            profile.write_bytes(raw)
            audio = work / "tone.wav"
            subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i",
                            "sine=frequency=1000:sample_rate=48000:duration=3",
                            "-af", "volume=-2dB", "-c:a", "pcm_s24le", str(audio)], check=True, timeout=30)
            # Interpose only a test-scoped wrapper; still execute the actual FFprobe.
            # Replace the caller's file after admission with a stricter tolerance/target.
            real_probe = shutil.which("ffprobe")
            self.assertIsNotNone(real_probe)
            replacement = work / "replacement.json"
            changed = json.loads(raw)
            changed["loudness"]["targetLufs"] = -50
            replacement.write_text(json.dumps(changed))
            bin_dir = work / "bin"
            bin_dir.mkdir()
            wrapper = bin_dir / "ffprobe"
            wrapper.write_text('#!/bin/sh\ncase "$*" in *-show_streams*) cp -- "$REPLACEMENT" "$PROFILE" ;; esac\nexec "$REAL_FFPROBE" "$@"\n')
            wrapper.chmod(0o700)
            out = work / "evidence"
            env = dict(os.environ, PATH=f"{bin_dir}:{os.environ['PATH']}",
                       REPLACEMENT=str(replacement), PROFILE=str(profile), REAL_FFPROBE=str(real_probe))
            run = subprocess.run(["bash", str(ROOT / "processing/bin/probe-audio.sh"), str(audio), str(profile), str(out)],
                                 env=env, capture_output=True, text=True, timeout=60)
            self.assertEqual(profile.read_bytes(), replacement.read_bytes())
            self.assertEqual(run.returncode, 0, run.stderr)
            receipt = json.loads((out / "evidence.json").read_bytes())
            self.assertEqual(receipt["profile"]["digest"], digest(raw))
            self.assertEqual((out / receipt["profile"]["snapshotPath"]).read_bytes(), raw)
            self.assertTrue(receipt["technicalQc"]["ok"])

    def test_timed_text_numeric_limit_is_not_a_string(self):
        with tempfile.TemporaryDirectory() as temp:
            work = Path(temp)
            profile = json.loads((ROOT / "processing/profiles/timed-text-runtime-introduction-en.json").read_bytes())
            profile["maxEndSeconds"] = "1"
            path = work / "profile.json"
            path.write_text(json.dumps(profile))
            source = ROOT / "productions/runtime-introduction/timed-text/standard/narration.en.ttml"
            out = work / "evidence"
            run = subprocess.run(["bash", str(ROOT / "processing/bin/probe-timed-text.sh"), str(source), str(path), str(out)],
                                 capture_output=True, text=True, timeout=60)
            self.assertEqual(run.returncode, 65, run.stderr)
            self.assertFalse((out / "raw").exists())
