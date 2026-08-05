from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import secrets
import shutil
import subprocess
import urllib.parse
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import opentimelineio as otio


RUNNER_FILENAME = "Ordivon Studio Runner.py"
CONFIG_FILENAME = "ordivon-runner.config.json"
OPERATION_FILENAME = "resolve-operation.json"
RESULT_FILENAME = "resolve-result.json"
SMOKE_FIXTURE_FILENAME = "resolve-smoke-1080p30.mp4"
COMPATIBILITY_OTIO_FILENAME = "resolve-21.0.3.7-compatibility.otio"
COMPATIBILITY_PROJECT_PREFIX = "Ordivon Resolve 21 Compatibility "
COMPATIBILITY_PRODUCT_NAME = "DaVinci Resolve"
COMPATIBILITY_VERSION_STRING = "21.0.3.7"
COMPATIBILITY_VERSION = [21, 0, 3, 7, ""]
DEVELOPER_README_PATH = Path(
    "/mnt/c/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/README.txt"
)
ASSEMBLY_PROJECT_NAME = "Ordivon Runtime Introduction"
ASSEMBLY_TIMELINE_NAME = "Assembly v0"
ASSEMBLY_CONFORM_PROJECT_PREFIX = "Ordivon Runtime Introduction Conform Probe "
ASSEMBLY_CONFORM_TIMELINE_NAME = "Assembly v0 Conform Probe"
ASSEMBLY_CONFORM_OTIO_FILENAME = "assembly.v0.resolve-21.0.3.7.otio"
_OPERATION_ID = re.compile(r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$")
_DIGEST = re.compile(r"^sha256:[a-f0-9]{64}$")


@dataclass(frozen=True, slots=True)
class ResolvePaths:
    scripts_directory: Path
    control_directory: Path
    windows_control_directory: str


@dataclass(frozen=True, slots=True)
class MediaCachePaths:
    directory: Path
    windows_directory: str


def _canonical_digest(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def _hash_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    if not path.is_file():
        raise FileNotFoundError(path)
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {path.name}")
    return value


def _atomic_write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.tmp-{os.getpid()}")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def _powershell_environment() -> dict[str, str]:
    powershell = Path("/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe")
    if not powershell.is_file():
        raise RuntimeError("Windows PowerShell is unavailable; pass explicit Resolve paths")
    command = (
        "[Console]::OutputEncoding=[System.Text.UTF8Encoding]::new(); "
        "$value=[ordered]@{AppData=$env:APPDATA;LocalAppData=$env:LOCALAPPDATA}; "
        "$value | ConvertTo-Json -Compress"
    )
    result = subprocess.run(
        [str(powershell), "-NoProfile", "-Command", command],
        check=False,
        capture_output=True,
        text=True,
        timeout=20,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "PowerShell environment discovery failed")
    value = json.loads(result.stdout.strip())
    if not isinstance(value, dict) or not all(isinstance(value.get(key), str) for key in ("AppData", "LocalAppData")):
        raise RuntimeError("PowerShell returned incomplete Windows profile paths")
    return {"AppData": value["AppData"], "LocalAppData": value["LocalAppData"]}


def _wslpath(value: str, mode: str) -> str:
    executable = Path("/usr/bin/wslpath")
    if not executable.is_file():
        raise RuntimeError("wslpath is unavailable; pass explicit path forms")
    result = subprocess.run(
        [str(executable), mode, value],
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"wslpath {mode} failed")
    return result.stdout.strip()


def discover_resolve_paths() -> ResolvePaths:
    environment = _powershell_environment()
    windows_scripts = (
        environment["AppData"]
        + r"\Blackmagic Design\DaVinci Resolve\Support\Fusion\Scripts\Utility\Ordivon"
    )
    windows_control = environment["LocalAppData"] + r"\OrdivonStudio\control"
    return ResolvePaths(
        scripts_directory=Path(_wslpath(windows_scripts, "-u")),
        control_directory=Path(_wslpath(windows_control, "-u")),
        windows_control_directory=windows_control,
    )


def discover_smoke_fixture() -> tuple[Path, str]:
    environment = _powershell_environment()
    windows_path = environment["LocalAppData"] + rf"\OrdivonStudio\fixtures\{SMOKE_FIXTURE_FILENAME}"
    return Path(_wslpath(windows_path, "-u")), windows_path


def _windows_file_uri(path: str) -> str:
    normalized = path.replace("\\", "/")
    if len(normalized) < 3 or normalized[1] != ":" or normalized[2] != "/":
        raise ValueError("expected an absolute Windows drive path")
    return "file:///" + urllib.parse.quote(normalized, safe="/:")


def _media_frame_count(path: Path, *, ffprobe: str = "/usr/bin/ffprobe") -> int:
    result = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=nb_frames,avg_frame_rate:format=duration",
            "-of",
            "json",
            str(path),
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "ffprobe failed for compatibility fixture")
    value = json.loads(result.stdout)
    streams = value.get("streams")
    if not isinstance(streams, list) or len(streams) != 1 or not isinstance(streams[0], dict):
        raise ValueError("compatibility fixture must contain exactly one video stream")
    stream = streams[0]
    nb_frames = stream.get("nb_frames")
    if isinstance(nb_frames, str) and nb_frames.isdigit():
        frames = int(nb_frames)
    else:
        rate_text = stream.get("avg_frame_rate")
        duration_text = value.get("format", {}).get("duration") if isinstance(value.get("format"), dict) else None
        if not isinstance(rate_text, str) or "/" not in rate_text or not isinstance(duration_text, str):
            raise ValueError("compatibility fixture has no reliable frame count")
        numerator, denominator = (int(part) for part in rate_text.split("/", 1))
        if denominator == 0:
            raise ValueError("compatibility fixture frame rate denominator is zero")
        frames = round(float(duration_text) * numerator / denominator)
    if frames < 60:
        raise ValueError("compatibility fixture must contain at least 60 frames")
    return frames


def _write_compatibility_otio(path: Path, *, windows_media_path: str, media_frames: int) -> None:
    timeline = otio.schema.Timeline(
        name="Resolve 21.0.3.7 OTIO Compatibility",
        global_start_time=otio.opentime.RationalTime(108000, 30),
    )
    timeline.metadata.update(
        {
            "ordivon": {
                "kind": "resolve-compatibility-probe",
                "resolveVersion": COMPATIBILITY_VERSION_STRING,
                "expectedFrames": 60,
            }
        }
    )
    track = otio.schema.Track(name="V1 Compatibility", kind=otio.schema.TrackKind.Video)
    media_uri = _windows_file_uri(windows_media_path)
    first_range = otio.opentime.TimeRange(
        otio.opentime.RationalTime(0, 30),
        otio.opentime.RationalTime(24, 30),
    )
    second_range = otio.opentime.TimeRange(
        otio.opentime.RationalTime(24, 30),
        otio.opentime.RationalTime(30, 30),
    )
    available = otio.opentime.TimeRange(
        otio.opentime.RationalTime(0, 30),
        otio.opentime.RationalTime(media_frames, 30),
    )
    track.append(
        otio.schema.Clip(
            name="otio-first-24",
            media_reference=otio.schema.ExternalReference(target_url=media_uri, available_range=available),
            source_range=first_range,
        )
    )
    track.append(otio.schema.Gap(source_range=otio.opentime.TimeRange(duration=otio.opentime.RationalTime(6, 30))))
    track.append(
        otio.schema.Clip(
            name="otio-next-30",
            media_reference=otio.schema.ExternalReference(target_url=media_uri, available_range=available),
            source_range=second_range,
        )
    )
    timeline.tracks.append(track)
    path.parent.mkdir(parents=True, exist_ok=True)
    otio.adapters.write_to_file(timeline, str(path), adapter_name="otio_json")


def discover_production_media(production_id: str) -> MediaCachePaths:
    if not _OPERATION_ID.fullmatch(production_id):
        raise ValueError("productionId has an invalid format")
    environment = _powershell_environment()
    windows_directory = environment["LocalAppData"] + rf"\OrdivonStudio\productions\{production_id}\media"
    return MediaCachePaths(
        directory=Path(_wslpath(windows_directory, "-u")),
        windows_directory=windows_directory,
    )


def _resolved_paths(
    *,
    scripts_directory: Path | None = None,
    control_directory: Path | None = None,
    windows_control_directory: str | None = None,
) -> ResolvePaths:
    if scripts_directory is None and control_directory is None and windows_control_directory is None:
        return discover_resolve_paths()

    discovered: ResolvePaths | None = None
    if scripts_directory is None or control_directory is None:
        discovered = discover_resolve_paths()
    scripts = scripts_directory or discovered.scripts_directory  # type: ignore[union-attr]
    control = control_directory or discovered.control_directory  # type: ignore[union-attr]
    windows_control = windows_control_directory
    if windows_control is None:
        try:
            windows_control = _wslpath(str(control), "-w")
        except RuntimeError:
            if discovered and control == discovered.control_directory:
                windows_control = discovered.windows_control_directory
            else:
                raise
    return ResolvePaths(Path(scripts), Path(control), windows_control)


def install_runner(
    *,
    scripts_directory: Path | None = None,
    control_directory: Path | None = None,
    windows_control_directory: str | None = None,
) -> dict[str, Any]:
    paths = _resolved_paths(
        scripts_directory=scripts_directory,
        control_directory=control_directory,
        windows_control_directory=windows_control_directory,
    )
    source = Path(__file__).resolve().with_name("resolve_runner_menu.py")
    if not source.is_file():
        raise FileNotFoundError(source)

    paths.scripts_directory.mkdir(parents=True, exist_ok=True)
    paths.control_directory.mkdir(parents=True, exist_ok=True)
    destination = paths.scripts_directory / RUNNER_FILENAME
    shutil.copyfile(source, destination)
    config = {
        "schemaVersion": 1,
        "controlDirectory": paths.windows_control_directory,
    }
    _atomic_write_json(paths.scripts_directory / CONFIG_FILENAME, config)
    return {
        "installed": True,
        "runner": str(destination),
        "config": str(paths.scripts_directory / CONFIG_FILENAME),
        "controlDirectory": str(paths.control_directory),
        "menu": "Workspace > Scripts > Utility > Ordivon > Ordivon Studio Runner",
    }


def _new_operation_id(kind: str) -> str:
    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dt%H%M%Sz").lower()
    return f"resolve-{kind}-{timestamp}-{secrets.token_hex(4)}"


def _requested_at() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _validate_operation_id(operation_id: str) -> str:
    if not _OPERATION_ID.fullmatch(operation_id):
        raise ValueError("operationId has an invalid format")
    return operation_id


def build_probe_operation(operation_id: str | None = None) -> dict[str, Any]:
    operation_id = _validate_operation_id(operation_id or _new_operation_id("probe"))
    return {
        "schemaVersion": 1,
        "operationId": operation_id,
        "action": "probe",
        "requestedAt": _requested_at(),
    }


def build_smoke_operation(
    *,
    media_path: str,
    media_digest: str,
    operation_id: str | None = None,
    project_name: str | None = None,
) -> dict[str, Any]:
    operation_id = _validate_operation_id(operation_id or _new_operation_id("smoke"))
    if not _DIGEST.fullmatch(media_digest):
        raise ValueError("mediaDigest must be a sha256 digest")
    suffix = operation_id.removeprefix("resolve-smoke-")
    project_name = project_name or f"Ordivon Resolve Smoke {suffix}"
    if not project_name.startswith("Ordivon Resolve Smoke "):
        raise ValueError("smoke project name must use the reserved prefix")
    return {
        "schemaVersion": 1,
        "operationId": operation_id,
        "action": "create-smoke-project",
        "requestedAt": _requested_at(),
        "parameters": {
            "projectName": project_name,
            "timelineName": "Assembly",
            "binName": "01_SMOKE",
            "mediaPath": media_path,
            "mediaDigest": media_digest,
            "settings": {"frameRate": 30, "width": 1920, "height": 1080},
            "restorePreviousProject": True,
        },
    }


def build_compatibility_operation(
    *,
    media_path: str,
    media_digest: str,
    media_file_name: str,
    media_expected_frames: int,
    otio_path: str,
    otio_digest: str,
    source_clips_path: str,
    developer_package_digest: str,
    operation_id: str | None = None,
) -> dict[str, Any]:
    operation_id = _validate_operation_id(operation_id or _new_operation_id("compatibility"))
    if not _DIGEST.fullmatch(media_digest):
        raise ValueError("mediaDigest must be a sha256 digest")
    if not _DIGEST.fullmatch(otio_digest):
        raise ValueError("otioDigest must be a sha256 digest")
    if not _DIGEST.fullmatch(developer_package_digest):
        raise ValueError("developerPackageDigest must be a sha256 digest")
    if media_expected_frames < 60:
        raise ValueError("compatibility media must contain at least 60 frames")
    suffix = operation_id.removeprefix("resolve-compatibility-")
    return {
        "schemaVersion": 1,
        "operationId": operation_id,
        "action": "probe-compatibility",
        "requestedAt": _requested_at(),
        "parameters": {
            "projectName": COMPATIBILITY_PROJECT_PREFIX + suffix,
            "expectedProductName": COMPATIBILITY_PRODUCT_NAME,
            "expectedVersionString": COMPATIBILITY_VERSION_STRING,
            "expectedVersion": COMPATIBILITY_VERSION,
            "developerPackageDigest": developer_package_digest,
            "mediaPath": media_path,
            "mediaDigest": media_digest,
            "mediaFileName": media_file_name,
            "mediaExpectedFrames": media_expected_frames,
            "otioPath": otio_path,
            "otioDigest": otio_digest,
            "sourceClipsPath": source_clips_path,
            "settings": {"frameRate": 30, "width": 1920, "height": 1080},
            "restorePreviousProject": True,
            "cleanupProject": True,
        },
    }


def _time_to_frames(value: otio.opentime.RationalTime, expected_rate: float) -> int:
    if value.rate <= 0:
        raise ValueError("OTIO time rate must be positive")
    return int(round(value.value * expected_rate / value.rate))


def _asset_map(asset_manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    assets = asset_manifest.get("assets")
    if not isinstance(assets, list):
        raise ValueError("asset manifest assets must be an array")
    result: dict[str, dict[str, Any]] = {}
    for asset in assets:
        if not isinstance(asset, dict) or not isinstance(asset.get("id"), str):
            raise ValueError("asset manifest contains an invalid asset")
        asset_id = asset["id"]
        if asset_id in result:
            raise ValueError(f"duplicate asset id: {asset_id}")
        result[asset_id] = asset
    return result


def _windows_child(directory: str, file_name: str) -> str:
    if not file_name or "/" in file_name or "\\" in file_name:
        raise ValueError("asset technical.fileName must be a base file name")
    return directory.rstrip("\\/") + "\\" + file_name


def _write_resolve_assembly_otio(
    path: Path,
    *,
    production_id: str,
    start_timecode: str,
    segments: list[dict[str, Any]],
) -> None:
    start_frames = otio.opentime.from_timecode(start_timecode, 30).rescaled_to(30)
    timeline = otio.schema.Timeline(
        name=ASSEMBLY_TIMELINE_NAME,
        global_start_time=start_frames,
        metadata={
            "ordivon": {
                "productionId": production_id,
                "kind": "resolve-facing-conform",
                "resolveProfile": "resolve-free-21.0.3.7-windows-internal-menu",
                "totalFrames": sum(int(segment["durationFrames"]) for segment in segments),
            }
        },
    )
    track = otio.schema.Track(name="V1 Assembly", kind=otio.schema.TrackKind.Video)
    for segment in segments:
        duration = int(segment["durationFrames"])
        available = otio.opentime.TimeRange(
            otio.opentime.RationalTime(0, 30),
            otio.opentime.RationalTime(duration, 30),
        )
        reference = otio.schema.ExternalReference(
            target_url=_windows_file_uri(str(segment["mediaPath"])),
            available_range=available,
            metadata={
                "ordivon": {
                    "assetId": segment["assetId"],
                    "mediaDigest": segment["mediaDigest"],
                }
            },
        )
        track.append(
            otio.schema.Clip(
                name=segment["id"],
                media_reference=reference,
                source_range=available,
                metadata={
                    "ordivon": {
                        "segmentId": segment["id"],
                        "assetId": segment["assetId"],
                        "binName": segment["binName"],
                        "placeholder": segment["placeholder"],
                    }
                },
            )
        )
    timeline.tracks.append(track)
    path.parent.mkdir(parents=True, exist_ok=True)
    otio.adapters.write_to_file(timeline, str(path), adapter_name="otio_json")


def build_assembly_operation(
    *,
    production_root: Path,
    media_root: Path,
    windows_media_root: str,
    operation_id: str | None = None,
) -> dict[str, Any]:
    operation_id = _validate_operation_id(operation_id or _new_operation_id("assembly"))
    production_path = production_root / "production.json"
    assets_path = production_root / "assets.json"
    production = _load_json(production_path)
    asset_manifest = _load_json(assets_path)

    production_id = production.get("id")
    if production_id != asset_manifest.get("productionId") or not isinstance(production_id, str):
        raise ValueError("Production and Asset manifest identities do not match")

    profile = production.get("workingProfile")
    if not isinstance(profile, dict):
        raise ValueError("Production workingProfile is missing")
    frame_rate = profile.get("frameRate")
    canvas = profile.get("canvas")
    if frame_rate != {"numerator": 30, "denominator": 1}:
        raise ValueError("Assembly v0 currently requires a 30/1 Production frame rate")
    if canvas != {"width": 1920, "height": 1080}:
        raise ValueError("Assembly v0 currently requires a 1920x1080 Production canvas")

    sources = production.get("sources")
    snapshots = sources.get("otioSnapshots") if isinstance(sources, dict) else None
    if not isinstance(snapshots, list) or len(snapshots) != 1 or not isinstance(snapshots[0], str):
        raise ValueError("Production must select exactly one OTIO assembly snapshot")
    otio_path = production_root / snapshots[0]
    timeline = otio.adapters.read_from_file(str(otio_path))
    if not isinstance(timeline, otio.schema.Timeline):
        raise ValueError("OTIO snapshot root must be a Timeline")
    metadata = timeline.metadata.get("ordivon", {})
    if not isinstance(metadata, Mapping) or metadata.get("productionId") != production_id:
        raise ValueError("OTIO Production identity does not match")

    video_tracks = [track for track in timeline.video_tracks()]
    if len(video_tracks) != 1:
        raise ValueError("Assembly v0 must contain exactly one video track")
    track = video_tracks[0]
    assets = _asset_map(asset_manifest)
    expected_rate = 30.0
    segments: list[dict[str, Any]] = []
    cursor = 0

    for child in track:
        if not isinstance(child, otio.schema.Clip):
            raise ValueError("Assembly v0 video track may contain only Clips")
        clip_metadata = child.metadata.get("ordivon", {})
        if not isinstance(clip_metadata, Mapping):
            raise ValueError("OTIO Clip is missing Ordivon metadata")
        segment_id = clip_metadata.get("segmentId")
        asset_id = clip_metadata.get("assetId")
        bin_name = clip_metadata.get("binName")
        placeholder = clip_metadata.get("placeholder")
        if not isinstance(segment_id, str) or not _OPERATION_ID.fullmatch(segment_id):
            raise ValueError("OTIO segmentId has an invalid format")
        if not isinstance(asset_id, str) or asset_id not in assets:
            raise ValueError(f"OTIO Clip references an unknown Asset: {asset_id}")
        if bin_name not in {"01_PLACEHOLDERS", "02_MOTION"}:
            raise ValueError("OTIO Clip uses an unsupported Resolve Bin")
        if not isinstance(placeholder, bool):
            raise ValueError("OTIO Clip placeholder flag must be boolean")
        if child.source_range is None:
            raise ValueError("OTIO Clip must have a source range")
        duration_frames = _time_to_frames(child.source_range.duration, expected_rate)
        source_start = _time_to_frames(child.source_range.start_time, expected_rate)
        if source_start != 0 or duration_frames <= 0:
            raise ValueError("Assembly v0 Clips must use complete media from frame zero")

        asset = assets[asset_id]
        blob = asset.get("selectedBlob")
        technical = asset.get("technical")
        if not isinstance(blob, dict) or not isinstance(technical, dict):
            raise ValueError(f"Asset is not selected and technically described: {asset_id}")
        digest = blob.get("digest")
        size_bytes = blob.get("sizeBytes")
        file_name = technical.get("fileName")
        asset_duration = technical.get("durationFrames")
        if not isinstance(digest, str) or not _DIGEST.fullmatch(digest):
            raise ValueError(f"Asset digest is invalid: {asset_id}")
        if not isinstance(size_bytes, int) or size_bytes < 0:
            raise ValueError(f"Asset size is invalid: {asset_id}")
        if not isinstance(file_name, str):
            raise ValueError(f"Asset fileName is invalid: {asset_id}")
        if asset_duration != duration_frames:
            raise ValueError(f"OTIO duration differs from Asset duration: {asset_id}")

        local_path = media_root / file_name
        if not local_path.is_file():
            raise FileNotFoundError(f"selected Assembly media is missing: {file_name}")
        if local_path.stat().st_size != size_bytes:
            raise ValueError(f"selected Assembly media size differs: {file_name}")
        if _hash_file(local_path) != digest:
            raise ValueError(f"selected Assembly media digest differs: {file_name}")

        segments.append(
            {
                "id": segment_id,
                "assetId": asset_id,
                "fileName": file_name,
                "mediaPath": _windows_child(windows_media_root, file_name),
                "mediaDigest": digest,
                "binName": bin_name,
                "startFrame": cursor,
                "durationFrames": duration_frames,
                "placeholder": placeholder,
            }
        )
        cursor += duration_frames

    total_frames = metadata.get("totalFrames")
    if total_frames != cursor:
        raise ValueError("OTIO totalFrames does not match the assembled Clip duration")
    if cursor != 2340:
        raise ValueError("Runtime Introduction Assembly v0 must be exactly 2340 frames")

    global_start = timeline.global_start_time or otio.opentime.RationalTime(108000, expected_rate)
    start_timecode = otio.opentime.to_timecode(global_start, rate=expected_rate)
    return {
        "schemaVersion": 1,
        "operationId": operation_id,
        "action": "assemble-review",
        "requestedAt": _requested_at(),
        "parameters": {
            "productionId": production_id,
            "projectName": ASSEMBLY_PROJECT_NAME,
            "timelineName": ASSEMBLY_TIMELINE_NAME,
            "startTimecode": start_timecode,
            "settings": {"frameRate": 30, "width": 1920, "height": 1080},
            "totalFrames": cursor,
            "sourceDigests": {
                "production": _hash_file(production_path),
                "assets": _hash_file(assets_path),
                "timeline": _hash_file(otio_path),
            },
            "segments": segments,
            "restorePreviousProject": True,
        },
    }


def build_assembly_conform_operation(
    *,
    production_root: Path,
    media_root: Path,
    windows_media_root: str,
    resolve_otio_path: Path,
    windows_resolve_otio_path: str,
    developer_readme_path: Path = DEVELOPER_README_PATH,
    operation_id: str | None = None,
) -> dict[str, Any]:
    operation_id = _validate_operation_id(operation_id or _new_operation_id("assembly-conform"))
    operation = build_assembly_operation(
        production_root=production_root,
        media_root=media_root,
        windows_media_root=windows_media_root,
        operation_id=operation_id,
    )
    parameters = operation["parameters"]
    suffix = operation_id.removeprefix("resolve-assembly-conform-")
    _write_resolve_assembly_otio(
        resolve_otio_path,
        production_id=parameters["productionId"],
        start_timecode=parameters["startTimecode"],
        segments=parameters["segments"],
    )
    parameters.update(
        {
            "projectName": ASSEMBLY_CONFORM_PROJECT_PREFIX + suffix,
            "timelineName": ASSEMBLY_CONFORM_TIMELINE_NAME,
            "expectedProductName": COMPATIBILITY_PRODUCT_NAME,
            "expectedVersionString": COMPATIBILITY_VERSION_STRING,
            "expectedVersion": COMPATIBILITY_VERSION,
            "developerPackageDigest": _hash_file(developer_readme_path),
            "resolveOtioPath": windows_resolve_otio_path,
            "resolveOtioDigest": _hash_file(resolve_otio_path),
            "cleanupProject": True,
        }
    )
    operation["action"] = "probe-assembly-conform"
    return operation


def _prepare_operation(control: Path, operation: dict[str, Any]) -> dict[str, Any]:
    path = control / OPERATION_FILENAME
    _atomic_write_json(path, operation)
    stale_result = control / RESULT_FILENAME
    if stale_result.exists():
        stale_result.unlink()
    return {
        "prepared": True,
        "operation": operation,
        "operationDigest": _canonical_digest(operation),
        "operationPath": str(path),
    }


def prepare_probe(*, control_directory: Path | None = None, operation_id: str | None = None) -> dict[str, Any]:
    control = control_directory or discover_resolve_paths().control_directory
    return _prepare_operation(control, build_probe_operation(operation_id))


def prepare_smoke(
    *,
    control_directory: Path | None = None,
    media_path: Path | None = None,
    windows_media_path: str | None = None,
    operation_id: str | None = None,
) -> dict[str, Any]:
    control = control_directory or discover_resolve_paths().control_directory
    if media_path is None and windows_media_path is None:
        media_path, windows_media_path = discover_smoke_fixture()
    elif media_path is None:
        media_path = Path(_wslpath(windows_media_path, "-u"))  # type: ignore[arg-type]
    elif windows_media_path is None:
        windows_media_path = _wslpath(str(media_path), "-w")
    digest = _hash_file(media_path)
    operation = build_smoke_operation(
        media_path=windows_media_path,
        media_digest=digest,
        operation_id=operation_id,
    )
    prepared = _prepare_operation(control, operation)
    prepared["media"] = {
        "path": str(media_path),
        "digest": digest,
        "sizeBytes": media_path.stat().st_size,
    }
    return prepared


def prepare_compatibility(
    *,
    control_directory: Path | None = None,
    media_path: Path | None = None,
    windows_media_path: str | None = None,
    developer_readme_path: Path | None = None,
    operation_id: str | None = None,
) -> dict[str, Any]:
    control = control_directory or discover_resolve_paths().control_directory
    if media_path is None and windows_media_path is None:
        media_path, windows_media_path = discover_smoke_fixture()
    elif media_path is None:
        media_path = Path(_wslpath(windows_media_path, "-u"))  # type: ignore[arg-type]
    elif windows_media_path is None:
        windows_media_path = _wslpath(str(media_path), "-w")
    if media_path is None or windows_media_path is None:
        raise RuntimeError("compatibility media path resolution failed")
    media_frames = _media_frame_count(media_path)
    source_clips_path = windows_media_path.rsplit("\\", 1)[0]
    otio_path = media_path.parent / COMPATIBILITY_OTIO_FILENAME
    windows_otio_path = source_clips_path + "\\" + COMPATIBILITY_OTIO_FILENAME
    _write_compatibility_otio(
        otio_path,
        windows_media_path=windows_media_path,
        media_frames=media_frames,
    )
    developer_readme = developer_readme_path or DEVELOPER_README_PATH
    operation = build_compatibility_operation(
        media_path=windows_media_path,
        media_digest=_hash_file(media_path),
        media_file_name=media_path.name,
        media_expected_frames=media_frames,
        otio_path=windows_otio_path,
        otio_digest=_hash_file(otio_path),
        source_clips_path=source_clips_path,
        developer_package_digest=_hash_file(developer_readme),
        operation_id=operation_id,
    )
    prepared = _prepare_operation(control, operation)
    prepared["compatibility"] = {
        "expectedProductName": COMPATIBILITY_PRODUCT_NAME,
        "expectedVersionString": COMPATIBILITY_VERSION_STRING,
        "developerPackageDigest": operation["parameters"]["developerPackageDigest"],
        "mediaDigest": operation["parameters"]["mediaDigest"],
        "mediaExpectedFrames": media_frames,
        "otioDigest": operation["parameters"]["otioDigest"],
        "caseCount": 6,
        "cleanupProject": True,
    }
    return prepared


def prepare_assembly_conform(
    *,
    production_id: str = "runtime-introduction",
    production_root: Path | None = None,
    control_directory: Path | None = None,
    media_root: Path | None = None,
    windows_media_root: str | None = None,
    resolve_otio_root: Path | None = None,
    windows_resolve_otio_root: str | None = None,
    developer_readme_path: Path | None = None,
    operation_id: str | None = None,
) -> dict[str, Any]:
    repository_root = Path(__file__).resolve().parents[2]
    production_root = production_root or repository_root / "productions" / production_id
    control = control_directory or discover_resolve_paths().control_directory
    if media_root is None and windows_media_root is None:
        discovered = discover_production_media(production_id)
        media_root = discovered.directory
        windows_media_root = discovered.windows_directory
    elif media_root is None:
        media_root = Path(_wslpath(windows_media_root, "-u"))  # type: ignore[arg-type]
    elif windows_media_root is None:
        windows_media_root = _wslpath(str(media_root), "-w")
    if media_root is None or windows_media_root is None:
        raise RuntimeError("assembly conform media path resolution failed")

    if resolve_otio_root is None and windows_resolve_otio_root is None:
        resolve_otio_root = media_root.parent / "resolve"
        windows_resolve_otio_root = windows_media_root.rsplit("\\", 1)[0] + r"\resolve"
    elif resolve_otio_root is None:
        resolve_otio_root = Path(_wslpath(windows_resolve_otio_root, "-u"))  # type: ignore[arg-type]
    elif windows_resolve_otio_root is None:
        windows_resolve_otio_root = _wslpath(str(resolve_otio_root), "-w")
    if resolve_otio_root is None or windows_resolve_otio_root is None:
        raise RuntimeError("assembly conform OTIO path resolution failed")

    resolve_otio_path = resolve_otio_root / ASSEMBLY_CONFORM_OTIO_FILENAME
    windows_resolve_otio_path = _windows_child(windows_resolve_otio_root, ASSEMBLY_CONFORM_OTIO_FILENAME)
    operation = build_assembly_conform_operation(
        production_root=production_root,
        media_root=media_root,
        windows_media_root=windows_media_root,
        resolve_otio_path=resolve_otio_path,
        windows_resolve_otio_path=windows_resolve_otio_path,
        developer_readme_path=developer_readme_path or DEVELOPER_README_PATH,
        operation_id=operation_id,
    )
    prepared = _prepare_operation(control, operation)
    prepared["assemblyConform"] = {
        "productionId": production_id,
        "resolveProfile": "resolve-free-21.0.3.7-windows-internal-menu",
        "segmentCount": len(operation["parameters"]["segments"]),
        "totalFrames": operation["parameters"]["totalFrames"],
        "totalSeconds": operation["parameters"]["totalFrames"] / 30,
        "resolveOtioDigest": operation["parameters"]["resolveOtioDigest"],
        "cleanupProject": True,
    }
    return prepared


def prepare_assembly(
    *,
    production_id: str = "runtime-introduction",
    production_root: Path | None = None,
    control_directory: Path | None = None,
    media_root: Path | None = None,
    windows_media_root: str | None = None,
    operation_id: str | None = None,
) -> dict[str, Any]:
    repository_root = Path(__file__).resolve().parents[2]
    production_root = production_root or repository_root / "productions" / production_id
    control = control_directory or discover_resolve_paths().control_directory
    if media_root is None and windows_media_root is None:
        discovered = discover_production_media(production_id)
        media_root = discovered.directory
        windows_media_root = discovered.windows_directory
    elif media_root is None:
        media_root = Path(_wslpath(windows_media_root, "-u"))  # type: ignore[arg-type]
    elif windows_media_root is None:
        windows_media_root = _wslpath(str(media_root), "-w")

    operation = build_assembly_operation(
        production_root=production_root,
        media_root=media_root,
        windows_media_root=windows_media_root,
        operation_id=operation_id,
    )
    prepared = _prepare_operation(control, operation)
    prepared["assembly"] = {
        "productionId": production_id,
        "segmentCount": len(operation["parameters"]["segments"]),
        "totalFrames": operation["parameters"]["totalFrames"],
        "totalSeconds": operation["parameters"]["totalFrames"] / 30,
        "placeholderCount": sum(1 for segment in operation["parameters"]["segments"] if segment["placeholder"]),
    }
    return prepared


def validate_result(result: dict[str, Any], *, expected_operation_id: str | None = None) -> list[str]:
    errors: list[str] = []
    if result.get("schemaVersion") != 1:
        errors.append("schemaVersion must be 1")
    if result.get("adapter") != "resolve":
        errors.append("adapter must be resolve")
    action = result.get("action")
    if action not in {
        "probe",
        "create-smoke-project",
        "probe-compatibility",
        "probe-assembly-conform",
        "assemble-review",
    }:
        errors.append("action is unsupported")
    if result.get("status") not in {"succeeded", "failed"}:
        errors.append("status must be succeeded or failed")
    operation_id = result.get("operationId")
    if operation_id is not None and (not isinstance(operation_id, str) or not _OPERATION_ID.fullmatch(operation_id)):
        errors.append("operationId has an invalid format")
    if expected_operation_id is not None and operation_id != expected_operation_id:
        errors.append(f"operationId does not match expected {expected_operation_id}")
    digest = result.get("operationDigest")
    if digest is not None and (not isinstance(digest, str) or not _DIGEST.fullmatch(digest)):
        errors.append("operationDigest is invalid")
    if result.get("status") == "succeeded":
        if action == "probe":
            probe = result.get("probe")
            if not isinstance(probe, dict):
                errors.append("successful probe result must contain probe")
            elif not isinstance(probe.get("capabilities"), dict):
                errors.append("probe must contain capabilities")
        elif action == "create-smoke-project":
            smoke = result.get("smoke")
            if not isinstance(smoke, dict):
                errors.append("successful smoke result must contain smoke")
            else:
                project = smoke.get("project")
                timeline = smoke.get("timeline")
                media = smoke.get("media")
                if not isinstance(project, dict) or not str(project.get("name", "")).startswith("Ordivon Resolve Smoke "):
                    errors.append("smoke result has an invalid project")
                if not isinstance(timeline, dict) or not timeline.get("videoTrackItems"):
                    errors.append("smoke result has no video timeline item")
                if not isinstance(media, dict) or not _DIGEST.fullmatch(str(media.get("digest", ""))):
                    errors.append("smoke result has an invalid media digest")
                if smoke.get("restoredPreviousProject") is not True:
                    errors.append("smoke result did not restore the previous project")
        elif action == "probe-compatibility":
            compatibility = result.get("compatibility")
            if not isinstance(compatibility, dict):
                errors.append("successful compatibility result must contain compatibility")
            else:
                resolve = compatibility.get("resolve")
                cases = compatibility.get("cases")
                summary = compatibility.get("caseSummary")
                if not isinstance(resolve, dict):
                    errors.append("compatibility result has no Resolve identity")
                else:
                    if resolve.get("productName") != COMPATIBILITY_PRODUCT_NAME:
                        errors.append("compatibility result product does not match")
                    if resolve.get("versionString") != COMPATIBILITY_VERSION_STRING:
                        errors.append("compatibility result version does not match")
                    if resolve.get("edition") != "free":
                        errors.append("compatibility result edition does not match")
                if not isinstance(cases, list) or len(cases) != 6:
                    errors.append("compatibility result must contain six cases")
                if not isinstance(summary, dict) or summary.get("total") != 6:
                    errors.append("compatibility case summary is invalid")
                if compatibility.get("restoredPreviousProject") is not True:
                    errors.append("compatibility result did not restore the previous project")
        elif action == "probe-assembly-conform":
            conform = result.get("assemblyConform")
            if not isinstance(conform, dict):
                errors.append("successful assembly conform result must contain assemblyConform")
            else:
                project = conform.get("project")
                timeline = conform.get("timeline")
                segments = conform.get("segments")
                cleanup = conform.get("cleanup")
                resolve = conform.get("resolve")
                if not isinstance(project, dict) or not str(project.get("name", "")).startswith(
                    ASSEMBLY_CONFORM_PROJECT_PREFIX
                ):
                    errors.append("assembly conform result has an invalid project")
                if not isinstance(timeline, dict) or timeline.get("name") != ASSEMBLY_CONFORM_TIMELINE_NAME:
                    errors.append("assembly conform result has an invalid timeline")
                elif timeline.get("totalFrames") != 2340 or timeline.get("videoItemCount") != 11:
                    errors.append("assembly conform timeline structure is incomplete")
                if not isinstance(segments, list) or len(segments) != 11:
                    errors.append("assembly conform result must contain 11 segments")
                if conform.get("placeholderCount") != 8:
                    errors.append("assembly conform placeholder count differs")
                if conform.get("restoredPreviousProject") is not True:
                    errors.append("assembly conform did not restore the previous project")
                if not isinstance(cleanup, dict) or cleanup.get("deleted") is not True:
                    errors.append("assembly conform disposable project was not deleted")
                if not isinstance(resolve, dict) or resolve.get("versionString") != COMPATIBILITY_VERSION_STRING:
                    errors.append("assembly conform Resolve profile differs")
        elif action == "assemble-review":
            assembly = result.get("assembly")
            if not isinstance(assembly, dict):
                errors.append("successful assembly result must contain assembly")
            else:
                project = assembly.get("project")
                timeline = assembly.get("timeline")
                segments = assembly.get("segments")
                if not isinstance(project, dict) or project.get("name") != ASSEMBLY_PROJECT_NAME:
                    errors.append("assembly result has an invalid project")
                if not isinstance(timeline, dict) or timeline.get("name") != ASSEMBLY_TIMELINE_NAME:
                    errors.append("assembly result has an invalid timeline")
                elif timeline.get("totalFrames") != 2340 or timeline.get("videoItemCount") != 11:
                    errors.append("assembly timeline structure is incomplete")
                if not isinstance(segments, list) or len(segments) != 11:
                    errors.append("assembly result must contain 11 segments")
                if assembly.get("restoredPreviousProject") is not True:
                    errors.append("assembly result did not restore the previous project")
    if result.get("status") == "failed" and not isinstance(result.get("error"), dict):
        errors.append("failed result must contain error")
    encoded = json.dumps(result, ensure_ascii=False, sort_keys=True)
    for forbidden in ("Authorization", "Bearer ", "ORDIVON_BEARER_TOKEN", "\\Users\\", "/root/"):
        if forbidden in encoded:
            errors.append(f"result contains forbidden private material: {forbidden!r}")
    return errors


def validate_probe_result(result: dict[str, Any], *, expected_operation_id: str | None = None) -> list[str]:
    return validate_result(result, expected_operation_id=expected_operation_id)


def read_result(
    *, control_directory: Path | None = None, expected_operation_id: str | None = None
) -> dict[str, Any]:
    control = control_directory or discover_resolve_paths().control_directory
    path = control / RESULT_FILENAME
    if not path.is_file():
        raise FileNotFoundError(path)
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError("Resolve result root must be an object")
    errors = validate_result(value, expected_operation_id=expected_operation_id)
    if errors:
        raise ValueError("; ".join(errors))
    return value
