from __future__ import annotations

from fractions import Fraction
from typing import Any


def _fraction(value: str) -> Fraction:
    try:
        return Fraction(value)
    except (ValueError, ZeroDivisionError) as error:
        raise ValueError(f"invalid rational value: {value!r}") from error


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
