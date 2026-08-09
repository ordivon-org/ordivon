from __future__ import annotations

import math
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Iterable

from .assets import hash_file


_FRAME_LINE = re.compile(r"^frame:\d+\s+pts:\S+\s+pts_time:(?P<time>-?[0-9.]+)$")
_YAVG_LINE = re.compile(r"^lavfi\.signalstats\.YAVG=(?P<value>[0-9.]+)$")


def _extract_frame(video_path: Path, frame: int, output_path: Path, ffmpeg: str) -> None:
    if frame < 0:
        raise ValueError("review frame must be non-negative")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [
            ffmpeg,
            "-v",
            "error",
            "-y",
            "-i",
            str(video_path),
            "-vf",
            f"select=eq(n\\,{frame})",
            "-fps_mode",
            "passthrough",
            "-frames:v",
            "1",
            str(output_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"ffmpeg failed to extract frame {frame}")
    if not output_path.is_file() or output_path.stat().st_size == 0:
        raise RuntimeError(f"ffmpeg produced no review frame for {frame}")


def _parse_change_metadata(text: str, *, fps: float, total_frames: int) -> list[dict[str, Any]]:
    samples: list[dict[str, Any]] = []
    current_time: float | None = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        frame_match = _FRAME_LINE.match(line)
        if frame_match:
            current_time = float(frame_match.group("time"))
            continue
        value_match = _YAVG_LINE.match(line)
        if value_match and current_time is not None:
            original_frame = min(total_frames - 1, max(0, int(round(current_time * fps))))
            samples.append(
                {
                    "frame": original_frame,
                    "timeSeconds": round(original_frame / fps, 6),
                    "meanAbsoluteLumaDifference": float(value_match.group("value")),
                }
            )
            current_time = None
    return samples


def analyze_temporal_change(
    video_path: Path,
    *,
    fps: float,
    total_frames: int,
    sample_step_frames: int,
    ffmpeg: str,
) -> list[dict[str, Any]]:
    if sample_step_frames < 1:
        raise ValueError("sample_step_frames must be positive")
    with tempfile.NamedTemporaryFile(prefix="ordivon-change-", suffix=".txt", delete=False) as handle:
        metadata_path = Path(handle.name)
    try:
        filter_graph = (
            f"select='not(mod(n\\,{sample_step_frames}))',"
            "tblend=all_mode=difference,"
            "signalstats,"
            f"metadata=print:file={metadata_path}"
        )
        result = subprocess.run(
            [ffmpeg, "-v", "error", "-i", str(video_path), "-vf", filter_graph, "-an", "-f", "null", "-"],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "ffmpeg temporal-change analysis failed")
        return _parse_change_metadata(metadata_path.read_text(encoding="utf-8"), fps=fps, total_frames=total_frames)
    finally:
        metadata_path.unlink(missing_ok=True)


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


def build_contact_sheet(
    frame_paths: list[Path],
    *,
    output_path: Path,
    ffmpeg: str,
    thumbnail_width: int = 480,
    thumbnail_height: int = 270,
    columns: int = 4,
) -> dict[str, Any]:
    if not frame_paths:
        raise ValueError("contact sheet requires at least one frame")
    effective_columns = min(columns, len(frame_paths))
    rows = math.ceil(len(frame_paths) / effective_columns)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    args = [ffmpeg, "-v", "error", "-y"]
    for path in frame_paths:
        args.extend(["-i", str(path)])
    chains = [f"[{index}:v]scale={thumbnail_width}:{thumbnail_height}[v{index}]" for index in range(len(frame_paths))]
    inputs = "".join(f"[v{index}]" for index in range(len(frame_paths)))
    layout = "|".join(
        f"{(index % effective_columns) * thumbnail_width}_{(index // effective_columns) * thumbnail_height}"
        for index in range(len(frame_paths))
    )
    chains.append(f"{inputs}xstack=inputs={len(frame_paths)}:layout={layout}:fill=black[out]")
    args.extend(["-filter_complex", ";".join(chains), "-map", "[out]", "-frames:v", "1", "-update", "1", str(output_path)])
    result = subprocess.run(args, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "ffmpeg contact-sheet generation failed")
    if not output_path.is_file() or output_path.stat().st_size == 0:
        raise RuntimeError("ffmpeg produced no contact sheet")
    return {
        "path": output_path,
        "blob": hash_file(output_path).as_dict(),
        "layout": {
            "columns": effective_columns,
            "rows": rows,
            "thumbnailWidth": thumbnail_width,
            "thumbnailHeight": thumbnail_height,
            "frameOrder": [],
        },
    }


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
