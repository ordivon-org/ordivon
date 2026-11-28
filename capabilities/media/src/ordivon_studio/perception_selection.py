"""Pure, bounded selection of diagnostic video frames.

Coverage and luma-change peaks are sampling choices, never scene semantics,
quality, source currentness or creative approval.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any


def _coverage_frames(total_frames: int, count: int) -> list[int]:
    if total_frames < 1:
        raise ValueError("total_frames must be positive")
    if count < 2:
        return [0]
    last = total_frames - 1
    return list(dict.fromkeys(round(index * last / (count - 1)) for index in range(count)))


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
    if max_frames < 2:
        raise ValueError("max_frames must be at least 2")
    reasons: dict[int, list[str]] = {}

    def add(frame: int, reason: str) -> None:
        frame = min(total_frames - 1, max(0, frame))
        reasons.setdefault(frame, [])
        if reason not in reasons[frame]:
            reasons[frame].append(reason)

    for frame in requested_frames:
        add(int(frame), "requested")
    for frame in _coverage_frames(total_frames, coverage_count):
        add(frame, "coverage")

    ranked = sorted(
        (sample for sample in change_samples if isinstance(sample.get("frame"), int)),
        key=lambda sample: float(sample.get("meanAbsoluteLumaDifference", 0.0)),
        reverse=True,
    )
    peaks: list[dict[str, Any]] = []
    for sample in ranked:
        frame = int(sample["frame"])
        if any(abs(frame - int(selected["frame"])) < min_peak_gap_frames for selected in peaks):
            continue
        peaks.append(sample)
        add(frame, "change-peak")
        if len(peaks) >= change_peak_count:
            break

    # Requested frames and endpoints have priority; if the union exceeds the model-view budget,
    # keep the highest-ranked change peaks and evenly distributed coverage rather than arbitrary order.
    requested = [frame for frame, frame_reasons in reasons.items() if "requested" in frame_reasons]
    endpoints = [frame for frame in (0, total_frames - 1) if frame in reasons]
    peak_frames = [int(sample["frame"]) for sample in peaks]
    coverage = _coverage_frames(total_frames, coverage_count)
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
    selected_peaks = [sample for sample in peaks if int(sample["frame"]) in selected]
    return selected, selected_reasons, selected_peaks
