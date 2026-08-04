from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .assets import hash_file, probe_media, r2_object_key
from .qc import validate_video_probe
from .timed_text import export_srt, export_webvtt


def _write_json(value: object) -> None:
    json.dump(value, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


def _command_hash(args: argparse.Namespace) -> int:
    blob = hash_file(Path(args.path))
    output = blob.as_dict()
    output["r2ObjectKey"] = r2_object_key(blob.digest)
    _write_json(output)
    return 0


def _command_probe(args: argparse.Namespace) -> int:
    path = Path(args.path)
    _write_json({"blob": hash_file(path).as_dict(), "probe": probe_media(path, args.ffprobe)})
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
            },
            "errors": errors,
        }
    )
    return 0 if not errors else 1


def _command_timed_text(args: argparse.Namespace) -> int:
    document = json.loads(Path(args.input).read_text(encoding="utf-8"))
    rendered = export_webvtt(document) if args.format == "vtt" else export_srt(document)
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ordivon-studio")
    commands = parser.add_subparsers(dest="command", required=True)

    hash_parser = commands.add_parser("hash", help="hash one immutable media Blob")
    hash_parser.add_argument("path")
    hash_parser.set_defaults(handler=_command_hash)

    probe_parser = commands.add_parser("probe", help="hash and inspect one media file")
    probe_parser.add_argument("path")
    probe_parser.add_argument("--ffprobe", default="/usr/bin/ffprobe")
    probe_parser.set_defaults(handler=_command_probe)

    qc_parser = commands.add_parser("qc-video", help="verify structural video and color facts")
    qc_parser.add_argument("path")
    qc_parser.add_argument("--width", type=int, required=True)
    qc_parser.add_argument("--height", type=int, required=True)
    qc_parser.add_argument("--frame-rate", required=True)
    qc_parser.add_argument("--codec", default="h264")
    qc_parser.add_argument("--pixel-format", default="yuv420p")
    qc_parser.add_argument("--color-space", default="bt709")
    qc_parser.add_argument("--color-range", default="tv")
    audio_group = qc_parser.add_mutually_exclusive_group(required=True)
    audio_group.add_argument("--expect-audio", action="store_true")
    audio_group.add_argument("--no-audio", action="store_false", dest="expect_audio")
    qc_parser.add_argument("--ffprobe", default="/usr/bin/ffprobe")
    qc_parser.set_defaults(handler=_command_qc_video)

    timed_parser = commands.add_parser("timed-text", help="export internal TimedText")
    timed_parser.add_argument("input")
    timed_parser.add_argument("--format", choices=["vtt", "srt"], required=True)
    timed_parser.add_argument("--output")
    timed_parser.set_defaults(handler=_command_timed_text)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        raise SystemExit(args.handler(args))
    except (FileNotFoundError, ValueError, RuntimeError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(2) from error


if __name__ == "__main__":
    main()
