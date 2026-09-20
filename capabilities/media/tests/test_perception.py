from __future__ import annotations

import unittest

from ordivon_studio.perception import _parse_change_metadata, select_perception_frames


class PerceptionTests(unittest.TestCase):
    def test_parses_change_samples_back_to_original_frame_time(self) -> None:
        text = """frame:0    pts:15000   pts_time:0.166667\nlavfi.signalstats.YAVG=0.271873\nframe:1    pts:30000   pts_time:0.333333\nlavfi.signalstats.YAVG=4.5\n"""
        samples = _parse_change_metadata(text, fps=30.0, total_frames=180)
        self.assertEqual(samples[0]["frame"], 5)
        self.assertEqual(samples[1]["frame"], 10)
        self.assertEqual(samples[1]["meanAbsoluteLumaDifference"], 4.5)

    def test_selection_combines_coverage_change_and_requested_without_calling_it_meaning(self) -> None:
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
