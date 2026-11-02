"""Deterministic statistical profile operators shared by article and media analysis."""

from __future__ import annotations

import hashlib
import json
import math
import statistics
from collections.abc import Sequence
from typing import Any


def _mean(values: Sequence[float]) -> float:
    return statistics.fmean(values) if values else 0.0

def _cv(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    mean = statistics.fmean(values)
    return statistics.pstdev(values) / abs(mean) if mean else 0.0

def _quantile(values: Sequence[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = fraction * (len(ordered) - 1)
    lower = int(math.floor(position))
    upper = min(len(ordered) - 1, lower + 1)
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight

def _correlation(left: Sequence[float], right: Sequence[float]) -> float:
    # Media's domain contract treats degenerate *finite* profiles as zero coupling.
    # Reject non-finite samples before calling the standard Pearson operator.
    if any(not math.isfinite(value) for series in (left, right) for value in series):
        raise ValueError("Media correlation profiles must contain finite numbers")
    if len(left) != len(right) or len(left) < 2:
        return 0.0
    try:
        result = statistics.correlation(left, right)
    except statistics.StatisticsError:
        return 0.0
    if not math.isfinite(result):
        raise ValueError("Media correlation result must be finite")
    return result

def _normalized_entropy(values: Sequence[float]) -> float:
    positive = [max(0.0, float(value)) for value in values]
    total = sum(positive)
    if total <= 0.0 or len(positive) < 2:
        return 0.0
    probabilities = [value / total for value in positive if value > 0.0]
    entropy = -sum(value * math.log(value) for value in probabilities)
    return entropy / math.log(len(positive)) if len(positive) > 1 else 0.0

def _z_profile(values: Sequence[float]) -> list[float]:
    if not values:
        return []
    mean = statistics.fmean(values)
    scale = statistics.pstdev(values) or 1.0
    return [(float(value) - mean) / scale for value in values]

def profile_signature(values: Sequence[float]) -> dict[str, float]:
    sequence = [float(value) for value in values]
    if not sequence:
        return {
            "coefficientVariation": 0.0,
            "normalizedEntropy": 0.0,
            "lag1Correlation": 0.0,
            "peakPosition": 0.0,
            "earlyLateDeltaZ": 0.0,
            "turningPointRate": 0.0,
        }
    z = _z_profile(sequence)
    peak_index = max(range(len(sequence)), key=lambda index: sequence[index])
    third = max(1, len(z) // 3)
    early = _mean(z[:third])
    late = _mean(z[-third:])
    turning_points = 0
    for index in range(1, len(sequence) - 1):
        before = sequence[index] - sequence[index - 1]
        after = sequence[index + 1] - sequence[index]
        if before and after and before * after < 0:
            turning_points += 1
    return {
        "coefficientVariation": _cv(sequence),
        "normalizedEntropy": _normalized_entropy(sequence),
        "lag1Correlation": _correlation(sequence[:-1], sequence[1:]) if len(sequence) > 1 else 0.0,
        "peakPosition": peak_index / max(1, len(sequence) - 1),
        "earlyLateDeltaZ": early - late,
        "turningPointRate": turning_points / max(1, len(sequence) - 2),
    }

def _bin_series(samples: Sequence[tuple[float, float]], *, duration: float, bins: int) -> list[float]:
    if bins < 2:
        raise ValueError("bins must be at least two")
    grouped: list[list[float]] = [[] for _ in range(bins)]
    if duration <= 0.0:
        return [0.0] * bins
    for time_seconds, value in samples:
        index = min(bins - 1, max(0, int((float(time_seconds) / duration) * bins)))
        grouped[index].append(float(value))
    result: list[float] = []
    last = 0.0
    for values in grouped:
        if values:
            last = statistics.fmean(values)
        result.append(last)
    return result

def _resample_profile(values: Sequence[float], bins: int) -> list[float]:
    if not values:
        return [0.0] * bins
    if len(values) == bins:
        return [float(value) for value in values]
    grouped: list[list[float]] = [[] for _ in range(bins)]
    for index, value in enumerate(values):
        target = min(bins - 1, int(index * bins / len(values)))
        grouped[target].append(float(value))
    return [_mean(group) for group in grouped]

def _vector_distance(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right):
        raise ValueError("vector lengths differ")
    if not left:
        return 0.0
    return math.sqrt(statistics.fmean((a - b) ** 2 for a, b in zip(left, right)))

def canonical_digest(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()
