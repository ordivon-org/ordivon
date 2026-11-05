"""Blob, R2 storage, media QC, review and timed-text CLI handlers."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ..assets import archive_blob, hash_file, materialize_blob, probe_media, r2_object_key
from ..cloudflare_r2 import replicate_r2_blob, restore_r2_blob
from ..qc import measure_loudness, validate_loudness, validate_video_probe
from ..review import build_video_review_packet
from ..timed_text import export_srt, export_webvtt, validate_timed_text_delivery
from ..video import normalize_h264_bt709
from . import _write_json


def _command_hash(args: argparse.Namespace) -> int:
    blob = hash_file(Path(args.path))
    output = blob.as_dict()
    output["r2ObjectKey"] = r2_object_key(blob.digest)
    _write_json(output)
    return 0


def _command_archive(args: argparse.Namespace) -> int:
    _write_json(archive_blob(Path(args.path), Path(args.cache_root)))
    return 0


def _command_materialize(args: argparse.Namespace) -> int:
    _write_json(materialize_blob(args.digest, Path(args.cache_root), Path(args.destination)))
    return 0


def _command_r2_replicate(args: argparse.Namespace) -> int:
    _write_json(
        replicate_r2_blob(
            Path(args.path),
            bucket=args.bucket,
            credentials_path=Path(args.credentials),
            curl=args.curl,
        )
    )
    return 0


def _command_r2_restore(args: argparse.Namespace) -> int:
    _write_json(
        restore_r2_blob(
            args.digest,
            Path(args.cache_root),
            bucket=args.bucket,
            credentials_path=Path(args.credentials),
            curl=args.curl,
        )
    )
    return 0


def _command_probe(args: argparse.Namespace) -> int:
    path = Path(args.path)
    _write_json({"blob": hash_file(path).as_dict(), "probe": probe_media(path, args.ffprobe)})
    return 0


def _command_normalize_h264_bt709(args: argparse.Namespace) -> int:
    path = Path(args.path)
    before = hash_file(path)
    normalize_h264_bt709(path, args.ffmpeg)
    after = hash_file(path)
    _write_json({
        "ok": True,
        "path": str(path),
        "transform": "h264-bt709-vui-stream-copy",
        "before": before.as_dict(),
        "after": after.as_dict(),
    })
    return 0


def _command_qc_video(args: argparse.Namespace) -> int:
    path = Path(args.path)
    blob = hash_file(path)
    probe = probe_media(path, args.ffprobe)
    errors = validate_video_probe(
        probe,
        width=args.width,
        height=args.height,
        frame_rate=args.frame_rate,
        codec=args.codec,
        pixel_format=args.pixel_format,
        color_space=args.color_space,
        color_range=args.color_range,
        expect_audio=args.expect_audio,
        audio_stream_count=args.audio_stream_count,
        audio_codec=args.audio_codec,
        audio_sample_rate=args.audio_sample_rate,
        audio_channels=args.audio_channels,
        audio_channel_layout=args.audio_channel_layout,
        audio_stream_index=args.audio_stream_index,
    )
    loudness = None
    loudness_requested = args.loudness_target_lufs is not None or args.max_true_peak_dbtp is not None
    if loudness_requested:
        streams = probe.get("streams", [])
        has_audio = isinstance(streams, list) and any(
            isinstance(stream, dict) and stream.get("codec_type") == "audio" for stream in streams
        )
        if not args.expect_audio:
            errors.append("loudness expectations require --expect-audio")
        elif not has_audio:
            errors.append("loudness measurement requires an audio stream")
        else:
            loudness = measure_loudness(path, args.ffmpeg)
            errors.extend(
                validate_loudness(
                    loudness,
                    target_lufs=args.loudness_target_lufs,
                    tolerance_lu=args.loudness_tolerance_lu,
                    max_true_peak_dbtp=args.max_true_peak_dbtp,
                )
            )
    _write_json(
        {
            "ok": not errors,
            "blob": blob.as_dict(),
            "expectation": {
                "width": args.width,
                "height": args.height,
                "frameRate": args.frame_rate,
                "codec": args.codec,
                "pixelFormat": args.pixel_format,
                "colorSpace": args.color_space,
                "colorRange": args.color_range,
                "expectAudio": args.expect_audio,
                "audioStreamCount": args.audio_stream_count,
                "audioStreamIndex": args.audio_stream_index,
                "audioCodec": args.audio_codec,
                "audioSampleRate": args.audio_sample_rate,
                "audioChannels": args.audio_channels,
                "audioChannelLayout": args.audio_channel_layout,
                "loudnessTargetLufs": args.loudness_target_lufs,
                "loudnessToleranceLu": args.loudness_tolerance_lu if loudness_requested else None,
                "maxTruePeakDbtp": args.max_true_peak_dbtp,
            },
            "loudness": loudness,
            "errors": errors,
        }
    )
    return 0 if not errors else 1


def _parse_frames(value: str) -> list[int]:
    frames: list[int] = []
    for item in value.split(","):
        item = item.strip()
        if not item:
            continue
        frame = int(item)
        if frame < 0:
            raise ValueError("review frames must be non-negative")
        frames.append(frame)
    if not frames:
        raise ValueError("at least one review frame is required")
    return frames


def _command_review_video(args: argparse.Namespace) -> int:
    packet = build_video_review_packet(
        production_root=Path(args.production_root),
        video_path=Path(args.path),
        source_paths=[Path(value) for value in args.source],
        frames=_parse_frames(args.frames) if args.frames else [],
        output_directory=Path(args.output_dir),
        codec=args.codec,
        pixel_format=args.pixel_format,
        color_space=args.color_space,
        color_range=args.color_range,
        expect_audio=args.expect_audio,
        ffprobe=args.ffprobe,
        ffmpeg=args.ffmpeg,
        repository_root=Path.cwd(),
    )
    _write_json({
        "ok": True,
        "review": str(Path(args.output_dir) / "review.json"),
        "artifactDigest": packet["reviewedArtifact"]["blob"]["digest"],
        "frames": [item["frame"] for item in packet["perception"]["selectedFrames"]],
        "modelViews": [item["path"] for item in packet["perception"]["modelViews"]],
        "semanticAudit": packet["semanticAudit"]["status"],
    })
    return 0


def _command_timed_text(args: argparse.Namespace) -> int:
    document = json.loads(Path(args.input).read_text(encoding="utf-8"))
    rendered = export_webvtt(document) if args.format == "vtt" else export_srt(document)
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0


def _command_qc_timed_text(args: argparse.Namespace) -> int:
    source_path = Path(args.input)
    media_path = Path(args.media)
    document = json.loads(source_path.read_text(encoding="utf-8"))
    probe = probe_media(media_path, args.ffprobe)
    format_data = probe.get("format")
    if not isinstance(format_data, dict) or not isinstance(format_data.get("duration"), str):
        raise ValueError("ffprobe result does not contain an exact format.duration string")
    result = validate_timed_text_delivery(
        document,
        media_duration_seconds=format_data["duration"],
        require_locked=not args.allow_provisional,
    )
    _write_json(
        {
            "ok": result["ok"],
            "timedTextBlob": hash_file(source_path).as_dict(),
            "mediaBlob": hash_file(media_path).as_dict(),
            "delivery": result,
            "truthBoundary": (
                "Mechanical cue/timing delivery was evaluated. Semantic caption completeness, "
                "audio-description need, audience comprehension, and WCAG outcome remain not evaluated."
            ),
        }
    )
    return 0 if result["ok"] else 1
