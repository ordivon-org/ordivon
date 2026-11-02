"""Media signal observation, audio/video structural features and controlled comparison."""

from __future__ import annotations

import math
import re
import statistics
import subprocess
import tempfile
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from .assets import probe_media
from .perception import analyze_temporal_change
from .perception_profiles import (
    _bin_series,
    _correlation,
    _mean,
    _resample_profile,
    _vector_distance,
    _z_profile,
    profile_signature,
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

def structural_distance(left: dict[str, Any], right: dict[str, Any]) -> float:
    return _vector_distance(left["structuralVector"], right["structuralVector"])

def technical_fingerprint(features: dict[str, Any]) -> dict[str, Any]:
    return dict(features.get("technical", {}))

def cue_boundary_silence_score(audio: dict[str, Any], timed_text: dict[str, Any], *, window_seconds: float = 0.35) -> dict[str, float]:
    cues = timed_text.get("cues")
    time_base = timed_text.get("timeBase")
    ticks = time_base.get("ticksPerSecond") if isinstance(time_base, dict) else None
    if not isinstance(cues, list) or not isinstance(ticks, int) or ticks <= 0:
        raise ValueError("invalid timed text")
    rms = audio.get("profiles", {}).get("rmsAmplitude")
    duration = float(audio.get("technical", {}).get("durationSeconds") or 0.0)
    if not isinstance(rms, list) or not rms or duration <= 0.0:
        raise ValueError("audio RMS profile unavailable")
    boundaries = sorted({float(cue["startTick"]) / ticks for cue in cues[1:] if isinstance(cue, dict) and isinstance(cue.get("startTick"), int)})
    bin_width = duration / len(rms)
    boundary_values: list[float] = []
    for boundary in boundaries:
        for index, value in enumerate(rms):
            center = (index + 0.5) * bin_width
            if abs(center - boundary) <= window_seconds:
                boundary_values.append(float(value))
    global_mean = _mean([float(value) for value in rms])
    boundary_mean = _mean(boundary_values)
    contrast = (global_mean - boundary_mean) / (statistics.pstdev([float(value) for value in rms]) or 1.0)
    return {
        "boundaryCount": float(len(boundaries)),
        "globalMeanRmsAmplitude": global_mean,
        "boundaryMeanRmsAmplitude": boundary_mean,
        "boundarySilenceContrastZ": contrast,
    }

def crossmodal_profile_coupling(video: dict[str, Any], audio: dict[str, Any]) -> dict[str, float]:
    video_change = video.get("profiles", {}).get("change")
    audio_flux = audio.get("profiles", {}).get("spectralFlux")
    audio_rms = audio.get("profiles", {}).get("rmsAmplitude")
    if not isinstance(video_change, list) or not isinstance(audio_flux, list) or not isinstance(audio_rms, list):
        raise ValueError("crossmodal profiles unavailable")
    bins = min(len(video_change), len(audio_flux), len(audio_rms))
    v = _resample_profile(video_change, bins)
    flux = _resample_profile(audio_flux, bins)
    rms = _resample_profile(audio_rms, bins)
    return {
        "videoChangeAudioFluxCorrelation": _correlation(v, flux),
        "videoChangeAudioRmsCorrelation": _correlation(v, rms),
    }

def _circular_shift_correlation_null(left: Sequence[float], right: Sequence[float]) -> dict[str, float | int]:
    if len(left) != len(right) or len(left) < 4:
        raise ValueError("circular-shift null requires equal profiles with at least four bins")
    values: list[float] = []
    right_values = list(right)
    for shift in range(len(right_values)):
        shifted = right_values[shift:] + right_values[:shift]
        values.append(_correlation(left, shifted))
    baseline = values[0]
    null = values[1:]
    return {
        "baseline": baseline,
        "rankHigh": 1 + sum(value > baseline for value in null),
        "shiftCount": len(null),
        "percentile": sum(value <= baseline for value in values) / len(values),
        "nullMean": statistics.fmean(null),
        "nullSd": statistics.pstdev(null),
        "maxNull": max(null),
        "twoSidedAbsExceedRate": sum(abs(value) >= abs(baseline) for value in null) / len(null),
    }

def crossmodal_circular_shift_null(video: dict[str, Any], audio: dict[str, Any]) -> dict[str, Any]:
    video_change = video.get("profiles", {}).get("change")
    audio_flux = audio.get("profiles", {}).get("spectralFlux")
    audio_rms = audio.get("profiles", {}).get("rmsAmplitude")
    if not isinstance(video_change, list) or not isinstance(audio_flux, list) or not isinstance(audio_rms, list):
        raise ValueError("crossmodal profiles unavailable")
    bins = min(len(video_change), len(audio_flux), len(audio_rms))
    v = _resample_profile(video_change, bins)
    flux = _resample_profile(audio_flux, bins)
    rms = _resample_profile(audio_rms, bins)
    tests = {
        "videoChangeVsAudioFlux": _circular_shift_correlation_null(v, flux),
        "videoChangeVsAudioRms": _circular_shift_correlation_null(v, rms),
    }
    percentiles = [float(item["percentile"]) for item in tests.values()]
    abs_exceed = [float(item["twoSidedAbsExceedRate"]) for item in tests.values()]
    return {
        "bins": bins,
        "tests": tests,
        "disposition": "bounded-positive-alignment-signal" if min(percentiles) >= 0.95 and max(abs_exceed) <= 0.15 else "no-robust-alignment-signal",
        "boundary": "Circular time shifts preserve each modality's marginal profile while perturbing temporal relation. A high baseline percentile is alignment evidence for this artifact, not semantic congruence or aesthetic quality.",
    }

def media_intervention_report(
    *,
    baseline: dict[str, Any],
    controls: Sequence[tuple[str, dict[str, Any]]],
    perturbations: Sequence[tuple[str, dict[str, Any]]],
) -> dict[str, Any]:
    control_distances = [{"id": name, "distance": structural_distance(baseline, features)} for name, features in controls]
    perturbation_distances = [{"id": name, "distance": structural_distance(baseline, features)} for name, features in perturbations]
    max_control = max((item["distance"] for item in control_distances), default=0.0)
    min_perturbation = min((item["distance"] for item in perturbation_distances), default=0.0)
    median_perturbation = statistics.median([item["distance"] for item in perturbation_distances]) if perturbation_distances else 0.0
    return {
        "technicalBaseline": technical_fingerprint(baseline),
        "controls": control_distances,
        "perturbations": perturbation_distances,
        "maxControlDistance": max_control,
        "minPerturbationDistance": min_perturbation,
        "medianPerturbationDistance": median_perturbation,
        "strictSeparation": min_perturbation > max_control,
        "separationRatio": min_perturbation / max_control if max_control > 0.0 else None,
        "exactControlMatch": max_control == 0.0,
        "equipmentDecision": "earned-controlled-sensitivity" if min_perturbation > max_control + 0.05 else "insufficient-controlled-sensitivity",
        "boundary": "This measures whether rich perception detects known structural interventions hidden from shallow technical metadata. It does not claim the perturbation is aesthetically better or worse.",
    }
