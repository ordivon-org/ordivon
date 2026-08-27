from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .assets import (
    archive_blob,
    hash_file,
    materialize_blob,
    probe_media,
    r2_object_key,
)
from .production_context import build_production_context
from .qc import validate_video_probe
from .r2 import replicate_r2_blob, restore_r2_blob
from .review import build_video_review_packet
from .timed_text import export_srt, export_webvtt
from .video import normalize_h264_bt709


def _write_json(value: object) -> None:
    json.dump(value, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


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


def _parse_source_repositories(values: list[str]) -> dict[str, Path]:
    repositories: dict[str, Path] = {}
    for value in values:
        binding_id, separator, path = value.partition("=")
        if not separator or not binding_id or not path:
            raise ValueError("--source-repo must use BINDING_ID=PATH")
        if binding_id in repositories:
            raise ValueError(f"duplicate --source-repo binding: {binding_id}")
        repositories[binding_id] = Path(path)
    return repositories


def _command_production_context(args: argparse.Namespace) -> int:
    _write_json(
        build_production_context(
            Path(args.production_root),
            source_repositories=_parse_source_repositories(args.source_repo),
        )
    )
    return 0


def _optional_path(value: str | None) -> Path | None:
    return Path(value) if value else None


def _equipment_module():
    from . import equipment
    return equipment


def _command_equipment_inventory(args: argparse.Namespace) -> int:
    module = _equipment_module()
    world = module.load_equipment_world(Path(args.world))
    inventory = module.discover_equipment(world)
    _write_json(inventory)
    return 0


def _command_equipment_select(args: argparse.Namespace) -> int:
    module = _equipment_module()
    world = module.load_equipment_world(Path(args.world))
    inventory = module.discover_equipment_for_capability(world, args.capability) if args.local else None
    _write_json({"capability": args.capability, "matches": module.select_for_capability(world, args.capability, inventory=inventory)})
    return 0


def _command_equipment_coverage(args: argparse.Namespace) -> int:
    module = _equipment_module()
    world = module.load_equipment_world(Path(args.world))
    _write_json(module.capability_coverage(world))
    return 0


def _command_equipment_providers(args: argparse.Namespace) -> int:
    module = _equipment_module()
    world = module.load_equipment_world(Path(args.world))
    _write_json(module.local_provider_surface(world))
    return 0


def _command_equipment_plan(args: argparse.Namespace) -> int:
    module = _equipment_module()
    parameters = json.loads(args.parameters) if args.parameters else {}
    _write_json(module.compile_operation(args.equipment_id, args.capability, parameters).as_dict())
    return 0


def _command_equipment_propose(args: argparse.Namespace) -> int:
    module = _equipment_module()
    world = module.load_equipment_world(Path(args.world))
    parameters = json.loads(args.parameters) if args.parameters else {}
    proposal = module.propose_operation(
        world,
        args.capability,
        parameters,
        equipment_id=args.equipment_id,
        local=not args.no_local,
    )
    _write_json(proposal)
    return 0 if proposal.get("ready") else 3


def _command_figma_route(args: argparse.Namespace) -> int:
    from .figma_provider import route_figma_operation
    _write_json(route_figma_operation(
        args.operation, desktop_state=args.desktop_state, remote_state=args.remote_state, prefer_local=not args.prefer_remote
    ).as_dict())
    return 0


def _resolve_adapter():
    try:
        from . import resolve_adapter
    except ModuleNotFoundError as error:
        if error.name == "opentimelineio":
            raise RuntimeError(
                "Resolve/OTIO equipment is optional; install the 'resolve' extra "
                "or run through `uv run --extra resolve ...`"
            ) from error
        raise
    return resolve_adapter


def _command_resolve_paths(args: argparse.Namespace) -> int:
    paths = _resolve_adapter().discover_resolve_paths()
    _write_json(
        {
            "scriptsDirectory": str(paths.scripts_directory),
            "controlDirectory": str(paths.control_directory),
            "windowsControlDirectory": paths.windows_control_directory,
        }
    )
    return 0


def _command_resolve_install(args: argparse.Namespace) -> int:
    _write_json(
        _resolve_adapter().install_runner(
            scripts_directory=_optional_path(args.scripts_directory),
            control_directory=_optional_path(args.control_directory),
            windows_control_directory=args.windows_control_directory,
        )
    )
    return 0


def _command_resolve_prepare_probe(args: argparse.Namespace) -> int:
    _write_json(
        _resolve_adapter().prepare_probe(
            control_directory=_optional_path(args.control_directory),
            operation_id=args.operation_id,
        )
    )
    return 0


def _command_resolve_prepare_smoke(args: argparse.Namespace) -> int:
    _write_json(
        _resolve_adapter().prepare_smoke(
            control_directory=_optional_path(args.control_directory),
            media_path=_optional_path(args.media),
            windows_media_path=args.windows_media_path,
            operation_id=args.operation_id,
        )
    )
    return 0


def _command_resolve_prepare_compatibility(args: argparse.Namespace) -> int:
    _write_json(
        _resolve_adapter().prepare_compatibility(
            control_directory=_optional_path(args.control_directory),
            media_path=_optional_path(args.media),
            windows_media_path=args.windows_media_path,
            developer_readme_path=_optional_path(args.developer_readme),
            operation_id=args.operation_id,
        )
    )
    return 0


def _command_resolve_prepare_assembly_conform(args: argparse.Namespace) -> int:
    _write_json(
        _resolve_adapter().prepare_assembly_conform(
            production_id=args.production_id,
            production_root=_optional_path(args.production_root),
            control_directory=_optional_path(args.control_directory),
            media_root=_optional_path(args.media_root),
            windows_media_root=args.windows_media_root,
            resolve_otio_root=_optional_path(args.resolve_otio_root),
            windows_resolve_otio_root=args.windows_resolve_otio_root,
            developer_readme_path=_optional_path(args.developer_readme),
            operation_id=args.operation_id,
        )
    )
    return 0


def _command_resolve_result(args: argparse.Namespace) -> int:
    result = _resolve_adapter().read_result(
        control_directory=_optional_path(args.control_directory),
        expected_operation_id=args.operation_id,
    )
    _write_json(result)
    return 0 if result.get("status") == "succeeded" else 1


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
    qc_parser.add_argument("--ffprobe", default="/usr/bin/ffprobe")
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
    production_context_parser.set_defaults(handler=_command_production_context)

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

    resolve_parser = commands.add_parser("resolve", help="operate the DaVinci Resolve-specific adapter")
    resolve_commands = resolve_parser.add_subparsers(dest="resolve_command", required=True)

    resolve_paths = resolve_commands.add_parser("paths", help="show discovered Windows adapter paths")
    resolve_paths.set_defaults(handler=_command_resolve_paths)

    resolve_install = resolve_commands.add_parser("install", help="install the internal Resolve menu runner")
    resolve_install.add_argument("--scripts-directory")
    resolve_install.add_argument("--control-directory")
    resolve_install.add_argument("--windows-control-directory")
    resolve_install.set_defaults(handler=_command_resolve_install)

    resolve_prepare = resolve_commands.add_parser("prepare-probe", help="prepare one read-only Resolve probe")
    resolve_prepare.add_argument("--control-directory")
    resolve_prepare.add_argument("--operation-id")
    resolve_prepare.set_defaults(handler=_command_resolve_prepare_probe)

    resolve_smoke = resolve_commands.add_parser(
        "prepare-smoke", help="prepare one bounded Resolve project mutation acceptance"
    )
    resolve_smoke.add_argument("--control-directory")
    resolve_smoke.add_argument("--media", help="WSL path to the smoke media fixture")
    resolve_smoke.add_argument("--windows-media-path", help="matching absolute Windows media path")
    resolve_smoke.add_argument("--operation-id")
    resolve_smoke.set_defaults(handler=_command_resolve_prepare_smoke)

    resolve_compatibility = resolve_commands.add_parser(
        "prepare-compatibility",
        help="prepare a Resolve Free 21.0.3.7 version-specific compatibility probe",
    )
    resolve_compatibility.add_argument("--control-directory")
    resolve_compatibility.add_argument("--media", help="WSL path to the compatibility media fixture")
    resolve_compatibility.add_argument("--windows-media-path", help="matching absolute Windows media path")
    resolve_compatibility.add_argument("--developer-readme", help="WSL path to the installed Developer README")
    resolve_compatibility.add_argument("--operation-id")
    resolve_compatibility.set_defaults(handler=_command_resolve_prepare_compatibility)

    resolve_assembly_conform = resolve_commands.add_parser(
        "prepare-assembly-conform",
        help="prepare a disposable Resolve 21.0.3.7 native OTIO conform acceptance",
    )
    resolve_assembly_conform.add_argument("--production-id", default="runtime-introduction")
    resolve_assembly_conform.add_argument("--production-root")
    resolve_assembly_conform.add_argument("--control-directory")
    resolve_assembly_conform.add_argument("--media-root")
    resolve_assembly_conform.add_argument("--windows-media-root")
    resolve_assembly_conform.add_argument("--resolve-otio-root")
    resolve_assembly_conform.add_argument("--windows-resolve-otio-root")
    resolve_assembly_conform.add_argument("--developer-readme")
    resolve_assembly_conform.add_argument("--operation-id")
    resolve_assembly_conform.set_defaults(handler=_command_resolve_prepare_assembly_conform)

    resolve_result = resolve_commands.add_parser("result", help="validate and print the latest Resolve result")
    resolve_result.add_argument("--control-directory")
    resolve_result.add_argument("--operation-id")
    resolve_result.set_defaults(handler=_command_resolve_result)
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
