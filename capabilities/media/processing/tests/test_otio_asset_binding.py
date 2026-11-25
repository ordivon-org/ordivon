from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import opentimelineio as otio

from ordivon_studio.editorial_asset_binding import verify_editorial_assets

ROOT = Path(__file__).resolve().parents[2]
PRODUCTION = ROOT / "productions/runtime-introduction"
MANIFEST = PRODUCTION / "assets.json"
TIMELINE = PRODUCTION / "timeline/assembly.v2.otio"


def digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


class EditorialAssetBindingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.manifest = self.root / "assets.json"
        self.data = json.loads(MANIFEST.read_bytes())
        self.timeline = self.root / "assembly.otio"

    def verify(self, timeline=TIMELINE, manifest=MANIFEST, **kwargs):
        return verify_editorial_assets(
            timeline, manifest, production_id="runtime-introduction", **kwargs
        )

    def write_manifest(self):
        self.manifest.write_text(json.dumps(self.data), encoding="utf-8")

    def test_real_assemblies_and_native_time_origin(self):
        for version, count in ((0, 11), (1, 1), (2, 2)):
            with self.subTest(version=version):
                path = PRODUCTION / f"timeline/assembly.v{version}.otio"
                result = self.verify(
                    path, expected_timeline_digest=digest(path),
                    expected_manifest_digest=digest(MANIFEST),
                )
                self.assertEqual(len(result["activeReferences"]), count)
                self.assertEqual(result["globalStartTime"], {"value": 108000, "rate": 30})
                self.assertEqual(result["relativeDuration"], {"value": 2340, "rate": 30})
                self.assertEqual(result["frozenBindingStanding"], "caller-commitments-match")
                self.assertEqual(result["materializationStanding"], "not-fully-observed")
                self.assertEqual(result["recipientStanding"], "not-observed")
                self.assertEqual(result["editorialGate"], "not-evaluated")

    def test_native_reference_substitution_rejects_even_with_same_duration(self):
        timeline = otio.adapters.read_from_file(str(TIMELINE))
        clip = timeline.find_clips()[0]
        clip.media_reference.target_url = "ordivon-asset://absent-substitute"
        otio.adapters.write_to_file(timeline, str(self.timeline))
        with self.assertRaisesRegex(ValueError, "undeclared"):
            self.verify(self.timeline)

    def test_duplicate_and_missing_selection_reject(self):
        self.data["assets"].append(self.data["assets"][0])
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, "duplicate Asset ID"):
            self.verify(manifest=self.manifest)
        self.data["assets"].pop()
        selected_id = self.verify()["activeReferences"][0]["assetId"]
        next(a for a in self.data["assets"] if a["id"] == selected_id).pop("selectedBlob")
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, "no selected Blob"):
            self.verify(manifest=self.manifest)

    def test_same_asset_id_changed_blob_is_not_frozen_binding(self):
        selected_id = self.verify()["activeReferences"][0]["assetId"]
        next(a for a in self.data["assets"] if a["id"] == selected_id)["selectedBlob"]["digest"] = (
            "sha256:" + "0" * 64
        )
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, "manifest digest"):
            self.verify(manifest=self.manifest, expected_manifest_digest=digest(MANIFEST))
        self.assertEqual(
            self.verify(manifest=self.manifest)["frozenBindingStanding"], "not-established"
        )
        with self.assertRaisesRegex(ValueError, "timeline digest"):
            self.verify(expected_timeline_digest="sha256:" + "0" * 64)

    def test_physical_match_mismatch_absence_and_receiver_independence(self):
        original = self.verify()
        paths = {}
        for i, asset_id in enumerate(original["assets"]):
            path = self.root / f"blob-{i}"
            path.write_bytes(f"minimal byte identity fixture {i}".encode())
            paths[asset_id] = path
            next(a for a in self.data["assets"] if a["id"] == asset_id)["selectedBlob"] = {
                "digest": digest(path), "sizeBytes": path.stat().st_size,
                "mediaType": "application/octet-stream",
            }
        self.write_manifest()
        result = self.verify(manifest=self.manifest, materialized=paths)
        self.assertEqual(result["materializationStanding"], "all-local-bytes-match")
        self.assertEqual(result["recipientStanding"], "not-observed")
        self.assertEqual(result["frozenBindingStanding"], "not-established")
        asset_id, path = next(iter(paths.items()))
        self.assertEqual(
            self.verify(manifest=self.manifest, materialized={asset_id: path})[
                "materializationStanding"
            ], "not-fully-observed"
        )
        path.write_bytes(b"wrong")
        with self.assertRaisesRegex(ValueError, "bytes do not match"):
            self.verify(manifest=self.manifest, materialized=paths)
        path.unlink()
        with self.assertRaises(FileNotFoundError):
            self.verify(manifest=self.manifest, materialized=paths)
        with self.assertRaisesRegex(ValueError, "not selected"):
            self.verify(materialized={"wrong": path})

    def test_wrong_production_and_unsupported_active_reference(self):
        self.data["productionId"] = "other"
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, "productionId"):
            self.verify(manifest=self.manifest)
        timeline = otio.adapters.read_from_file(str(TIMELINE))
        timeline.find_clips()[0].media_reference = otio.schema.MissingReference()
        otio.adapters.write_to_file(timeline, str(self.timeline))
        with self.assertRaisesRegex(ValueError, "no supported active"):
            self.verify(self.timeline)

    def test_active_reference_key_and_native_range_are_bound(self):
        timeline = otio.adapters.read_from_file(str(TIMELINE))
        clip = timeline.find_clips()[0]
        refs = clip.media_references()
        refs["alternate"] = otio.schema.ExternalReference(
            target_url="ordivon-asset://missing-alternate",
            available_range=clip.media_reference.available_range,
        )
        clip.set_media_references(refs, "DEFAULT_MEDIA")
        otio.adapters.write_to_file(timeline, str(self.timeline))
        result = self.verify(self.timeline)
        first = result["activeReferences"][0]
        self.assertEqual(first["clipIndex"], 0)
        self.assertEqual(first["activeReferenceKey"], "DEFAULT_MEDIA")
        self.assertEqual(first["sourceRange"], {
            "start": {"value": 0, "rate": 30}, "duration": {"value": 2340, "rate": 30}
        })
        self.assertEqual(first["availableRange"], first["sourceRange"])
        clip.set_media_references(refs, "alternate")
        otio.adapters.write_to_file(timeline, str(self.timeline))
        with self.assertRaisesRegex(ValueError, "undeclared"):
            self.verify(self.timeline)

    def test_ambiguous_manifest_key_rejected_even_when_value_matches(self):
        raw = MANIFEST.read_text()
        raw = raw.replace('"schemaVersion": 1,', '"schemaVersion": 1, "schemaVersion": 1,', 1)
        self.manifest.write_text(raw)
        with self.assertRaisesRegex(ValueError, "duplicate manifest key"):
            self.verify(manifest=self.manifest)
