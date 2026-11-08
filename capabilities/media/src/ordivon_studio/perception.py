"""Build one reviewable Video Perception bundle from native observations.

The presentation boundary composes explicit, source-bound FFmpeg observations
with pure bounded frame selection, without becoming a second video engine.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any

from .assets import hash_file
from .perception_selection import select_perception_frames
from .perception_timing import video_timing
from .perception_video_io import (
    _extract_frame,
    analyze_temporal_change,
    build_contact_sheet,
    count_video_frames,
)


def build_video_perception_bundle(
    *,
    video_path: Path,
    probe: dict[str, Any],
    output_directory: Path,
    requested_frames: Iterable[int] = (),
    ffmpeg: str = "/usr/bin/ffmpeg",
    ffprobe: str = "/usr/bin/ffprobe",
    sample_step_frames: int = 5,
) -> dict[str, Any]:
    timing = video_timing(probe)
    fps = float(timing.rate)
    total_frames = timing.total_frames
    count_basis = timing.frame_count_basis
    if count_basis == "duration-times-reported-rate-estimate":
        total_frames = count_video_frames(video_path, ffprobe)
        count_basis = "native-ffprobe-decoded-frame-count"
    frame_rate = timing.rate_label

    change_samples = analyze_temporal_change(
        video_path,
        total_frames=total_frames,
        sample_step_frames=sample_step_frames,
        ffmpeg=ffmpeg,
    )
    selected, reasons, peaks = select_perception_frames(
        total_frames=total_frames,
        change_samples=change_samples,
        requested_frames=requested_frames,
    )

    samples_by_frame = {sample["frame"]: sample for sample in change_samples}
    frames_directory = output_directory / "frames"
    frame_records: list[dict[str, Any]] = []
    frame_paths: list[Path] = []
    for frame in selected:
        output_path = frames_directory / f"frame-{frame:06d}.png"
        _extract_frame(video_path, frame, output_path, ffmpeg)
        frame_paths.append(output_path)
        frame_records.append(
            {
                "frame": frame,
                "timeSeconds": (
                    samples_by_frame[frame]["timeSeconds"]
                    if frame in samples_by_frame else round(frame / fps, 6)
                ),
                "timeSecondsBasis": (
                    "native-ffmpeg-filter-pts"
                    if frame in samples_by_frame else "average-rate-estimate-not-source-pts"
                ),
                "selectionReasons": reasons[frame],
                "path": output_path.relative_to(output_directory).as_posix(),
                "blob": hash_file(output_path).as_dict(),
            }
        )

    contact_path = output_directory / "model-views" / "temporal-contact-sheet.png"
    contact = build_contact_sheet(frame_paths, output_path=contact_path, ffmpeg=ffmpeg)
    contact["path"] = contact_path.relative_to(output_directory).as_posix()
    contact["layout"]["frameOrder"] = selected

    return {
        "strategy": "coverage-plus-temporal-change",
        "totalFrames": total_frames,
        "frameCountBasis": count_basis,
        "frameRate": frame_rate,
        "frameRateBasis": timing.rate_source,
        "sampleStepFrames": sample_step_frames,
        "changeMetric": {
            "id": "mean-absolute-luma-difference",
            "unit": "8-bit luma levels averaged over the difference frame",
            "role": "diagnostic-event-sampling-only",
            "note": "A large value means more pixels changed between sampled moments. It does not identify meaning, importance, quality, or a film scene boundary.",
        },
        "changePeaks": peaks,
        "selectedFrames": frame_records,
        "modelViews": [
            {
                "kind": "temporal-contact-sheet",
                "path": contact["path"],
                "blob": contact["blob"],
                "layout": contact["layout"],
                "intendedConsumer": "vision-capable-agent",
            }
        ],
        "inspectionLayers": [
            {"order": 1, "kind": "coarse-temporal-scan", "inputs": [contact["path"]]},
            {"order": 2, "kind": "full-resolution-frame-inspection", "inputs": [record["path"] for record in frame_records]},
            {"order": 3, "kind": "continuous-playback", "inputs": ["reviewed-artifact"], "when": "timing, pacing, continuity, animation, or audio-image relation remains material"},
        ],
        "interpretationBoundary": "Mechanical sampling prepares real pixels for perception; it does not infer hierarchy, legibility, causality, affect, truth, or aesthetic quality.",
    }
