"""Source-scoped rational timing interpretation of one FFprobe video stream.

This is metadata interpretation, not a decoder or proof of VFR frame PTS.
A frame count inferred from duration and rate remains an estimate.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any


@dataclass(frozen=True, slots=True)
class VideoTiming:
    rate: Fraction
    rate_source: str
    rate_label: str
    total_frames: int
    frame_count_basis: str
    duration: Fraction | None


def video_timing(probe: dict[str, Any]) -> VideoTiming:
    streams = probe.get("streams")
    videos = [
        row for row in streams
        if isinstance(row, dict) and row.get("codec_type") == "video"
    ] if isinstance(streams, list) else []
    if len(videos) != 1:
        raise ValueError("video timing requires exactly one video stream")

    video = videos[0]
    rate: Fraction | None = None
    rate_source: str | None = None
    rate_label: str | None = None
    for key in ("avg_frame_rate", "r_frame_rate"):
        value = video.get(key)
        if not isinstance(value, str):
            continue
        try:
            candidate = Fraction(value)
        except (ValueError, ZeroDivisionError):
            continue
        if candidate > 0:
            rate, rate_source, rate_label = candidate, key, value
            break
    if rate is None or rate_source is None or rate_label is None:
        raise ValueError("video frame rate is missing, zero or invalid")

    format_info = probe.get("format")
    raw_duration = video.get("duration")
    if raw_duration is None or raw_duration == "N/A":
        raw_duration = format_info.get("duration") if isinstance(format_info, dict) else None
    duration: Fraction | None = None
    if raw_duration is not None:
        try:
            duration = Fraction(str(raw_duration))
        except (ValueError, ZeroDivisionError) as error:
            raise ValueError("video duration is invalid") from error
        if duration <= 0:
            raise ValueError("video duration must be positive")

    raw_frame_count = video.get("nb_frames")
    if isinstance(raw_frame_count, str) and raw_frame_count.isdigit() and int(raw_frame_count) > 0:
        total_frames = int(raw_frame_count)
        count_basis = "container-reported-frame-count"
    elif type(raw_frame_count) is int and raw_frame_count > 0:
        total_frames = raw_frame_count
        count_basis = "container-reported-frame-count"
    else:
        if duration is None:
            raise ValueError("video frame count and duration are both unavailable")
        total_frames = max(1, round(duration * rate))
        count_basis = "duration-times-reported-rate-estimate"

    return VideoTiming(
        rate=rate, rate_source=rate_source, rate_label=rate_label,
        total_frames=total_frames, frame_count_basis=count_basis,
        duration=duration,
    )
