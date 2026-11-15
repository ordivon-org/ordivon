from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ordivon_studio.perception_selection import select_perception_frames
from ordivon_studio.perception_video_io import _parse_change_metadata, extract_review_frames


class PerceptionTests(unittest.TestCase):
    def test_parses_change_samples_back_to_original_frame_time(self) -> None:
        text = """frame:0    pts:15000   pts_time:0.166667\nlavfi.signalstats.YAVG=0.271873\nframe:1    pts:30000   pts_time:0.333333\nlavfi.signalstats.YAVG=4.5\n"""
        samples = _parse_change_metadata(text, fps=30.0, total_frames=180)
        self.assertEqual(samples[0]["frame"], 5)
        self.assertEqual(samples[1]["frame"], 10)
        self.assertEqual(samples[1]["meanAbsoluteLumaDifference"], 4.5)

    def test_selection_combines_coverage_change_and_requested_without_calling_it_meaning(
        self,
    ) -> None:
        samples = [
            {"frame": 25, "meanAbsoluteLumaDifference": 8.0},
            {"frame": 30, "meanAbsoluteLumaDifference": 7.0},
            {"frame": 80, "meanAbsoluteLumaDifference": 6.0},
            {"frame": 140, "meanAbsoluteLumaDifference": 5.0},
            {"frame": 160, "meanAbsoluteLumaDifference": 4.0},
        ]
        frames, reasons, peaks = select_perception_frames(
            total_frames=180,
            change_samples=samples,
            requested_frames=[165],
        )
        self.assertIn(0, frames)
        self.assertIn(179, frames)
        self.assertIn(165, frames)
        self.assertIn("requested", reasons[165])
        self.assertIn(25, [item["frame"] for item in peaks])
        self.assertNotIn(30, [item["frame"] for item in peaks])
        self.assertLessEqual(len(frames), 8)
        self.assertEqual(frames, sorted(frames))

    def test_review_frames_are_extracted_by_one_native_process(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            observed: list[list[str]] = []

            def fake_ffmpeg(args, **_kwargs):
                observed.append(args)
                pattern = str(args[-1])
                for index in range(3):
                    Path(pattern.replace("%06d", f"{index:06d}")).write_bytes(
                        f"selected-{index}".encode()
                    )
                return subprocess.CompletedProcess(args, 0, "", "")

            with patch(
                "ordivon_studio.perception_video_io.subprocess.run",
                side_effect=fake_ffmpeg,
            ) as runner:
                selected = extract_review_frames(
                    root / "source.mp4", [0, 75, 179], root / "frames", "ffmpeg"
                )
            self.assertEqual(runner.call_count, 1)
            self.assertEqual(
                [path.name for path in selected],
                ["frame-000000.png", "frame-000075.png", "frame-000179.png"],
            )
            self.assertEqual(
                [path.read_bytes() for path in selected],
                [b"selected-0", b"selected-1", b"selected-2"],
            )
            self.assertIn("select=eq(n\\,0)+eq(n\\,75)+eq(n\\,179)", observed[0])

    def test_incomplete_native_batch_does_not_publish_partial_frames(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "frames"
            output.mkdir()
            selected = output / "frame-000000.png"
            selected.write_bytes(b"previous complete frame")

            def incomplete_ffmpeg(args, **_kwargs):
                Path(str(args[-1]).replace("%06d", "000000")).write_bytes(b"only-one")
                return subprocess.CompletedProcess(args, 0, "", "")

            with patch(
                "ordivon_studio.perception_video_io.subprocess.run",
                side_effect=incomplete_ffmpeg,
            ):
                with self.assertRaisesRegex(RuntimeError, "incomplete review-frame set"):
                    extract_review_frames(root / "video.mp4", [0, 10], output, "ffmpeg")
            self.assertEqual(selected.read_bytes(), b"previous complete frame")
            self.assertFalse((output / "frame-000010.png").exists())
            self.assertFalse(any(output.glob(".ordivon-review-*")))

    def test_review_frame_batch_rejects_invalid_order_and_negative_indices(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for indices in ([5, 2], [2, 2], [-1], [True]):
                with self.subTest(indices=indices):
                    with self.assertRaises(ValueError):
                        extract_review_frames(root / "video.mp4", indices, root, "ffmpeg")

    def test_small_contact_sheet_contract_does_not_assume_four_real_columns(self) -> None:
        # Layout arithmetic is tested indirectly here as a design invariant: a short source may
        # yield fewer than four distinct observation frames and must not claim empty columns.
        frames, _reasons, _peaks = select_perception_frames(
            total_frames=3,
            change_samples=[],
            max_frames=8,
        )
        self.assertEqual(frames, [0, 1, 2])


if __name__ == "__main__":
    unittest.main()
