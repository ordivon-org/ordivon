"""Pure, bounded selection of diagnostic video frames.

Coverage and luma-change peaks are sampling choices, never scene semantics,
quality, source currentness or creative approval.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from fractions import Fraction
from typing import Any


def _coverage_frames(total_frames: int, count: int) -> list[int]:
    count = min(count, total_frames)
    if count < 2:
        return [0]
    last = total_frames - 1
    return list(dict.fromkeys(round(Fraction(index * last, count - 1)) for index in range(count)))


def select_perception_frames(
    *,
    total_frames: int,
    change_samples: Iterable[dict[str, Any]],
    coverage_count: int = 4,
    change_peak_count: int = 4,
    min_peak_gap_frames: int = 15,
    requested_frames: Iterable[int] = (),
    max_frames: int = 8,
) -> tuple[list[int], dict[int, list[str]], list[dict[str, Any]]]:
    for name, value, minimum in (
        ("total_frames", total_frames, 1), ("coverage_count", coverage_count, 1),
        ("change_peak_count", change_peak_count, 0), ("min_peak_gap_frames", min_peak_gap_frames, 0),
        ("max_frames", max_frames, 2),
    ):
        if type(value) is not int or value < minimum:
            raise ValueError(f"{name} must be an integer >= {minimum}")

    def require_frame(value: object) -> int:
        if type(value) is not int or not 0 <= value < total_frames:
            raise ValueError(f"frame identity outside selected source: {value!r}")
        return value

    requested_frames = list(dict.fromkeys(require_frame(frame) for frame in requested_frames))
    if len(requested_frames) > max_frames:
        raise ValueError("requested frames exceed model-view budget")
    reasons: dict[int, list[str]] = {}

    def add(frame: int, reason: str) -> None:
        reasons.setdefault(frame, [])
        if reason not in reasons[frame]:
            reasons[frame].append(reason)

    for frame in requested_frames:
        add(frame, "requested")
    for frame in _coverage_frames(total_frames, min(coverage_count, max_frames)):
        add(frame, "coverage")

    samples = {}
    for sample in change_samples:
        frame = require_frame(sample.get("frame"))
        score = sample.get("meanAbsoluteLumaDifference")
        if type(score) not in (int, float) or not 0 <= score or (
            type(score) is float and not math.isfinite(score)
        ):
            raise ValueError("invalid finite nonnegative change observation")
        if frame in samples:
            raise ValueError("duplicate native change observation")
        samples[frame] = sample

    ranked = sorted(samples.values(), key=lambda sample: (
        -sample["meanAbsoluteLumaDifference"], sample["frame"],
    ))
    peaks: list[dict[str, Any]] = []
    for sample in ranked:
        if len(peaks) >= change_peak_count:
            break
        frame = sample["frame"]
        if any(abs(frame - selected["frame"]) < min_peak_gap_frames for selected in peaks):
            continue
        peaks.append(sample)
        add(frame, "change-peak")

    # Requested frames and endpoints have priority; if the union exceeds the model-view budget,
    # keep the highest-ranked change peaks and evenly distributed coverage rather than arbitrary order.
    requested = [frame for frame, frame_reasons in reasons.items() if "requested" in frame_reasons]
    endpoints = [frame for frame in (0, total_frames - 1) if frame in reasons]
    peak_frames = [sample["frame"] for sample in peaks]
    coverage = _coverage_frames(total_frames, min(coverage_count, max_frames))
    priority = list(dict.fromkeys(requested + endpoints + peak_frames + coverage))
    selected = priority[:max_frames]

    # Fill sparse unions so the contact sheet remains temporally informative.
    if len(selected) < max_frames:
        fill_count = max_frames + 2
        for frame in _coverage_frames(total_frames, fill_count):
            if frame not in selected:
                add(frame, "coverage-fill")
                selected.append(frame)
            if len(selected) >= max_frames:
                break

    selected = sorted(selected)
    selected_reasons = {frame: reasons.get(frame, ["coverage-fill"]) for frame in selected}
    selected_peaks = [sample for sample in peaks if sample["frame"] in selected]
    return selected, selected_reasons, selected_peaks
