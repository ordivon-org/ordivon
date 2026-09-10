from __future__ import annotations

import json
import math
import subprocess
from fractions import Fraction
from pathlib import Path
from typing import Any


def _fraction(value: str) -> Fraction:
    try:
        return Fraction(value)
    except (ValueError, ZeroDivisionError) as error:
        raise ValueError(f"invalid rational value: {value!r}") from error


def _int_field(value: object, *, field: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError(f"{field} must be an integer")
    try:
        return int(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{field} must be an integer, found {value!r}") from error


def validate_video_probe(
    probe: dict[str, Any],
    *,
    width: int,
    height: int,
    frame_rate: str,
    codec: str,
    pixel_format: str,
    color_space: str,
    color_range: str,
    expect_audio: bool,
    audio_stream_count: int | None = None,
    audio_codec: str | None = None,
    audio_sample_rate: int | None = None,
    audio_channels: int | None = None,
    audio_channel_layout: str | None = None,
    audio_stream_index: int = 0,
) -> list[str]:
    errors: list[str] = []
    streams = probe.get("streams")
    if not isinstance(streams, list):
        return ["ffprobe result does not contain a streams array"]

    videos = [stream for stream in streams if isinstance(stream, dict) and stream.get("codec_type") == "video"]
    audios = [stream for stream in streams if isinstance(stream, dict) and stream.get("codec_type") == "audio"]
    if len(videos) != 1:
        errors.append(f"expected one video stream, found {len(videos)}")
        return errors

    video = videos[0]
    expectations: list[tuple[str, object]] = [
        ("codec_name", codec),
        ("width", width),
        ("height", height),
        ("pix_fmt", pixel_format),
        ("color_space", color_space),
        ("color_transfer", color_space),
        ("color_primaries", color_space),
        ("color_range", color_range),
    ]
    for field, expected in expectations:
        actual = video.get(field)
        if actual != expected:
            errors.append(f"video {field}: expected {expected!r}, found {actual!r}")

    actual_rate = video.get("avg_frame_rate") or video.get("r_frame_rate")
    if not isinstance(actual_rate, str):
        errors.append("video frame rate is missing")
    elif _fraction(actual_rate) != _fraction(frame_rate):
        errors.append(f"video frame rate: expected {frame_rate}, found {actual_rate}")

    if expect_audio and not audios:
        errors.append("expected an audio stream, found none")
    if not expect_audio and audios:
        errors.append(f"expected no audio stream, found {len(audios)}")
        return errors

    if audio_stream_count is not None and len(audios) != audio_stream_count:
        errors.append(f"audio stream count: expected {audio_stream_count}, found {len(audios)}")

    audio_expectations_present = any(
        value is not None
        for value in (audio_codec, audio_sample_rate, audio_channels, audio_channel_layout)
    )
    if audio_expectations_present:
        if not expect_audio:
            errors.append("audio technical expectations require expect_audio=True")
        elif audio_stream_index < 0 or audio_stream_index >= len(audios):
            errors.append(
                f"audio stream index {audio_stream_index} is unavailable; found {len(audios)} audio stream(s)"
            )
        else:
            audio = audios[audio_stream_index]
            if audio_codec is not None and audio.get("codec_name") != audio_codec:
                errors.append(
                    f"audio codec_name: expected {audio_codec!r}, found {audio.get('codec_name')!r}"
                )
            if audio_sample_rate is not None:
                try:
                    actual_sample_rate = _int_field(audio.get("sample_rate"), field="audio sample_rate")
                except ValueError as error:
                    errors.append(str(error))
                else:
                    if actual_sample_rate != audio_sample_rate:
                        errors.append(
                            f"audio sample_rate: expected {audio_sample_rate}, found {actual_sample_rate}"
                        )
            if audio_channels is not None:
                try:
                    actual_channels = _int_field(audio.get("channels"), field="audio channels")
                except ValueError as error:
                    errors.append(str(error))
                else:
                    if actual_channels != audio_channels:
                        errors.append(f"audio channels: expected {audio_channels}, found {actual_channels}")
            if audio_channel_layout is not None and audio.get("channel_layout") != audio_channel_layout:
                errors.append(
                    "audio channel_layout: "
                    f"expected {audio_channel_layout!r}, found {audio.get('channel_layout')!r}"
                )
    return errors


def measure_loudness(path: Path, ffmpeg: str = "/usr/bin/ffmpeg") -> dict[str, float]:
    """Measure the first audio programme with FFmpeg's BS.1770-family loudnorm filter.

    This performs analysis only. The fixed filter target is used to obtain the filter's
    input measurement fields; acceptance targets remain caller/profile-owned and are
    applied separately by validate_loudness().
    """
    if not path.is_file():
        raise FileNotFoundError(path)
    result = subprocess.run(
        [
            ffmpeg,
            "-hide_banner",
            "-nostats",
            "-i",
            str(path),
            "-map",
            "0:a:0",
            "-af",
            "loudnorm=I=-23:LRA=7:TP=-1:print_format=json",
            "-f",
            "null",
            "-",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"ffmpeg exited {result.returncode}")
    start = result.stderr.rfind("{")
    end = result.stderr.rfind("}")
    if start < 0 or end < start:
        raise RuntimeError("ffmpeg loudnorm output did not contain a JSON measurement")
    try:
        raw = json.loads(result.stderr[start : end + 1])
    except json.JSONDecodeError as error:
        raise RuntimeError("ffmpeg loudnorm JSON measurement could not be parsed") from error

    fields = {
        "integratedLoudnessLufs": "input_i",
        "truePeakDbtp": "input_tp",
        "loudnessRangeLu": "input_lra",
        "thresholdLufs": "input_thresh",
    }
    measurement: dict[str, float] = {}
    for output_field, input_field in fields.items():
        if input_field not in raw:
            raise RuntimeError(f"ffmpeg loudnorm measurement is missing {input_field}")
        try:
            measurement[output_field] = float(raw[input_field])
        except (TypeError, ValueError) as error:
            raise RuntimeError(
                f"ffmpeg loudnorm measurement {input_field} is not numeric: {raw[input_field]!r}"
            ) from error
    return measurement


def validate_loudness(
    measurement: dict[str, float],
    *,
    target_lufs: float | None = None,
    tolerance_lu: float = 1.0,
    max_true_peak_dbtp: float | None = None,
) -> list[str]:
    """Validate measured programme loudness against an explicit Output profile.

    The function intentionally carries no global loudness target. Broadcast, web,
    podcast, archive and platform delivery profiles can set different acceptance
    targets while sharing the same measurement semantics.
    """
    if tolerance_lu < 0:
        raise ValueError("loudness tolerance must be non-negative")
    errors: list[str] = []
    integrated = measurement.get("integratedLoudnessLufs")
    true_peak = measurement.get("truePeakDbtp")

    if target_lufs is not None:
        if integrated is None or not math.isfinite(integrated):
            errors.append(f"integrated loudness is not finite: {integrated!r}")
        elif abs(integrated - target_lufs) > tolerance_lu:
            errors.append(
                "integrated loudness: "
                f"expected {target_lufs:.1f} ± {tolerance_lu:.1f} LU, found {integrated:.1f} LUFS"
            )
    if max_true_peak_dbtp is not None:
        if true_peak is None or not math.isfinite(true_peak):
            errors.append(f"true peak is not finite: {true_peak!r}")
        elif true_peak > max_true_peak_dbtp:
            errors.append(
                f"true peak: expected <= {max_true_peak_dbtp:.1f} dBTP, found {true_peak:.1f} dBTP"
            )
    return errors
