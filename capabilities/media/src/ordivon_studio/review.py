from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from .assets import hash_file, probe_media
from .perception import build_video_perception_bundle
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


def build_video_review_packet(
    *,
    production_root: Path,
    video_path: Path,
    source_paths: Iterable[Path],
    frames: Iterable[int] = (),
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

    perception = build_video_perception_bundle(
        video_path=video_path,
        probe=probe,
        output_directory=output_directory,
        requested_frames=list(dict.fromkeys(int(frame) for frame in frames)),
        ffmpeg=ffmpeg,
    )
    frame_records = perception["selectedFrames"]

    sources = production.get("sources")
    cognition = sources.get("cognition") if isinstance(sources, dict) else None
    claims = sources.get("claims") if isinstance(sources, dict) else None

    decision_context: list[dict[str, Any]] = [
        {
            "role": "production",
            "path": _repository_relative(production_path, repo),
            "blob": hash_file(production_path).as_dict(),
        }
    ]
    for role, relative in (("cognition", cognition), ("claims", claims)):
        if isinstance(relative, str):
            context_path = (production_root / relative).resolve()
            decision_context.append(
                {
                    "role": role,
                    "path": _repository_relative(context_path, repo),
                    "blob": hash_file(context_path).as_dict(),
                }
            )

    packet = {
        "schemaVersion": 1,
        "kind": "ordivon-studio-video-review-packet",
        "disposition": "disposable-review-evidence",
        "productionId": production_id,
        "productionSource": _repository_relative(production_path, repo),
        "cognitionSource": _repository_relative(production_root / cognition, repo) if isinstance(cognition, str) else None,
        "decisionContext": decision_context,
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
        "perception": perception,
        "semanticAudit": {
            "status": "pending-agent-inspection",
            "note": "The packet proves artifact identity, technical QC and a bounded perception surface. It does not infer aesthetic or semantic correctness from those facts.",
        },
    }
    output_directory.mkdir(parents=True, exist_ok=True)
    (output_directory / "review.json").write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return packet
