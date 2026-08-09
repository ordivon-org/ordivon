from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ordivon_studio.assets import BlobInfo
from ordivon_studio.review import build_video_review_packet


GOOD_PROBE = {
    "streams": [
        {
            "codec_type": "video",
            "codec_name": "h264",
            "pix_fmt": "yuv420p",
            "width": 1920,
            "height": 1080,
            "avg_frame_rate": "30/1",
            "color_space": "bt709",
            "color_transfer": "bt709",
            "color_primaries": "bt709",
            "color_range": "tv",
        }
    ],
    "format": {},
}


class ReviewPacketTests(unittest.TestCase):
    def test_review_packet_binds_sources_and_leaves_semantics_pending(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            production_root = root / "productions" / "demo"
            production_root.mkdir(parents=True)
            (production_root / "cognition.md").write_text("## FRAME\n", encoding="utf-8")
            (production_root / "production.json").write_text(
                json.dumps(
                    {
                        "id": "demo",
                        "workingProfile": {
                            "frameRate": {"numerator": 30, "denominator": 1},
                            "canvas": {"width": 1920, "height": 1080},
                        },
                        "sources": {"cognition": "cognition.md"},
                    }
                ),
                encoding="utf-8",
            )
            video = root / "out.mp4"
            video.write_bytes(b"video")
            source = root / "source.tsx"
            source.write_text("source", encoding="utf-8")
            output = root / "review"

            def fake_extract(_video: Path, frame: int, output_path: Path, _ffmpeg: str) -> None:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_bytes(f"frame-{frame}".encode())

            with (
                patch("ordivon_studio.review.probe_media", return_value=GOOD_PROBE),
                patch("ordivon_studio.review._extract_frame", side_effect=fake_extract),
            ):
                packet = build_video_review_packet(
                    production_root=production_root,
                    video_path=video,
                    source_paths=[source],
                    frames=[0, 15, 15, 29],
                    output_directory=output,
                    repository_root=root,
                )

            self.assertEqual(packet["productionId"], "demo")
            self.assertEqual(packet["disposition"], "disposable-review-evidence")
            self.assertEqual([item["frame"] for item in packet["keyframes"]], [0, 15, 29])
            self.assertEqual(packet["semanticAudit"]["status"], "pending-agent-inspection")
            self.assertTrue(packet["technicalQc"]["ok"])
            self.assertEqual(packet["sourceFiles"][0]["path"], "source.tsx")
            self.assertTrue((output / "review.json").is_file())

    def test_review_packet_rejects_technical_failure_before_keyframe_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            production_root = root / "production"
            production_root.mkdir()
            (production_root / "production.json").write_text(
                json.dumps(
                    {
                        "id": "demo",
                        "workingProfile": {
                            "frameRate": {"numerator": 30, "denominator": 1},
                            "canvas": {"width": 1920, "height": 1080},
                        },
                        "sources": {},
                    }
                ),
                encoding="utf-8",
            )
            video = root / "bad.mp4"
            video.write_bytes(b"bad")
            bad_probe = json.loads(json.dumps(GOOD_PROBE))
            bad_probe["streams"][0]["width"] = 1280
            with patch("ordivon_studio.review.probe_media", return_value=bad_probe):
                with self.assertRaisesRegex(ValueError, "video review QC failed"):
                    build_video_review_packet(
                        production_root=production_root,
                        video_path=video,
                        source_paths=[],
                        frames=[0],
                        output_directory=root / "review",
                        repository_root=root,
                    )


if __name__ == "__main__":
    unittest.main()
