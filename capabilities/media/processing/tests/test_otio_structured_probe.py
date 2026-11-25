"""Native behavior tests for the production probe, not implementation shape."""
from __future__ import annotations

import concurrent.futures
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
    def test_evidence_directory_is_single_attempt_and_preserves_history(self):
        source_path = ROOT / "productions/runtime-introduction/timeline/assembly.v2.otio"
        profile = ROOT / "processing/profiles/otio-runtime-introduction-v2.json"
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source.otio"
            source.write_bytes(source_path.read_bytes())

            def run(out):
                return subprocess.run(
                    ["bash", str(PROBE), str(source), str(profile), str(out)],
                    capture_output=True, text=True, timeout=45,
                )

            out = root / "attempt"
            first = run(out)
            self.assertEqual(first.returncode, 0, first.stderr)
            before = {p.relative_to(out): p.read_bytes() for p in out.rglob("*") if p.is_file()}
            self.assertEqual(json.loads(first.stdout)["editorialGate"]["ok"], True)
            # Valid repeat is rejected, rather than overwriting the first receipt.
            repeat = run(out)
            self.assertNotEqual(repeat.returncode, 0)
            self.assertEqual(repeat.stdout, "")
            self.assertEqual({p.relative_to(out): p.read_bytes() for p in out.rglob("*") if p.is_file()}, before)

            # Concurrent callers for one destination cannot both publish evidence.
            raced = root / "raced"
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(run, (raced, raced)))
            self.assertEqual(sum(r.returncode == 0 for r in results), 1)
            winner = next(r for r in results if r.returncode == 0)
            receipt = json.loads((raced / "evidence.json").read_bytes())
            self.assertEqual(receipt, json.loads(winner.stdout))
            self.assertEqual(receipt["evidenceDirectory"], str(raced.resolve()))
            self.assertEqual(list(raced.rglob("*.tmp")), [])

            # A failed new attempt cannot publish a previous success; a prior
            # receipt remains immutable and cannot match substituted input.
            source.write_bytes(b"invalid OTIO")
            failed = run(root / "failed")
            self.assertNotEqual(failed.returncode, 0)
            self.assertEqual(failed.stdout, "")
            self.assertFalse((root / "failed/evidence.json").exists())
            self.assertEqual({p.relative_to(out): p.read_bytes() for p in out.rglob("*") if p.is_file()}, before)
            self.assertNotEqual(receipt["input"]["digest"],
                                "sha256:" + hashlib.sha256(source.read_bytes()).hexdigest())

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
