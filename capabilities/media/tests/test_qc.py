from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from ordivon_studio.qc import measure_loudness, validate_loudness, validate_video_probe


GOOD_VIDEO = {
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
GOOD_AUDIO = {
    "codec_type": "audio",
    "codec_name": "aac",
    "sample_rate": "48000",
    "channels": 1,
    "channel_layout": "mono",
}
GOOD_PROBE = {"streams": [GOOD_VIDEO]}
GOOD_AV_PROBE = {"streams": [GOOD_VIDEO, GOOD_AUDIO]}


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

    def test_accepts_profile_bound_audio_facts(self) -> None:
        self.assertEqual(
            validate_video_probe(
                GOOD_AV_PROBE,
                width=1920,
                height=1080,
                frame_rate="30/1",
                codec="h264",
                pixel_format="yuv420p",
                color_space="bt709",
                color_range="tv",
                expect_audio=True,
                audio_stream_count=1,
                audio_codec="aac",
                audio_sample_rate=48000,
                audio_channels=1,
                audio_channel_layout="mono",
            ),
            [],
        )

    def test_rejects_wrong_audio_profile_facts(self) -> None:
        probe = {
            "streams": [
                GOOD_VIDEO,
                {**GOOD_AUDIO, "sample_rate": "44100", "channels": 2, "channel_layout": "stereo"},
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
            expect_audio=True,
            audio_stream_count=1,
            audio_codec="aac",
            audio_sample_rate=48000,
            audio_channels=1,
            audio_channel_layout="mono",
        )
        self.assertTrue(any("sample_rate" in error for error in errors))
        self.assertTrue(any("channels" in error for error in errors))
        self.assertTrue(any("channel_layout" in error for error in errors))

    def test_rejects_wrong_color_and_empty_audio_track(self) -> None:
        probe = {
            "streams": [
                {**GOOD_VIDEO, "pix_fmt": "yuvj420p", "color_space": "bt470bg"},
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

    def test_audio_expectations_cannot_hide_behind_no_audio_profile(self) -> None:
        errors = validate_video_probe(
            GOOD_PROBE,
            width=1920,
            height=1080,
            frame_rate="30/1",
            codec="h264",
            pixel_format="yuv420p",
            color_space="bt709",
            color_range="tv",
            expect_audio=False,
            audio_sample_rate=48000,
        )
        self.assertTrue(any("require expect_audio=True" in error for error in errors))


class LoudnessQcTests(unittest.TestCase):
    def test_profile_target_is_explicit_not_global(self) -> None:
        measurement = {
            "integratedLoudnessLufs": -20.5,
            "truePeakDbtp": -2.2,
            "loudnessRangeLu": 3.0,
            "thresholdLufs": -30.5,
        }
        self.assertEqual(
            validate_loudness(
                measurement,
                target_lufs=-20.0,
                tolerance_lu=1.0,
                max_true_peak_dbtp=-1.0,
            ),
            [],
        )
        errors = validate_loudness(
            measurement,
            target_lufs=-23.0,
            tolerance_lu=1.0,
            max_true_peak_dbtp=-3.0,
        )
        self.assertTrue(any("integrated loudness" in error for error in errors))
        self.assertTrue(any("true peak" in error for error in errors))

    @unittest.skipUnless(shutil.which("ffmpeg"), "ffmpeg is required for real loudness measurement")
    def test_real_ffmpeg_loudness_measurement(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tone.wav"
            result = subprocess.run(
                [
                    shutil.which("ffmpeg") or "/usr/bin/ffmpeg",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-f",
                    "lavfi",
                    "-i",
                    "sine=frequency=1000:sample_rate=48000:duration=2",
                    "-c:a",
                    "pcm_s24le",
                    str(path),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            measurement = measure_loudness(path, shutil.which("ffmpeg") or "/usr/bin/ffmpeg")
            self.assertTrue(measurement["integratedLoudnessLufs"] < 0)
            self.assertTrue(measurement["truePeakDbtp"] <= 0)


if __name__ == "__main__":
    unittest.main()
