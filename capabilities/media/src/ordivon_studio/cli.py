"""Ordivon Studio console entry point and existing argparse subcommand schema.

Handlers live with their domain; this module owns only parsing and dispatch.
"""

from __future__ import annotations

import argparse
import json
import sys

from .cli_handlers.ecology import (
    _command_ecology_collection,
    _command_ecology_project,
    _command_ecology_threads,
    _command_production_context,
)
from .cli_handlers.equipment import (
    _command_equipment_coverage,
    _command_equipment_inventory,
    _command_equipment_plan,
    _command_equipment_propose,
    _command_equipment_providers,
    _command_equipment_select,
    _command_figma_route,
)
from .cli_handlers.media import (
    _command_archive,
    _command_hash,
    _command_materialize,
    _command_normalize_h264_bt709,
    _command_probe,
    _command_qc_timed_text,
    _command_qc_video,
    _command_r2_replicate,
    _command_r2_restore,
    _command_review_video,
    _command_timed_text,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ordivon-studio")
    commands = parser.add_subparsers(dest="command", required=True)

    hash_parser = commands.add_parser("hash", help="hash one immutable media Blob")
    hash_parser.add_argument("path")
    hash_parser.set_defaults(handler=_command_hash)

    archive_parser = commands.add_parser("archive", help="copy one exact Blob into a verified local content-addressed cache")
    archive_parser.add_argument("path")
    archive_parser.add_argument("--cache-root", required=True)
    archive_parser.set_defaults(handler=_command_archive)

    materialize_parser = commands.add_parser("materialize", help="recover one exact verified Blob from a local content-addressed cache")
    materialize_parser.add_argument("digest")
    materialize_parser.add_argument("destination")
    materialize_parser.add_argument("--cache-root", required=True)
    materialize_parser.set_defaults(handler=_command_materialize)

    r2_parser = commands.add_parser("r2", help="replicate and restore exact selected Blobs through Cloudflare R2")
    r2_commands = r2_parser.add_subparsers(dest="r2_command", required=True)

    r2_replicate = r2_commands.add_parser("replicate", help="copy one exact local Blob to R2 and redownload-verify it")
    r2_replicate.add_argument("path")
    r2_replicate.add_argument("--bucket", required=True)
    r2_replicate.add_argument("--credentials", required=True, help="JSON containing account_id and api_token")
    r2_replicate.add_argument("--curl", default="/usr/bin/curl")
    r2_replicate.set_defaults(handler=_command_r2_replicate)

    r2_restore = r2_commands.add_parser("restore", help="restore one exact R2 Blob into the local content-addressed cache")
    r2_restore.add_argument("digest")
    r2_restore.add_argument("--cache-root", required=True)
    r2_restore.add_argument("--bucket", required=True)
    r2_restore.add_argument("--credentials", required=True, help="JSON containing account_id and api_token")
    r2_restore.add_argument("--curl", default="/usr/bin/curl")
    r2_restore.set_defaults(handler=_command_r2_restore)

    probe_parser = commands.add_parser("probe", help="hash and inspect one media file")
    probe_parser.add_argument("path")
    probe_parser.add_argument("--ffprobe", default="/usr/bin/ffprobe")
    probe_parser.set_defaults(handler=_command_probe)

    normalize_parser = commands.add_parser("normalize-h264-bt709", help="write complete BT.709 H.264 VUI metadata without re-encoding picture data")
    normalize_parser.add_argument("path")
    normalize_parser.add_argument("--ffmpeg", default="/usr/bin/ffmpeg")
    normalize_parser.set_defaults(handler=_command_normalize_h264_bt709)

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
    qc_parser.add_argument("--audio-stream-count", type=int)
    qc_parser.add_argument("--audio-stream-index", type=int, default=0)
    qc_parser.add_argument("--audio-codec")
    qc_parser.add_argument("--audio-sample-rate", type=int)
    qc_parser.add_argument("--audio-channels", type=int)
    qc_parser.add_argument("--audio-channel-layout")
    qc_parser.add_argument("--loudness-target-lufs", type=float)
    qc_parser.add_argument("--loudness-tolerance-lu", type=float, default=1.0)
    qc_parser.add_argument("--max-true-peak-dbtp", type=float)
    qc_parser.add_argument("--ffprobe", default="/usr/bin/ffprobe")
    qc_parser.add_argument("--ffmpeg", default="/usr/bin/ffmpeg")
    qc_parser.set_defaults(handler=_command_qc_video)

    review_parser = commands.add_parser("review-video", help="build disposable technical and keyframe evidence for one rendered Production video")
    review_parser.add_argument("path")
    review_parser.add_argument("--production-root", required=True)
    review_parser.add_argument("--source", action="append", default=[], help="source file materially responsible for this render; repeat as needed")
    review_parser.add_argument("--frames", help="optional comma-separated semantic anchor frames; automatic coverage/change sampling still runs")
    review_parser.add_argument("--output-dir", required=True)
    review_parser.add_argument("--codec", default="h264")
    review_parser.add_argument("--pixel-format", default="yuv420p")
    review_parser.add_argument("--color-space", default="bt709")
    review_parser.add_argument("--color-range", default="tv")
    review_audio = review_parser.add_mutually_exclusive_group(required=True)
    review_audio.add_argument("--expect-audio", action="store_true")
    review_audio.add_argument("--no-audio", action="store_false", dest="expect_audio")
    review_parser.add_argument("--ffprobe", default="/usr/bin/ffprobe")
    review_parser.add_argument("--ffmpeg", default="/usr/bin/ffmpeg")
    review_parser.set_defaults(handler=_command_review_video)

    timed_parser = commands.add_parser("timed-text", help="export internal TimedText")
    timed_parser.add_argument("input")
    timed_parser.add_argument("--format", choices=["vtt", "srt"], required=True)
    timed_parser.add_argument("--output")
    timed_parser.set_defaults(handler=_command_timed_text)

    timed_qc_parser = commands.add_parser(
        "qc-timed-text", help="verify mechanical TimedText delivery against one exact media file"
    )
    timed_qc_parser.add_argument("input")
    timed_qc_parser.add_argument("--media", required=True)
    timed_qc_parser.add_argument("--allow-provisional", action="store_true")
    timed_qc_parser.add_argument("--ffprobe", default="/usr/bin/ffprobe")
    timed_qc_parser.set_defaults(handler=_command_qc_timed_text)

    production_context_parser = commands.add_parser(
        "production-context",
        help=(
            "project one Production, Claims, Outputs, and optional source-binding Git relation "
            "without rendering or editing"
        ),
    )
    production_context_parser.add_argument("production_root")
    production_context_parser.add_argument(
        "--source-repo",
        action="append",
        default=[],
        metavar="BINDING_ID=PATH",
        help=(
            "optionally revalidate one source binding against a local Git repository; "
            "repeat for multiple bindings"
        ),
    )
    production_context_parser.add_argument(
        "--output-file",
        action="append",
        default=[],
        metavar="OUTPUT_ID=PATH",
        help=(
            "optionally compare an exact consumer-selected local file with an Output's "
            "declared blobDigest; repeat for multiple Outputs; read-only, no approval"
        ),
    )
    production_context_parser.set_defaults(handler=_command_production_context)

    ecology_parser = commands.add_parser(
        "ecology",
        help="derive thread, collection, and activity-feed views without minting new source truth",
    )
    ecology_commands = ecology_parser.add_subparsers(dest="ecology_command", required=True)

    ecology_threads = ecology_commands.add_parser(
        "threads", help="derive Board reply trees from an explicit Host Board JSON snapshot"
    )
    ecology_threads.add_argument("board", nargs="+", help="one Host Board response or a cursor-linked sequence of incremental pages")
    ecology_threads.set_defaults(handler=_command_ecology_threads)

    ecology_collection = ecology_commands.add_parser(
        "collection", help="validate one exact source-fenced Media Collection manifest"
    )
    ecology_collection.add_argument("collection")
    ecology_collection.set_defaults(handler=_command_ecology_collection)

    ecology_project = ecology_commands.add_parser(
        "project", help="build one derived Media ecology projection from explicit Board/Collection sources"
    )
    ecology_project.add_argument("--board", action="append", default=[], help="Host Board JSON response; repeat for cursor-linked incremental pages; no live Host read is performed")
    ecology_project.add_argument("--collection", action="append", default=[], help="validated collection JSON; repeat as needed")
    ecology_project.add_argument("--observed-at-ms", type=int, help="explicit observation time; defaults to latest supplied source time")
    ecology_project.set_defaults(handler=_command_ecology_project)

    equipment_parser = commands.add_parser("equipment", help="inspect and plan Studio professional equipment without executing it")
    equipment_commands = equipment_parser.add_subparsers(dest="equipment_command", required=True)

    equipment_inventory = equipment_commands.add_parser("inventory", help="probe the current machine against the Equipment World registry")
    equipment_inventory.add_argument("--world", default="research/equipment/equipment-world.json")
    equipment_inventory.set_defaults(handler=_command_equipment_inventory)

    equipment_select = equipment_commands.add_parser("select", help="rank equipment candidates for one exact capability using truthful readiness")
    equipment_select.add_argument("capability")
    equipment_select.add_argument("--world", default="research/equipment/equipment-world.json")
    equipment_select.add_argument("--local", action="store_true", help="freshly observe only physical candidates relevant to this capability")
    equipment_select.set_defaults(handler=_command_equipment_select)

    equipment_coverage = equipment_commands.add_parser("coverage", help="classify advertised capabilities by mechanical Agent actionability")
    equipment_coverage.add_argument("--world", default="research/equipment/equipment-world.json")
    equipment_coverage.set_defaults(handler=_command_equipment_coverage)

    equipment_providers = equipment_commands.add_parser("providers", help="project validated Studio-local provider mechanics without exposing provider protocol folklore to callers")
    equipment_providers.add_argument("--world", default="research/equipment/equipment-world.json")
    equipment_providers.set_defaults(handler=_command_equipment_providers)

    equipment_plan = equipment_commands.add_parser("plan", help="compile one Studio equipment intent into a Runtime-ready exact proposal without executing it")
    equipment_plan.add_argument("equipment_id")
    equipment_plan.add_argument("capability")
    equipment_plan.add_argument("--parameters", help="JSON object of operation parameters")
    equipment_plan.set_defaults(handler=_command_equipment_plan)

    equipment_propose = equipment_commands.add_parser("propose", help="select current equipment and compile one truthful Agent-facing operation proposal plus verification contract")
    equipment_propose.add_argument("capability")
    equipment_propose.add_argument("--equipment-id")
    equipment_propose.add_argument("--parameters", help="JSON object of operation parameters")
    equipment_propose.add_argument("--world", default="research/equipment/equipment-world.json")
    equipment_propose.add_argument("--no-local", action="store_true", help="do not perform current physical observation; normally unsuitable for executable proposals")
    equipment_propose.set_defaults(handler=_command_equipment_propose)

    figma_route = equipment_commands.add_parser("figma-route", help="select a Figma provider backend from explicit current backend evidence without performing OAuth or design effects")
    figma_route.add_argument("operation")
    figma_route.add_argument("--desktop-state", choices=["available", "unavailable", "unknown"], default="unknown")
    figma_route.add_argument("--remote-state", choices=["available", "unavailable", "unknown"], default="unknown")
    figma_route.add_argument("--prefer-remote", action="store_true")
    figma_route.set_defaults(handler=_command_figma_route)

    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        raise SystemExit(args.handler(args))
    except (
        FileNotFoundError,
        OSError,
        TypeError,
        ValueError,
        RuntimeError,
        json.JSONDecodeError,
    ) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(2) from error


if __name__ == "__main__":
    main()
