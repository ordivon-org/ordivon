from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Iterable

from .assets import hash_file, probe_media
from .qc import validate_video_probe


def _load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: root must be an object")
    return value


def _repository_relative(path: Path, root: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(resolved)


def _normalized_video_summary(probe: dict[str, Any]) -> dict[str, Any]:
    streams = probe.get("streams")
    if not isinstance(streams, list):
        raise ValueError("ffprobe result does not contain streams")
    videos = [item for item in streams if isinstance(item, dict) and item.get("codec_type") == "video"]
    audios = [item for item in streams if isinstance(item, dict) and item.get("codec_type") == "audio"]
    if len(videos) != 1:
        raise ValueError(f"review artifact must contain exactly one video stream, found {len(videos)}")
    video = videos[0]
    return {
        "codec": video.get("codec_name"),
        "pixelFormat": video.get("pix_fmt"),
        "width": video.get("width"),
        "height": video.get("height"),
        "frameRate": video.get("avg_frame_rate") or video.get("r_frame_rate"),
        "colorSpace": video.get("color_space"),
        "colorTransfer": video.get("color_transfer"),
        "colorPrimaries": video.get("color_primaries"),
        "colorRange": video.get("color_range"),
        "audioStreams": len(audios),
    }


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


def build_video_review_packet(
    *,
    production_root: Path,
    video_path: Path,
    source_paths: Iterable[Path],
    frames: Iterable[int],
    output_directory: Path,
    codec: str = "h264",
    pixel_format: str = "yuv420p",
    color_space: str = "bt709",
    color_range: str = "tv",
    expect_audio: bool = False,
    ffprobe: str = "/usr/bin/ffprobe",
    ffmpeg: str = "/usr/bin/ffmpeg",
    repository_root: Path | None = None,
) -> dict[str, Any]:
    production_path = production_root / "production.json"
    production = _load_object(production_path)
    production_id = production.get("id")
    if not isinstance(production_id, str) or not production_id:
        raise ValueError("Production id is missing")
    working = production.get("workingProfile")
    if not isinstance(working, dict):
        raise ValueError("Production workingProfile is missing")
    canvas = working.get("canvas")
    frame_rate = working.get("frameRate")
    if not isinstance(canvas, dict) or not isinstance(frame_rate, dict):
        raise ValueError("Production canvas/frameRate is missing")
    width = canvas.get("width")
    height = canvas.get("height")
    numerator = frame_rate.get("numerator")
    denominator = frame_rate.get("denominator")
    if not all(isinstance(value, int) and value > 0 for value in (width, height, numerator, denominator)):
        raise ValueError("Production video dimensions/frame rate are invalid")
    expected_frame_rate = f"{numerator}/{denominator}"

    repo = repository_root or production_root.resolve().parents[1]
    video_path = video_path.resolve()
    probe = probe_media(video_path, ffprobe)
    video_blob = hash_file(video_path)
    qc_errors = validate_video_probe(
        probe,
        width=width,
        height=height,
        frame_rate=expected_frame_rate,
        codec=codec,
        pixel_format=pixel_format,
        color_space=color_space,
        color_range=color_range,
        expect_audio=expect_audio,
    )
    if qc_errors:
        raise ValueError("video review QC failed: " + "; ".join(qc_errors))

    source_records: list[dict[str, Any]] = []
    for source_path in source_paths:
        resolved = source_path.resolve()
        blob = hash_file(resolved)
        source_records.append({"path": _repository_relative(resolved, repo), "blob": blob.as_dict()})

    frame_records: list[dict[str, Any]] = []
    unique_frames = list(dict.fromkeys(int(frame) for frame in frames))
    if not unique_frames:
        raise ValueError("at least one review frame is required")
    frames_directory = output_directory / "frames"
    for frame in unique_frames:
        output_path = frames_directory / f"frame-{frame:06d}.png"
        _extract_frame(video_path, frame, output_path, ffmpeg)
        frame_records.append(
            {
                "frame": frame,
                "path": output_path.relative_to(output_directory).as_posix(),
                "blob": hash_file(output_path).as_dict(),
            }
        )

    sources = production.get("sources")
    cognition = sources.get("cognition") if isinstance(sources, dict) else None
    packet = {
        "schemaVersion": 1,
        "kind": "ordivon-studio-video-review-packet",
        "disposition": "disposable-review-evidence",
        "productionId": production_id,
        "productionSource": _repository_relative(production_path, repo),
        "cognitionSource": _repository_relative(production_root / cognition, repo) if isinstance(cognition, str) else None,
        "reviewedArtifact": {
            "path": _repository_relative(video_path, repo),
            "blob": video_blob.as_dict(),
            "technical": _normalized_video_summary(probe),
        },
        "technicalQc": {
            "ok": True,
            "expectation": {
                "width": width,
                "height": height,
                "frameRate": expected_frame_rate,
                "codec": codec,
                "pixelFormat": pixel_format,
                "colorSpace": color_space,
                "colorRange": color_range,
                "expectAudio": expect_audio,
            },
            "errors": [],
        },
        "sourceFiles": source_records,
        "keyframes": frame_records,
        "semanticAudit": {
            "status": "pending-agent-inspection",
            "note": "The packet proves artifact identity, technical QC and exact review frames. It does not infer aesthetic or semantic correctness from those facts.",
        },
    }
    output_directory.mkdir(parents=True, exist_ok=True)
    (output_directory / "review.json").write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return packet
