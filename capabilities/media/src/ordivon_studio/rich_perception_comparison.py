"""Pure structural and cross-modal comparison of observed media profiles.

No FFmpeg, file I/O, provider state or creative acceptance authority lives here.
Operates only on caller-supplied, bounded observation profiles and native
statistics/Profile operators. Alignment evidence is not semantic or quality truth.
"""

from __future__ import annotations

import statistics
from collections.abc import Sequence
from typing import Any

from .perception_profiles import _correlation, _mean, _resample_profile, _vector_distance


def structural_distance(left: dict[str, Any], right: dict[str, Any]) -> float:
    return _vector_distance(left["structuralVector"], right["structuralVector"])


def technical_fingerprint(features: dict[str, Any]) -> dict[str, Any]:
    return dict(features.get("technical", {}))


def cue_boundary_silence_score(
    audio: dict[str, Any], timed_text: dict[str, Any], *, window_seconds: float = 0.35
) -> dict[str, float]:
    cues = timed_text.get("cues")
    time_base = timed_text.get("timeBase")
    ticks = time_base.get("ticksPerSecond") if isinstance(time_base, dict) else None
    if not isinstance(cues, list) or not isinstance(ticks, int) or ticks <= 0:
        raise ValueError("invalid timed text")
    rms = audio.get("profiles", {}).get("rmsAmplitude")
    duration = float(audio.get("technical", {}).get("durationSeconds") or 0.0)
    if not isinstance(rms, list) or not rms or duration <= 0.0:
        raise ValueError("audio RMS profile unavailable")
    boundaries = sorted(
        {
            float(cue["startTick"]) / ticks
            for cue in cues[1:]
            if isinstance(cue, dict) and isinstance(cue.get("startTick"), int)
        }
    )
    bin_width = duration / len(rms)
    boundary_values: list[float] = []
    for boundary in boundaries:
        for index, value in enumerate(rms):
            center = (index + 0.5) * bin_width
            if abs(center - boundary) <= window_seconds:
                boundary_values.append(float(value))
    global_mean = _mean([float(value) for value in rms])
    boundary_mean = _mean(boundary_values)
    contrast = (global_mean - boundary_mean) / (
        statistics.pstdev([float(value) for value in rms]) or 1.0
    )
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
    if (
        not isinstance(video_change, list)
        or not isinstance(audio_flux, list)
        or not isinstance(audio_rms, list)
    ):
        raise ValueError("crossmodal profiles unavailable")
    bins = min(len(video_change), len(audio_flux), len(audio_rms))
    v = _resample_profile(video_change, bins)
    flux = _resample_profile(audio_flux, bins)
    rms = _resample_profile(audio_rms, bins)
    return {
        "videoChangeAudioFluxCorrelation": _correlation(v, flux),
        "videoChangeAudioRmsCorrelation": _correlation(v, rms),
    }


def _circular_shift_correlation_null(
    left: Sequence[float], right: Sequence[float]
) -> dict[str, float | int]:
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
    if (
        not isinstance(video_change, list)
        or not isinstance(audio_flux, list)
        or not isinstance(audio_rms, list)
    ):
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
        "disposition": "bounded-positive-alignment-signal"
        if min(percentiles) >= 0.95 and max(abs_exceed) <= 0.15
        else "no-robust-alignment-signal",
        "boundary": "Circular time shifts preserve each modality's marginal profile while perturbing temporal relation. A high baseline percentile is alignment evidence for this artifact, not semantic congruence or aesthetic quality.",
    }


def media_intervention_report(
    *,
    baseline: dict[str, Any],
    controls: Sequence[tuple[str, dict[str, Any]]],
    perturbations: Sequence[tuple[str, dict[str, Any]]],
) -> dict[str, Any]:
    control_distances = [
        {"id": name, "distance": structural_distance(baseline, features)}
        for name, features in controls
    ]
    perturbation_distances = [
        {"id": name, "distance": structural_distance(baseline, features)}
        for name, features in perturbations
    ]
    max_control = max((item["distance"] for item in control_distances), default=0.0)
    min_perturbation = min((item["distance"] for item in perturbation_distances), default=0.0)
    median_perturbation = (
        statistics.median([item["distance"] for item in perturbation_distances])
        if perturbation_distances
        else 0.0
    )
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
        "equipmentDecision": "earned-controlled-sensitivity"
        if min_perturbation > max_control + 0.05
        else "insufficient-controlled-sensitivity",
        "boundary": "This measures whether rich perception detects known structural interventions hidden from shallow technical metadata. It does not claim the perturbation is aesthetically better or worse.",
    }
