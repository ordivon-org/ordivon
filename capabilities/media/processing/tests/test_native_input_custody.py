"""Qualify the original selected byte identity against actual native observations."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def digest(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


class NativeInputCustodyTests(unittest.TestCase):
    def setUp(self):
        scratch = tempfile.TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        self.work = Path(scratch.name)
        self.bin = self.work / "bin"
        self.bin.mkdir()
        self.env = dict(os.environ, PATH=f"{self.bin}:{os.environ['PATH']}")

    def interpose(self, name, body, **values):
        real = shutil.which(name)
        self.assertIsNotNone(real)
        self.env.update(values, REAL_NATIVE=real)
        wrapper = self.bin / name
        wrapper.write_text("#!/bin/sh\n" + body)
        wrapper.chmod(0o700)

    def native(self, kind, source, profile, out):
        return subprocess.run(
            ["bash", str(ROOT / f"processing/bin/probe-{kind}.sh"),
             str(source), str(ROOT / f"processing/profiles/{profile}.json"), str(out)],
            env=self.env, capture_output=True, text=True, timeout=60,
        )

    def make_video(self, path, size):
        subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i",
                        f"color=c=black:s={size}:r=30:d=0.3",
                        "-vf", "setparams=range=limited:color_primaries=bt709:color_trc=bt709:colorspace=bt709",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(path)], check=True, timeout=30)

    def make_audio(self, path, rate):
        subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i",
                        f"sine=frequency=1000:sample_rate={rate}:duration=3",
                        "-af", "volume=-2dB", "-c:a", "pcm_s24le", str(path)], check=True, timeout=30)

    def assert_retired(self, out):
        self.assertEqual(list(out.glob(".input.*")), [])

    def test_actual_source_replacement_cannot_relabel_native_observation(self):
        cases = (
            ("av", "video.mp4", "av-sdr-web-1080p30-noaudio", "artifact", "ffprobe"),
            ("audio", "audio.wav", "audio-program-48k-mono-lufs23", "artifact", "ffprobe"),
            ("timed-text", "captions.ttml", "timed-text-runtime-introduction-en", "input", "xmllint"),
        )
        for kind, filename, profile, key, tool in cases:
            with self.subTest(kind=kind):
                source = self.work / filename
                replacement = self.work / ("other-" + filename)
                if kind == "av":
                    self.make_video(source, "1920x1080")
                    self.make_video(replacement, "320x240")
                elif kind == "audio":
                    self.make_audio(source, 48000)
                    self.make_audio(replacement, 44100)
                else:
                    raw = (ROOT / "productions/runtime-introduction/timed-text/standard/narration.en.ttml").read_bytes()
                    source.write_bytes(raw)
                    replacement.write_bytes(b"<invalid/>")
                original = source.read_bytes()
                self.interpose(tool, '''"$REAL_NATIVE" "$@"
status=$?
case "$*" in *-show_streams*|*--noout*) cp -- "$REPLACEMENT" "$SOURCE" ;; esac
exit "$status"
''', SOURCE=str(source), REPLACEMENT=str(replacement))
                out = self.work / ("evidence-" + kind)
                result = self.native(kind, source, profile, out)
                (self.bin / tool).unlink()
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(source.read_bytes(), replacement.read_bytes())
                receipt = json.loads((out / "evidence.json").read_bytes())
                self.assertEqual(receipt[key]["digest"], digest(original))
                self.assertEqual(receipt[key]["sizeBytes"], len(original))
                self.assertEqual(receipt[key]["path"], str(source))
                self.assertEqual(receipt[key]["observationMode"], "attempt-private-copy-retired")
                self.assert_retired(out)
                if kind == "av":
                    probe = json.loads((out / "raw/ffprobe.json").read_bytes())
                    self.assertEqual(probe["streams"][0]["width"], 1920)
                elif kind == "audio":
                    probe = json.loads((out / "raw/ffprobe.json").read_bytes())
                    self.assertEqual(probe["streams"][0]["sample_rate"], "48000")
                else:
                    self.assertEqual(receipt["normalizedFacts"]["cueCount"], 9)

    def test_copy_drift_refuses_observation_and_retires_private_copy(self):
        source = self.work / "video.mp4"
        self.make_video(source, "1920x1080")
        self.interpose("cp", '''"$REAL_NATIVE" "$@" || exit $?
printf changed >> "$SOURCE"
''', SOURCE=str(source))
        out = self.work / "copy-drift"
        result = self.native("av", source, "av-sdr-web-1080p30-noaudio", out)
        self.assertEqual(result.returncode, 75, result.stderr)
        self.assertFalse((out / "raw").exists())
        self.assertFalse((out / "evidence.json").exists())
        self.assert_retired(out)

    def test_observation_snapshot_mutation_refuses_receipt(self):
        source = self.work / "video.mp4"
        self.make_video(source, "1920x1080")
        self.interpose("ffprobe", '''"$REAL_NATIVE" "$@"
status=$?
case "$*" in *-show_streams*)
  for arg do last="$arg"; done
  touch -m -d @1 -- "$last"
  ;;
esac
exit "$status"
''')
        out = self.work / "observation-drift"
        result = self.native("av", source, "av-sdr-web-1080p30-noaudio", out)
        self.assertEqual(result.returncode, 75, result.stderr)
        self.assertTrue((out / "raw/ffprobe.json").is_file())
        self.assertFalse((out / "evidence.json").exists())
        self.assert_retired(out)

    def test_failed_native_observation_retires_copy(self):
        source = self.work / "bad.mp4"
        source.write_bytes(b"not a media container")
        out = self.work / "bad-native"
        result = self.native("av", source, "av-sdr-web-1080p30-noaudio", out)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((out / "evidence.json").exists())
        self.assert_retired(out)
