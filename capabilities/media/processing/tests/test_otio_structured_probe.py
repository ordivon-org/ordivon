"""Native behavior tests for the production probe, not implementation shape."""
from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

import opentimelineio as otio

ROOT = Path(__file__).resolve().parents[2]
PROBE = ROOT / "processing/bin/probe-otio.sh"


class StructuredProbeTests(unittest.TestCase):
    def test_native_ranges_and_literal_prefix_not_log_text(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            rng = otio.opentime.TimeRange(
                otio.opentime.RationalTime(0, 30), otio.opentime.RationalTime(30, 30)
            )
            for label, name, url, available, prefix, require, wanted in (
                ("good", "OUT OF BOUNDS", "ordivon-asset://fixture", rng, "ordivon-asset://", True, 0),
                ("unknown", "clip", "ordivon-asset://fixture", None, "ordivon-asset://", True, 2),
                ("optional", "clip", "ordivon-asset://fixture", None, "ordivon-asset://", False, 0),
                ("literal", "clip", "ordivonXasset://fixture", rng, "ordivon.asset://", True, 2),
            ):
                with self.subTest(label=label):
                    timeline = otio.schema.Timeline(name="Smoke")
                    track = otio.schema.Track(name="V1")
                    track.append(otio.schema.Clip(
                        name=name, source_range=rng,
                        media_reference=otio.schema.ExternalReference(
                            target_url=url, available_range=available,
                        ),
                    ))
                    timeline.tracks.append(track)
                    source = root / f"{label}.otio"
                    otio.adapters.write_to_file(timeline, str(source))
                    profile = root / f"{label}.json"
                    profile.write_text(json.dumps({
                        "schemaVersion": 1, "kind": "ordivon.media.v2.otio-profile",
                        "id": label, "timelineName": "Smoke",
                        "startTimecode": "00:00:00:00", "endTimecode": "00:00:01:00",
                        "durationTimecode": "00:00:01:00", "trackCount": 1, "clipCount": 1,
                        "mediaReferenceCount": 1, "requiredMediaPrefix": prefix,
                        "requireAllRangesInBounds": require,
                    }))
                    out = root / label
                    run = subprocess.run(
                        ["bash", str(PROBE), str(source), str(profile), str(out)],
                        capture_output=True, text=True, timeout=45,
                    )
                    self.assertEqual(run.returncode, wanted, run.stderr)
                    evidence = json.loads((out / "evidence.json").read_bytes())
                    self.assertEqual(evidence["editorialGate"]["ok"], wanted == 0)
                    raw = (out / evidence["evidence"]["inspectionPath"]).read_bytes()
                    self.assertEqual(evidence["evidence"]["inspectionDigest"],
                                     "sha256:" + hashlib.sha256(raw).hexdigest())
                    self.assertEqual(evidence["input"]["digest"],
                                     "sha256:" + hashlib.sha256(source.read_bytes()).hexdigest())
                    self.assertEqual(evidence["normalizedFacts"]["unknownRangeCount"],
                                     int(available is None))
                    self.assertEqual(evidence["normalizedFacts"]["outOfBoundsCount"], 0)
                    self.assertEqual(evidence["normalizedFacts"]["badMediaReferencePrefixCount"],
                                     int(label == "literal"))
