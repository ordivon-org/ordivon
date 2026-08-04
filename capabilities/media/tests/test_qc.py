from __future__ import annotations

import unittest

from ordivon_studio.qc import validate_video_probe


GOOD_PROBE = {
    "streams": [
        {
            "codec_type": "video",
            "codec_name": "h264",
            "width": 1920,
            "height": 1080,
            "pix_fmt": "yuv420p",
            "avg_frame_rate": "30/1",
            "color_space": "bt709",
            "color_transfer": "bt709",
            "color_primaries": "bt709",
            "color_range": "tv",
        }
    ]
}


class VideoQcTests(unittest.TestCase):
    def test_accepts_expected_motion_render(self) -> None:
        self.assertEqual(
            validate_video_probe(
                GOOD_PROBE,
                width=1920,
                height=1080,
                frame_rate="30/1",
                codec="h264",
                pixel_format="yuv420p",
                color_space="bt709",
                color_range="tv",
                expect_audio=False,
            ),
            [],
        )

    def test_rejects_wrong_color_and_empty_audio_track(self) -> None:
        probe = {
            "streams": [
                {**GOOD_PROBE["streams"][0], "pix_fmt": "yuvj420p", "color_space": "bt470bg"},
                {"codec_type": "audio", "codec_name": "aac"},
            ]
        }
        errors = validate_video_probe(
            probe,
            width=1920,
            height=1080,
            frame_rate="30/1",
            codec="h264",
            pixel_format="yuv420p",
            color_space="bt709",
            color_range="tv",
            expect_audio=False,
        )
        self.assertTrue(any("pix_fmt" in error for error in errors))
        self.assertTrue(any("color_space" in error for error in errors))
        self.assertTrue(any("no audio" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
