"""Observe audio/video signals and assemble profiles; delegate pure comparison."""

from __future__ import annotations

import math
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from .perception_profiles import (
    _bin_series,
    _z_profile,
    profile_signature,
)
from .perception_video_io import analyze_temporal_change
from .qc import probe_media
from .rich_perception_comparison import (
    crossmodal_circular_shift_null as crossmodal_circular_shift_null,
)
from .rich_perception_comparison import (
    crossmodal_profile_coupling as crossmodal_profile_coupling,
)
from .rich_perception_comparison import (
    cue_boundary_silence_score as cue_boundary_silence_score,
)
from .rich_perception_comparison import (
    media_intervention_report as media_intervention_report,
)
from .rich_perception_comparison import (
    structural_distance as structural_distance,
)
from .rich_perception_comparison import (
    technical_fingerprint as technical_fingerprint,
)

RICH_MEDIA_KIND = "ordivon.studio-rich-media-experiment"
AUDIO_PROFILE_KEYS = ("rmsAmplitude", "zeroCrossingRate", "spectralCentroid", "spectralEntropy", "spectralFlatness", "spectralFlux")
_META_FRAME = re.compile(r"^frame:\d+\s+pts:\S+\s+pts_time:(?P<time>-?[0-9.]+)$")
_META_VALUE = re.compile(r"^(?P<key>lavfi\.[^=]+)=(?P<value>.+)$")
_SIGNAL_YAVG = "lavfi.signalstats.YAVG"
_SIGNAL_SATAVG = "lavfi.signalstats.SATAVG"
_AUDIO_KEY_MAP = {
    "lavfi.astats.1.RMS_level": "rmsDb",
    "lavfi.astats.1.Zero_crossings_rate": "zeroCrossingRate",
    "lavfi.aspectralstats.1.centroid": "spectralCentroid",
    "lavfi.aspectralstats.1.entropy": "spectralEntropy",
    "lavfi.aspectralstats.1.flatness": "spectralFlatness",
    "lavfi.aspectralstats.1.flux": "spectralFlux",
}


def _media_duration(probe: dict[str, Any]) -> float:
    value = (probe.get("format") or {}).get("duration") if isinstance(probe.get("format"), dict) else None
    if value is not None:
        return float(value)
    streams = probe.get("streams")
    if isinstance(streams, list):
        durations = [float(item["duration"]) for item in streams if isinstance(item, dict) and item.get("duration") is not None]
        if durations:
            return max(durations)
    raise ValueError("media duration unavailable")

def _video_stream(probe: dict[str, Any]) -> dict[str, Any]:
    streams = probe.get("streams")
    videos = [item for item in streams if isinstance(item, dict) and item.get("codec_type") == "video"] if isinstance(streams, list) else []
    if len(videos) != 1:
        raise ValueError("exactly one video stream required")
    return videos[0]

def _video_geometry(probe: dict[str, Any]) -> tuple[float, int, float]:
    stream = _video_stream(probe)
    frame_rate = stream.get("avg_frame_rate") or stream.get("r_frame_rate")
    if not isinstance(frame_rate, str) or "/" not in frame_rate:
        raise ValueError("video frame rate unavailable")
    numerator, denominator = frame_rate.split("/", 1)
    fps = float(numerator) / float(denominator)
    duration = _media_duration(probe)
    frame_count = stream.get("nb_frames")
    total_frames = int(frame_count) if isinstance(frame_count, str) and frame_count.isdigit() else max(1, int(round(duration * fps)))
    return fps, total_frames, duration

def _parse_signal_metadata(text: str) -> list[dict[str, float]]:
    records: list[dict[str, float]] = []
    current: dict[str, float] | None = None
    for raw in text.splitlines():
        line = raw.strip()
        frame = _META_FRAME.match(line)
        if frame:
            if current is not None:
                records.append(current)
            current = {"timeSeconds": float(frame.group("time"))}
            continue
        value = _META_VALUE.match(line)
        if value and current is not None and value.group("key") in {_SIGNAL_YAVG, _SIGNAL_SATAVG}:
            try:
                current[value.group("key")] = float(value.group("value"))
            except ValueError:
                pass
    if current is not None:
        records.append(current)
    return records

def analyze_video_signal(
    path: Path,
    *,
    sample_step_frames: int = 6,
    ffmpeg: str = "/usr/bin/ffmpeg",
) -> list[dict[str, float]]:
    with tempfile.NamedTemporaryFile(prefix="ordivon-video-signal-", suffix=".txt", delete=False) as handle:
        metadata = Path(handle.name)
    try:
        filter_graph = f"select='not(mod(n\\,{sample_step_frames}))',signalstats,metadata=print:file={metadata}"
        result = subprocess.run(
            [ffmpeg, "-v", "error", "-i", str(path), "-vf", filter_graph, "-an", "-f", "null", "-"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "ffmpeg signalstats failed")
        return _parse_signal_metadata(metadata.read_text(encoding="utf-8"))
    finally:
        metadata.unlink(missing_ok=True)

def video_structure_features(
    path: Path,
    *,
    bins: int = 24,
    sample_step_frames: int = 6,
    ffmpeg: str = "/usr/bin/ffmpeg",
    ffprobe: str = "/usr/bin/ffprobe",
) -> dict[str, Any]:
    probe = probe_media(path, ffprobe)
    fps, total_frames, duration = _video_geometry(probe)
    change = analyze_temporal_change(path, fps=fps, total_frames=total_frames, sample_step_frames=sample_step_frames, ffmpeg=ffmpeg)
    signal = analyze_video_signal(path, sample_step_frames=sample_step_frames, ffmpeg=ffmpeg)
    change_profile = _bin_series(
        [(float(item["timeSeconds"]), float(item["meanAbsoluteLumaDifference"])) for item in change],
        duration=duration,
        bins=bins,
    )
    luma_profile = _bin_series(
        [(float(item["timeSeconds"]), float(item.get(_SIGNAL_YAVG, 0.0))) for item in signal],
        duration=duration,
        bins=bins,
    )
    saturation_profile = _bin_series(
        [(float(item["timeSeconds"]), float(item.get(_SIGNAL_SATAVG, 0.0))) for item in signal],
        duration=duration,
        bins=bins,
    )
    vector = _z_profile(change_profile) + _z_profile(luma_profile) + _z_profile(saturation_profile)
    stream = _video_stream(probe)
    audio_streams = sum(1 for item in probe.get("streams", []) if isinstance(item, dict) and item.get("codec_type") == "audio")
    return {
        "technical": {
            "durationSeconds": duration,
            "width": stream.get("width"),
            "height": stream.get("height"),
            "frameRate": stream.get("avg_frame_rate") or stream.get("r_frame_rate"),
            "audioStreams": audio_streams,
        },
        "profiles": {"change": change_profile, "luma": luma_profile, "saturation": saturation_profile},
        "signatures": {
            "change": profile_signature(change_profile),
            "luma": profile_signature(luma_profile),
            "saturation": profile_signature(saturation_profile),
        },
        "structuralVector": vector,
        "interpretationBoundary": "Temporal change, average luma, and saturation are mechanical visual signals. They detect temporal/content reordering but do not identify semantic scene boundaries or visual quality.",
    }

def _finite_number(text: str, *, floor: float | None = None) -> float | None:
    try:
        value = float(text)
    except ValueError:
        return None
    if math.isfinite(value):
        return value
    return floor

def _parse_audio_metadata(text: str) -> list[dict[str, float]]:
    frames: list[dict[str, float]] = []
    current: dict[str, float] | None = None
    for raw in text.splitlines():
        line = raw.strip()
        frame = _META_FRAME.match(line)
        if frame:
            if current is not None:
                frames.append(current)
            current = {"timeSeconds": float(frame.group("time"))}
            continue
        value = _META_VALUE.match(line)
        if value and current is not None:
            key = _AUDIO_KEY_MAP.get(value.group("key"))
            if key:
                parsed = _finite_number(value.group("value"), floor=-120.0 if key == "rmsDb" else 0.0)
                if parsed is not None:
                    current[key] = parsed
    if current is not None:
        frames.append(current)
    for frame in frames:
        rms_db = frame.get("rmsDb", -120.0)
        frame["rmsAmplitude"] = 10.0 ** (rms_db / 20.0)
    return frames

def analyze_audio_frames(path: Path, *, ffmpeg: str = "/usr/bin/ffmpeg") -> list[dict[str, float]]:
    with tempfile.NamedTemporaryFile(prefix="ordivon-audio-structure-", suffix=".txt", delete=False) as handle:
        metadata = Path(handle.name)
    try:
        filter_graph = (
            "aresample=16000,asetnsamples=n=1600:p=1,"
            "astats=metadata=1:reset=1,"
            "aspectralstats=win_size=1024:measure=centroid+entropy+flatness+flux,"
            f"ametadata=print:file={metadata}"
        )
        result = subprocess.run(
            [ffmpeg, "-v", "error", "-i", str(path), "-vn", "-af", filter_graph, "-f", "null", "-"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "ffmpeg audio structural analysis failed")
        return _parse_audio_metadata(metadata.read_text(encoding="utf-8"))
    finally:
        metadata.unlink(missing_ok=True)

def audio_structure_features(
    path: Path,
    *,
    bins: int = 24,
    ffmpeg: str = "/usr/bin/ffmpeg",
    ffprobe: str = "/usr/bin/ffprobe",
) -> dict[str, Any]:
    probe = probe_media(path, ffprobe)
    duration = _media_duration(probe)
    frames = analyze_audio_frames(path, ffmpeg=ffmpeg)
    profiles: dict[str, list[float]] = {}
    for key in AUDIO_PROFILE_KEYS:
        profiles[key] = _bin_series([(item["timeSeconds"], item.get(key, 0.0)) for item in frames], duration=duration, bins=bins)
    vector: list[float] = []
    for key in AUDIO_PROFILE_KEYS:
        vector.extend(_z_profile(profiles[key]))
    streams = probe.get("streams")
    audios = [item for item in streams if isinstance(item, dict) and item.get("codec_type") == "audio"] if isinstance(streams, list) else []
    if not audios:
        raise ValueError("audio structure requires an audio stream")
    audio = audios[0]
    return {
        "technical": {
            "durationSeconds": duration,
            "sampleRate": audio.get("sample_rate"),
            "channels": audio.get("channels"),
            "codec": audio.get("codec_name"),
        },
        "profiles": profiles,
        "signatures": {key: profile_signature(values) for key, values in profiles.items()},
        "structuralVector": vector,
        "frameCount": len(frames),
        "interpretationBoundary": "Energy, zero crossing, centroid, entropy, flatness, and spectral flux are mechanical audio structure signals. They do not establish musical quality, speech meaning, emotion, or listener preference.",
    }
