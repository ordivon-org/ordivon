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
from .perception_video_io import (
    _extract_frame,
    analyze_temporal_change,
    build_contact_sheet,
)


def build_video_perception_bundle(
    *,
    video_path: Path,
    probe: dict[str, Any],
    output_directory: Path,
    requested_frames: Iterable[int] = (),
    ffmpeg: str = "/usr/bin/ffmpeg",
    sample_step_frames: int = 5,
) -> dict[str, Any]:
    streams = probe.get("streams")
    videos = [item for item in streams if isinstance(item, dict) and item.get("codec_type") == "video"] if isinstance(streams, list) else []
    if len(videos) != 1:
        raise ValueError("perception requires exactly one video stream")
    stream = videos[0]
    frame_rate = stream.get("avg_frame_rate") or stream.get("r_frame_rate")
    if not isinstance(frame_rate, str) or "/" not in frame_rate:
        raise ValueError("video frame rate is unavailable")
    numerator_text, denominator_text = frame_rate.split("/", 1)
    fps = float(numerator_text) / float(denominator_text)
    frame_count = stream.get("nb_frames")
    if isinstance(frame_count, str) and frame_count.isdigit():
        total_frames = int(frame_count)
    else:
        duration = stream.get("duration") or (probe.get("format") or {}).get("duration")
        if duration is None:
            raise ValueError("video frame count/duration is unavailable")
        total_frames = max(1, int(round(float(duration) * fps)))

    change_samples = analyze_temporal_change(
        video_path,
        fps=fps,
        total_frames=total_frames,
        sample_step_frames=sample_step_frames,
        ffmpeg=ffmpeg,
    )
    selected, reasons, peaks = select_perception_frames(
        total_frames=total_frames,
        change_samples=change_samples,
        requested_frames=requested_frames,
    )

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
                "timeSeconds": round(frame / fps, 6),
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
        "frameRate": frame_rate,
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
