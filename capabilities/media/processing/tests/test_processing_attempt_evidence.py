"""Exercise the real native AV, audio and timed-text evidence boundaries."""
from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def run(*args):
    return subprocess.run(args, capture_output=True, text=True, timeout=45)


def digest(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()


class NativeAttemptEvidenceTests(unittest.TestCase):
    def test_native_attempt_exclusivity_and_receipt_custody(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            video = root / "video.mp4"
            audio = root / "audio.wav"
            text = root / "narration.ttml"
            for cmd in (
                ("ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                 "testsrc2=size=1920x1080:rate=30:duration=1", "-vf",
                 "setparams=range=limited:color_primaries=bt709:color_trc=bt709:colorspace=bt709",
                 "-c:v", "libx264", "-pix_fmt", "yuv420p", "-color_primaries",
                 "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
                 "-color_range", "tv", "-an", str(video)),
                ("ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                 "sine=frequency=1000:sample_rate=48000:duration=3", "-af",
                 "volume=-2dB", "-c:a", "pcm_s24le", str(audio)),
            ):
                result = run(*cmd)
                self.assertEqual(result.returncode, 0, result.stderr)
            text.write_bytes((ROOT / "productions/runtime-introduction/timed-text/standard/narration.en.ttml").read_bytes())
            cases = (
                ("av", video, "av-sdr-web-1080p30-noaudio", "artifact", "technicalQc",
                 {"rawProbeDigest": "raw/ffprobe.json"}),
                ("audio", audio, "audio-program-48k-mono-lufs23", "artifact", "technicalQc",
                 {"rawProbeDigest": "raw/ffprobe.json", "rawLoudnormStderrDigest": "raw/ffmpeg-loudnorm.stderr",
                  "rawLoudnormJsonDigest": "raw/ffmpeg-loudnorm.json"}),
                ("timed-text", text, "timed-text-runtime-introduction-en", "input", "mechanicalDelivery",
                 {"normalizedVttDigest": "raw/normalized.vtt", "packetEvidenceDigest": "raw/ffprobe-subtitle-packets.json"}),
            )
            for kind, source, profile_id, input_key, gate, raw_paths in cases:
                with self.subTest(adapter=kind):
                    profile = ROOT / "processing/profiles" / f"{profile_id}.json"
                    adapter = ROOT / "processing/bin" / f"probe-{kind}.sh"
                    def probe(out):
                        return run("bash", str(adapter), str(source), str(profile), str(out))

                    out = root / kind / "attempt"
                    first = probe(out)
                    self.assertEqual(first.returncode, 0, first.stderr)
                    original = {p.relative_to(out): p.read_bytes() for p in out.rglob("*") if p.is_file()}
                    repeat = probe(out)
                    self.assertEqual(repeat.returncode, 3, repeat.stderr)
                    self.assertEqual(repeat.stdout, "")
                    self.assertEqual({p.relative_to(out): p.read_bytes() for p in out.rglob("*") if p.is_file()}, original)

                    raced = root / kind / "raced"
                    with ThreadPoolExecutor(max_workers=2) as pool:
                        results = list(pool.map(probe, (raced, raced)))
                    self.assertEqual(sorted(r.returncode for r in results), [0, 3])
                    winner = next(r for r in results if r.returncode == 0)
                    receipt = json.loads((raced / "evidence.json").read_bytes())
                    self.assertEqual(receipt, json.loads(winner.stdout))
                    self.assertTrue(receipt[gate]["ok"])
                    self.assertEqual(receipt["evidenceDirectory"], str(raced.resolve()))
                    self.assertEqual(receipt[input_key]["digest"], digest(source.read_bytes()))
                    self.assertEqual(receipt["profile"]["digest"], digest(profile.read_bytes()))
                    for key, path in {**raw_paths, "assertionsDigest": "assertions.json"}.items():
                        self.assertEqual(receipt["evidence"][key], digest((raced / path).read_bytes()))
                    self.assertEqual(list(raced.rglob("*.tmp")), [])

                    source.write_bytes(b"invalid native input")
                    bad = probe(root / kind / "bad")
                    self.assertNotEqual(bad.returncode, 0)
                    self.assertEqual(bad.stdout, "")
                    self.assertFalse((root / kind / "bad/evidence.json").exists())
                    self.assertEqual({p.relative_to(out): p.read_bytes() for p in out.rglob("*") if p.is_file()}, original)
