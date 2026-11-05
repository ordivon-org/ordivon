"""Resolve-private OpenTimelineIO conform and selected-asset binding.

Consumes source-owned Production/Asset records and preserves the selected
media bytes' digest. Not a general timeline validator or NLE runtime.
"""

from __future__ import annotations

import json
import re
import urllib.parse
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import opentimelineio as otio

from .assets import hash_file
from .resolve_contracts import COMPATIBILITY_VERSION_STRING

ASSEMBLY_PROJECT_NAME = "Ordivon Runtime Introduction"
ASSEMBLY_TIMELINE_NAME = "Assembly v0"
_SEGMENT_ID = re.compile(r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$")
_SELECTED_DIGEST = re.compile(r"^sha256:[a-f0-9]{64}$")


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {path.name}")
    return value


def _windows_file_uri(path: str) -> str:
    normalized = path.replace("\\", "/")
    if len(normalized) < 3 or normalized[1] != ":" or normalized[2] != "/":
        raise ValueError("expected an absolute Windows drive path")
    return "file:///" + urllib.parse.quote(normalized, safe="/:")


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


def _build_assembly_source_parameters(
    *,
    production_root: Path,
    media_root: Path,
    windows_media_root: str,
) -> dict[str, Any]:
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
        if not isinstance(segment_id, str) or not _SEGMENT_ID.fullmatch(segment_id):
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
        if not isinstance(digest, str) or not _SELECTED_DIGEST.fullmatch(digest):
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
        if hash_file(local_path).digest != digest:
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
        "productionId": production_id,
        "projectName": ASSEMBLY_PROJECT_NAME,
        "timelineName": ASSEMBLY_TIMELINE_NAME,
        "startTimecode": start_timecode,
        "settings": {"frameRate": 30, "width": 1920, "height": 1080},
        "totalFrames": cursor,
        "sourceDigests": {
            "production": hash_file(production_path).digest,
            "assets": hash_file(assets_path).digest,
            "timeline": hash_file(otio_path).digest,
        },
        "segments": segments,
        "restorePreviousProject": True,
    }
