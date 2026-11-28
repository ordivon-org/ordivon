"""Use the actual Production Context, lineage and review consumers."""
from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_operation_impact import make_case
from test_review import GOOD_PROBE

from ordivon_studio.production_context import build_production_context
from ordivon_studio.review import build_video_review_packet


class ProductionStrictRepresentationTests(unittest.TestCase):
    def test_actual_context_and_lineage_reject_raw_ambiguity(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_case(root)
            for file, field in (("production.json", "id"), ("claims.json", "productionId"),
                                ("operation-lineage.json", "productionId")):
                path = root / file
                good = path.read_bytes()
                encoded_key = f"\\u{ord(field[0]):04x}{field[1:]}"
                cases = (
                    good.replace(b'{', ('{"' + field + '":"foreign",').encode(), 1),
                    good.replace(b'{', ('{"' + encoded_key + '":"foreign",').encode(), 1),
                    good.replace(b'{', b'{"extra":{"duplicate":1,"duplicate":2},', 1),
                    good.replace(b'{', b'{"extra":NaN,', 1),
                    good.replace(b'{', b'{"extra":1e999,', 1),
                    good + b'{}',
                )
                for invalid in cases:
                    with self.subTest(file=file, raw=invalid[:65]):
                        path.write_bytes(invalid)
                        with self.assertRaises(ValueError):
                            build_production_context(root)
                path.write_bytes(good)
                self.assertIsNotNone(build_production_context(root)["operationLineage"])

    def test_review_rejects_before_native_probe_and_binds_interpreted_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            production = root / "production"
            production.mkdir()
            path = production / "production.json"
            raw = json.dumps({
                "id": "demo",
                "workingProfile": {
                    "frameRate": {"numerator": 30, "denominator": 1},
                    "canvas": {"width": 1920, "height": 1080},
                },
                "sources": {},
            }).encode()
            video = root / "video.mp4"
            video.write_bytes(b"synthetic fixture")
            args = dict(production_root=production, video_path=video,
                        source_paths=[], output_directory=root / "review", repository_root=root)
            path.write_bytes(raw.replace(b'{', b'{"id":"foreign",', 1))
            with patch("ordivon_studio.review.probe_media") as probe:
                with self.assertRaisesRegex(ValueError, "duplicate"):
                    build_video_review_packet(**args)
                probe.assert_not_called()
                self.assertFalse((root / "review").exists())
            path.write_bytes(raw)

            def replace_during_observation(*args, **kwargs):
                path.write_bytes(b'{"id":"replacement"}')
                return GOOD_PROBE

            with patch("ordivon_studio.review.probe_media", side_effect=replace_during_observation), patch(
                "ordivon_studio.review.build_video_perception_bundle", return_value={}
            ):
                result = build_video_review_packet(**args)
            self.assertEqual(result["productionId"], "demo")
            observed = result["decisionContext"][0]["blob"]
            self.assertEqual(observed["digest"], "sha256:" + hashlib.sha256(raw).hexdigest())
            self.assertEqual(observed["sizeBytes"], len(raw))
            self.assertNotEqual(path.read_bytes(), raw)
