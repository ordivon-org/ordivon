"""Native FFmpeg observation and diagnostic visual contact-sheet rendering.

This module only extracts real pixels and luma-difference metadata with
existing FFmpeg; no inference, model, source ownership or quality verdict.
"""

from __future__ import annotations

import json
import math
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from .assets import hash_file

_FRAME_LINE = re.compile(r"^frame:(?P<filtered>\d+)\s+pts:\S+\s+pts_time:(?P<time>-?[0-9.]+)$")
_YAVG_LINE = re.compile(r"^lavfi\.signalstats\.YAVG=(?P<value>[0-9.]+)$")


def extract_review_frames(
    video_path: Path, frames: list[int], output_directory: Path, ffmpeg: str
) -> list[Path]:
    """Extract selected frames with one FFmpeg decode, not one decode per frame.

    The filter is selected by exact frame indices, with passthrough timestamps.
    FFmpeg's output image sequence is ordinal; stage first, then rename to the
    selected source-frame identities only after all expected images exist.
    """
    if not frames:
        return []
    if any(type(frame) is not int or frame < 0 for frame in frames):
        raise ValueError("review frames must be non-negative integers")
    if frames != sorted(set(frames)):
        raise ValueError("review frames must be unique and sorted")

    output_directory.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".ordivon-review-", dir=output_directory) as temporary:
        staged_root = Path(temporary)
        expression = "+".join(f"eq(n\\,{frame})" for frame in frames)
        result = subprocess.run(
            [
                ffmpeg,
                "-v",
                "error",
                "-y",
                "-i",
                str(video_path),
                "-vf",
                f"select={expression}",
                "-fps_mode",
                "passthrough",
                "-frames:v",
                str(len(frames)),
                "-start_number",
                "0",
                str(staged_root / "selected-%06d.png"),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "ffmpeg failed to extract review frames")
        staged = [staged_root / f"selected-{index:06d}.png" for index in range(len(frames))]
        if any(not path.is_file() or path.stat().st_size == 0 for path in staged):
            raise RuntimeError("ffmpeg produced an incomplete review-frame set")
        outputs = [output_directory / f"frame-{frame:06d}.png" for frame in frames]
        for source, destination in zip(staged, outputs, strict=True):
            source.replace(destination)
        return outputs


def count_video_frames(video_path: Path, ffprobe: str = "/usr/bin/ffprobe") -> int:
    """Request an exact decoded-frame count from the established native tool.

    A duration multiplied by average FPS is not a frame count for VFR.
    Only use this extra I/O pass when the initial stream has no nb_frames.
    """
    result = subprocess.run(
        [
            ffprobe, "-v", "error", "-select_streams", "v:0",
            "-count_frames", "-show_entries", "stream=nb_read_frames",
            "-of", "json", str(video_path),
        ],
        check=False, capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "ffprobe frame count failed")
    value = json.loads(result.stdout)
    streams = value.get("streams") if isinstance(value, dict) else None
    if not isinstance(streams, list) or len(streams) != 1:
        raise ValueError("native video frame count is unavailable")
    raw = streams[0].get("nb_read_frames")
    if not isinstance(raw, str) or not raw.isdigit() or int(raw) < 1:
        raise ValueError("native video frame count is unavailable")
    return int(raw)


def _parse_change_metadata(
    text: str, *, sample_step_frames: int, total_frames: int,
) -> list[dict[str, Any]]:
    # FFmpeg's select keeps original frames 0, step, 2*step ... .
    # tblend discards the first selected frame. The printed frame index
    # therefore maps to original frame (filtered_index + 1) * step,
    # independently of variable presentation timestamps and average FPS.
    if sample_step_frames < 1 or total_frames < 1:
        raise ValueError("sample step and frame count must be positive")
    samples: list[dict[str, Any]] = []
    current: tuple[int, float] | None = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        frame_match = _FRAME_LINE.match(line)
        if frame_match:
            original = (int(frame_match.group("filtered")) + 1) * sample_step_frames
            if original >= total_frames:
                raise ValueError("native change metadata references an unavailable source frame")
            current = (original, float(frame_match.group("time")))
            continue
        value_match = _YAVG_LINE.match(line)
        if value_match and current is not None:
            original_frame, native_pts = current
            samples.append(
                {
                    "frame": original_frame,
                    "timeSeconds": native_pts,
                    "timeSecondsBasis": "native-ffmpeg-filter-pts",
                    "meanAbsoluteLumaDifference": float(value_match.group("value")),
                }
            )
            current = None
    return samples


def analyze_temporal_change(
    video_path: Path,
    *,
    total_frames: int,
    sample_step_frames: int,
    ffmpeg: str,
) -> list[dict[str, Any]]:
    if sample_step_frames < 1:
        raise ValueError("sample_step_frames must be positive")
    with tempfile.NamedTemporaryFile(
        prefix="ordivon-change-", suffix=".txt", delete=False
    ) as handle:
        metadata_path = Path(handle.name)
    try:
        filter_graph = (
            f"select='not(mod(n\\,{sample_step_frames}))',"
            "tblend=all_mode=difference,"
            "signalstats,"
            f"metadata=print:file={metadata_path}"
        )
        result = subprocess.run(
            [
                ffmpeg,
                "-v",
                "error",
                "-i",
                str(video_path),
                "-vf",
                filter_graph,
                "-an",
                "-f",
                "null",
                "-",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "ffmpeg temporal-change analysis failed")
        return _parse_change_metadata(
            metadata_path.read_text(encoding="utf-8"),
            sample_step_frames=sample_step_frames, total_frames=total_frames,
        )
    finally:
        metadata_path.unlink(missing_ok=True)


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
    if any(type(value) is not int or value < 2 or value % 2 for value in (thumbnail_width, thumbnail_height)):
        raise ValueError("thumbnail dimensions must be positive even integers")
    if type(columns) is not int or columns < 1:
        raise ValueError("contact sheet columns must be a positive integer")
    effective_columns = min(columns, len(frame_paths))
    rows = math.ceil(len(frame_paths) / effective_columns)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    args = [ffmpeg, "-v", "error", "-y"]
    for path in frame_paths:
        args.extend(["-i", str(path)])
    # Fit each observed frame into its tile without stretching its geometry.
    # xstack has a minimum input cardinality of two; a singleton is simply
    # one native scaled/padded tile, not a duplicated observation.
    fit = (
        f"scale={thumbnail_width}:{thumbnail_height}:"
        "force_original_aspect_ratio=decrease:force_divisible_by=2,"
        f"pad={thumbnail_width}:{thumbnail_height}:(ow-iw)/2:(oh-ih)/2:black"
    )
    if len(frame_paths) == 1:
        chains = [f"[0:v]{fit}[out]"]
    else:
        chains = [f"[{index}:v]{fit}[v{index}]" for index in range(len(frame_paths))]
        inputs = "".join(f"[v{index}]" for index in range(len(frame_paths)))
        layout = "|".join(
            f"{(index % effective_columns) * thumbnail_width}_{(index // effective_columns) * thumbnail_height}"
            for index in range(len(frame_paths))
        )
        chains.append(f"{inputs}xstack=inputs={len(frame_paths)}:layout={layout}:fill=black[out]")
    args.extend(
        [
            "-filter_complex",
            ";".join(chains),
            "-map",
            "[out]",
            "-frames:v",
            "1",
            "-update",
            "1",
            str(output_path),
        ]
    )
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
            "thumbnailFit": "aspect-preserving-fit-with-black-padding",
            "frameOrder": [],
        },
    }
