"""Independent bounded sampling invariants and exact frame identity."""
from __future__ import annotations

import unittest

from hypothesis import given, settings
from hypothesis import strategies as st

from ordivon_studio.perception_selection import select_perception_frames


@st.composite
def cases(draw):
    total = draw(st.integers(1, 200))
    budget = draw(st.integers(2, 12))
    ids = st.integers(0, total - 1)
    requested = draw(st.lists(ids, unique=True, max_size=min(total, budget)))
    samples = draw(st.dictionaries(ids, st.integers(0, 255), max_size=min(total, 20)))
    rows = [{"frame": frame, "meanAbsoluteLumaDifference": score} for frame, score in samples.items()]
    return total, budget, requested, rows, draw(st.integers(0, 8)), draw(st.integers(0, 10))


class SamplingProperties(unittest.TestCase):
    @settings(max_examples=150, deadline=None)
    @given(cases())
    def test_selection_identity_budget_and_permutation(self, case):
        total, budget, requested, rows, peak_budget, gap = case
        opts = dict(total_frames=total, max_frames=budget, requested_frames=requested,
                    change_peak_count=peak_budget, min_peak_gap_frames=gap)
        selected, reasons, peaks = select_perception_frames(change_samples=rows, **opts)
        self.assertEqual(selected, sorted(set(selected)))
        self.assertTrue(set(requested) <= set(selected) <= set(range(total)))
        self.assertLessEqual(len(selected), budget)
        self.assertLessEqual(len(peaks), peak_budget)
        self.assertEqual(set(reasons), set(selected))
        self.assertTrue(all("requested" in reasons[frame] for frame in requested))
        self.assertTrue(all(peak in rows and peak["frame"] in selected for peak in peaks))
        self.assertEqual((selected, reasons, peaks),
                         select_perception_frames(change_samples=list(reversed(rows)), **opts))
        for index, peak in enumerate(peaks):
            self.assertTrue(all(abs(peak["frame"] - other["frame"]) >= gap for other in peaks[index+1:]))

    def test_invalid_requests_and_observations_are_not_relabelled(self):
        for opts in (
            {"requested_frames": [99]}, {"requested_frames": [-1]}, {"requested_frames": [True]},
            {"requested_frames": [1.5]}, {"requested_frames": [0, 1, 2], "max_frames": 2},
            {"change_samples": [{"frame": 99, "meanAbsoluteLumaDifference": 1}]},
            {"change_samples": [{"frame": True, "meanAbsoluteLumaDifference": 1}]},
            {"change_samples": [{"frame": 1, "meanAbsoluteLumaDifference": float("nan")}]},
            {"change_samples": [{"frame": 1, "meanAbsoluteLumaDifference": -1}]},
            {"change_samples": [{"frame": 1, "meanAbsoluteLumaDifference": 1}]*2},
            {"change_peak_count": -1}, {"coverage_count": 0}, {"total_frames": 0},
        ):
            with self.subTest(opts=opts), self.assertRaises(ValueError):
                select_perception_frames(**(dict(total_frames=5, change_samples=[]) | opts))

    def test_large_frame_coordinates_remain_exact_without_float(self):
        n = 2**60 + 3
        selected, reasons, _ = select_perception_frames(
            total_frames=n, coverage_count=4, max_frames=4, change_samples=[], change_peak_count=0)
        self.assertEqual(selected[0], 0)
        self.assertEqual(selected[-1], n - 1)
        self.assertEqual(len(reasons), 4)
