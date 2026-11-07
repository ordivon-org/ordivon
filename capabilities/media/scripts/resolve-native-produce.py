#!/usr/bin/env python3
"""Native Resolve visual cut or OTIO import, CDL grade, optional audio and MP4/DRP."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import time
import uuid
from pathlib import Path


def digest(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            sha.update(chunk)
    return "sha256:" + sha.hexdigest()


def checked(value: object, operation: str):
    if value is None or value is False or value == []:
        raise RuntimeError("Resolve failed: " + operation)
    return value


def connect():
    api = os.environ.get("RESOLVE_SCRIPT_API", r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting")
    os.environ.setdefault("RESOLVE_SCRIPT_LIB", r"C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll")
    sys.path.insert(0, str(Path(api) / "Modules"))
    import DaVinciResolveScript as dvr
    for _ in range(12):
        instance = dvr.scriptapp("Resolve")
        if instance:
            return instance
        time.sleep(2)
    raise RuntimeError("Resolve not accepting scripts in this Windows session")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    editorial = ap.add_mutually_exclusive_group(required=True)
    editorial.add_argument("--visual", action="append", help="Still or video path; repeat for consecutive clips")
    editorial.add_argument("--otio", help="Existing OTIO editorial timeline; referenced media must be available")
    ap.add_argument("--source-clips-dir", help="Optional native Resolve media relink directory for OTIO")
    ap.add_argument("--audio", help="Optional separate audio track")
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--name", default="ordivon-native")
    ap.add_argument("--width", type=int, default=1920)
    ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--fps", type=int, default=24)
    ap.add_argument("--grade-saturation", type=float)
    ap.add_argument("--grade-slope", help="ASC CDL R,G,B slope; comma-separated")
    ap.add_argument("--grade-offset", help="ASC CDL R,G,B offset; comma-separated")
    ap.add_argument("--grade-power", help="ASC CDL R,G,B power; comma-separated")
    ap.add_argument("--timeout", type=int, default=180)
    ap.add_argument("--min-timeline-frames", type=int, default=1, help="Consumer-selected minimum timeline length")
    ap.add_argument("--keep-project", action="store_true")
    args = ap.parse_args()
    if min(args.width, args.height, args.fps, args.timeout, args.min_timeline_frames) <= 0:
        ap.error("width, height, fps, timeout and min-timeline-frames must be positive")
    if args.grade_saturation is not None and (
            not math.isfinite(args.grade_saturation) or not 0 <= args.grade_saturation <= 4):
        ap.error("grade-saturation must be finite and 0..4")
    grade_requested = any(value is not None for value in (
        args.grade_saturation, args.grade_slope, args.grade_offset, args.grade_power))
    def parse_rgb(value: str | None, default: tuple[float, float, float], label: str):
        if value is None:
            return default
        try:
            rgb = tuple(float(piece) for piece in value.split(","))
        except ValueError:
            ap.error(label + " must contain exactly three numeric components")
        if len(rgb) != 3 or not all(math.isfinite(component) for component in rgb):
            ap.error(label + " must contain exactly three finite numeric components")
        return rgb
    grade = {
        "NodeIndex": "1",
        "Slope": " ".join(map(str, parse_rgb(args.grade_slope, (1.0, 1.0, 1.0), "--grade-slope"))),
        "Offset": " ".join(map(str, parse_rgb(args.grade_offset, (0.0, 0.0, 0.0), "--grade-offset"))),
        "Power": " ".join(map(str, parse_rgb(args.grade_power, (1.0, 1.0, 1.0), "--grade-power"))),
        "Saturation": str(args.grade_saturation if args.grade_saturation is not None else 1.0),
    } if grade_requested else None
    if not args.name or any(c in args.name for c in '<>:"/\\|?*'):
        ap.error("invalid output name")
    inputs = [Path(p).resolve() for p in (args.visual or [])]
    otio = Path(args.otio).resolve() if args.otio else None
    source_clips_dir = Path(args.source_clips_dir).resolve() if args.source_clips_dir else None
    audio = Path(args.audio).resolve() if args.audio else None
    if source_clips_dir and (not otio or not source_clips_dir.is_dir()):
        ap.error("source-clips-dir requires OTIO and an existing directory")
    for p in inputs + ([otio] if otio else []) + ([audio] if audio else []):
        if not p.is_file():
            ap.error("input not found: " + str(p))
    output = Path(args.output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    mp4 = output / (args.name + ".mp4")
    drp = output / (args.name + ".drp")
    receipt_path = output / (args.name + ".receipt.json")
    if any(p.exists() for p in (mp4, drp, receipt_path)):
        ap.error("output exists; choose a unique name")
    resolve = connect()
    manager = checked(resolve.GetProjectManager(), "GetProjectManager")
    project_name = "Ordivon_Native_" + uuid.uuid4().hex[:16]
    project = checked(manager.CreateProject(project_name), "CreateProject")
    job = None
    try:
        for key, val in (
            ("timelineResolutionWidth", str(args.width)),
            ("timelineResolutionHeight", str(args.height)),
            ("timelineFrameRate", str(args.fps)),
        ):
            checked(project.SetSetting(key, val), "SetSetting " + key)
        pool = checked(project.GetMediaPool(), "GetMediaPool")
        if otio:
            options = {"timelineName": args.name, "importSourceClips": True}
            if source_clips_dir:
                options["sourceClipsPath"] = str(source_clips_dir)
            timeline = checked(pool.ImportTimelineFromFile(str(otio), options), "ImportTimelineFromFile OTIO")
        else:
            visual_items = checked(pool.ImportMedia([str(p) for p in inputs]), "ImportMedia visuals")
            if len(visual_items) != len(inputs):
                raise RuntimeError("partial visual media import")
            timeline = checked(pool.CreateEmptyTimeline(args.name), "CreateEmptyTimeline")
            checked(project.SetCurrentTimeline(timeline), "SetCurrentTimeline")
            checked(pool.AppendToTimeline(visual_items), "AppendToTimeline visual")
        checked(project.SetCurrentTimeline(timeline), "SetCurrentTimeline")
        if audio:
            audio_items = checked(pool.ImportMedia([str(audio)]), "ImportMedia audio")
            if len(audio_items) != 1:
                raise RuntimeError("partial audio media import")
            audio_item = audio_items[0]
            audio_info = audio_item.GetClipProperty()
            value = str(audio_info.get("Frames") or "").replace(",", "")
            if value.isdigit():
                audio_frames = int(value)
            else:
                parts = str(audio_info.get("Duration") or "").replace(";", ":").split(":")
                if len(parts) != 4 or not all(x.isdigit() for x in parts):
                    raise RuntimeError("Resolve did not report audio clip duration")
                h, m, s, f = map(int, parts)
                audio_frames = (h * 3600 + m * 60 + s) * args.fps + f
            if audio_frames <= 0:
                raise RuntimeError("Resolve reported zero-length audio")
            start = int(timeline.GetStartFrame())
            checked(pool.AppendToTimeline([{
                "mediaPoolItem": audio_item, "startFrame": 0,
                "endFrame": audio_frames - 1, "mediaType": 2,
                "trackIndex": 1, "recordFrame": start,
            }]), "AppendToTimeline audio at timeline start")
        clips = [
            clip
            for track in range(1, timeline.GetTrackCount("video") + 1)
            for clip in timeline.GetItemListInTrack("video", track)
        ]
        timeline_frames = int(timeline.GetEndFrame()) - int(timeline.GetStartFrame())
        if (not clips or (inputs and len(clips) < len(inputs))
                or (audio and not timeline.GetItemListInTrack("audio", 1))
                or timeline_frames < args.min_timeline_frames):
            raise RuntimeError("timeline readback failed: missing clips or insufficient frames")
        if grade is not None:
            for clip in clips:
                checked(clip.SetCDL(grade), "SetCDL")
        timeline_media = []
        for track_kind in ("video", "audio"):
            for track_number in range(1, timeline.GetTrackCount(track_kind) + 1):
                for item in timeline.GetItemListInTrack(track_kind, track_number) or []:
                    media_pool_item = item.GetMediaPoolItem()
                    properties = media_pool_item.GetClipProperty() if media_pool_item else None
                    source_path = properties.get("File Path") if isinstance(properties, dict) else None
                    linked_file = Path(source_path) if isinstance(source_path, str) and source_path else None
                    verified = bool(linked_file and linked_file.is_file())
                    timeline_media.append({
                        "trackType": track_kind,
                        "trackIndex": track_number,
                        "clipName": item.GetName(),
                        "sourcePath": source_path,
                        "sourceDigest": digest(linked_file) if verified else None,
                        "physicalReadback": "VERIFIED" if verified else "UNKNOWN",
                    })
        checked(manager.SaveProject(), "SaveProject")
        checked(manager.ExportProject(project_name, str(drp)), "ExportProject")
        codec = project.GetRenderCodecs("mp4").get("H.264")
        checked(codec, "discover native H.264 codec")
        checked(project.SetCurrentRenderFormatAndCodec("mp4", codec), "SetCurrentRenderFormatAndCodec")
        checked(project.SetCurrentRenderMode(1), "SetCurrentRenderMode")
        settings = {
            "TargetDir": str(output), "CustomName": args.name,
            "ExportVideo": True, "ExportAudio": True,
            "SelectAllFrames": True,
        }
        checked(project.SetRenderSettings(settings), "SetRenderSettings")
        job = checked(project.AddRenderJob(), "AddRenderJob")
        checked(project.StartRendering([job]), "StartRendering")
        deadline = time.monotonic() + args.timeout
        while time.monotonic() < deadline:
            state = project.GetRenderJobStatus(job)
            status = state.get("JobStatus") if isinstance(state, dict) else None
            if status in ("Complete", "Completed"):
                break
            if status in ("Failed", "Cancelled"):
                raise RuntimeError("Resolve render status: " + repr(state))
            if (isinstance(state, dict) and
                    state.get("CompletionPercentage") == 100 and
                    not project.IsRenderingInProgress()):
                print("RENDER_FINAL_STATE", state, flush=True)
                break
            if int(args.timeout - (deadline - time.monotonic())) % 10 < 2:
                print("RENDER_PROGRESS", state, flush=True)
            time.sleep(2)
        else:
            raise TimeoutError("Resolve render timeout")
        if not mp4.is_file() or mp4.stat().st_size < 1024:
            raise RuntimeError("MP4 output not found or empty")
        reimported = checked(pool.ImportMedia([str(mp4)]), "re-import rendered MP4 for native readback")
        output_properties = reimported[0].GetClipProperty()
        if not isinstance(output_properties, dict):
            raise TypeError("Resolve rendered-media properties unavailable")
        receipt = {
            "schemaVersion": 1,
            "kind": "ordivon.media.resolve-native-production-receipt",
            "nativeRenderedMediaReadback": {
                key: output_properties.get(key) for key in
                ("Format", "Video Codec", "Audio Codec", "Resolution", "FPS", "Duration")
            },
            "nativeRenderJobStatus": state,
            "resolveVersion": resolve.GetVersionString(),
            "project": project_name,
            "timeline": timeline.GetName(),
            "videoClipCount": len(clips),
            "timelineFrames": timeline_frames,
            "requestedMinimumTimelineFrames": args.min_timeline_frames,
            "editorialFormat": "otio" if otio else "native-consecutive-visuals",
            "otioMediaReferencesIndependentlyVerified": False if otio else None,
            "sourceClipsDirectory": str(source_clips_dir) if source_clips_dir else None,
            "audioTrackCount": timeline.GetTrackCount("audio"),
            "gradeSaturation": args.grade_saturation,
            "gradeCDL": grade,
            "nativeTimelineMediaReadback": timeline_media,
            "nativeTimelineMediaReadbackComplete": bool(timeline_media) and all(
                item["physicalReadback"] == "VERIFIED" for item in timeline_media),
            "sources": [{"path": str(p), "digest": digest(p)}
                        for p in inputs + ([otio] if otio else []) + ([audio] if audio else [])],
            "deliverables": [{"path": str(p), "digest": digest(p), "size": p.stat().st_size}
                             for p in (mp4, drp)],
        }
        receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(receipt, ensure_ascii=False), flush=True)
        return 0
    finally:
        if job is not None:
            if project.IsRenderingInProgress():
                project.StopRendering()
            project.DeleteRenderJob(job)
        if not args.keep_project:
            manager.CloseProject(project)
            manager.DeleteProject(project_name)


if __name__ == "__main__":
    raise SystemExit(main())
