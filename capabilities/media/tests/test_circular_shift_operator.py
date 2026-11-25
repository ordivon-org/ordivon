"""Exact native circular-shift operator qualification, no FFT tolerance."""
from __future__ import annotations

import math
import random
import statistics
import subprocess
import tempfile
import unittest
from itertools import product
from pathlib import Path
from unittest.mock import patch

from ordivon_studio.perception_profiles import _circular_shift_correlations, _correlation
from ordivon_studio.rich_perception import (
    audio_structure_features,
    crossmodal_circular_shift_null,
    video_structure_features,
)
from ordivon_studio.rich_perception_comparison import _circular_shift_correlation_null


class CircularShiftOperatorTest(unittest.TestCase):
    def test_circular_shift_native_oracle_exhaustive(self) -> None:
        def oracle(left, right):
            values = []
            for shift in range(len(right)):
                try:
                    values.append(statistics.correlation(left, right[shift:] + right[:shift]))
                except statistics.StatisticsError:
                    values.append(0.0)
            baseline, null = values[0], values[1:]
            return {
                "baseline": baseline,
                "rankHigh": 1 + sum(value > baseline for value in null),
                "shiftCount": len(null),
                "percentile": sum(value <= baseline for value in values) / len(values),
                "nullMean": statistics.fmean(null),
                "nullSd": statistics.pstdev(null),
                "maxNull": max(null),
                "twoSidedAbsExceedRate": sum(abs(v) >= abs(baseline) for v in null) / len(null),
            }

        vectors = list(product((-1.0, 0.0, 1.0), repeat=4))
        for left in vectors:
            for right in vectors:
                self.assertEqual(_circular_shift_correlation_null(left, right), oracle(left, right))
        rng = random.Random(32628)
        for n in (5, 7, 12, 24, 31, 156):
            for _ in range(12):
                left = [rng.randrange(4) for _ in range(n)]
                right = [rng.randrange(4) for _ in range(n)]
                self.assertEqual(_circular_shift_correlation_null(left, right), oracle(left, right))
        # Previously falsified FFT tie case, plus ULP and signed-zero cases.
        for left, right in [
            ([1, 2, 3, 3, 0], [0, 2, 0, 2, 2]),
            ([0.0, -0.0, 1.0, -1.0], [-0.0, 0.0, -1.0, 1.0]),
            ([1.0, math.nextafter(1., 0.), 1., math.nextafter(1., 2.)], [2., 1., 4., 3.]),
        ]:
            self.assertEqual(_circular_shift_correlation_null(left, right), oracle(left, right))

    def test_circular_shift_validates_all_samples_before_native_pearson(self) -> None:
        for bad in (math.nan, math.inf, -math.inf):
            for left, right in [
                ([1., bad, 2., 3.], [1., 2., 3., 4.]),
                ([1., 2., 3., 4.], [1., bad, 2., 3.]),
            ]:
                with patch.object(statistics, "correlation", wraps=statistics.correlation) as native:
                    with self.assertRaises(ValueError):
                        _circular_shift_correlations(left, right)
                    native.assert_not_called()
        for left, right in [([1., 2.], [1., 2.]), ([1.] * 4, [1.] * 5)]:
            with self.assertRaises(ValueError):
                _circular_shift_correlations(left, right)

    def test_circular_shift_native_order_and_single_input_validation(self) -> None:
        left, right = [1., 2., 4., 8.], [2., 8., 1., 4.]
        from ordivon_studio import perception_profiles
        with (
            patch.object(statistics, "correlation", wraps=statistics.correlation) as native,
            patch.object(perception_profiles, "_require_finite_profiles",
                         wraps=perception_profiles._require_finite_profiles) as validate,
        ):
            values = _circular_shift_correlations(left, right)
            validate.assert_called_once_with(left, right)
            self.assertEqual(native.call_count, 4)
            self.assertEqual([c.args for c in native.call_args_list],
                             [(left, right[i:] + right[:i]) for i in range(4)])
            self.assertEqual(values, [statistics.correlation(left, right[i:] + right[:i])
                                      for i in range(4)])

    def test_native_ffmpeg_profiles_keep_exact_report(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            audio = root / "tone.wav"
            video = root / "motion.mp4"
            subprocess.run(
                ["/usr/bin/ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                 "aevalsrc=0.2*sin(2*PI*440*t)*(0.5+0.5*sin(2*PI*t)):s=48000:d=4",
                 "-c:a", "pcm_s24le", str(audio)],
                check=True,
            )
            subprocess.run(
                ["/usr/bin/ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                 "testsrc2=size=160x90:rate=40:duration=4",
                 "-c:v", "libx264", "-pix_fmt", "yuv420p", str(video)],
                check=True,
            )
            a = audio_structure_features(audio, bins=156)
            v = video_structure_features(video, bins=156, sample_step_frames=1)
            candidate = crossmodal_circular_shift_null(v, a)

            def original_rotations(left, right):
                return [_correlation(left, right[i:] + right[:i]) for i in range(len(right))]

            with patch("ordivon_studio.rich_perception_comparison._circular_shift_correlations",
                       side_effect=original_rotations):
                baseline = crossmodal_circular_shift_null(v, a)
            self.assertEqual(candidate, baseline)
            self.assertEqual(candidate["bins"], 156)
            self.assertEqual(candidate["tests"]["videoChangeVsAudioFlux"]["shiftCount"], 155)


if __name__ == "__main__":
    unittest.main()
