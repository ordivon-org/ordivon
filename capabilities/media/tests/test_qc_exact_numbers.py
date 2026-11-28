"""Exact mechanical numeric semantics independent of native spelling."""
from __future__ import annotations

import unittest

from test_qc import GOOD_AUDIO, GOOD_VIDEO

from ordivon_studio.qc import validate_video_probe
from ordivon_studio.qc_numeric import rates_equal


class ExactQcNumbersTests(unittest.TestCase):
    def test_rational_scale_metamorphism(self):
        for scale in (1, 2, 17, 100000000000000003):
            with self.subTest(scale=scale):
                self.assertTrue(rates_equal("30000/1001", f"{30000*scale}/{1001*scale}"))
                self.assertFalse(rates_equal("30000/1001", f"{30000*scale+1}/{1001*scale}"))
        for invalid in (None, True, 30, "0/0", "30/0", "-30/1", "30.0", "", "3e1/1"):
            self.assertFalse(rates_equal(invalid, "30/1"))

    def test_public_qc_never_truncates_audio_integer_or_accepts_boolean_width(self):
        options = dict(width=1920, height=1080, frame_rate="60/2", codec="h264",
                       pixel_format="yuv420p", color_space="bt709", color_range="tv",
                       expect_audio=True, audio_sample_rate=48000, audio_channels=1)
        for field, invalid in (("sample_rate", 48000.9), ("channels", 1.9),
                               ("channels", True), ("sample_rate", "48000.0")):
            with self.subTest(field=field, invalid=invalid):
                errors = validate_video_probe({"streams": [GOOD_VIDEO, {**GOOD_AUDIO, field: invalid}]}, **options)
                self.assertTrue(any(field in error for error in errors), errors)
        self.assertEqual(validate_video_probe({"streams": [GOOD_VIDEO, GOOD_AUDIO]}, **options), [])
        options["width"] = 1
        self.assertTrue(validate_video_probe({"streams": [{**GOOD_VIDEO, "width": True}, GOOD_AUDIO]}, **options))
