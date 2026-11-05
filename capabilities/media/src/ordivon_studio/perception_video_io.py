"""Native FFmpeg observation and diagnostic visual contact-sheet rendering.

This module only extracts real pixels and luma-difference metadata with
existing FFmpeg; no inference, model, source ownership or quality verdict.
"""

from __future__ import annotations

import math
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

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
